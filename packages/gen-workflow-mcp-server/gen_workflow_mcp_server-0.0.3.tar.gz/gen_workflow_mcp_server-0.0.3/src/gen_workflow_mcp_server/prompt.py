from textwrap import dedent


def prompt_for_chart(user_query: str):
    return f"""
    <instruction>
        - Extract mermaid chart only
        - Use Sequence diagrams
        - No other contents needed
    </instruction>

    <requirements>
        - Define the agents for each role.
        - Define the interactions for each agent including conditional, looping
        - Next, the output into a final mermaid chart.
    </requirements>
    \n

    Here is query:\n
    {user_query}
"""


def prompt_for_spec(mermaid_chart: str):
    return dedent(f"""
    <format>
        # TODO

        - agents
        {{snake_cased_agents}}

        - workflows
        {{snake_cased_workflow}}
            - steps: {{snake_cased_agents}}
            - condition: {{snake_cased_agents}}
            - loop: {{snake_cased_agents}}
    </format>
    \n

    Analyze given chart and applying given format:\n
    {mermaid_chart}
""")
