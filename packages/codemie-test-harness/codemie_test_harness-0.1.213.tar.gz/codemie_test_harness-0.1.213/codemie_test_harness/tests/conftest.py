import os
import subprocess
import uuid
from pathlib import Path
from time import sleep
from typing import List, Optional

import pytest
from codemie_sdk.models.assistant import (
    ToolKitDetails,
    ToolDetails,
    Context,
    ContextType,
)
from codemie_sdk.models.datasource import DataSource
from codemie_sdk.models.integration import (
    IntegrationType,
    CredentialValues,
    CredentialTypes,
    Integration,
)
from codemie_sdk.models.workflow import WorkflowCreateRequest, WorkflowMode, Workflow
from dotenv import load_dotenv
from requests import HTTPError

from codemie_test_harness.tests import PROJECT, autotest_entity_prefix
from codemie_test_harness.tests.test_data.file_test_data import file_test_data
from codemie_test_harness.tests.test_data.google_datasource_test_data import (
    GOOGLE_DOC_URL,
)
from codemie_test_harness.tests.utils.assistant_utils import AssistantUtils
from codemie_test_harness.tests.utils.base_utils import get_random_name, wait_for_entity
from codemie_test_harness.tests.utils.client_factory import get_client
from codemie_test_harness.tests.utils.confluence_utils import ConfluenceUtils
from codemie_test_harness.tests.utils.constants import TESTS_PATH, FILES_PATH
from codemie_test_harness.tests.utils.conversation_utils import ConversationUtils
from codemie_test_harness.tests.utils.credentials_manager import CredentialsManager
from codemie_test_harness.tests.utils.datasource_utils import DataSourceUtils
from codemie_test_harness.tests.utils.env_resolver import (
    EnvironmentResolver,
    get_environment,
)
from codemie_test_harness.tests.utils.gitbud_utils import GitBudUtils
from codemie_test_harness.tests.utils.integration_utils import IntegrationUtils
from codemie_test_harness.tests.utils.jira_utils import JiraUtils
from codemie_test_harness.tests.utils.llm_utils import LLMUtils
from codemie_test_harness.tests.utils.logger_util import setup_logger
from codemie_test_harness.tests.utils.notification_utils import GmailUtils
from codemie_test_harness.tests.utils.provider_utils import ProviderUtils
from codemie_test_harness.tests.utils.search_utils import SearchUtils
from codemie_test_harness.tests.utils.similarity_check import SimilarityCheck
from codemie_test_harness.tests.utils.user_utils import UserUtils
from codemie_test_harness.tests.utils.webhook_utils import WebhookUtils
from codemie_test_harness.tests.utils.workflow_utils import WorkflowUtils
from codemie_test_harness.tests.utils.yaml_utils import (
    WorkflowYamlModel,
    AssistantModel,
    ToolModel,
    StateModel,
    prepare_yaml_content,
)

logger = setup_logger(__name__)


def cleanup_plugin_process(process):
    """Helper function to cleanly terminate a plugin process.

    Args:
        process: The subprocess.Popen process to terminate
    """
    if process and process.poll() is None:  # Process is still running
        logger.info(f"Terminating plugin process with PID: {process.pid}")
        try:
            process.terminate()
            process.wait(timeout=10)  # Wait up to 10 seconds for graceful shutdown
            logger.info(
                f"Successfully terminated plugin process with PID: {process.pid}"
            )
        except subprocess.TimeoutExpired:
            logger.warning(
                f"Plugin process {process.pid} did not terminate gracefully, forcing kill"
            )
            process.kill()
            process.wait()
            logger.info(f"Successfully killed plugin process with PID: {process.pid}")
        except Exception as e:
            logger.error(f"Error during plugin process cleanup: {e}")
    else:
        logger.info("Plugin process already terminated or not found")


