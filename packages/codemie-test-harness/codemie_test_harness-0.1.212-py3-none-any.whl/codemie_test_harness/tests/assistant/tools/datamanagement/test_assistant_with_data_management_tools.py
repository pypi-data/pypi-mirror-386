import uuid

import pytest
from codemie_sdk.models.integration import CredentialTypes

from codemie_test_harness.tests.enums.integrations import DataBaseDialect
from codemie_test_harness.tests.enums.tools import (
    Toolkit,
    DataManagementTool,
)
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
from codemie_test_harness.tests.utils.base_utils import assert_tool_triggered
from codemie_test_harness.tests.utils.credentials_manager import CredentialsManager
from codemie_test_harness.tests.utils.env_resolver import EnvironmentResolver

pytestmark = pytest.mark.skipif(
    EnvironmentResolver.is_localhost(),
    reason="Skipping this tests on local environment",
)


@pytest.mark.assistant
@pytest.mark.elastic
@pytest.mark.api
@pytest.mark.testcase("EPMCDME-6132")
def test_create_assistant_with_elastic_tool(
    integration_utils, assistant, assistant_utils, similarity_check
):
    credential_values = CredentialsManager.elasticsearch_credentials()
    settings = integration_utils.create_integration(
        CredentialTypes.ELASTIC, credential_values
    )
    assistant = assistant(
        Toolkit.DATA_MANAGEMENT,
        DataManagementTool.ELASTIC,
        settings=settings,
    )

    response, triggered_tools = assistant_utils.ask_assistant(
        assistant, ELASTIC_TOOL_TASK, minimal_response=False
    )

    assert_tool_triggered(DataManagementTool.ELASTIC, triggered_tools)
    similarity_check.check_similarity(response, RESPONSE_FOR_ELASTIC)


@pytest.mark.assistant
@pytest.mark.sql
@pytest.mark.api
@pytest.mark.testcase("EPMCDME-6132")
@pytest.mark.parametrize(
    "db_dialect",
    sql_tools_test_data,
)
@pytest.mark.testcase("EPMCDME-6132")
def test_create_assistant_with_sql_tool(
    integration_utils, assistant_utils, assistant, similarity_check, db_dialect
):
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

    conversation_id = str(uuid.uuid4())

    _, triggered_tools = assistant_utils.ask_assistant(
        assistant,
        SQL_TOOL_CREATE_TABLE_TASK,
        conversation_id=conversation_id,
        minimal_response=False,
    )
    assert_tool_triggered(DataManagementTool.SQL, triggered_tools)

    _, triggered_tools = assistant_utils.ask_assistant(
        assistant,
        SQL_TOOL_INSERT_TABLE_TASK,
        conversation_id=conversation_id,
        minimal_response=False,
    )
    assert_tool_triggered(DataManagementTool.SQL, triggered_tools)

    response, triggered_tools = assistant_utils.ask_assistant(
        assistant,
        SQL_TOOL_QUERY_TABLE_TASK,
        conversation_id=conversation_id,
        minimal_response=False,
    )
    assert_tool_triggered(DataManagementTool.SQL, triggered_tools)
    similarity_check.check_similarity(response, RESPONSE_FOR_SQL)

    _, triggered_tools = assistant_utils.ask_assistant(
        assistant,
        SQL_TOOL_DELETE_TABLE_TASK,
        conversation_id=conversation_id,
        minimal_response=False,
    )
    assert_tool_triggered(DataManagementTool.SQL, triggered_tools)


@pytest.mark.assistant
@pytest.mark.sql
@pytest.mark.influx
@pytest.mark.api
@pytest.mark.testcase("EPMCDME-6132")
@pytest.mark.skipif(
    not EnvironmentResolver.is_sandbox(),
    reason="InfluxDB is only available in sandbox environments",
)
def test_create_assistant_with_influxdb_tool(
    integration_utils, assistant_utils, assistant, similarity_check
):
    """Test creating assistant with InfluxDB tool and performing time-series operations."""

    credential_values = CredentialsManager.sql_credentials(DataBaseDialect.INFLUX)
    settings = integration_utils.create_integration(
        CredentialTypes.SQL, credential_values
    )

    assistant = assistant(
        Toolkit.DATA_MANAGEMENT, DataManagementTool.SQL, settings=settings
    )

    conversation_id = str(uuid.uuid4())

    # Query the measurement
    response, triggered_tools = assistant_utils.ask_assistant(
        assistant,
        INFLUXDB_QUERY_MEASUREMENT_TASK,
        conversation_id=conversation_id,
        minimal_response=False,
    )
    assert_tool_triggered(DataManagementTool.SQL, triggered_tools)
    similarity_check.check_similarity(response, RESPONSE_FOR_INFLUXDB)
