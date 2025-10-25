import asyncio
import os
import shutil

from agno.tools import tool


async def __write_files(data: list[tuple[str, str]], templates: dict, files: list[str]):
    def write_file(dir_path: str, file_name: str, content: str) -> None:
        fp = os.path.join(dir_path, file_name)
        with open(fp, "w", encoding="utf-8") as f:
            f.write(content)

    write_tasks = []
    for p, c in data:
        os.makedirs(p, exist_ok=True)
        for fname in files:
            content = templates.get(fname, "")

            if fname.endswith(".py"):
                if fname == "agent.py" or fname == "workflow.py":
                    content = f"{content}\n{c}"

            write_tasks.append(asyncio.to_thread(write_file, p, fname, content))

    await asyncio.gather(*write_tasks)
    await asyncio.gather(
        *(asyncio.to_thread(os.makedirs, p, exist_ok=True) for (p, _) in data)
    )


def remove_path(path: str):
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path, exist_ok=True)


def __generate_data(children, path):
    remove_path(path)

    def mapper(x: tuple[str, str]):
        return (f"{path}/{x[0]}", x[1])

    data = list(map(mapper, children))
    return data


@tool(stop_after_tool_call=True)
async def write_agent_files(
    session_state, agent_names: list[str], agent_codes: list[str]
):
    """
    Creates sub-agent directories and writes agent files using the provided names and codes.

    Args:
        agent_names (list[str]): A list of agent names.
        agent_codes (list[str]): A list of agent code snippets corresponding to the agent names.
        absolute_out_dir (str) : path for output
    """
    absolute_out_dir = session_state["absolute_out_dir"]
    children = list(zip(agent_names, agent_codes))
    sub_agent_path = f"{absolute_out_dir}/sub_agents"
    templates = {
        "agent.py": "from agno.agent import Agent\n",
        "constant.py": 'from textwrap import dedent\n\nDB = None\nMODEL = None\nPROMPT = dedent("""""")',
        "tools.py": "from agno.tools import tool\n",
    }
    filees = ["agent.py", "constant.py", "tools.py"]

    data = __generate_data(children, sub_agent_path)
    await __write_files(data, templates, filees)


@tool(stop_after_tool_call=True)
async def write_workflow_files(
    session_state, workflow_names: list[str], workflow_codes: list[str]
):
    """
    Creates workflow directories and writes workflow files using the provided names and codes.

    Args:
        workflow_names (list[str]): A list of workflow names.
        workflow_codes (list[str]): A list of workflow code snippets corresponding to the workflow names.
        absolute_out_dir (str) : path for output
    """
    absolute_out_dir = session_state["absolute_out_dir"]
    children = list(zip(workflow_names, workflow_codes))
    workflow_path = f"{absolute_out_dir}/workflows"
    templates = {
        "workflow.py": "from agno.workflow import Workflow, Step, Condition, Loop\n",
        "constant.py": "DB = None\nMODEL = None\n",
    }
    files = ["workflow.py", "constant.py"]

    data = __generate_data(children, workflow_path)
    await __write_files(data, templates, files)