def pytest_configure(config):
    """Pytest hook that runs before test collection starts.

    This hook loads environment variables from .env file and optionally
    retrieves additional configuration from AWS Parameter Store.
    """
    import platform
    from codemie_test_harness.cli.runner import resolve_tests_path_and_root
    from codemie_test_harness.tests.utils.aws_parameters_store import AwsParameterStore
    from codemie_test_harness.tests.utils.env_utils import EnvManager

    # Set timeout method based on OS
    # Windows requires 'thread' method, Unix-like systems can use 'signal'
    config.option.timeout_method = (
        "thread" if platform.system() == "Windows" else "signal"
    )

    # Resolve the root directory and .env file path
    _, root_dir = resolve_tests_path_and_root()
    env_file_path = Path(root_dir) / ".env"

    # Load initial .env file
    if env_file_path.exists():
        load_dotenv(env_file_path)

    # Check if AWS credentials are available for parameter store
    if os.getenv("AWS_ACCESS_KEY") and os.getenv("AWS_SECRET_KEY"):
        aws_parameters_store = AwsParameterStore.get_instance(
            access_key=os.getenv("AWS_ACCESS_KEY"),
            secret_key=os.getenv("AWS_SECRET_KEY"),
            session_token=os.getenv("AWS_SESSION_TOKEN", ""),
        )

        # Get dotenv configuration from AWS Parameter Store
        dotenv = aws_parameters_store.get_parameter(
            f"/codemie/autotests/dotenv/{str(get_environment())}"
        )

        # Safely update .env file with new content
        EnvManager.update_env_file_safely(
            env_file_path=env_file_path, new_content=dotenv, clear_old_vars=True
        )


@pytest.fixture(scope="session")
def client():
    return get_client()


@pytest.fixture(scope="session")
def default_llm(client):
    models = client.llms.list()
    return models[0]


@pytest.fixture(scope="session")
def default_embedding_llm(client):
    embeddings_models = client.llms.list_embeddings()
    return embeddings_models[0]


@pytest.fixture(scope="session")
def similarity_workflow_yaml(default_llm):
    assistant = AssistantModel(
        id="similarity_analysis",
        model=default_llm.base_name,
        system_prompt="""
            You are a similarity analyzer. Your task is to compare two texts and rank their semantic similarity.
            You will receive two texts from user input: text1 and text2.
            Your output should be a JSON object with a single key "similarity_rank" and an integer value from 0 to 100.
            A similarity rank of 0 indicates entirely different meanings and facts,
            A similarity rank of 100 means they are entirely the same.
            IMPORTANT! Output format MUST be an integer number from 0 to 100.
            Do not describe any your thoughts!
        """,
    )
    state = StateModel(
        id="similarity_analysis",
        assistant_id="similarity_analysis",
        task="""
            Compare two texts from user input: text1 and text2 and rank their semantic similarity from 0 to 100.
            A similarity rank of 0 indicates entirely different meanings and facts,
            A similarity rank of 100 means they are entirely the same.
            IMPORTANT! Output format MUST be an integer number from 0 to 100.
            Do not describe any your thoughts!
        """,
        output_schema="""
              ```json
              {
                "similarity_rank": "..."
              }
            """,
    )

    workflow_yaml = WorkflowYamlModel(
        assistants=[assistant],
        states=[state],
    )

    return prepare_yaml_content(workflow_yaml.model_dump(exclude_none=True))


@pytest.fixture(scope="session")
def similarity_check(client, similarity_workflow_yaml, workflow_utils):
    workflow_name = get_random_name()
    create_request = WorkflowCreateRequest(
        name=workflow_name,
        description="Similarity expert",
        project=PROJECT,
        yaml_config=similarity_workflow_yaml,
        mode=WorkflowMode.SEQUENTIAL,
        shared=False,
    )
    client.workflows.create_workflow(create_request)
    similarity_workflow = wait_for_entity(
        lambda: client.workflows.list(per_page=50),
        entity_name=workflow_name,
    )
    yield SimilarityCheck(client, similarity_workflow.id)
    if similarity_workflow:
        workflow_utils.delete_workflow(similarity_workflow)


@pytest.fixture(scope="session")
def integration_utils(client):
    return IntegrationUtils(client)


@pytest.fixture(scope="session")
def datasource_utils(client):
    return DataSourceUtils(client)


@pytest.fixture(scope="session")
def assistant_utils(client):
    return AssistantUtils(client)


@pytest.fixture(scope="session")
def workflow_utils(client):
    return WorkflowUtils(client)


@pytest.fixture(scope="session")
def git_utils():
    """Create GitBudUtils instance"""
    return GitBudUtils(
        url=CredentialsManager.get_parameter("GITLAB_URL"),
        token=CredentialsManager.get_parameter("GITLAB_TOKEN"),
        project_id=CredentialsManager.get_parameter("GITLAB_PROJECT_ID"),
    )


