from agno.run.workflow import WorkflowRunEvent
from agno.workflow import Condition, Loop, Step, Workflow
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from src.conditional import condition_quality_checker, is_okay
from src.constant import db
from src.steps import context_provider, generate_codes, path_agent, start, writer_agent

mcp = FastMCP("agent_generater")

_prompt = """
I'm planning multi-agents for analyzing mathematics exams score for students'.\n
My agent's candidates are reader, analyzer, reviewer, feedbacker, summarizer.\n
Could you outline their roles and their interaction relationships in a diagram or text?
"""


@mcp.tool()
async def generate_workflow(prompt: str):
    """
    Generate multi-agents and workflows based on user prompt
    """
    load_dotenv()

    main_workflow = Workflow(
        name="MainWorkflow",
        db=db,
        session_state={},
        steps=[
            Step(name="query_evaluater", agent=path_agent),
            Step(name="start", executor=start),  # type: ignore
            Condition(
                name="is_okay",
                evaluator=is_okay,
                steps=[
                    Step(name="context_provider", executor=context_provider),  # type: ignore
                    Loop(
                        name="generate_codes_loop",
                        steps=[Step("generate_codes", executor=generate_codes)],  # type: ignore
                        end_condition=condition_quality_checker,  # type: ignore
                        max_iterations=3,
                    ),
                    Step("write_files", agent=writer_agent),
                ],
            ),
        ],
    )

    # await main_workflow.aprint_response(prompt, stream=True)

    resp = await main_workflow.arun(prompt, stream=True)

    async for event in resp:
        if event.event == WorkflowRunEvent.condition_execution_started.value:
            yield event.to_json()
        elif event.event == WorkflowRunEvent.condition_execution_completed.value:
            yield event.to_json()
        elif event.event == WorkflowRunEvent.workflow_started.value:
            yield event.to_json()
        elif event.event == WorkflowRunEvent.step_started.value:
            yield event.to_json()
        elif event.event == WorkflowRunEvent.step_completed.value:
            yield event.to_json()
        elif event.event == WorkflowRunEvent.workflow_completed.value:
            yield event.to_json()


def main():
    print("running")
    mcp.run(transport="stdio")

    # import asyncio

    # asyncio.run(generate_workflow(_prompt))


if __name__ == "__main__":
    main()
