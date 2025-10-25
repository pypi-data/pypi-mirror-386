from textwrap import dedent
from agno.agent import Agent
from agno.workflow.types import StepInput, StepOutput

from src.model import AnalzyedOutput, ValidateOutput
from src.constant import model
import json


def condition_quality_checker(outputs: StepOutput) -> bool:
    """
    Validate the code and grammar of the content carried by the given StepInput.
    This function constructs a prompt from step_input[0].content, sends it to a validation
    agent (an Agent instance that uses a language model), and interprets the agent's
    response (expected to conform to the ValidateOutput schema). The function returns True
    when the validator indicates the code is valid, otherwise False.
    Args:
        step_input (StepInput): A sequence-like container where the first element
            (step_input[0]) is expected to be a StepOutput-like object exposing a
            `content` attribute or property containing the code/text to validate.
    Returns:
        bool: True if the validator agent's response indicates the code/text is valid
        (resp.is_valid is truthy), False otherwise.
    """
    analyzed: AnalzyedOutput = outputs[0].content  # type: ignore
    codes = [*analyzed.agent_codes, *analyzed.workflow_codes]
    prompt_for_validation = dedent(f"""
        Validate code only then Check both gramatically correction and completion:\n
        {json.dumps(codes) or ""}
    """)
    validater_agent = Agent(
        name="ValidaterAgent",
        model=model,
        instructions="check given codes are valid and completed",
        output_schema=ValidateOutput,
    )
    resp = validater_agent.run(prompt_for_validation).content
    if not resp:
        return False

    output: ValidateOutput = resp
    if output.is_valid_and_completed:
        return True
    return False


def is_okay(step_input: StepInput) -> bool:
    cont = step_input.previous_step_content
    if not cont:
        return False
    if "ready" in cont:
        return True
    return False
