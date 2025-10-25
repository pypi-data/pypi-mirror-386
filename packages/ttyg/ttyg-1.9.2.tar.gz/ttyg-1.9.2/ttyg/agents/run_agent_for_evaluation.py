import time
from typing import Any

from langchain_core.messages import AIMessage, ToolMessage, ToolCall
from langchain_core.messages.ai import UsageMetadata
from langgraph.graph.state import CompiledStateGraph


def run_agent_for_evaluation(
        agent: CompiledStateGraph,
        question_id: str,
        input_: dict[str, Any] | Any,
) -> dict[str, Any]:
    """
    Runs an agent over a given question and returns the output as expected by the evaluation library https://github.com/Ontotext-AD/graphrag-eval.
    :param agent: the agent
    :type agent: CompiledStateGraph
    :param question_id: the unique question id for tracing purposes
    :type question_id: str
    :param input_: the input (question) passed to the agent
    :type input_: dict[str, Any] | Any
    :return: check https://github.com/Ontotext-AD/graphrag-eval documentation for the expected keys in the result
    :rtype: dict[str, Any]
    """
    try:
        sum_input_tokens, sum_output_tokens, sum_total_tokens = 0, 0, 0
        tools_calls, tools_outputs = [], dict()

        start = time.time()
        output = agent.invoke(input_)
        elapsed_sec = time.time() - start

        for message in output["messages"]:
            if isinstance(message, AIMessage):
                tool_calls: list[ToolCall] = message.tool_calls
                for tool_call in tool_calls:
                    tools_calls.append({
                        "name": tool_call["name"],
                        "args": tool_call["args"],
                        "id": tool_call["id"],
                    })
                usage_metadata: UsageMetadata = message.usage_metadata
                sum_input_tokens += usage_metadata["input_tokens"]
                sum_output_tokens += usage_metadata["output_tokens"]
                sum_total_tokens += usage_metadata["total_tokens"]
            elif isinstance(message, ToolMessage):
                tools_outputs[message.tool_call_id] = {
                    "status": message.status,
                    "output": message.content
                }

        for tool_call in tools_calls:
            tool_call.update(tools_outputs[tool_call["id"]])

        return {
            "question_id": question_id,
            "input_tokens": sum_input_tokens,
            "output_tokens": sum_output_tokens,
            "total_tokens": sum_total_tokens,
            "elapsed_sec": elapsed_sec,
            "actual_steps": tools_calls,
            "actual_answer": output["messages"][-1].content
        }
    except Exception as e:
        return {
            "question_id": question_id,
            "error": str(e),
            "status": "error",
        }
