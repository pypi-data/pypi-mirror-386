## API Reference

This section provides a comprehensive reference for all UiPath SDK services and methods. Each service is documented with complete method signatures, including parameter types and return types.

### SDK Initialization

Initialize the UiPath SDK client

```python
from uipath import UiPath

# Initialize with environment variables
sdk = UiPath()

# Or with explicit credentials
sdk = UiPath(base_url="https://cloud.uipath.com/...", secret="your_token")
```

### Actions

Actions service

```python
# Creates a new action synchronously.
sdk.actions.create(title: str, data: Optional[Dict[str, Any]]=None, app_name: Optional[str]=None, app_key: Optional[str]=None, app_folder_path: Optional[str]=None, app_folder_key: Optional[str]=None, app_version: Optional[int]=1, assignee: Optional[str]=None) -> uipath.models.actions.Action

# Creates a new action asynchronously.
sdk.actions.create_async(title: str, data: Optional[Dict[str, Any]]=None, app_name: Optional[str]=None, app_key: Optional[str]=None, app_folder_path: Optional[str]=None, app_folder_key: Optional[str]=None, app_version: Optional[int]=1, assignee: Optional[str]=None) -> uipath.models.actions.Action

# Retrieves an action by its key synchronously.
sdk.actions.retrieve(action_key: str, app_folder_path: str="", app_folder_key: str="") -> uipath.models.actions.Action

# Retrieves an action by its key asynchronously.
sdk.actions.retrieve_async(action_key: str, app_folder_path: str="", app_folder_key: str="") -> uipath.models.actions.Action

```

### Api Client

Api Client service

```python
# Access api_client service methods
service = sdk.api_client

```

### Assets

Assets service

```python
# Retrieve an asset by its name.
sdk.assets.retrieve(name: str, folder_key: Optional[str]=None, folder_path: Optional[str]=None) -> uipath.models.assets.UserAsset | uipath.models.assets.Asset

# Asynchronously retrieve an asset by its name.
sdk.assets.retrieve_async(name: str, folder_key: Optional[str]=None, folder_path: Optional[str]=None) -> uipath.models.assets.UserAsset | uipath.models.assets.Asset

# Gets a specified Orchestrator credential.
sdk.assets.retrieve_credential(name: str, folder_key: Optional[str]=None, folder_path: Optional[str]=None) -> typing.Optional[str]

# Asynchronously gets a specified Orchestrator credential.
sdk.assets.retrieve_credential_async(name: str, folder_key: Optional[str]=None, folder_path: Optional[str]=None) -> typing.Optional[str]

# Update an asset's value.
sdk.assets.update(robot_asset: uipath.models.assets.UserAsset, folder_key: Optional[str]=None, folder_path: Optional[str]=None) -> httpx.Response

# Asynchronously update an asset's value.
sdk.assets.update_async(robot_asset: uipath.models.assets.UserAsset, folder_key: Optional[str]=None, folder_path: Optional[str]=None) -> httpx.Response

```

### Context Grounding

Context Grounding service

