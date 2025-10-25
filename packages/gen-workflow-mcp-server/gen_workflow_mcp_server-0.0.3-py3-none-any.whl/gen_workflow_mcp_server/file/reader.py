import os

from agno.agent import Agent

from src.constant import model_pro
from src.model import AnalzyedOutput


def get_root_dir(directory: str):
    directory = directory[1:] if directory.startswith("/") else directory
    return os.path.join(os.getcwd(), directory)


def gather_files(directory: str, allows: list[str] = ["md"]):
    markdown_contents = []
    root = get_root_dir(directory)
    files = os.listdir(root)

    for f in files:
        for allow in allows:
            ext = ""
            if "." in ext:
                ext = allow[1:]
            else:
                ext = allow

            if f.endswith(ext):
                markdown_contents.append(f)

    return files


def generate_output(input: str, step2: str) -> AnalzyedOutput | None:
    output_agent = Agent(
        name="OutputAgent",
        instructions=f"{step2}",
        model=model_pro,
        output_schema=AnalzyedOutput,
    )

    result = output_agent.run(input).content
    if not result:
        return

    output: AnalzyedOutput = result
    texts = [
        output.agent_codes,
        output.agent_names,
        output.workflow_codes,
        output.workflow_names,
    ]

    for t in texts:
        if not t:
            return

    return result
