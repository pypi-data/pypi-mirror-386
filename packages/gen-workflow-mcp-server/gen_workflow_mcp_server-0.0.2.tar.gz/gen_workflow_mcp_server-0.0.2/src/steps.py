from agno.agent import Agent
from agno.workflow.types import StepInput, StepOutput

from .constant import model, model_pro
from .file.reader import gather_files, generate_output, get_root_dir
from .file.writer import remove_path, write_agent_files, write_workflow_files
from .model import PathOutput
from .prompt import prompt_for_chart, prompt_for_spec

# -> { query: str, out_directory: str }
path_agent = Agent(
    name="path_agent",
    instructions="extract values from prompt into query and out_directory",
    output_schema=PathOutput,
    model=model,
)

chart_agent = Agent(
    name="chart_agent", instructions="Extract chart as text", model=model_pro
)

generate_context_agent = Agent(
    name="generate_context_agent",
    instructions="Generate text based on context",
    model=model_pro,
)


def start(step_input: StepInput, session_state) -> StepOutput:
    """Initialize session_state"""
    session_state["step_1"] = "/base"
    session_state["step_2"] = """
        Please generate agent & workflow with instructions if it is nessasary according to the following rules:
        ```
        - agent_names: Use file name including *_agent
        - agent_codes: Use code variables, functions, ex> *_agent=Agent(...)
        - workflow_names: Use file name including *_workflow
        - workflow_codes: Use code variables, functions, ex> *_workflow=Workflow(...)
        ```
    """

    prev_output = step_input.previous_step_content
    if not prev_output:
        return StepOutput(content="fail to setting up", success=False)

    query = getattr(prev_output, "query", None)
    out_directory = getattr(prev_output, "out_directory", None)
    session_state["query"] = query or ""
    session_state["absolute_out_dir"] = out_directory or "C:\\Users\\k0108\\Downloads"
    session_state["step_3"] = (
        f"Create sub agents and workflows, directory: {out_directory}"
    )

    return StepOutput(content="All steps are ready", success=True)


def context_provider(_: StepInput, session_state) -> StepOutput:
    """Prepare and provide context for downstream agents.

    Ensure the session_state contains required keys used by later steps (for example
    "step_1", "step_2", "step_3", and "query"). Build the prompt for the chart agent
    from session_state["query"], call the chart agent asynchronously to obtain a
    chart description, then call the code agent to convert that chart into a final
    specification. Return the agent-produced specification wrapped in a StepOutput.

    Parameters:
        _ (StepInput): unused; the function reads context from session_state.
        session_state (dict): mutable mapping holding per-session state and the user query.

    Returns:
        StepOutput: result produced by the code agent (specification content and status).

    Side effects:
        - May mutate session_state in-place to populate or normalize keys.
        - May propagate exceptions from agent calls.
    """
    chart = (chart_agent.run(prompt_for_chart(session_state["query"]))).content

    absolute_out_dir = session_state["absolute_out_dir"]
    absolute_out_dir = get_root_dir(f"{absolute_out_dir}\\out")
    remove_path(absolute_out_dir)
    with open(f"{absolute_out_dir}\\flow.mmd", "w", encoding="utf-8") as f:
        if chart:
            f.write(chart)

    return StepOutput(
        content=(generate_context_agent.run(prompt_for_spec(chart or "")).content)
    )


def generate_codes(step_input: StepInput, session_state) -> StepOutput:
    directory = session_state["step_1"]
    files = gather_files(directory)
    file_content = ""

    for d in files:
        with open(f"{get_root_dir(directory)}/{d}") as f:
            for line in f.readlines():
                if not line or line == "":
                    continue

                file_content += line

    query = f"{file_content}\n{step_input.previous_step_content}"
    return StepOutput(content=generate_output(query, session_state["step_2"]))


writer_agent = Agent(
    name="WriterAgent",
    model=model,
    instructions=[
        "you are a writer, extract code only from context",
        "then run {step_3}",
    ],
    tool_call_limit=3,
    tools=[write_agent_files, write_workflow_files],
)
