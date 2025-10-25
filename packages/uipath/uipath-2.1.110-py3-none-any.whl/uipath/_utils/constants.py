# Environment variables
DOTENV_FILE = ".env"
ENV_BASE_URL = "UIPATH_URL"
ENV_EVAL_BACKEND_URL = "UIPATH_EVAL_BACKEND_URL"
ENV_UNATTENDED_USER_ACCESS_TOKEN = "UNATTENDED_USER_ACCESS_TOKEN"
ENV_UIPATH_ACCESS_TOKEN = "UIPATH_ACCESS_TOKEN"
ENV_FOLDER_KEY = "UIPATH_FOLDER_KEY"
ENV_FOLDER_PATH = "UIPATH_FOLDER_PATH"
ENV_JOB_KEY = "UIPATH_JOB_KEY"
ENV_JOB_ID = "UIPATH_JOB_ID"
ENV_ROBOT_KEY = "UIPATH_ROBOT_KEY"
ENV_TENANT_ID = "UIPATH_TENANT_ID"
ENV_ORGANIZATION_ID = "UIPATH_ORGANIZATION_ID"
ENV_TELEMETRY_ENABLED = "UIPATH_TELEMETRY_ENABLED"

# Headers
HEADER_FOLDER_KEY = "x-uipath-folderkey"
HEADER_FOLDER_PATH = "x-uipath-folderpath"
HEADER_USER_AGENT = "x-uipath-user-agent"
HEADER_TENANT_ID = "x-uipath-tenantid"
HEADER_INTERNAL_TENANT_ID = "x-uipath-internal-tenantid"
HEADER_JOB_KEY = "x-uipath-jobkey"
HEADER_SW_LOCK_KEY = "x-uipath-sw-lockkey"

# Data sources
ORCHESTRATOR_STORAGE_BUCKET_DATA_SOURCE = (
    "#UiPath.Vdbs.Domain.Api.V20Models.StorageBucketDataSourceRequest"
)
CONFLUENCE_DATA_SOURCE = "#UiPath.Vdbs.Domain.Api.V20Models.ConfluenceDataSourceRequest"
DROPBOX_DATA_SOURCE = "#UiPath.Vdbs.Domain.Api.V20Models.DropboxDataSourceRequest"
GOOGLE_DRIVE_DATA_SOURCE = (
    "#UiPath.Vdbs.Domain.Api.V20Models.GoogleDriveDataSourceRequest"
)
ONEDRIVE_DATA_SOURCE = "#UiPath.Vdbs.Domain.Api.V20Models.OneDriveDataSourceRequest"

# Preprocessing request types
LLMV3Mini = "#UiPath.Vdbs.Domain.Api.V20Models.LLMV3MiniPreProcessingRequest"
LLMV4 = "#UiPath.Vdbs.Domain.Api.V20Models.LLMV4PreProcessingRequest"
NativeV1 = "#UiPath.Vdbs.Domain.Api.V20Models.NativeV1PreProcessingRequest"


# Local storage
TEMP_ATTACHMENTS_FOLDER = "uipath_attachments"

# LLM models
COMMUNITY_agents_SUFFIX = "-community-agents"

# File names
UIPATH_CONFIG_FILE = "uipath.json"

# Evaluators
CUSTOM_EVALUATOR_PREFIX = "file://"
