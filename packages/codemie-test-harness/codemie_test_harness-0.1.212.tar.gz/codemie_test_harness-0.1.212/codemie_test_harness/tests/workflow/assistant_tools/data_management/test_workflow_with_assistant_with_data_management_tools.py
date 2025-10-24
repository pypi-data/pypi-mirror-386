import pytest
from codemie_sdk.models.integration import CredentialTypes

from codemie_test_harness.tests.enums.integrations import DataBaseDialect
from codemie_test_harness.tests.enums.tools import DataManagementTool, Toolkit
from codemie_test_harness.tests.utils.base_utils import assert_tool_triggered
from codemie_test_harness.tests.test_data.data_management_tools_test_data import (
    ELASTIC_TOOL_TASK,
    RESPONSE_FOR_ELASTIC,
    sql_tools_test_data,
    SQL_TOOL_CREATE_TABLE_TASK,
    SQL_TOOL_DELETE_TABLE_TASK,
    SQL_TOOL_INSERT_TABLE_TASK,
    SQL_TOOL_QUERY_TABLE_TASK,
    RESPONSE_FOR_SQL,
    INFLUXDB_QUERY_MEASUREMENT_TASK,
    RESPONSE_FOR_INFLUXDB,
)
from codemie_test_harness.tests.utils.credentials_manager import CredentialsManager
from codemie_test_harness.tests.utils.env_resolver import EnvironmentResolver

pytestmark = pytest.mark.skipif(
    EnvironmentResolver.is_localhost(),
    reason="Skipping this tests on local environment",
)


@pytest.mark.workflow
@pytest.mark.workflow_with_assistant
@pytest.mark.elastic
@pytest.mark.api
def test_workflow_with_assistant_with_elastic_tools(
    assistant,
    workflow_with_assistant,
    workflow_utils,
    integration_utils,
    similarity_check,
):
    """Test workflow execution with Elastic tools."""
    credential_values = CredentialsManager.elasticsearch_credentials()
    settings = integration_utils.create_integration(
        CredentialTypes.ELASTIC, credential_values
    )
    assistant = assistant(
        Toolkit.DATA_MANAGEMENT, DataManagementTool.ELASTIC, settings=settings
    )

    workflow_with_assistant = workflow_with_assistant(assistant, ELASTIC_TOOL_TASK)
    response = workflow_utils.execute_workflow(
        workflow_with_assistant.id, assistant.name
    )

    triggered_tools = workflow_utils.extract_triggered_tools_from_execution(
        workflow_with_assistant
    )
    assert_tool_triggered(DataManagementTool.ELASTIC, triggered_tools)

    similarity_check.check_similarity(response, RESPONSE_FOR_ELASTIC)


@pytest.mark.workflow
@pytest.mark.workflow_with_assistant
@pytest.mark.sql
@pytest.mark.api
@pytest.mark.parametrize(
    "db_dialect",
    sql_tools_test_data,
)
def test_workflow_with_assistant_with_sql_tools(
    assistant,
    workflow_with_assistant,
    workflow_utils,
    integration_utils,
    similarity_check,
    db_dialect,
):
    """Test workflow execution with SQL data management tools (various dialects)."""
    credential_values = CredentialsManager.sql_credentials(db_dialect)
    settings = integration_utils.create_integration(
        CredentialTypes.SQL, credential_values
    )

    assistant = assistant(
        Toolkit.DATA_MANAGEMENT,
        DataManagementTool.SQL,
        settings=settings,
        system_prompt="Always run tools for user prompt",
    )
    workflow_with_assistant = workflow_with_assistant(assistant, "Run")

    # Step 1: Create table
    workflow_utils.execute_workflow(
        workflow_with_assistant.id, assistant.name, SQL_TOOL_CREATE_TABLE_TASK
    )
    triggered_tools = workflow_utils.extract_triggered_tools_from_execution(
        workflow_with_assistant
    )
    assert_tool_triggered(DataManagementTool.SQL, triggered_tools)

    # Step 2: Insert data
    workflow_utils.execute_workflow(
        workflow_with_assistant.id, assistant.name, SQL_TOOL_INSERT_TABLE_TASK
    )
    triggered_tools = workflow_utils.extract_triggered_tools_from_execution(
        workflow_with_assistant
    )
    assert_tool_triggered(DataManagementTool.SQL, triggered_tools)

    # Step 3: Query data
    response = workflow_utils.execute_workflow(
        workflow_with_assistant.id, assistant.name, SQL_TOOL_QUERY_TABLE_TASK
    )
    triggered_tools = workflow_utils.extract_triggered_tools_from_execution(
        workflow_with_assistant
    )
    assert_tool_triggered(DataManagementTool.SQL, triggered_tools)

    # Step 4: Delete table
    workflow_utils.execute_workflow(
        workflow_with_assistant.id, assistant.name, SQL_TOOL_DELETE_TABLE_TASK
    )
    triggered_tools = workflow_utils.extract_triggered_tools_from_execution(
        workflow_with_assistant
    )
    assert_tool_triggered(DataManagementTool.SQL, triggered_tools)

    similarity_check.check_similarity(response, RESPONSE_FOR_SQL)


@pytest.mark.workflow
@pytest.mark.workflow_with_assistant
@pytest.mark.influx
@pytest.mark.api
@pytest.mark.skipif(
    not EnvironmentResolver.is_sandbox(),
    reason="InfluxDB is only available in sandbox environments",
)
def test_workflow_with_assistant_with_influxdb_tools(
    assistant,
    workflow_with_assistant,
    workflow_utils,
    integration_utils,
    similarity_check,
):
    """Test workflow execution with InfluxDB tools via assistant."""

    credential_values = CredentialsManager.sql_credentials(DataBaseDialect.INFLUX)
    settings = integration_utils.create_integration(
        CredentialTypes.SQL, credential_values
    )

    assistant = assistant(
        Toolkit.DATA_MANAGEMENT, DataManagementTool.SQL, settings=settings
    )
    workflow_with_assistant = workflow_with_assistant(assistant, "Run")

    # Query the measurement
    response = workflow_utils.execute_workflow(
        workflow_with_assistant.id, assistant.name, INFLUXDB_QUERY_MEASUREMENT_TASK
    )

    similarity_check.check_similarity(response, RESPONSE_FOR_INFLUXDB)
