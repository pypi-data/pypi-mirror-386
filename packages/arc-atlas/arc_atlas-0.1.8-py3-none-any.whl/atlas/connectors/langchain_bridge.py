"""Bridge between Atlas BYOA adapters and LangChain chat models."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

import os

os.environ.setdefault("TRANSFORMERS_NO_TORCH", "1")

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.messages import BaseMessage
from langchain_core.messages import ToolMessage
from langchain_core.messages.tool import ToolCall
from langchain_core.outputs import ChatGeneration
from langchain_core.outputs import ChatResult
from langchain_core.tools import BaseTool
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, ConfigDict, Field, create_model
from langchain_core.callbacks.manager import AsyncCallbackManagerForLLMRun, CallbackManagerForLLMRun

from atlas.connectors.registry import AgentAdapter
from atlas.connectors.utils import normalise_usage_payload
from atlas.config.models import ToolDefinition

logger = logging.getLogger(__name__)

def _python_type_for_schema(schema_entry: Dict[str, Any]):
    type_name = schema_entry.get("type")
    if type_name == "string":
        return str
    if type_name == "integer":
        return int
    if type_name == "number":
        return float
    if type_name == "boolean":
        return bool
    if type_name == "array":
        return List[Any]
    if type_name == "object":
        return Dict[str, Any]
    return Any

def _build_args_model(tool: ToolDefinition) -> type[BaseModel]:
    fields: Dict[str, Tuple[Any, Any]] = {}
    required = set(tool.parameters.required)
    for name, entry in tool.parameters.properties.items():
        field_type = _python_type_for_schema(entry)
        description = entry.get("description")
        if name in required:
            default_value = ...
        else:
            default_value = entry.get("default")
            field_type = Optional[field_type]
        field_kwargs = {"description": description} if description else {}
        fields[name] = (field_type, Field(default=default_value, **field_kwargs))
    model_name = f"{tool.name.title().replace(' ', '')}Args"
    model_config = ConfigDict(extra="forbid")
    return create_model(model_name, __config__=model_config, **fields)  # type: ignore[call-overload]

def _build_tool(adapter: AgentAdapter, tool: ToolDefinition) -> BaseTool:
    args_model = _build_args_model(tool)

    def _sync_tool(**kwargs):
        payload = {"tool": {"name": tool.name, "arguments": kwargs}}
        return adapter.execute(json.dumps(payload), metadata=payload)

    async def _async_tool(**kwargs):
        payload = {"tool": {"name": tool.name, "arguments": kwargs}}
        return await adapter.ainvoke(json.dumps(payload), metadata=payload)

    return StructuredTool.from_function(
        func=_sync_tool,
        coroutine=_async_tool,
        name=tool.name,
        description=tool.description,
        args_schema=args_model,
    )

def _summarize_tool(tool: ToolDefinition) -> Dict[str, Any]:
    return {
        "name": tool.name,
        "description": tool.description,
        "parameters": tool.parameters.model_dump(by_alias=True),
        "output_schema": tool.output_schema,
    }

class BYOABridgeLLM(BaseChatModel):
    """LangChain chat model that proxies requests through an Atlas adapter."""

    def __init__(self, adapter: AgentAdapter, tool_definitions: Sequence[ToolDefinition]):
        super().__init__()
        self._adapter = adapter
        self._tool_definitions = list(tool_definitions)
        self._tool_metadata = [_summarize_tool(tool) for tool in tool_definitions]
        self._bound_tools: List[BaseTool] = []
    @property
    def _llm_type(self) -> str:
        return "atlas-byoa-bridge"
    def bind_tools(
        self,
        tools: Sequence[dict[str, Any] | type | Callable[..., Any] | BaseTool],
        *,
        tool_choice: str | None = None,
        **kwargs: Any,
    ) -> "BYOABridgeLLM":
        del tool_choice, kwargs
        bound_tools = [tool for tool in tools if isinstance(tool, BaseTool)]
        clone = BYOABridgeLLM(self._adapter, self._tool_definitions)
        clone._bound_tools = bound_tools
        return clone
    def _serialize_message(self, message: BaseMessage) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"type": message.type}
        content = message.content
        if isinstance(content, list):
            payload["content"] = content
        else:
            payload["content"] = str(content)
        if isinstance(message, AIMessage) and message.tool_calls:
            payload["tool_calls"] = [
                {
                    "name": call["name"],
                    "args": call.get("args", {}),
                    "id": call.get("id"),
                }
                for call in message.tool_calls
            ]
        if isinstance(message, ToolMessage):
            payload["tool_call_id"] = message.tool_call_id
            payload["status"] = message.status
        return payload
    def _render_prompt(self, messages: Sequence[BaseMessage]) -> str:
        parts = []
        for message in messages:
            content = message.content
            if isinstance(content, list):
                content = json.dumps(content)
            parts.append(f"{message.type.upper()}: {content}")
        return "\n\n".join(parts)
    def _parse_response(self, response: Any) -> Tuple[str, List[ToolCall], Optional[Dict[str, Any]]]:
        original_response = response
        if isinstance(response, str):
            if hasattr(response, "tool_calls") or hasattr(response, "usage"):
                parsed = {"content": str(response)}
                tool_calls_attr = getattr(response, "tool_calls", None)
                if tool_calls_attr:
                    parsed["tool_calls"] = tool_calls_attr
                usage_attr = getattr(response, "usage", None)
                if usage_attr is not None:
                    parsed["usage"] = usage_attr
            else:
                try:
                    parsed = json.loads(response)
                except json.JSONDecodeError:
                    return response, [], None
        else:
            parsed = response
        if not isinstance(parsed, dict) and hasattr(parsed, "model_dump"):
            try:
                candidate = parsed.model_dump()
                if isinstance(candidate, dict):
                    parsed = candidate
            except Exception:
                pass
        if not isinstance(parsed, dict):
            raw_usage = getattr(parsed, "usage", None)
            return str(parsed), [], normalise_usage_payload(raw_usage)
        content = parsed.get("content")
        raw_calls_obj: Any = parsed.get("tool_calls", [])
        raw_calls: list[dict[str, Any]] = []
        if isinstance(raw_calls_obj, list):
            raw_calls = [item for item in raw_calls_obj if isinstance(item, dict)]
        usage_payload = normalise_usage_payload(parsed.get("usage"))
        tool_calls: List[ToolCall] = []
        for index, item in enumerate(raw_calls):
            name = item.get("name")
            if not name:
                continue
            args = item.get("arguments") or item.get("args") or {}
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    args = {"raw": args}
            args_dict = args if isinstance(args, dict) else {"raw": args}
            identifier = item.get("id")
            if not isinstance(identifier, str):
                identifier = f"{name}-{index}"
            tool_call: ToolCall = {"name": str(name), "args": args_dict, "id": identifier}
            tool_calls.append(tool_call)

        # If content is missing, preserve the original response so Student._normalise_executor_message can parse it
        if content is None and not tool_calls:
            if isinstance(original_response, str):
                content = original_response
            else:
                content = json.dumps(parsed, ensure_ascii=False)

        return str(content or ""), tool_calls, usage_payload
    def _to_chat_result(self, content: str, tool_calls: List[ToolCall], usage: Optional[Dict[str, Any]]) -> ChatResult:
        additional_kwargs = {"usage": usage} if usage else {}
        message = AIMessage(content=content, tool_calls=tool_calls, additional_kwargs=additional_kwargs)
        generation = ChatGeneration(message=message)
        return ChatResult(generations=[generation])
    async def _agenerate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: AsyncCallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        del run_manager, kwargs
        prompt = self._render_prompt(messages)
        response = await self._adapter.ainvoke(prompt)
        content, tool_calls, usage = self._parse_response(response)
        return self._to_chat_result(content, tool_calls, usage)
    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        del run_manager
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self._agenerate(messages, stop=stop, **kwargs))
        raise RuntimeError("synchronous generation is not available inside an event loop")
    @property
    def bound_tools(self) -> List[BaseTool]:
        if self._bound_tools:
            return self._bound_tools
        return [_build_tool(self._adapter, tool) for tool in self._tool_definitions]

def build_bridge(adapter: AgentAdapter, tool_definitions: Sequence[ToolDefinition]) -> Tuple[BYOABridgeLLM, List[BaseTool]]:
    base_llm = BYOABridgeLLM(adapter, tool_definitions)
    tools = base_llm.bound_tools
    bridged_llm = base_llm.bind_tools(tools)
    return bridged_llm, list(tools)

__all__ = ["BYOABridgeLLM", "build_bridge"]