@pytest.fixture(scope="session")
def search_utils(client):
    return SearchUtils(client)


@pytest.fixture(scope="session")
def user_utils(client):
    return UserUtils(client)


@pytest.fixture(scope="session")
def llm_utils(client):
    return LLMUtils(client)


@pytest.fixture(scope="session")
def conversation_utils(client):
    return ConversationUtils(client)


@pytest.fixture(scope="session")
def webhook_utils(client):
    return WebhookUtils(client)


@pytest.fixture(scope="session")
def gitlab_integration(integration_utils):
    integration = integration_utils.create_integration(
        credential_type=CredentialTypes.GIT,
        credential_values=CredentialsManager.gitlab_credentials(),
    )
    yield integration
    if integration:
        integration_utils.delete_integration(integration)


@pytest.fixture(scope="session")
def github_integration(integration_utils):
    integration = integration_utils.create_integration(
        credential_type=CredentialTypes.GIT,
        credential_values=CredentialsManager.github_credentials(),
    )
    yield integration
    if integration:
        integration_utils.delete_integration(integration)


@pytest.fixture(scope="function")
def jira_integration(integration_utils):
    integration = integration_utils.create_integration(
        credential_type=CredentialTypes.JIRA,
        credential_values=CredentialsManager.jira_credentials(),
    )
    yield integration
    if integration:
        integration_utils.delete_integration(integration)


@pytest.fixture(scope="function")
def jira_cloud_integration(integration_utils):
    integration = integration_utils.create_integration(
        credential_type=CredentialTypes.JIRA,
        credential_values=CredentialsManager.jira_cloud_credentials(),
    )
    yield integration
    if integration:
        integration_utils.delete_integration(integration)


@pytest.fixture(scope="function")
def confluence_integration(integration_utils):
    integration = integration_utils.create_integration(
        credential_type=CredentialTypes.CONFLUENCE,
        credential_values=CredentialsManager.confluence_credentials(),
    )
    yield integration
    if integration:
        integration_utils.delete_integration(integration)


@pytest.fixture(scope="function")
def confluence_cloud_integration(integration_utils):
    integration = integration_utils.create_integration(
        credential_type=CredentialTypes.CONFLUENCE,
        credential_values=CredentialsManager.confluence_cloud_credentials(),
    )
    yield integration
    if integration:
        integration_utils.delete_integration(integration)


@pytest.fixture(scope="module")
def filesystem_integration(integration_utils):
    """Create Filesystem integration"""
    integration = integration_utils.create_integration(
        credential_type=CredentialTypes.FILESYSTEM,
        credential_values=CredentialsManager.file_system_credentials(),
    )
    yield integration
    if integration:
        integration_utils.delete_integration(integration)


@pytest.fixture(scope="module")
def open_api_integration(client, integration_utils):
    credential_values = CredentialsManager.open_api_credentials(str(client.token))
    integration = integration_utils.create_integration(
        CredentialTypes.OPENAPI, credential_values
    )
    yield integration
    if integration:
        integration_utils.delete_integration(integration)


@pytest.fixture(scope="module")
def email_integration(integration_utils):
    credential_values = CredentialsManager.gmail_credentials()
    integration = integration_utils.create_integration(
        CredentialTypes.EMAIL, credential_values
    )
    yield integration
    if integration:
        integration_utils.delete_integration(integration)


@pytest.fixture(scope="module")
def telegram_integration(integration_utils):
    credential_values = CredentialsManager.telegram_credentials()
    integration = integration_utils.create_integration(
        CredentialTypes.TELEGRAM, credential_values
    )
    yield integration
    if integration:
        integration_utils.delete_integration(integration)


@pytest.fixture(scope="module")
def service_now_integration(integration_utils):
    credential_values = CredentialsManager.servicenow_credentials()
    integration = integration_utils.create_integration(
        CredentialTypes.SERVICE_NOW, credential_values
    )
    yield integration
    if integration:
        integration_utils.delete_integration(integration)


@pytest.fixture(scope="module")
def keycloak_integration(integration_utils):
    credential_values = CredentialsManager.keycloak_credentials()
    integration = integration_utils.create_integration(
        CredentialTypes.KEYCLOAK, credential_values
    )
    yield integration
    if integration:
        integration_utils.delete_integration(integration)


