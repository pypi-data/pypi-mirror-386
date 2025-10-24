import copy
import json
import random

import pytest

from codemie_test_harness.tests.test_data.direct_tools.project_management_tools_test_data import (
    project_management_tools_data,
)
from codemie_test_harness.tests.utils.base_utils import get_random_name
from codemie_test_harness.tests.utils.constants import project_management_integrations


@pytest.mark.workflow
@pytest.mark.direct_tool
@pytest.mark.project_management
@pytest.mark.api
@pytest.mark.parametrize(
    "toolkit, tool_name, integration_type, prompt, expected_response",
    project_management_tools_data,
    ids=[f"{row[1]}" for row in project_management_tools_data],
)
def test_workflow_with_project_management_tools_direct(
    request,
    workflow_with_tool,
    workflow_utils,
    similarity_check,
    toolkit,
    tool_name,
    integration_type,
    prompt,
    expected_response,
):
    tool_and_state_name = get_random_name()

    integration = request.getfixturevalue(
        project_management_integrations[integration_type]
    )

    test_workflow = workflow_with_tool(
        tool_and_state_name, tool_name, integration=integration
    )
    response = workflow_utils.execute_workflow(
        test_workflow.id, tool_and_state_name, json.dumps(prompt)
    )
    similarity_check.check_similarity(response, expected_response, 90)


@pytest.mark.workflow
@pytest.mark.direct_tool
@pytest.mark.project_management
@pytest.mark.api
@pytest.mark.parametrize(
    "toolkit, tool_name, integration_type, prompt, expected_response",
    project_management_tools_data,
    ids=[f"{row[1]}" for row in project_management_tools_data],
)
def test_workflow_with_project_management_tools_with_hardcoded_args(
    request,
    workflow_with_tool,
    workflow_utils,
    similarity_check,
    toolkit,
    tool_name,
    integration_type,
    prompt,
    expected_response,
):
    tool_and_state_name = get_random_name()

    integration = request.getfixturevalue(
        project_management_integrations[integration_type]
    )

    test_workflow = workflow_with_tool(
        tool_and_state_name, tool_name, integration=integration, tool_args=prompt
    )
    response = workflow_utils.execute_workflow(test_workflow.id, tool_and_state_name)
    similarity_check.check_similarity(response, expected_response, 90)


@pytest.mark.workflow
@pytest.mark.direct_tool
@pytest.mark.project_management
@pytest.mark.api
@pytest.mark.parametrize(
    "toolkit, tool_name, integration_type, prompt, expected_response",
    project_management_tools_data,
    ids=[f"{row[1]}" for row in project_management_tools_data],
)
def test_workflow_with_project_management_tools_with_overriding_args(
    request,
    workflow_with_tool,
    workflow_utils,
    similarity_check,
    toolkit,
    tool_name,
    integration_type,
    prompt,
    expected_response,
):
    tool_and_state_name = get_random_name()

    args_copy = copy.deepcopy(prompt)
    args_copy = {key: random.randint(1, 10) for key in args_copy}

    integration = request.getfixturevalue(
        project_management_integrations[integration_type]
    )

    test_workflow = workflow_with_tool(
        tool_and_state_name, tool_name, integration=integration, tool_args=args_copy
    )
    response = workflow_utils.execute_workflow(
        test_workflow.id, tool_and_state_name, json.dumps(prompt)
    )
    similarity_check.check_similarity(response, expected_response, 90)
