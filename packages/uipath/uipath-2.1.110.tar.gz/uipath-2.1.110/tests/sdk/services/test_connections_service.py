from unittest.mock import MagicMock
from urllib.parse import unquote_plus

import pytest
from pydantic import ValidationError
from pytest_httpx import HTTPXMock

from uipath._config import Config
from uipath._execution_context import ExecutionContext
from uipath._services.connections_service import ConnectionsService
from uipath._services.folder_service import FolderService
from uipath._utils.constants import HEADER_FOLDER_KEY, HEADER_USER_AGENT
from uipath.models import (
    Connection,
    ConnectionMetadata,
    ConnectionToken,
    EventArguments,
)
from uipath.utils.dynamic_schema import jsonschema_to_pydantic


@pytest.fixture
def mock_folders_service() -> MagicMock:
    """Mock FolderService for testing."""
    service = MagicMock(spec=FolderService)
    service.retrieve_key.return_value = "test-folder-key"
    return service


@pytest.fixture
def service(
    config: Config,
    execution_context: ExecutionContext,
    mock_folders_service: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> ConnectionsService:
    monkeypatch.setenv("UIPATH_FOLDER_PATH", "test-folder-path")
    return ConnectionsService(
        config=config,
        execution_context=execution_context,
        folders_service=mock_folders_service,
    )


class TestConnectionsService:
    def test_retrieve(
        self,
        httpx_mock: HTTPXMock,
        service: ConnectionsService,
        base_url: str,
        org: str,
        tenant: str,
        version: str,
    ) -> None:
        connection_key = "test-connection"
        httpx_mock.add_response(
            url=f"{base_url}{org}{tenant}/connections_/api/v1/Connections/{connection_key}",
            status_code=200,
            json={
                "id": "test-id",
                "name": "Test Connection",
                "state": "active",
                "elementInstanceId": 123,
            },
        )

        connection = service.retrieve(key=connection_key)

        assert isinstance(connection, Connection)
        assert connection.id == "test-id"
        assert connection.name == "Test Connection"
        assert connection.state == "active"
        assert connection.element_instance_id == 123

        sent_request = httpx_mock.get_request()
        if sent_request is None:
            raise Exception("No request was sent")

        assert sent_request.method == "GET"
        assert (
            sent_request.url
            == f"{base_url}{org}{tenant}/connections_/api/v1/Connections/{connection_key}"
        )

        assert HEADER_USER_AGENT in sent_request.headers
        assert (
            sent_request.headers[HEADER_USER_AGENT]
            == f"UiPath.Python.Sdk/UiPath.Python.Sdk.Activities.ConnectionsService.retrieve/{version}"
        )

    def test_metadata(
        self,
        httpx_mock: HTTPXMock,
        service: ConnectionsService,
        base_url: str,
        org: str,
        tenant: str,
        version: str,
    ) -> None:
        element_instance_id = 123
        tool_path = "test-tool"
        valid_choice = {
            "index": 0,
            "finishReason": "done",
            "message": {"content": "foo", "role": "user"},
        }
        invalid_choice = {
            "index": 0,
            "finishReason": "done",
            "message": {"content": 123, "role": "user"},
        }
        valid_object = {
            "choices": [valid_choice],
            "usage": {"totalTokens": 100},
            "created": 1000,
        }
        invalid_object_1 = {
            "choices": [valid_choice],
            "usage": {"totalTokens": 100},
            "created": "string",
        }
        invalid_object_2 = {
            "choices": [invalid_choice],
            "usage": {"totalTokens": 100},
            "created": 1000,
        }
        json_schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "choices": {
                    "title": "Choices",
                    "type": "array",
                    "items": {"$ref": "#/definitions/choices"},
                },
                "usage": {"title": "Usage", "$ref": "#/definitions/usage"},
                "created": {
                    "title": "Creation timestamp",
                    "type": "integer",
                    "format": "int64",
                },
            },
            "definitions": {
                "message": {
                    "type": "object",
                    "title": "Message",
                    "properties": {
                        "content": {
                            "title": "Translated message content",
                            "type": "string",
                        },
                        "role": {
                            "title": "Role of the message sender",
                            "type": "string",
                        },
                    },
                },
                "choices": {
                    "type": "object",
                    "title": "Choices",
                    "properties": {
                        "index": {
                            "title": "Choice index",
                            "type": "integer",
                            "format": "int64",
                        },
                        "finish_reason": {
                            "title": "Completion reason",
                            "type": "string",
                        },
                        "message": {
                            "title": "Message",
                            "$ref": "#/definitions/message",
                        },
                    },
                },
                "usage": {
                    "type": "object",
                    "title": "Usage",
                    "properties": {
                        "total_tokens": {
                            "title": "Total tokens used",
                            "type": "integer",
                            "format": "int64",
                        }
                    },
                },
            },
        }
        httpx_mock.add_response(
            url=f"{base_url}{org}{tenant}/elements_/v3/element/instances/{element_instance_id}/elements/{tool_path}/metadata",
            status_code=200,
            json={
                "fields": json_schema,
            },
        )

        metadata = service.metadata(element_instance_id, tool_path)

        assert isinstance(metadata, ConnectionMetadata)
        dynamic_type = jsonschema_to_pydantic(metadata.fields)

        dynamic_type.model_validate(valid_object)
        with pytest.raises(ValidationError):
            assert dynamic_type.model_validate(invalid_object_1)
        with pytest.raises(ValidationError):
            assert dynamic_type.model_validate(invalid_object_2)
        dynamic_type.model_json_schema()

    @pytest.mark.anyio
    async def test_retrieve_async(
        self,
        httpx_mock: HTTPXMock,
        service: ConnectionsService,
        base_url: str,
        org: str,
        tenant: str,
        version: str,
    ) -> None:
        connection_key = "test-connection"
        httpx_mock.add_response(
            url=f"{base_url}{org}{tenant}/connections_/api/v1/Connections/{connection_key}",
            status_code=200,
            json={
                "id": "test-id",
                "name": "Test Connection",
                "state": "active",
                "elementInstanceId": 123,
            },
        )

        connection = await service.retrieve_async(key=connection_key)

        assert isinstance(connection, Connection)
        assert connection.id == "test-id"
        assert connection.name == "Test Connection"
        assert connection.state == "active"
        assert connection.element_instance_id == 123

        sent_request = httpx_mock.get_request()
        if sent_request is None:
            raise Exception("No request was sent")

        assert sent_request.method == "GET"
        assert (
            sent_request.url
            == f"{base_url}{org}{tenant}/connections_/api/v1/Connections/{connection_key}"
        )

        assert HEADER_USER_AGENT in sent_request.headers
        assert (
            sent_request.headers[HEADER_USER_AGENT]
            == f"UiPath.Python.Sdk/UiPath.Python.Sdk.Activities.ConnectionsService.retrieve_async/{version}"
        )

    async def test_metadata_async(
        self,
        httpx_mock: HTTPXMock,
        service: ConnectionsService,
        base_url: str,
        org: str,
        tenant: str,
        version: str,
    ) -> None:
        element_instance_id = 123
        tool_path = "test-tool"
        valid_choice = {
            "index": 0,
            "finishReason": "done",
            "message": {"content": "foo", "role": "user"},
        }
        invalid_choice = {
            "index": 0,
            "finishReason": "done",
            "message": {"content": 123, "role": "user"},
        }
        valid_object = {
            "choices": [valid_choice],
            "usage": {"totalTokens": 100},
            "created": 1000,
        }
        invalid_object_1 = {
            "choices": [valid_choice],
            "usage": {"totalTokens": 100},
            "created": "string",
        }
        invalid_object_2 = {
            "choices": [invalid_choice],
            "usage": {"totalTokens": 100},
            "created": 1000,
        }
        json_schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "choices": {
                    "title": "Choices",
                    "type": "array",
                    "items": {"$ref": "#/definitions/choices"},
                },
                "usage": {"title": "Usage", "$ref": "#/definitions/usage"},
                "created": {
                    "title": "Creation timestamp",
                    "type": "integer",
                    "format": "int64",
                },
            },
            "definitions": {
                "message": {
                    "type": "object",
                    "title": "Message",
                    "properties": {
                        "content": {
                            "title": "Translated message content",
                            "type": "string",
                        },
                        "role": {
                            "title": "Role of the message sender",
                            "type": "string",
                        },
                    },
                },
                "choices": {
                    "type": "object",
                    "title": "Choices",
                    "properties": {
                        "index": {
                            "title": "Choice index",
                            "type": "integer",
                            "format": "int64",
                        },
                        "finish_reason": {
                            "title": "Completion reason",
                            "type": "string",
                        },
                        "message": {
                            "title": "Message",
                            "$ref": "#/definitions/message",
                        },
                    },
                },
                "usage": {
                    "type": "object",
                    "title": "Usage",
                    "properties": {
                        "total_tokens": {
                            "title": "Total tokens used",
                            "type": "integer",
                            "format": "int64",
                        }
                    },
                },
            },
        }
        httpx_mock.add_response(
            url=f"{base_url}{org}{tenant}/elements_/v3/element/instances/{element_instance_id}/elements/{tool_path}/metadata",
            status_code=200,
            json={
                "fields": json_schema,
            },
        )

        metadata = await service.metadata_async(element_instance_id, tool_path)

        assert isinstance(metadata, ConnectionMetadata)
        dynamic_type = jsonschema_to_pydantic(metadata.fields)

        dynamic_type.model_validate(valid_object)
        with pytest.raises(ValidationError):
            assert dynamic_type.model_validate(invalid_object_1)
        with pytest.raises(ValidationError):
            assert dynamic_type.model_validate(invalid_object_2)
        dynamic_type.model_json_schema()

    def test_retrieve_token(
        self,
        httpx_mock: HTTPXMock,
        service: ConnectionsService,
        base_url: str,
        org: str,
        tenant: str,
        version: str,
    ) -> None:
        connection_key = "test-connection"
        httpx_mock.add_response(
            url=f"{base_url}{org}{tenant}/connections_/api/v1/Connections/{connection_key}/token?tokenType=direct",
            status_code=200,
            json={
                "accessToken": "test-token",
                "tokenType": "Bearer",
                "expiresIn": 3600,
            },
        )

        token = service.retrieve_token(key=connection_key)

        assert isinstance(token, ConnectionToken)
        assert token.access_token == "test-token"
        assert token.token_type == "Bearer"
        assert token.expires_in == 3600

        sent_request = httpx_mock.get_request()
        if sent_request is None:
            raise Exception("No request was sent")

        assert sent_request.method == "GET"
        assert (
            sent_request.url
            == f"{base_url}{org}{tenant}/connections_/api/v1/Connections/{connection_key}/token?tokenType=direct"
        )

        assert HEADER_USER_AGENT in sent_request.headers
        assert (
            sent_request.headers[HEADER_USER_AGENT]
            == f"UiPath.Python.Sdk/UiPath.Python.Sdk.Activities.ConnectionsService.retrieve_token/{version}"
        )

    @pytest.mark.anyio
    async def test_retrieve_token_async(
        self,
        httpx_mock: HTTPXMock,
        service: ConnectionsService,
        base_url: str,
        org: str,
        tenant: str,
        version: str,
    ) -> None:
        connection_key = "test-connection"
        httpx_mock.add_response(
            url=f"{base_url}{org}{tenant}/connections_/api/v1/Connections/{connection_key}/token?tokenType=direct",
            status_code=200,
            json={
                "accessToken": "test-token",
                "tokenType": "Bearer",
                "expiresIn": 3600,
            },
        )

        token = await service.retrieve_token_async(key=connection_key)

        assert isinstance(token, ConnectionToken)
        assert token.access_token == "test-token"
        assert token.token_type == "Bearer"
        assert token.expires_in == 3600

        sent_request = httpx_mock.get_request()
        if sent_request is None:
            raise Exception("No request was sent")

        assert sent_request.method == "GET"
        assert (
            sent_request.url
            == f"{base_url}{org}{tenant}/connections_/api/v1/Connections/{connection_key}/token?tokenType=direct"
        )

        assert HEADER_USER_AGENT in sent_request.headers
        assert (
            sent_request.headers[HEADER_USER_AGENT]
            == f"UiPath.Python.Sdk/UiPath.Python.Sdk.Activities.ConnectionsService.retrieve_token_async/{version}"
        )

    def test_list_no_filters(
        self,
        httpx_mock: HTTPXMock,
        service: ConnectionsService,
        base_url: str,
        org: str,
        tenant: str,
        version: str,
    ) -> None:
        """Test list method without any filters."""
        httpx_mock.add_response(
            url=f"{base_url}{org}{tenant}/connections_/api/v1/Connections?%24expand=connector%2Cfolder",
            status_code=200,
            json={
                "value": [
                    {
                        "id": "conn-1",
                        "name": "Slack Connection",
                        "state": "active",
                        "elementInstanceId": 101,
                    },
                    {
                        "id": "conn-2",
                        "name": "Salesforce Connection",
                        "state": "active",
                        "elementInstanceId": 102,
                    },
                ]
            },
        )

        connections = service.list()

        assert isinstance(connections, list)
        assert len(connections) == 2
        assert connections[0].id == "conn-1"
        assert connections[0].name == "Slack Connection"
        assert connections[1].id == "conn-2"
        assert connections[1].name == "Salesforce Connection"

        sent_request = httpx_mock.get_request()
        if sent_request is None:
            raise Exception("No request was sent")

        assert sent_request.method == "GET"
        # Check for URL-encoded version
        assert "%24expand=connector%2Cfolder" in str(sent_request.url)

    def test_list_with_name_filter(
        self,
        httpx_mock: HTTPXMock,
        service: ConnectionsService,
        base_url: str,
        org: str,
        tenant: str,
        version: str,
    ) -> None:
        """Test list method with name filtering."""
        httpx_mock.add_response(
            url=f"{base_url}{org}{tenant}/connections_/api/v1/Connections?%24filter=contains%28Name%2C%20%27Salesforce%27%29&%24expand=connector%2Cfolder",
            status_code=200,
            json={
                "value": [
                    {
                        "id": "conn-2",
                        "name": "Salesforce Connection",
                        "state": "active",
                        "elementInstanceId": 102,
                    }
                ]
            },
        )

        connections = service.list(name="Salesforce")

        assert len(connections) == 1
        assert connections[0].name == "Salesforce Connection"

        sent_request = httpx_mock.get_request()
        if sent_request is None:
            raise Exception("No request was sent")

        # Decode URL-encoded characters (including + as space)
        url_str = unquote_plus(str(sent_request.url))
        assert "contains(Name, 'Salesforce')" in url_str

    def test_list_with_folder_path_resolution(
        self,
        httpx_mock: HTTPXMock,
        service: ConnectionsService,
        mock_folders_service: MagicMock,
        base_url: str,
        org: str,
        tenant: str,
        version: str,
    ) -> None:
        """Test list method with folder path resolution."""
        mock_folders_service.retrieve_key.return_value = "folder-123"

        httpx_mock.add_response(
            url=f"{base_url}{org}{tenant}/connections_/api/v1/Connections?%24expand=connector%2Cfolder",
            status_code=200,
            json={"value": []},
        )

        service.list(folder_path="Finance/Production")

        # Verify folder service was called
        mock_folders_service.retrieve_key.assert_called_once_with(
            folder_path="Finance/Production"
        )

        sent_request = httpx_mock.get_request()
        if sent_request is None:
            raise Exception("No request was sent")

        # Verify the resolved key was used in headers
        assert HEADER_FOLDER_KEY in sent_request.headers
        assert sent_request.headers[HEADER_FOLDER_KEY] == "folder-123"

    def test_list_with_connector_filter(
        self,
        httpx_mock: HTTPXMock,
        service: ConnectionsService,
        base_url: str,
        org: str,
        tenant: str,
        version: str,
    ) -> None:
        """Test list method with connector key filtering."""
        httpx_mock.add_response(
            url=f"{base_url}{org}{tenant}/connections_/api/v1/Connections?%24filter=connector%2Fkey%20eq%20%27uipath-slack%27&%24expand=connector%2Cfolder",
            status_code=200,
            json={
                "value": [
                    {
                        "id": "conn-1",
                        "name": "Slack Connection",
                        "state": "active",
                        "elementInstanceId": 101,
                    }
                ]
            },
        )

        connections = service.list(connector_key="uipath-slack")

        assert len(connections) == 1
        assert connections[0].name == "Slack Connection"

        sent_request = httpx_mock.get_request()
        if sent_request is None:
            raise Exception("No request was sent")

        # Decode URL-encoded characters (including + as space)
        url_str = unquote_plus(str(sent_request.url))
        assert "connector/key eq 'uipath-slack'" in url_str

    def test_list_with_pagination(
        self,
        httpx_mock: HTTPXMock,
        service: ConnectionsService,
        base_url: str,
        org: str,
        tenant: str,
        version: str,
    ) -> None:
        """Test list method with pagination parameters."""
        httpx_mock.add_response(
            url=f"{base_url}{org}{tenant}/connections_/api/v1/Connections?%24skip=10&%24top=5&%24expand=connector%2Cfolder",
            status_code=200,
            json={"value": []},
        )

        service.list(skip=10, top=5)

        sent_request = httpx_mock.get_request()
        if sent_request is None:
            raise Exception("No request was sent")

        assert "%24skip=10" in str(sent_request.url)
        assert "%24top=5" in str(sent_request.url)

    def test_list_with_combined_filters(
        self,
        httpx_mock: HTTPXMock,
        service: ConnectionsService,
        mock_folders_service: MagicMock,
        base_url: str,
        org: str,
        tenant: str,
        version: str,
    ) -> None:
        """Test list method with multiple filters combined."""
        mock_folders_service.retrieve_key.return_value = "folder-456"

        httpx_mock.add_response(
            url=f"{base_url}{org}{tenant}/connections_/api/v1/Connections?%24filter=contains%28Name%2C%20%27Slack%27%29%20and%20connector%2Fkey%20eq%20%27uipath-slack%27&%24expand=connector%2Cfolder",
            status_code=200,
            json={"value": []},
        )

        service.list(name="Slack", folder_path="Finance", connector_key="uipath-slack")

        sent_request = httpx_mock.get_request()
        if sent_request is None:
            raise Exception("No request was sent")

        # Decode URL-encoded characters (including + as space)
        url_str = unquote_plus(str(sent_request.url))
        assert "contains(Name, 'Slack')" in url_str
        assert "connector/key eq 'uipath-slack'" in url_str
        assert " and " in url_str

    @pytest.mark.anyio
    async def test_list_async(
        self,
        httpx_mock: HTTPXMock,
        service: ConnectionsService,
        base_url: str,
        org: str,
        tenant: str,
        version: str,
    ) -> None:
        """Test async version of list method."""
        httpx_mock.add_response(
            url=f"{base_url}{org}{tenant}/connections_/api/v1/Connections?%24expand=connector%2Cfolder",
            status_code=200,
            json={
                "value": [
                    {
                        "id": "conn-1",
                        "name": "Test Connection",
                        "state": "active",
                        "elementInstanceId": 101,
                    }
                ]
            },
        )

        connections = await service.list_async()

        assert len(connections) == 1
        assert connections[0].name == "Test Connection"

    def test_retrieve_event_payload(
        self,
        httpx_mock: HTTPXMock,
        service: ConnectionsService,
        base_url: str,
        org: str,
        tenant: str,
        version: str,
    ) -> None:
        event_id = "test-event-id"
        additional_event_data = '{"processedEventId": "test-event-id"}'

        event_args = EventArguments(additional_event_data=additional_event_data)

        httpx_mock.add_response(
            url=f"{base_url}{org}{tenant}/elements_/v1/events/{event_id}",
            status_code=200,
            json={
                "eventId": event_id,
                "eventType": "test-event",
                "data": {"key": "value"},
                "timestamp": "2025-08-12T10:00:00Z",
            },
        )

        payload = service.retrieve_event_payload(event_args=event_args)

        assert payload["eventId"] == event_id
        assert payload["eventType"] == "test-event"
        assert payload["data"]["key"] == "value"
        assert payload["timestamp"] == "2025-08-12T10:00:00Z"

        sent_request = httpx_mock.get_request()
        if sent_request is None:
            raise Exception("No request was sent")

        assert sent_request.method == "GET"
        assert (
            sent_request.url
            == f"{base_url}{org}{tenant}/elements_/v1/events/{event_id}"
        )

        assert HEADER_USER_AGENT in sent_request.headers
        assert (
            sent_request.headers[HEADER_USER_AGENT]
            == f"UiPath.Python.Sdk/UiPath.Python.Sdk.Activities.ConnectionsService.retrieve_event_payload/{version}"
        )

    def test_retrieve_event_payload_with_raw_event_id(
        self,
        httpx_mock: HTTPXMock,
        service: ConnectionsService,
        base_url: str,
        org: str,
        tenant: str,
        version: str,
    ) -> None:
        event_id = "test-raw-event-id"
        additional_event_data = '{"rawEventId": "test-raw-event-id"}'

        event_args = EventArguments(additional_event_data=additional_event_data)

        httpx_mock.add_response(
            url=f"{base_url}{org}{tenant}/elements_/v1/events/{event_id}",
            status_code=200,
            json={
                "eventId": event_id,
                "eventType": "test-raw-event",
                "data": {"rawKey": "rawValue"},
            },
        )

        payload = service.retrieve_event_payload(event_args=event_args)

        assert payload["eventId"] == event_id
        assert payload["eventType"] == "test-raw-event"
        assert payload["data"]["rawKey"] == "rawValue"

        sent_request = httpx_mock.get_request()
        if sent_request is None:
            raise Exception("No request was sent")

        assert sent_request.method == "GET"
        assert (
            sent_request.url
            == f"{base_url}{org}{tenant}/elements_/v1/events/{event_id}"
        )

    def test_retrieve_event_payload_missing_additional_event_data(
        self,
        service: ConnectionsService,
    ) -> None:
        event_args = EventArguments(additional_event_data=None)

        with pytest.raises(ValueError, match="additional_event_data is required"):
            service.retrieve_event_payload(event_args=event_args)

    def test_retrieve_event_payload_missing_event_id(
        self,
        service: ConnectionsService,
    ) -> None:
        additional_event_data = '{"someOtherField": "value"}'
        event_args = EventArguments(additional_event_data=additional_event_data)

        with pytest.raises(
            ValueError, match="Event Id not found in additional event data"
        ):
            service.retrieve_event_payload(event_args=event_args)

    @pytest.mark.anyio
    async def test_retrieve_event_payload_async(
        self,
        httpx_mock: HTTPXMock,
        service: ConnectionsService,
        base_url: str,
        org: str,
        tenant: str,
        version: str,
    ) -> None:
        event_id = "test-event-id-async"
        additional_event_data = '{"processedEventId": "test-event-id-async"}'

        event_args = EventArguments(additional_event_data=additional_event_data)

        httpx_mock.add_response(
            url=f"{base_url}{org}{tenant}/elements_/v1/events/{event_id}",
            status_code=200,
            json={
                "eventId": event_id,
                "eventType": "test-async-event",
                "data": {"asyncKey": "asyncValue"},
                "timestamp": "2025-08-12T11:00:00Z",
            },
        )

        payload = await service.retrieve_event_payload_async(event_args=event_args)

        assert payload["eventId"] == event_id
        assert payload["eventType"] == "test-async-event"
        assert payload["data"]["asyncKey"] == "asyncValue"
        assert payload["timestamp"] == "2025-08-12T11:00:00Z"

        sent_request = httpx_mock.get_request()
        if sent_request is None:
            raise Exception("No request was sent")

        assert sent_request.method == "GET"
        assert (
            sent_request.url
            == f"{base_url}{org}{tenant}/elements_/v1/events/{event_id}"
        )

        assert HEADER_USER_AGENT in sent_request.headers
        assert (
            sent_request.headers[HEADER_USER_AGENT]
            == f"UiPath.Python.Sdk/UiPath.Python.Sdk.Activities.ConnectionsService.retrieve_event_payload_async/{version}"
        )

    @pytest.mark.anyio
    async def test_retrieve_event_payload_async_with_raw_event_id(
        self,
        httpx_mock: HTTPXMock,
        service: ConnectionsService,
        base_url: str,
        org: str,
        tenant: str,
        version: str,
    ) -> None:
        event_id = "test-raw-event-id-async"
        additional_event_data = '{"rawEventId": "test-raw-event-id-async"}'

        event_args = EventArguments(additional_event_data=additional_event_data)

        httpx_mock.add_response(
            url=f"{base_url}{org}{tenant}/elements_/v1/events/{event_id}",
            status_code=200,
            json={
                "eventId": event_id,
                "eventType": "test-async-raw-event",
                "data": {"asyncRawKey": "asyncRawValue"},
            },
        )

        payload = await service.retrieve_event_payload_async(event_args=event_args)

        assert payload["eventId"] == event_id
        assert payload["eventType"] == "test-async-raw-event"
        assert payload["data"]["asyncRawKey"] == "asyncRawValue"

        sent_request = httpx_mock.get_request()
        if sent_request is None:
            raise Exception("No request was sent")

        assert sent_request.method == "GET"
        assert (
            sent_request.url
            == f"{base_url}{org}{tenant}/elements_/v1/events/{event_id}"
        )

    @pytest.mark.anyio
    async def test_retrieve_event_payload_async_missing_additional_event_data(
        self,
        service: ConnectionsService,
    ) -> None:
        event_args = EventArguments(additional_event_data=None)

        with pytest.raises(ValueError, match="additional_event_data is required"):
            await service.retrieve_event_payload_async(event_args=event_args)

    @pytest.mark.anyio
    async def test_retrieve_event_payload_async_missing_event_id(
        self,
        service: ConnectionsService,
    ) -> None:
        additional_event_data = '{"someOtherField": "value"}'
        event_args = EventArguments(additional_event_data=additional_event_data)

        with pytest.raises(
            ValueError, match="Event Id not found in additional event data"
        ):
            await service.retrieve_event_payload_async(event_args=event_args)

    def test_list_with_invalid_folder_path(
        self, service: ConnectionsService, mock_folders_service: MagicMock
    ) -> None:
        """Test that ValueError is raised when folder_path cannot be resolved."""
        mock_folders_service.retrieve_key.return_value = None

        with pytest.raises(ValueError) as exc_info:
            service.list(folder_path="NonExistent/Folder")

        assert "Folder with path 'NonExistent/Folder' not found" in str(exc_info.value)
        mock_folders_service.retrieve_key.assert_called_once_with(
            folder_path="NonExistent/Folder"
        )

    def test_list_with_name_containing_quote(
        self, httpx_mock: HTTPXMock, service: ConnectionsService
    ) -> None:
        """Test that names with quotes are properly escaped."""
        httpx_mock.add_response(json={"value": []})

        service.list(name="O'Malley")

        sent_request = httpx_mock.get_request()
        if sent_request is None:
            raise Exception("No request was sent")

        # Verify the single quote was doubled (escaped) in the OData filter
        # The URL should contain O''Malley (with doubled single quote)
        url_str = str(sent_request.url)
        # Check that the filter contains the escaped quote
        assert "O%27%27Malley" in url_str or "O''Malley" in url_str.replace(
            "%27%27", "''"
        )

    def test_list_with_raw_list_response(
        self,
        httpx_mock: HTTPXMock,
        service: ConnectionsService,
        base_url: str,
        org: str,
        tenant: str,
    ) -> None:
        """Test that list method handles raw list responses (not wrapped in 'value')."""
        # Some API endpoints return a raw list instead of OData format
        httpx_mock.add_response(
            url=f"{base_url}{org}{tenant}/connections_/api/v1/Connections?%24expand=connector%2Cfolder",
            status_code=200,
            json=[
                {
                    "id": "conn-1",
                    "name": "Direct List Connection",
                    "state": "active",
                    "elementInstanceId": 101,
                }
            ],
        )

        connections = service.list()

        assert isinstance(connections, list)
        assert len(connections) == 1
        assert connections[0].id == "conn-1"
        assert connections[0].name == "Direct List Connection"

    def test_list_with_both_folder_path_and_folder_key_raises_error(
        self, service: ConnectionsService
    ) -> None:
        """Test that providing both folder_path and folder_key raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            service.list(folder_path="Finance/Production", folder_key="folder-123")

        assert "folder_path and folder_key are mutually exclusive" in str(
            exc_info.value
        )
        assert "cannot be provided together" in str(exc_info.value)
