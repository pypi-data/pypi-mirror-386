from typing import Awaitable, Callable, Optional, cast

from langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse
from langchain.agents.middleware.types import ModelCallResult
from langchain_core.messages import AnyMessage, SystemMessage
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

from langchain_dev_utils.chat_models import load_chat_model
from langchain_dev_utils.message_convert import format_sequence


class ModelDict(TypedDict):
    model_name: str
    model_description: str


class SelectModel(BaseModel):
    """Tool for model selection - Must call this tool to return the finally selected model"""

    model_name: str = Field(
        ...,
        description="Selected model name (must be the full model name, for example, openai:gpt-4o)",
    )


_ROUTER_MODEL_PROMPT = """
# Role Description
You are an intelligent routing model, specializing in analyzing task requirements and matching appropriate AI models.

# Available Model List
{model_card}

# Core Responsibilities
1. **Task Analysis**: Deeply understand the type, complexity, and special needs of the user's task
2. **Model Matching**: Select the most appropriate model based on the task characteristics
3. **Tool Call**: **Must call SelectModel tool** to return the final selection

# ⚠️ Important Instructions
**After completing the analysis, you must immediately call the SelectModel tool to return the model selection result.**
**This is the only way to output, and you are forbidden to return the result in any other form.**

# Selection Standards
- Consider the type of the task (dialogue, inference, creation, analysis, etc.)
- Evaluate the complexity of the task
- Match the professional ability and applicable scenario of the model
- Ensure that the model's ability matches the task requirements to a high degree

# Execution Process
1. Analyze user task requirements
2. Compare the capabilities of available models
3. Call **SelectModel tool** to submit selection
4. Task completion

Strictly adhere to tool call requirements!
"""


class ModelRouterMiddleware(AgentMiddleware):
    """Model routing middleware that automatically selects the most suitable model based on input content.

    Args:
        router_model: Model identifier used for routing selection
        model_list: List of available routing models, each containing name and description
        router_prompt: Routing prompt template, uses default template if None

    Examples:
        ```python
        from langchain_dev_utils.agents.middleware import ModelRouterMiddleware

        model_list = [
            {
                "model_name": "vllm:qwen3-8b",
                "model_description": "Suitable for general conversation and text generation tasks"
            },
            {
                "model_name": "openrouter:qwen/qwen3-vl-32b-instruct",
                "model_description": "For visual tasks"
            },
            {
                "model_name": "openrouter:qwen/qwen3-coder-plus",
                "model_description": "For code generation tasks"
            }
        ]

        middleware = ModelRouterMiddleware(
            router_model="vllm:qwen3-4b",
            model_list=model_list
        )
        ```
    """

    def __init__(
        self,
        router_model: str,
        model_list: list[ModelDict],
        router_prompt: Optional[str] = None,
    ) -> None:
        super().__init__()
        self.router_model = load_chat_model(router_model).with_structured_output(
            SelectModel
        )
        self.model_list = model_list

        if router_prompt is None:
            router_prompt = _ROUTER_MODEL_PROMPT.format(
                model_card=format_sequence(
                    [
                        f"model_name:\n {model['model_name']}\n model_description:\n {model['model_description']}"
                        for model in model_list
                    ],
                    with_num=True,
                )
            )

        self.router_prompt = router_prompt

    def _select_model(self, messages: list[AnyMessage]):
        try:
            response = cast(
                SelectModel,
                self.router_model.invoke(
                    [SystemMessage(content=self.router_prompt), *messages]
                ),
            )
        except Exception:
            return None
        if response is None:
            return None
        return response.model_name

    async def _aselect_model(self, messages: list[AnyMessage]):
        try:
            response = cast(
                SelectModel,
                await self.router_model.ainvoke(
                    [SystemMessage(content=self.router_prompt), *messages]
                ),
            )
        except Exception:
            return None
        if response is None:
            return None
        return response.model_name

    def wrap_model_call(
        self, request: ModelRequest, handler: Callable[[ModelRequest], ModelResponse]
    ) -> ModelCallResult:
        model_name = self._select_model(request.messages)
        if model_name is not None:
            request.model = load_chat_model(model_name)

        return handler(request)

    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], Awaitable[ModelResponse]],
    ) -> ModelCallResult:
        model_name = await self._aselect_model(request.messages)
        if model_name is not None:
            request.model = load_chat_model(model_name)

        return await handler(request)