```python
# Add content to the index.
sdk.context_grounding.add_to_index(name: str, blob_file_path: str, content_type: Optional[str]=None, content: Union[str, bytes, NoneType]=None, source_path: Optional[str]=None, folder_key: Optional[str]=None, folder_path: Optional[str]=None, ingest_data: bool=True) -> None

# Asynchronously add content to the index.
sdk.context_grounding.add_to_index_async(name: str, blob_file_path: str, content_type: Optional[str]=None, content: Union[str, bytes, NoneType]=None, source_path: Optional[str]=None, folder_key: Optional[str]=None, folder_path: Optional[str]=None, ingest_data: bool=True) -> None

# Create a new context grounding index.
sdk.context_grounding.create_index(name: str, source: Dict[str, Any], description: Optional[str]=None, cron_expression: Optional[str]=None, time_zone_id: Optional[str]=None, advanced_ingestion: Optional[bool]=True, preprocessing_request: Optional[str]="#UiPath.Vdbs.Domain.Api.V20Models.LLMV4PreProcessingRequest", folder_key: Optional[str]=None, folder_path: Optional[str]=None) -> uipath.models.context_grounding_index.ContextGroundingIndex

# Create a new context grounding index.
sdk.context_grounding.create_index_async(name: str, source: Dict[str, Any], description: Optional[str]=None, cron_expression: Optional[str]=None, time_zone_id: Optional[str]=None, advanced_ingestion: Optional[bool]=True, preprocessing_request: Optional[str]="#UiPath.Vdbs.Domain.Api.V20Models.LLMV4PreProcessingRequest", folder_key: Optional[str]=None, folder_path: Optional[str]=None) -> uipath.models.context_grounding_index.ContextGroundingIndex

# Delete a context grounding index.
sdk.context_grounding.delete_index(index: uipath.models.context_grounding_index.ContextGroundingIndex, folder_key: Optional[str]=None, folder_path: Optional[str]=None) -> None

# Asynchronously delete a context grounding index.
sdk.context_grounding.delete_index_async(index: uipath.models.context_grounding_index.ContextGroundingIndex, folder_key: Optional[str]=None, folder_path: Optional[str]=None) -> None

# Ingest data into the context grounding index.
sdk.context_grounding.ingest_data(index: uipath.models.context_grounding_index.ContextGroundingIndex, folder_key: Optional[str]=None, folder_path: Optional[str]=None) -> None

# Asynchronously ingest data into the context grounding index.
sdk.context_grounding.ingest_data_async(index: uipath.models.context_grounding_index.ContextGroundingIndex, folder_key: Optional[str]=None, folder_path: Optional[str]=None) -> None

# Retrieve context grounding index information by its name.
sdk.context_grounding.retrieve(name: str, folder_key: Optional[str]=None, folder_path: Optional[str]=None) -> uipath.models.context_grounding_index.ContextGroundingIndex

# Asynchronously retrieve context grounding index information by its name.
sdk.context_grounding.retrieve_async(name: str, folder_key: Optional[str]=None, folder_path: Optional[str]=None) -> uipath.models.context_grounding_index.ContextGroundingIndex

# Retrieve context grounding index information by its ID.
sdk.context_grounding.retrieve_by_id(id: str, folder_key: Optional[str]=None, folder_path: Optional[str]=None) -> typing.Any

# Retrieve asynchronously context grounding index information by its ID.
sdk.context_grounding.retrieve_by_id_async(id: str, folder_key: Optional[str]=None, folder_path: Optional[str]=None) -> typing.Any

# Search for contextual information within a specific index.
sdk.context_grounding.search(name: str, query: str, number_of_results: int=10, folder_key: Optional[str]=None, folder_path: Optional[str]=None) -> typing.List[uipath.models.context_grounding.ContextGroundingQueryResponse]

# Search asynchronously for contextual information within a specific index.
sdk.context_grounding.search_async(name: str, query: str, number_of_results: int=10, folder_key: Optional[str]=None, folder_path: Optional[str]=None) -> typing.List[uipath.models.context_grounding.ContextGroundingQueryResponse]

```

### Documents

Documents service

```python
# Create a validation action for a document based on the extraction response. More details about validation actions can be found in the [official documentation](https://docs.uipath.com/ixp/automation-cloud/latest/user-guide/validating-extractions).
sdk.documents.create_validation_action(action_title: str, action_priority: <enum 'ActionPriority, action_catalog: str, action_folder: str, storage_bucket_name: str, storage_bucket_directory_path: str, extraction_response: uipath.models.documents.ExtractionResponse) -> uipath.models.documents.ValidationAction

# Asynchronously create a validation action for a document based on the extraction response.
sdk.documents.create_validation_action_async(action_title: str, action_priority: <enum 'ActionPriority, action_catalog: str, action_folder: str, storage_bucket_name: str, storage_bucket_directory_path: str, extraction_response: uipath.models.documents.ExtractionResponse) -> uipath.models.documents.ValidationAction

# Extract predicted data from a document using an IXP project.
sdk.documents.extract(project_name: str, tag: str, file: Union[IO[bytes], bytes, str, NoneType]=None, file_path: Optional[str]=None) -> uipath.models.documents.ExtractionResponse

# Asynchronously extract predicted data from a document using an IXP project.
sdk.documents.extract_async(project_name: str, tag: str, file: Union[IO[bytes], bytes, str, NoneType]=None, file_path: Optional[str]=None) -> uipath.models.documents.ExtractionResponse

# Get the result of a validation action.
sdk.documents.get_validation_result(validation_action: uipath.models.documents.ValidationAction) -> uipath.models.documents.ValidatedResult

# Asynchronously get the result of a validation action.
sdk.documents.get_validation_result_async(validation_action: uipath.models.documents.ValidationAction) -> uipath.models.documents.ValidatedResult

```

### Entities

Entities service

