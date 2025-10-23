import pytest

from codemie_sdk.models.integration import (
    CredentialTypes,
    IntegrationType,
)
from codemie_test_harness.tests import PROJECT
from codemie_test_harness.tests.integrations import integrations
from codemie_test_harness.tests.enums.tools import Toolkit, GitTool
from codemie_test_harness.tests.test_data.git_tools_test_data import (
    list_branches_set_active_branch_test_data,
)
from codemie_test_harness.tests.utils.credentials_manager import CredentialsManager
from codemie_test_harness.tests.utils.constants import test_project_name
from codemie_test_harness.tests.utils.base_utils import assert_tool_triggered


git_tool_prompt = list_branches_set_active_branch_test_data[0][2]
git_tool_answer = list_branches_set_active_branch_test_data[0][3]


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
    datasource_utils,
    default_embedding_llm,
    gitlab_datasource,
    code_context,
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
            integration_type, CredentialTypes.GIT, test_project_name
        )

    _git_integration = integration_utils.create_user_integration(
        CredentialTypes.GIT, CredentialsManager.gitlab_credentials(), test_project_name
    )

    # create a new datasource
    git_datasource = datasource_utils.create_gitlab_datasource(
        setting_id=_git_integration.id,
        embeddings_model=default_embedding_llm.base_name,
        project_name=test_project_name,
    )

    if is_global:
        integration_utils.create_global_integration(
            CredentialTypes.GIT,
            CredentialsManager.invalid_git_credentials(),
            test_project_name,
        )

    if project_integration:
        integration_utils.create_project_integration(
            CredentialTypes.GIT,
            CredentialsManager.invalid_git_credentials(),
            test_project_name,
        )

    git_assistant = assistant(
        Toolkit.GIT,
        GitTool.LIST_BRANCHES_IN_REPO,
        context=code_context(git_datasource),
        project_name=test_project_name,
    )

    response, triggered_tools = assistant_utils.ask_assistant(
        git_assistant, git_tool_prompt, minimal_response=False
    )

    assert_tool_triggered(GitTool.LIST_BRANCHES_IN_REPO, triggered_tools)
    similarity_check.check_similarity(response, git_tool_answer)


