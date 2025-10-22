"""Workflow CLI commands for executing and managing workflows."""

from __future__ import annotations


import click

from codemie_test_harness.tests.utils.client_factory import get_client
from ..constants import CONSOLE


@click.group(name="workflow")
def workflow_cmd():
    """Interact with CodeMie workflows."""
    pass


@workflow_cmd.command(name="execute")
@click.option(
    "--workflow-id",
    required=True,
    help="Workflow ID to execute",
)
@click.option(
    "--user-input",
    "-i",
    default="",
    help="User input for the workflow execution (optional)",
)
def execute_cmd(
    workflow_id: str,
    user_input: str,
):
    """Execute a workflow.

    Example:
        codemie-test-harness workflow execute --workflow-id "wf_123"
        codemie-test-harness workflow execute --workflow-id "wf_123" --user-input "process this data"
    """
    try:
        client = get_client()

        CONSOLE.print(f"[yellow]Executing workflow {workflow_id}...[/yellow]")
        if user_input:
            CONSOLE.print(f"[blue]User input: {user_input}[/blue]")

        # Execute workflow
        response = client.workflows.run(workflow_id=workflow_id, user_input=user_input)

        # Display response
        CONSOLE.print("[green]Workflow execution started successfully![/green]")

        if hasattr(response, "execution_id"):
            CONSOLE.print(f"[cyan]Execution ID: {response.execution_id}[/cyan]")

        if hasattr(response, "status"):
            CONSOLE.print(f"[cyan]Status: {response.status}[/cyan]")

        # Display the full response for debugging
        CONSOLE.print(f"[dim]Response: {response}[/dim]")

    except Exception as e:
        CONSOLE.print(f"[red]Error executing workflow: {e}[/red]")
        raise click.ClickException(str(e))
