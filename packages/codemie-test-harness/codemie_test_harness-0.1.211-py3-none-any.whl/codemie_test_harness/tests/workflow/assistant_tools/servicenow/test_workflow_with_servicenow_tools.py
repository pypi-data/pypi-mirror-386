import pytest

from codemie_test_harness.tests.enums.tools import ServiceNowTool, Toolkit
from codemie_test_harness.tests.test_data.servicenow_tools_test_data import (
    PROMPT,
    EXPECTED_RESPONSE,
)
from codemie_test_harness.tests.utils.base_utils import assert_tool_triggered


@pytest.mark.workflow
@pytest.mark.workflow_with_assistant
@pytest.mark.servicenow
@pytest.mark.api
def test_workflow_with_assistant_with_servicenow_tools(
    service_now_integration,
    workflow_with_assistant,
    workflow_utils,
    similarity_check,
    assistant,
):
    assistant = assistant(
        Toolkit.SERVICENOW,
        ServiceNowTool.SERVICE_NOW,
        settings=service_now_integration,
    )

    workflow_with_assistant = workflow_with_assistant(assistant, PROMPT)

    response = workflow_utils.execute_workflow(
        workflow_with_assistant.id, assistant.name
    )

    triggered_tools = workflow_utils.extract_triggered_tools_from_execution(
        workflow_with_assistant
    )
    assert_tool_triggered(ServiceNowTool.SERVICE_NOW, triggered_tools)

    similarity_check.check_similarity(response, EXPECTED_RESPONSE, 80)