```python
# Delete multiple records from an entity in a single batch operation.
sdk.entities.delete_records(entity_key: str, record_ids: List[str]) -> uipath.models.entities.EntityRecordsBatchResponse

# Asynchronously delete multiple records from an entity in a single batch operation.
sdk.entities.delete_records_async(entity_key: str, record_ids: List[str]) -> uipath.models.entities.EntityRecordsBatchResponse

# Insert multiple records into an entity in a single batch operation.
sdk.entities.insert_records(entity_key: str, records: List[Any], schema: Optional[Type[Any]]=None) -> uipath.models.entities.EntityRecordsBatchResponse

# Asynchronously insert multiple records into an entity in a single batch operation.
sdk.entities.insert_records_async(entity_key: str, records: List[Any], schema: Optional[Type[Any]]=None) -> uipath.models.entities.EntityRecordsBatchResponse

# List all entities in the Data Service.
sdk.entities.list_entities() -> typing.List[uipath.models.entities.Entity]

# Asynchronously list all entities in the Data Service.
sdk.entities.list_entities_async() -> typing.List[uipath.models.entities.Entity]

# List records from an entity with optional pagination and schema validation.
sdk.entities.list_records(entity_key: str, schema: Optional[Type[Any]]=None, start: Optional[int]=None, limit: Optional[int]=None) -> typing.List[uipath.models.entities.EntityRecord]

# Asynchronously list records from an entity with optional pagination and schema validation.
sdk.entities.list_records_async(entity_key: str, schema: Optional[Type[Any]]=None, start: Optional[int]=None, limit: Optional[int]=None) -> typing.List[uipath.models.entities.EntityRecord]

# Retrieve an entity by its key.
sdk.entities.retrieve(entity_key: str) -> uipath.models.entities.Entity

# Asynchronously retrieve an entity by its key.
sdk.entities.retrieve_async(entity_key: str) -> uipath.models.entities.Entity

# Update multiple records in an entity in a single batch operation.
sdk.entities.update_records(entity_key: str, records: List[Any], schema: Optional[Type[Any]]=None) -> uipath.models.entities.EntityRecordsBatchResponse

# Asynchronously update multiple records in an entity in a single batch operation.
sdk.entities.update_records_async(entity_key: str, records: List[Any], schema: Optional[Type[Any]]=None) -> uipath.models.entities.EntityRecordsBatchResponse

```

### Jobs

Jobs service

```python
# Create and upload an attachment, optionally linking it to a job.
sdk.jobs.create_attachment(name: str, content: Union[str, bytes, NoneType]=None, source_path: Union[str, pathlib.Path, NoneType]=None, job_key: Union[str, uuid.UUID, NoneType]=None, category: Optional[str]=None, folder_key: Optional[str]=None, folder_path: Optional[str]=None) -> uuid.UUID

# Create and upload an attachment asynchronously, optionally linking it to a job.
sdk.jobs.create_attachment_async(name: str, content: Union[str, bytes, NoneType]=None, source_path: Union[str, pathlib.Path, NoneType]=None, job_key: Union[str, uuid.UUID, NoneType]=None, category: Optional[str]=None, folder_key: Optional[str]=None, folder_path: Optional[str]=None) -> uuid.UUID

# Get the actual output data, downloading from attachment if necessary.
sdk.jobs.extract_output(job: uipath.models.job.Job) -> typing.Optional[str]

# Asynchronously fetch the actual output data, downloading from attachment if necessary.
sdk.jobs.extract_output_async(job: uipath.models.job.Job) -> typing.Optional[str]

# Link an attachment to a job.
sdk.jobs.link_attachment(attachment_key: uuid.UUID, job_key: uuid.UUID, category: Optional[str]=None, folder_key: Optional[str]=None, folder_path: Optional[str]=None)

# Link an attachment to a job asynchronously.
sdk.jobs.link_attachment_async(attachment_key: uuid.UUID, job_key: uuid.UUID, category: Optional[str]=None, folder_key: Optional[str]=None, folder_path: Optional[str]=None)

# List attachments associated with a specific job.
sdk.jobs.list_attachments(job_key: uuid.UUID, folder_key: Optional[str]=None, folder_path: Optional[str]=None) -> typing.List[str]

# List attachments associated with a specific job asynchronously.
sdk.jobs.list_attachments_async(job_key: uuid.UUID, folder_key: Optional[str]=None, folder_path: Optional[str]=None) -> typing.List[str]

# Sends a payload to resume a paused job waiting for input, identified by its inbox ID.
sdk.jobs.resume(inbox_id: Optional[str]=None, job_id: Optional[str]=None, folder_key: Optional[str]=None, folder_path: Optional[str]=None, payload: Any) -> None

# Asynchronously sends a payload to resume a paused job waiting for input, identified by its inbox ID.
sdk.jobs.resume_async(inbox_id: Optional[str]=None, job_id: Optional[str]=None, folder_key: Optional[str]=None, folder_path: Optional[str]=None, payload: Any) -> None

# Retrieve a job identified by its key.
sdk.jobs.retrieve(job_key: str, folder_key: Optional[str]=None, folder_path: Optional[str]=None) -> uipath.models.job.Job

# Fetch payload data for API triggers.
sdk.jobs.retrieve_api_payload(inbox_id: str) -> typing.Any

# Asynchronously fetch payload data for API triggers.
sdk.jobs.retrieve_api_payload_async(inbox_id: str) -> typing.Any

# Asynchronously retrieve a job identified by its key.
sdk.jobs.retrieve_async(job_key: str, folder_key: Optional[str]=None, folder_path: Optional[str]=None) -> uipath.models.job.Job

```

