from pydantic import BaseModel, Field


class PathOutput(BaseModel):
    query: str | None = Field(default=None)
    out_directory: str | None = Field(default=None)


class StepsSchema(BaseModel):
    step_1: str | None = Field(default=None)
    step_2: str | None = Field(default=None)
    step_3: str | None = Field(default=None)
    query: str | None = Field(default=None)


class AnalzyedOutput(BaseModel):
    agent_names: list[str] = Field(default_factory=list)
    agent_codes: list[str] = Field(default_factory=list)
    workflow_names: list[str] = Field(default_factory=list)
    workflow_codes: list[str] = Field(default_factory=list)


class ValidateOutput(BaseModel):
    is_valid_and_completed: bool = Field(default=False)