@pytest.mark.integration
@pytest.mark.default_integration
@pytest.mark.not_for_parallel_run
@pytest.mark.api
@pytest.mark.testcase("EPMCDME-6708")
def test_assistant_with_global_and_project_integration(
    datasource_utils,
    default_embedding_llm,
    code_context,
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
    # Create datasource
    _git_integration = integration_utils.create_global_integration(
        CredentialTypes.GIT, CredentialsManager.gitlab_credentials(), test_project_name
    )
    git_datasource = datasource_utils.create_gitlab_datasource(
        setting_id=_git_integration.id,
        embeddings_model=default_embedding_llm.base_name,
        project_name=test_project_name,
    )

    # Delete all integrations of type GIT
    for integration_type in IntegrationType:
        integration_utils.delete_integrations_by_type(
            integration_type, CredentialTypes.GIT, test_project_name
        )

    # Create only global (valid) and project (invalid) integrations.
    # Global integration is created in project which is different from the project of the assistant.
    _git_integration = integration_utils.create_global_integration(
        CredentialTypes.GIT, CredentialsManager.gitlab_credentials(), PROJECT
    )

    integration_utils.create_project_integration(
        CredentialTypes.GIT,
        CredentialsManager.invalid_git_credentials(),
        test_project_name,
    )

    git_assistant = assistant(
        Toolkit.GIT,
        GitTool.LIST_BRANCHES_IN_REPO,
        context=code_context(git_datasource),
        project_name=test_project_name,
    )

    response, triggered_tools = assistant_utils.ask_assistant(
        git_assistant, git_tool_prompt, minimal_response=False
    )

    assert_tool_triggered(GitTool.LIST_BRANCHES_IN_REPO, triggered_tools)
    similarity_check.check_similarity(response, git_tool_answer)


@pytest.mark.integration
@pytest.mark.default_integration
@pytest.mark.not_for_parallel_run
@pytest.mark.api
@pytest.mark.testcase("EPMCDME-6708")
def test_assistant_with_project_integration_only(
    datasource_utils,
    default_embedding_llm,
    code_context,
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
            integration_type, CredentialTypes.GIT, test_project_name
        )

    # Create project integration only
    _git_integration = integration_utils.create_project_integration(
        CredentialTypes.GIT, CredentialsManager.gitlab_credentials(), test_project_name
    )

    # create a new datasource
    git_datasource = datasource_utils.create_gitlab_datasource(
        setting_id=_git_integration.id,
        embeddings_model=default_embedding_llm.base_name,
        project_name=test_project_name,
    )

    git_assistant = assistant(
        Toolkit.GIT,
        GitTool.LIST_BRANCHES_IN_REPO,
        context=code_context(git_datasource),
        project_name=test_project_name,
    )

    response, triggered_tools = assistant_utils.ask_assistant(
        git_assistant, git_tool_prompt, minimal_response=False
    )

    assert_tool_triggered(GitTool.LIST_BRANCHES_IN_REPO, triggered_tools)
    similarity_check.check_similarity(response, git_tool_answer)


@pytest.mark.integration
@pytest.mark.default_integration
@pytest.mark.not_for_parallel_run
@pytest.mark.api
def test_assistant_with_global_valid_and_user_invalid_integration(
    assistant,
    assistant_utils,
    integration_utils,
    similarity_check,
    datasource_utils,
    default_embedding_llm,
    code_context,
):
    """
    Test to verify that an assistant should use GLOBAL integration if USER integration is not valid,
    and both GLOBAL and USER integrations exist.
    GLOBAL integration has valid credentials, USER has invalid.
    """
    # Create datasource
    _git_integration = integration_utils.create_global_integration(
        CredentialTypes.GIT, CredentialsManager.gitlab_credentials(), test_project_name
    )
    git_datasource = datasource_utils.create_gitlab_datasource(
        setting_id=_git_integration.id,
        embeddings_model=default_embedding_llm.base_name,
        project_name=test_project_name,
    )

    # Delete all integrations of type GIT
    for integration_type in IntegrationType:
        integration_utils.delete_integrations_by_type(
            integration_type, CredentialTypes.GIT, test_project_name
        )

    # Create global valid integration
    _git_integration = integration_utils.create_global_integration(
        CredentialTypes.GIT, CredentialsManager.gitlab_credentials(), PROJECT
    )

    # Create user invalid integration
    integration_utils.create_user_integration(
        CredentialTypes.GIT,
        CredentialsManager.invalid_git_credentials(),
        PROJECT,
    )

    git_assistant = assistant(
        Toolkit.GIT,
        GitTool.LIST_BRANCHES_IN_REPO,
        context=code_context(git_datasource),
        project_name=test_project_name,
    )

    response, triggered_tools = assistant_utils.ask_assistant(
        git_assistant, git_tool_prompt, minimal_response=False
    )

    assert_tool_triggered(GitTool.LIST_BRANCHES_IN_REPO, triggered_tools)
    similarity_check.check_similarity(response, git_tool_answer)


@pytest.mark.integration
@pytest.mark.default_integration
@pytest.mark.not_for_parallel_run
@pytest.mark.api
def test_assistant_with_project_valid_and_user_invalid_integration(
    assistant,
    assistant_utils,
    integration_utils,
    similarity_check,
    datasource_utils,
    default_embedding_llm,
    code_context,
):
    """
    Test to verify that an assistant should use PROJECT integration if USER integration is not valid,
    and both PROJECT and USER integrations exist.
    PROJECT integration has valid credentials, USER has invalid.
    """
    # Create datasource
    _git_integration = integration_utils.create_global_integration(
        CredentialTypes.GIT, CredentialsManager.gitlab_credentials(), test_project_name
    )
    git_datasource = datasource_utils.create_gitlab_datasource(
        setting_id=_git_integration.id,
        embeddings_model=default_embedding_llm.base_name,
        project_name=test_project_name,
    )

    # Delete all integrations of type GIT
    for integration_type in IntegrationType:
        integration_utils.delete_integrations_by_type(
            integration_type, CredentialTypes.GIT, test_project_name
        )

    # Create global valid integration
    _git_integration = integration_utils.create_project_integration(
        CredentialTypes.GIT, CredentialsManager.gitlab_credentials(), test_project_name
    )

    # Create user invalid integration
    integration_utils.create_user_integration(
        CredentialTypes.GIT,
        CredentialsManager.invalid_git_credentials(),
        PROJECT,
    )

    git_assistant = assistant(
        Toolkit.GIT,
        GitTool.LIST_BRANCHES_IN_REPO,
        context=code_context(git_datasource),
        project_name=test_project_name,
    )

    response, triggered_tools = assistant_utils.ask_assistant(
        git_assistant, git_tool_prompt, minimal_response=False
    )

    assert_tool_triggered(GitTool.LIST_BRANCHES_IN_REPO, triggered_tools)
    similarity_check.check_similarity(response, git_tool_answer)