@pytest.fixture(scope="module")
def report_portal_integration(integration_utils):
    credential_values = CredentialsManager.report_portal_credentials()
    integration = integration_utils.create_integration(
        CredentialTypes.REPORT_PORTAL, credential_values
    )
    yield integration
    if integration:
        integration_utils.delete_integration(integration)


@pytest.fixture(scope="module")
def webhook_integration(integration_utils):
    created_integrations = []

    def _create(webhook_id, resource_type, resource_id, is_enabled: bool = True):
        credential_values = [
            CredentialValues(key="url", value=CredentialsManager.AUTO_GENERATED),
            CredentialValues(key="webhook_id", value=webhook_id),
            CredentialValues(key="is_enabled", value=is_enabled),
            CredentialValues(key="resource_type", value=resource_type),
            CredentialValues(key="resource_id", value=resource_id),
        ]
        integration = integration_utils.create_integration(
            CredentialTypes.WEBHOOK, credential_values
        )
        created_integrations.append(integration)
        return integration

    yield _create

    for integration in created_integrations:
        try:
            integration_utils.delete_integration(integration)
        except HTTPError:
            pass


@pytest.fixture(scope="function")
def general_integration(integration_utils):
    created_integration: Optional[Integration] = None

    def _create_integration(
        integration_type: IntegrationType,
        credential_type: CredentialTypes,
        credential_values: List[CredentialValues],
        integration_alias: str = None,
        project_name: str = None,
        is_global: bool = False,
    ):
        nonlocal created_integration
        created_integration = integration_utils.create_integration(
            setting_type=integration_type,
            credential_type=credential_type,
            credential_values=credential_values,
            integration_alias=integration_alias,
            project_name=project_name,
            is_global=is_global,
        )
        return created_integration

    yield _create_integration
    try:
        integration_utils.delete_integration(created_integration)
    except HTTPError:
        pass


@pytest.fixture(scope="session")
def code_datasource(
    datasource_utils, gitlab_integration, github_integration, default_embedding_llm
):
    git_env = CredentialsManager.get_parameter("GIT_ENV", "gitlab")
    datasource = datasource_utils.create_code_datasource(
        link=CredentialsManager.get_parameter("GITLAB_PROJECT")
        if git_env == "gitlab"
        else CredentialsManager.get_parameter("GITHUB_PROJECT"),
        branch="main" if git_env == "gitlab" else "master",
        embeddings_model=default_embedding_llm.base_name,
        setting_id=gitlab_integration.id
        if git_env == "gitlab"
        else github_integration.id,
    )
    yield datasource
    if datasource:
        datasource_utils.delete_datasource(datasource)


@pytest.fixture(scope="session")
def file_datasource(datasource_utils, default_embedding_llm):
    file_name = file_test_data[2][0]

    datasource = datasource_utils.create_file_datasource(
        name=get_random_name(),
        description=f"[Autotest] {file_name} with {default_embedding_llm.base_name} embedding model",
        files=[str(FILES_PATH / file_name)],
        embeddings_model=default_embedding_llm.base_name,
    )
    yield datasource
    if datasource:
        datasource_utils.delete_datasource(datasource)


@pytest.fixture(scope="session")
def gitlab_datasource(datasource_utils, gitlab_integration, default_embedding_llm):
    datasource = datasource_utils.create_gitlab_datasource(
        setting_id=gitlab_integration.id,
        embeddings_model=default_embedding_llm.base_name,
    )
    yield datasource
    if datasource:
        datasource_utils.delete_datasource(datasource)


@pytest.fixture(scope="session")
def github_datasource(datasource_utils, github_integration, default_embedding_llm):
    datasource = datasource_utils.create_github_datasource(
        setting_id=github_integration.id,
        embeddings_model=default_embedding_llm.base_name,
    )
    yield datasource
    if datasource:
        datasource_utils.delete_datasource(datasource)


@pytest.fixture(scope="session")
def code_context():
    """Create code context"""

    def _create_code_context(datasource: DataSource):
        return Context(name=datasource.name, context_type=ContextType.CODE)

    return _create_code_context


@pytest.fixture(scope="session")
def kb_context():
    """Create KB context"""

    def _create_kb_context(datasource: DataSource):
        return Context(name=datasource.name, context_type=ContextType.KNOWLEDGE_BASE)

    return _create_kb_context


