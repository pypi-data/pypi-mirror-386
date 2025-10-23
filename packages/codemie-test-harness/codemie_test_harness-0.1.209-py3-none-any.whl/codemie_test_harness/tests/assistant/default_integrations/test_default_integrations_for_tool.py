import pytest

from codemie_sdk.models.integration import (
    CredentialTypes,
    IntegrationType,
)
from codemie_test_harness.tests import PROJECT
from codemie_test_harness.tests.enums.tools import Toolkit, ProjectManagementTool
from codemie_test_harness.tests.integrations import integrations
from codemie_test_harness.tests.test_data.pm_tools_test_data import (
    JIRA_TOOL_PROMPT,
    RESPONSE_FOR_JIRA_TOOL,
)
from codemie_test_harness.tests.utils.credentials_manager import CredentialsManager
from codemie_test_harness.tests.utils.constants import test_project_name
from codemie_test_harness.tests.utils.base_utils import assert_tool_triggered


@pytest.mark.integration
@pytest.mark.default_integration
@pytest.mark.not_for_parallel_run
@pytest.mark.api
@pytest.mark.testcase("EPMCDME-6708")
@pytest.mark.parametrize(
    "user_integration, is_global, project_integration",
    integrations,
    ids=[
        f"{row[0].value}-{'global' if row[1] else 'None'}-{row[2].value if row[2] else 'None'}"
        for row in integrations
    ],
)
def test_assistant_should_use_user_integration_by_default(
    integration_utils,
    assistant,
    assistant_utils,
    similarity_check,
    user_integration,
    is_global,
    project_integration,
):
    """
    Test to verify that an assistant should use USER integration by default
    if integration of all types [USER, GLOBAL, PROJECT] are available.
    """

    for integration_type in IntegrationType:
        integration_utils.delete_integrations_by_type(
            integration_type, CredentialTypes.JIRA
        )

    integration_utils.create_user_integration(
        CredentialTypes.JIRA, CredentialsManager.jira_credentials(), test_project_name
    )

    if is_global:
        integration_utils.create_global_integration(
            CredentialTypes.JIRA,
            CredentialsManager.invalid_jira_credentials(),
            test_project_name,
        )

    if project_integration:
        integration_utils.create_project_integration(
            CredentialTypes.JIRA,
            CredentialsManager.invalid_jira_credentials(),
            test_project_name,
        )

    jira_assistant = assistant(
        Toolkit.PROJECT_MANAGEMENT,
        ProjectManagementTool.JIRA,
        project_name=test_project_name,
    )

    response, triggered_tools = assistant_utils.ask_assistant(
        jira_assistant, JIRA_TOOL_PROMPT, minimal_response=False
    )

    assert_tool_triggered(ProjectManagementTool.JIRA, triggered_tools)
    similarity_check.check_similarity(response, RESPONSE_FOR_JIRA_TOOL)


@pytest.mark.integration
@pytest.mark.default_integration
@pytest.mark.not_for_parallel_run
@pytest.mark.api
@pytest.mark.testcase("EPMCDME-6708")
def test_assistant_with_global_and_project_integration(
    integration_utils,
    assistant,
    assistant_utils,
    similarity_check,
):
    """
    Test to verify that an assistant should use GLOBAL integration if USER integration is not available,
    and both GLOBAL and PROJECT integrations exist.
    GLOBAL integration has valid credentials, PROJECT has invalid.
    """
    for integration_type in IntegrationType:
        integration_utils.delete_integrations_by_type(
            integration_type, CredentialTypes.JIRA
        )

    # Create only global (valid) and project (invalid) integrations.
    # Global integration is created in project which is different from the project of the assistant.
    integration_utils.create_global_integration(
        CredentialTypes.JIRA, CredentialsManager.jira_credentials(), PROJECT
    )

    integration_utils.create_project_integration(
        CredentialTypes.JIRA,
        CredentialsManager.invalid_jira_credentials(),
        test_project_name,
    )

    jira_assistant = assistant(
        Toolkit.PROJECT_MANAGEMENT,
        ProjectManagementTool.JIRA,
        project_name=test_project_name,
    )

    response, triggered_tools = assistant_utils.ask_assistant(
        jira_assistant, JIRA_TOOL_PROMPT, minimal_response=False
    )

    assert_tool_triggered(ProjectManagementTool.JIRA, triggered_tools)
    similarity_check.check_similarity(response, RESPONSE_FOR_JIRA_TOOL)


