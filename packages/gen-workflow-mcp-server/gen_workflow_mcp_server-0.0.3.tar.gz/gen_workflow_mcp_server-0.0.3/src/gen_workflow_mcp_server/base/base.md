```py
# agent
{lower_cased_agent_name}_agent = Agent(
    name="{snake_cased_agent_name}",
    instructions="{generated_instructions}"
)

# Step for steps
Step(
    name="{snake_cased_agent_name}",
    agent={snake_cased_agent_name},
)

# workflow with steps
# steps property can contains Step, Condition, Loop
{lower_cased_workflow_name}_workflow = Workflow(
    name="{snake_cased_agent_name}",
    steps=[]
)

# Condition
Condition(
    name="condition_{snake_cased_agent_name}",
    evaluator="condition_{snake_cased_condition_name}",
    steps=[],
)

# Loop
Loop(
    name="loop_{snake_cased_agent_name}",
    end_condition="condition_{snake_cased_loop_name}",
    max_iterations=3,
    steps=[],
)

# Parallel (Many Step run concurrently)

Parallel(
    Step(name="{snake_cased_agent_name}", agent={snake_cased_agent_name}),
    name="parallel_{snake_cased_agent_name}",
)

# Steps (Grouping Step)
Steps(
    name="{snake_cased_agent_name}",
    steps=[],
)
```

# Instructions

- Grammer for generating python codes
- TODOs for generating codes based on Grammer
- Generate instructions for each *_agent
- When generating *_workflow, import each *_agent from files, each file's path:
  src.sub_agents.{snake_cased_agent_name}.agent import
  {snake_cased_agent_name}\n

# Rules

- name is required for each *_agent and *_workflow
- each names for agent and workflow are specified in TODO