@pytest.fixture(scope="function")
def assistant(default_llm, assistant_utils, conversation_utils):
    """Create assistant"""
    created_assistant = None

    def _create_assistant(
        toolkit: str = None,
        *tool_names: str,
        settings=None,
        context=None,
        mcp_server=None,
        project_name: str = None,
        description: str = None,
        system_prompt="You are a helpful integration test assistant",
    ):
        nonlocal created_assistant
        # Correctly handle empty `tool_names`
        if tool_names:  # Ensure `tool_names` is not empty
            tool_names = tool_names[0] if isinstance(tool_names, tuple) else tool_names
            toolkits = [
                ToolKitDetails(
                    toolkit=toolkit,
                    tools=[
                        ToolDetails(name=tool, settings=settings) for tool in tool_names
                    ]
                    if isinstance(tool_names, tuple)
                    else [ToolDetails(name=tool_names, settings=settings)],
                    settings=settings,
                )
            ]
        else:
            toolkits = []  # Assign an empty list if no tool_names provided

        created_assistant = assistant_utils.create_assistant(
            llm_model_type=default_llm.base_name,
            toolkits=toolkits,
            context=[context] if context else [],
            mcp_servers=[mcp_server] if mcp_server else [],
            system_prompt=system_prompt,
            project_name=project_name,
            description=description,
        )
        return created_assistant

    yield _create_assistant
    if created_assistant:
        assistant_utils.delete_assistant(created_assistant)
        conversations = conversation_utils.get_conversation_by_assistant_id(
            created_assistant["id"]
        )
        for conversation in conversations:
            conversation_utils.delete_conversation(conversation.id)


@pytest.fixture(scope="function")
def workflow(workflow_utils):
    created_workflow: Optional[Workflow] = None

    def _create_workflow(
        workflow_name=None,
        tool_model=None,
        assistant_model=None,
        state_model=None,
        project_name=None,
        description=None,
    ):
        workflow_name = workflow_name if workflow_name else get_random_name()

        workflow_yaml = WorkflowYamlModel(
            tools=[tool_model] if tool_model else [],
            assistants=[assistant_model] if assistant_model else [],
            states=[state_model],
        )

        yaml_content = prepare_yaml_content(workflow_yaml.model_dump(exclude_none=True))

        nonlocal created_workflow
        created_workflow = workflow_utils.create_workflow(
            workflow_name=workflow_name,
            workflow_type=WorkflowMode.SEQUENTIAL,
            description=description,
            shared=True,
            workflow_yaml=yaml_content,
            project_name=project_name,
        )
        return created_workflow

    yield _create_workflow
    if created_workflow:
        workflow_utils.delete_workflow(created_workflow)


@pytest.fixture(scope="function")
def workflow_with_virtual_assistant(workflow, default_llm):
    """Create workflow with virtual assistant"""

    def _create_workflow(
        assistant_and_state_name,
        tool_names=None,
        integration=None,
        system_prompt="You are a helpful assistant",
        task=None,
        mcp_servers=None,
        datasource_ids=None,
        project_name=None,
    ):
        # Normalize tool_names to a tuple; allow None or single or tuple
        if tool_names is None:
            tool_names_tuple = ()
        elif isinstance(tool_names, tuple):
            tool_names_tuple = tool_names
        else:
            tool_names_tuple = (tool_names,)

        tools_list = [
            ToolModel(
                name=tool_enum.value,
                integration_alias=integration.alias if integration else None,
            )
            for tool_enum in tool_names_tuple
        ]

        assistant = AssistantModel(
            id=assistant_and_state_name,
            model=default_llm.base_name,
            system_prompt=system_prompt,
            datasource_ids=datasource_ids,
            tools=tools_list,
            mcp_servers=mcp_servers,
        )

        state = StateModel(
            id=assistant_and_state_name,
            assistant_id=assistant_and_state_name,
            task=task,
        )

        return workflow(
            assistant_model=assistant, state_model=state, project_name=project_name
        )

    return _create_workflow


@pytest.fixture(scope="function")
def workflow_with_assistant(workflow, default_llm):
    """Create workflow with specific assistant id"""

    def _create_workflow(assistant, prompt):
        assistant_model = AssistantModel(
            id=assistant.name,
            model=default_llm.base_name,
            assistant_id=assistant.id,
        )
        state_model = StateModel(
            id=assistant.name,
            assistant_id=assistant.name,
            task=prompt,
        )

        return workflow(assistant_model=assistant_model, state_model=state_model)

    return _create_workflow