@pytest.mark.integration
@pytest.mark.default_integration
@pytest.mark.not_for_parallel_run
@pytest.mark.api
@pytest.mark.testcase("EPMCDME-6708")
def test_assistant_with_project_integration_only(
    integration_utils,
    assistant,
    assistant_utils,
    similarity_check,
):
    """
    Test to verify that an assistant should use PROJECT integration if it is the only one available.
    """
    for integration_type in IntegrationType:
        integration_utils.delete_integrations_by_type(
            integration_type, CredentialTypes.JIRA
        )

    # Create project integration only
    integration_utils.create_project_integration(
        CredentialTypes.JIRA, CredentialsManager.jira_credentials(), test_project_name
    )

    jira_assistant = assistant(
        Toolkit.PROJECT_MANAGEMENT,
        ProjectManagementTool.JIRA,
        project_name=test_project_name,
    )

    response, triggered_tools = assistant_utils.ask_assistant(
        jira_assistant, JIRA_TOOL_PROMPT, minimal_response=False
    )

    assert_tool_triggered(ProjectManagementTool.JIRA, triggered_tools)
    similarity_check.check_similarity(response, RESPONSE_FOR_JIRA_TOOL)


@pytest.mark.integration
@pytest.mark.default_integration
@pytest.mark.not_for_parallel_run
@pytest.mark.api
def test_assistant_with_global_valid_and_user_invalid_integration(
    assistant, assistant_utils, integration_utils, similarity_check
):
    """
    Test to verify that an assistant should use GLOBAL integration if USER integration is not valid,
    and both GLOBAL and USER integrations exist.
    GLOBAL integration has valid credentials, USER has invalid.
    """
    for integration_type in IntegrationType:
        integration_utils.delete_integrations_by_type(
            integration_type, CredentialTypes.JIRA
        )

    # Create global valid integration.
    integration_utils.create_global_integration(
        CredentialTypes.JIRA, CredentialsManager.jira_credentials(), PROJECT
    )

    # Create user invalid integration.
    integration_utils.create_user_integration(
        CredentialTypes.JIRA,
        CredentialsManager.invalid_jira_credentials(),
        PROJECT,
    )

    jira_assistant = assistant(
        Toolkit.PROJECT_MANAGEMENT,
        ProjectManagementTool.JIRA,
        project_name=test_project_name,
    )

    response, triggered_tools = assistant_utils.ask_assistant(
        jira_assistant, JIRA_TOOL_PROMPT, minimal_response=False
    )

    assert_tool_triggered(ProjectManagementTool.JIRA, triggered_tools)
    similarity_check.check_similarity(response, RESPONSE_FOR_JIRA_TOOL)


@pytest.mark.integration
@pytest.mark.default_integration
@pytest.mark.not_for_parallel_run
@pytest.mark.api
def test_assistant_with_project_valid_and_user_invalid_integration(
    assistant, assistant_utils, integration_utils, similarity_check
):
    """
    Test to verify that an assistant should use PROJECT integration if USER integration is not valid,
    and both PROJECT and USER integrations exist.
    PROJECT integration has valid credentials, USER has invalid.
    """
    for integration_type in IntegrationType:
        integration_utils.delete_integrations_by_type(
            integration_type, CredentialTypes.JIRA
        )

    # Create project valid integration.
    integration_utils.create_project_integration(
        CredentialTypes.JIRA, CredentialsManager.jira_credentials(), test_project_name
    )

    # Create user invalid integration.
    integration_utils.create_user_integration(
        CredentialTypes.JIRA,
        CredentialsManager.invalid_jira_credentials(),
        PROJECT,
    )

    jira_assistant = assistant(
        Toolkit.PROJECT_MANAGEMENT,
        ProjectManagementTool.JIRA,
        project_name=test_project_name,
    )

    response, triggered_tools = assistant_utils.ask_assistant(
        jira_assistant, JIRA_TOOL_PROMPT, minimal_response=False
    )

    assert_tool_triggered(ProjectManagementTool.JIRA, triggered_tools)
    similarity_check.check_similarity(response, RESPONSE_FOR_JIRA_TOOL)