### Llm

Llm service

```python
# Generate chat completions using UiPath's normalized LLM Gateway API.
sdk.llm.chat_completions(messages: Union[List[Dict[str, str]], List[tuple[str, str]]], model: str="gpt-4o-mini-2024-07-18", max_tokens: int=4096, temperature: float=0, n: int=1, frequency_penalty: float=0, presence_penalty: float=0, top_p: Optional[float]=1, top_k: Optional[int]=None, tools: Optional[List[uipath.models.llm_gateway.ToolDefinition]]=None, tool_choice: Union[uipath.models.llm_gateway.AutoToolChoice, uipath.models.llm_gateway.RequiredToolChoice, uipath.models.llm_gateway.SpecificToolChoice, Literal['auto', 'none'], NoneType]=None, response_format: Union[Dict[str, Any], type[pydantic.main.BaseModel], NoneType]=None, api_version: str="2024-08-01-preview")

```

### Llm Openai

Llm Openai service

```python
# Generate chat completions using UiPath's LLM Gateway service.
sdk.llm_openai.chat_completions(messages: List[Dict[str, str]], model: str="gpt-4o-mini-2024-07-18", max_tokens: int=4096, temperature: float=0, response_format: Union[Dict[str, Any], type[pydantic.main.BaseModel], NoneType]=None, api_version: str="2024-10-21")

# Generate text embeddings using UiPath's LLM Gateway service.
sdk.llm_openai.embeddings(input: str, embedding_model: str="text-embedding-ada-002", openai_api_version: str="2024-10-21")

```

### Processes

Processes service

```python
# Start execution of a process by its name.
sdk.processes.invoke(name: str, input_arguments: Optional[Dict[str, Any]]=None, folder_key: Optional[str]=None, folder_path: Optional[str]=None) -> uipath.models.job.Job

# Asynchronously start execution of a process by its name.
sdk.processes.invoke_async(name: str, input_arguments: Optional[Dict[str, Any]]=None, folder_key: Optional[str]=None, folder_path: Optional[str]=None) -> uipath.models.job.Job

```

### Queues

Queues service

```python
# Completes a transaction item with the specified result.
sdk.queues.complete_transaction_item(transaction_key: str, result: Union[Dict[str, Any], uipath.models.queues.TransactionItemResult]) -> httpx.Response

# Asynchronously completes a transaction item with the specified result.
sdk.queues.complete_transaction_item_async(transaction_key: str, result: Union[Dict[str, Any], uipath.models.queues.TransactionItemResult]) -> httpx.Response

# Creates a new queue item in the Orchestrator.
sdk.queues.create_item(item: Union[Dict[str, Any], uipath.models.queues.QueueItem]) -> httpx.Response

# Asynchronously creates a new queue item in the Orchestrator.
sdk.queues.create_item_async(item: Union[Dict[str, Any], uipath.models.queues.QueueItem]) -> httpx.Response

# Creates multiple queue items in bulk.
sdk.queues.create_items(items: List[Union[Dict[str, Any], uipath.models.queues.QueueItem]], queue_name: str, commit_type: <enum 'CommitType) -> httpx.Response

# Asynchronously creates multiple queue items in bulk.
sdk.queues.create_items_async(items: List[Union[Dict[str, Any], uipath.models.queues.QueueItem]], queue_name: str, commit_type: <enum 'CommitType) -> httpx.Response

# Creates a new transaction item in a queue.
sdk.queues.create_transaction_item(item: Union[Dict[str, Any], uipath.models.queues.TransactionItem], no_robot: bool=False) -> httpx.Response

# Asynchronously creates a new transaction item in a queue.
sdk.queues.create_transaction_item_async(item: Union[Dict[str, Any], uipath.models.queues.TransactionItem], no_robot: bool=False) -> httpx.Response

# Retrieves a list of queue items from the Orchestrator.
sdk.queues.list_items() -> httpx.Response

# Asynchronously retrieves a list of queue items from the Orchestrator.
sdk.queues.list_items_async() -> httpx.Response

# Updates the progress of a transaction item.
sdk.queues.update_progress_of_transaction_item(transaction_key: str, progress: str) -> httpx.Response

# Asynchronously updates the progress of a transaction item.
sdk.queues.update_progress_of_transaction_item_async(transaction_key: str, progress: str) -> httpx.Response

```