@pytest.fixture(scope="function")
def workflow_with_tool(workflow):
    """Create workflow with tool"""

    def _create_workflow(
        tool_and_state_name,
        tool_name,
        tool_args=None,
        integration=None,
        datasource_ids=None,
        project_name=None,
    ):
        state_model = StateModel(id=tool_and_state_name, tool_id=tool_and_state_name)

        tool_model = ToolModel(
            id=tool_and_state_name,
            tool=tool_name.value,
            integration_alias=integration.alias if integration else None,
            tool_args=tool_args,
            datasource_ids=datasource_ids,
        )

        return workflow(
            tool_model=tool_model, state_model=state_model, project_name=project_name
        )

    return _create_workflow


@pytest.fixture(scope="function")
def jira_datasource(datasource_utils, jira_integration):
    datasource = datasource_utils.create_jira_datasource(setting_id=jira_integration.id)
    yield datasource
    if datasource:
        datasource_utils.delete_datasource(datasource)


@pytest.fixture(scope="function")
def google_doc_datasource(datasource_utils):
    datasource = datasource_utils.create_google_doc_datasource(
        google_doc=GOOGLE_DOC_URL
    )
    yield datasource
    if datasource:
        datasource_utils.delete_datasource(datasource)


@pytest.fixture(scope="function")
def confluence_datasource(datasource_utils, confluence_integration):
    datasource = datasource_utils.create_confluence_datasource(
        setting_id=confluence_integration.id
    )
    yield datasource
    if datasource:
        datasource_utils.delete_datasource(datasource)


@pytest.fixture(scope="session")
def gmail_message_operator():
    gmail_utils = GmailUtils()
    yield gmail_utils
    gmail_utils.delete_all_messages()


@pytest.fixture(scope="session")
def filesystem_server(integration_utils):
    key = str(uuid.uuid4())
    logger.info(f"Plugin key: {key}")

    credential_values = CredentialsManager.plugin_credentials(key)
    settings = integration_utils.create_integration(
        CredentialTypes.PLUGIN, credential_values
    )
    logger.info(f"Integration id: {settings.id}")

    env = os.environ.copy()
    env["FILE_PATHS"] = f"{str(TESTS_PATH)},{str(TESTS_PATH / 'enums')}"
    env["PLUGIN_EXPERIMENTAL_PROTOCOL"] = "true"

    command = [
        "codemie-plugins",
        "--plugin-key",
        key,
        "--plugin-engine-uri",
        CredentialsManager.get_parameter("NATS_URL"),
        "mcp",
        "run",
        "-s",
        "filesystem",
        "-e",
        "filesystem=FILE_PATHS",
    ]
    process = subprocess.Popen(command, env=env)
    logger.info(f"Started filesystem server process with PID: {process.pid}")
    sleep(10)
    yield settings
    cleanup_plugin_process(process)


@pytest.fixture(scope="session")
def cli_server(integration_utils):
    key = str(uuid.uuid4())
    logger.info(f"Plugin key: {key}")

    credential_values = CredentialsManager.plugin_credentials(key)
    settings = integration_utils.create_integration(
        CredentialTypes.PLUGIN, credential_values
    )
    logger.info(f"Integration id: {settings.id}")

    env = os.environ.copy()
    env["ALLOWED_DIR"] = str(TESTS_PATH)
    env["PLUGIN_EXPERIMENTAL_PROTOCOL"] = "true"

    # Define the command
    command = [
        "codemie-plugins",
        "--plugin-key",
        key,
        "--plugin-engine-uri",
        CredentialsManager.get_parameter("NATS_URL"),
        "mcp",
        "run",
        "-s",
        "cli-mcp-server",
        "-e",
        "cli-mcp-server=ALLOWED_DIR",
    ]
    process = subprocess.Popen(command, env=env)
    logger.info(f"Started CLI server process with PID: {process.pid}")
    sleep(10)
    yield settings
    cleanup_plugin_process(process)


