from typing import Union

from langchain_core.messages import AIMessage


def has_tool_calling(message: AIMessage) -> bool:
    """Check if a message contains tool calls.

    This function determines whether an AI message contains tool calls,
    which is useful for routing messages to appropriate handlers.

    Args:
        message: Any message type to check for tool calls

    Returns:
        bool: True if message is an AIMessage with tool calls, False otherwise

    Example:
        Check for tool calls in response:
        >>> from langchain_dev_utils.tool_calling import has_tool_calling, parse_tool_calling
        >>> response = model.invoke("What time is it now?")
        >>> if has_tool_calling(response):
        ...     print("Tool calls found in response")
    """
    if (
        isinstance(message, AIMessage)
        and hasattr(message, "tool_calls")
        and len(message.tool_calls) > 0
    ):
        return True
    return False


def parse_tool_calling(
    message: AIMessage, first_tool_call_only: bool = False
) -> Union[tuple[str, dict], list[tuple[str, dict]]]:
    """Parse a tool call from a message.

    This function extracts tool call information from an AI message, returning
    either the first tool call or all tool calls depending on the parameter.

    Args:
        message: Any message type to parse for tool calls
        first_tool_call_only: If True, only the first tool call will be parsed

    Returns:
        Union[tuple[str, dict], list[tuple[str, dict]]]: The tool call name and args

    Example:
        Parse single tool call:
        >>> from langchain_dev_utils.tool_calling import has_tool_calling, parse_tool_calling
        >>> response = model.invoke("What time is it now?")
        >>> response
        >>> if has_tool_calling(response):
        ...     tool_name, tool_args = parse_tool_calling(response, first_tool_call_only=True)

        Parse multiple tool calls:
        >>> if has_tool_calling(response):
        ...     tool_calls = parse_tool_calling(response)
    """

    if first_tool_call_only:
        return (message.tool_calls[0]["name"], message.tool_calls[0]["args"])
    return [(tool_call["name"], tool_call["args"]) for tool_call in message.tool_calls]