@pytest.fixture(scope="session")
def development_plugin(integration_utils):
    key = str(uuid.uuid4())
    logger.info(f"Plugin key: {key}")

    credential_values = CredentialsManager.plugin_credentials(key)
    settings = integration_utils.create_integration(
        CredentialTypes.PLUGIN, credential_values
    )
    logger.info(f"Integration id: {settings.id}")

    env = os.environ.copy()
    env["PLUGIN_EXPERIMENTAL_PROTOCOL"] = "true"

    command = [
        "codemie-plugins",
        "--plugin-key",
        key,
        "--plugin-engine-uri",
        CredentialsManager.get_parameter("NATS_URL"),
        "development",
        "run",
        "--repo-path",
        str(TESTS_PATH),
    ]
    process = subprocess.Popen(command, env=env)
    logger.info(f"Started development plugin process with PID: {process.pid}")
    sleep(10)
    yield settings
    cleanup_plugin_process(process)


@pytest.fixture(scope="module")
def ado_integration(integration_utils):
    """Create Azure DevOps integration"""
    _integration = integration_utils.create_integration(
        CredentialTypes.AZURE_DEVOPS,
        CredentialsManager.azure_devops_credentials(),
    )
    yield _integration
    if _integration:
        integration_utils.delete_integration(_integration)


@pytest.fixture(scope="function")
def integration(integration_utils):
    """Create integration with custom credentials"""

    created_integration: Optional[Integration] = None

    def _integration(
        credential_type: CredentialTypes, credential_values, integration_alias=None
    ):
        nonlocal created_integration

        created_integration = integration_utils.create_integration(
            credential_type,
            credential_values,
            integration_alias=integration_alias,
        )
        return created_integration

    yield _integration
    if created_integration:
        integration_utils.delete_integration(created_integration)


def pytest_sessionfinish(session):
    """Run cleanup code after all tests have finished."""
    clean_up_timeout = 1 if EnvironmentResolver.is_production() else 0
    if CredentialsManager.get_parameter("CLEANUP_DATA", "true").lower() == "true":
        client = get_client()
        prefix = autotest_entity_prefix
        integrations = client.integrations.list(
            setting_type=IntegrationType.PROJECT,
            filters={"search": autotest_entity_prefix},
            per_page=200,
        )
        for integration in integrations:
            if prefix in integration.alias:
                client.integrations.delete(
                    setting_id=integration.id, setting_type=IntegrationType.PROJECT
                )
                sleep(clean_up_timeout)
        integrations = client.integrations.list(
            setting_type=IntegrationType.USER,
            filters={"search": autotest_entity_prefix},
            per_page=200,
        )
        for integration in integrations:
            if prefix in integration.alias:
                client.integrations.delete(
                    setting_id=integration.id, setting_type=IntegrationType.USER
                )
                sleep(clean_up_timeout)
        datasources = client.datasources.list(
            filters={"name": autotest_entity_prefix}, per_page=200
        )
        for datasource in datasources:
            if prefix in datasource.name:
                client.datasources.delete(datasource_id=datasource.id)
                sleep(clean_up_timeout)
        assistants = client.assistants.list(
            filters={"search": autotest_entity_prefix}, per_page=200
        )
        for assistant in assistants:
            if prefix in assistant.name:
                client.assistants.delete(assistant_id=assistant.id)
                sleep(clean_up_timeout)
                conversations = client.conversations.list_by_assistant_id(assistant.id)
                for conversation in conversations:
                    client.conversations.delete(conversation.id)
                    sleep(clean_up_timeout)
        workflows = client.workflows.list(
            filters={"name": autotest_entity_prefix}, per_page=200
        )
        for workflow in workflows:
            if prefix in workflow.name:
                client.workflows.delete(workflow_id=workflow.id)
                sleep(clean_up_timeout)

        providers_utils = ProviderUtils(client)
        providers_utils.cleanup_test_providers()

        # Clean up Jira test issues
        jira_utils = JiraUtils(is_cloud=False)
        jira_utils.cleanup_jira_project(summary_prefix=prefix)
        jira_utils = JiraUtils(is_cloud=True)
        jira_utils.cleanup_jira_project(summary_prefix=prefix)

        # Clean up Confluence test pages
        confluence_utils = ConfluenceUtils(is_cloud=False)
        confluence_utils.cleanup_confluence_space(title_prefix=prefix)
        confluence_utils = ConfluenceUtils(is_cloud=True)
        confluence_utils.cleanup_confluence_space(title_prefix=prefix)
