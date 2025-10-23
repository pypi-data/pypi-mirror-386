
"""
Constants used throughout the sdk
"""

import os

# -----GENERAL-----#

PACKAGE_NAME = "r7_surcom_sdk"
DISPLAY_NAME = "Surface Command SDK"
PLATFORM_NAME = "Rapid7 Surface Command Platform"
PRODUCT_NAME = "Surface Command"
PROGRAM_NAME = "surcom"
FULL_PROGRAM_NAME = "surcom-sdk"
SUPPORT_LINK = "https://www.rapid7.com/for-customers"

LOGGER_NAME = "r7_surcom_sdk_logger"
LOG_DIVIDER = "-----------------------"
PYTEST_MARKER_SDK_CLI = "sdk_cli"
MAX_INPUT_TRIES = 3
NOETIC_BUILTINS_VERSION = "1.0.821"
DEBUG_PORT = "5678"
ENCODING_UTF8_SIG = "utf-8-sig"
ENCODING_UTF8 = "utf-8"
DEFAULT_EXT_LIB_API_URL = "https://extensions-api.rapid7.com"

DATE_FORMAT_NOETIC = "%Y-%m-%d"
DATE_FORMAT_EXT_LIB = "%m/%d/%Y"

RUNTIME_MAP = {
    "py311": "noetic-fission-py311"
}

LEGACY_PREFIX = "__legacy__"

# A Surcom Connector has a connector.spec.yaml file
SURCOM_CONNECTOR = "SURCOM_CONNECTOR"

# A Legacy Connector has a manifest.yaml file
LEGACY_CONNECTOR = "LEGACY_CONNECTOR"

# 1Password Secret References are prefixed with this
OP_PREFIX = "op://"
ENV_OP_CLI = "ONEPASSWORD_CLI_PATH"

INSIGHT_CONNECT_MODULE = "insightconnect_plugin_runtime"

TEMPLATE_PATH_CONNECTORS = "data/cmds/connector"
TEMPLATE_PATH_CODEGEN = f"{TEMPLATE_PATH_CONNECTORS}/codegen"
TEMPLATE_PATH_FUNCTIONS = f"{TEMPLATE_PATH_CODEGEN}/functions"
TEMPLATE_PATH_TYPES = f"{TEMPLATE_PATH_CODEGEN}/types"
TEMPLATE_PATH_DOCS = f"{TEMPLATE_PATH_CODEGEN}/docs"
TEMPLATE_PATH_PACKAGE = f"{TEMPLATE_PATH_CONNECTORS}/package"
TEMPLATE_PATH_PLUGIN = f"{TEMPLATE_PATH_CONNECTORS}/package/plugin"
TEMPLATE_PATH_PLUGIN_SRC = f"{TEMPLATE_PATH_PLUGIN}/src"
TEMPLATE_PATH_PLUGIN_CONNECTION = f"{TEMPLATE_PATH_PLUGIN_SRC}/connection"
TEMPLATE_PATH_PLUGIN_ACTIONS = f"{TEMPLATE_PATH_PLUGIN_SRC}/actions"
TEMPLATE_PATH_PLUGIN_ACTION = f"{TEMPLATE_PATH_PLUGIN_SRC}/actions/plugin_action"
TEMPLATE_PATH_PLUGIN_UTIL = f"{TEMPLATE_PATH_PLUGIN_SRC}/util"
TEMPLATE_PATH_INVOKE = f"{TEMPLATE_PATH_CONNECTORS}/invoke"
TEMPLATE_PATH_DEV = "data/cmds/dev"

# -----ENV VARS -----#
ENV_SURCOM_SDK_PATH_ROOT = "SURCOM_SDK_PATH_ROOT"
ENV_SURCOM_SDK_PATH_SURCOM_CONFIG = "SURCOM_SDK_PATH_SURCOM_CONFIG"
ENV_SURCOM_SDK_DEV_MODE = "SURCOM_SDK_DEV_MODE"

# -----BUILTIN CONNECTOR IDS-----#
NOETIC_BUILTINS_ID = "noetic.builtins.app"

# -----MAIN CMDS-----#

CMD_MAIN = "main"
CMD_COMMANDS = "commands"
CMD_CONFIG = "config"
CMD_CONNECTORS = "connector"
CMD_DATA = "data"
CMD_TYPES = "type"
CMD_DEV = "dev"

# -----SUB CMDS------#

CMD_INIT = "init"
CMD_LIST_CONNECTIONS = "list"
CMD_ADD_CONNECTION = "add"
CMD_TEST_CONNECTION = "test"
CMD_DELETE_CONNECTION = "delete"
CMD_SET_ACTIVE = "set-active"
CMD_CODEGEN = "codegen"
CMD_VALIDATE = "validate"
CMD_PACKAGE = "package"
CMD_BUILD = "build"
CMD_INVOKE = "invoke"
CMD_IMPORT = "import"
CMD_GENERATE = "generate"
CMD_INSTALL = "install"
CMD_ENABLE_TABS = "enable-tabs"
CMD_EXT_LIBRARY_DOCS = "ext-lib-docs"

# -----CONFIGS------#

DIR_NAME_SURCOM_ROOT = ".r7-surcom-sdk"
PATH_USER = os.path.expanduser("~")
PATH_SURCOM_ROOT = os.getenv(ENV_SURCOM_SDK_PATH_ROOT, default=os.path.join(PATH_USER, DIR_NAME_SURCOM_ROOT))
CONFIG_FILE_NAME = "surcom_config"

PATH_SURCOM_CONFIG_FILE = os.getenv(
    ENV_SURCOM_SDK_PATH_SURCOM_CONFIG,
    default=os.path.join(PATH_SURCOM_ROOT, CONFIG_FILE_NAME)
)

CONFIG_SEC_MAIN = FULL_PROGRAM_NAME
CONFIG_NAME_PATH_CONNECTOR_WS = "path_connector_ws"
CONFIG_NAME_EXT_LIB_URL = "extensions_library_url"
CONFIG_NAME_USE_EXT_LIB = "use_extensions_library"
CONFIG_NAME_USE_ARTIFACTORY = "use_artifactory"
CONFIG_NAME_URL = "url"
CONFIG_NAME_API_KEY = "api_key"
CONFIG_NAME_ACTIVE = "active"
CONFIG_SEC_CONN_PREFIX = "connection"
CONFIG_SEC_CONNECTOR_PREFIX = "connector"

CONFIG_DEFAULT_URL = "us.surface.insight.rapid7.com"
CONFIG_DEFAULT_CONNECTOR_DEV = os.path.join(PATH_USER, "development", "r7-surcom-connectors")

# List of tuples, where each tuple is a section and a config
REQ_CONFIGS = [(CONFIG_SEC_MAIN, CONFIG_NAME_PATH_CONNECTOR_WS)]

REQ_CONNECTION_CONFIGS = [CONFIG_NAME_URL, CONFIG_NAME_API_KEY, CONFIG_NAME_ACTIVE]

# ---TEMPLATE/FILE/DIRECTORY NAMES----#

CONN_SPEC_YAML = "connector.spec.yaml"
MANIFEST_YAML = "manifest.yaml"
TEMPLATE_REQ_TXT = "requirements.txt"
TEMPLATE_INIT_PY = "__init__.py"
TEMPLATE_MAIN_PY = "__main__.py"
TEMPLATE_SETTINGS_PY = "sc_settings.py"
TEMPLATE_TEST_FN_PY = "fn_test.py"
TEMPLATE_IMPORT_FN_PY = "fn_import.py"
TEMPLATE_HELPERS_PY = "helpers.py"
TEMPLATE_TYPES_PY = "sc_types.py"
TEMPLATE_TYPES_YAML = "surcom_type.yaml"
TEMPLATE_TYPE_GENERATED_YAML = "surcom_type_generated.yaml"
TEMPLATE_DOCKERFILE_SIMPLE = "SimpleDockerfile"
TEMPLATE_ENV_FILE = "env"
TEMPLATE_EXT_LIB_MD = "ext_library_template.md"
TEMPLATE_ACTION_IMPORT_FN_PY = "action_import_fn.py"
TEMPLATE_ACTION_LEGACY_FN_PY = "action_legacy_fn.py"
TEMPLATE_IMPORT_ACTION_PY = "action_import_fn.py"
TEMPLATE_PYPROJECT_TOML = "pyproject.toml"
FILENAME_ENTRYPOINT_SH = "entrypoint.sh"
FILENAME_PLUGIN_WRAPPER = "icon_plugin_wrapper.py"
FILENAME_ICON = "icon.svg"
FILENAME_INSTRUCTIONS = "INSTRUCTIONS.md"
FILENAME_DOCKERFILE = "Dockerfile"
FILENAME_CONNECTION_PY = "connection.py"
FILENAME_SCHEMA_PY = "schema.py"
FILENAME_ACTION_PY = "action.py"
DIR_NAME_TYPES = "types"
DIR_NAME_FNS = "functions"
DIR_NAME_BUILD = "build"
DIR_NAME_DOCS = "docs"
DIR_NAME_OUTPUT = "output"
DIR_NAME_SURCOM_CONNECTOR = "surcom_connector"
DIR_NAME_SURCOM_PLUGIN = "surcom_plugin"
DIR_NAME_DOCKER = "docker"
DIR_NAME_SAMPLE_DATA = "sample_data"
DIR_NAME_DATA = "data"
DIR_NAME_REFDOCS = "refdocs"


# -----PACKAGE------#

MANIFEST_KEY_README = "readme"
MANIFEST_KEY_REQUIREMENTS = "requirements"
MANIFEST_KEY_DESC = "description"
MD_SECTION_DESCRIPTION = "__Description__"
MD_SECTION_OVERVIEW = "__Overview__"
MD_SECTION_DOCUMENTATION = "__Documentation__"
MD_SECTION_SETUP = "__Setup__"
REGEX_SS_REFERENCES = r"\(([^)]+\.png)"

# -----CODEGEN------#

DIR_FUNCTIONS = "functions"

# -----VALIDATE------#

ISSUE_LEVEL_CRITICAL = "CRITICAL"
ISSUE_LEVEL_WARNING = "WARNING"
ISSUE_LEVEL_INFO = "INFO"

SCALAR_FOLDED = "folded"  # (>)
SCALAR_LITERAL = "literal"  # (|)
SCALAR_FOLDED_CHOMPED = "folded_chomped"  # (>-)
SCALAR_LITERAL_CHOMPED = "literal_chomped"  # (|-)

VALID_LEVELS = [ISSUE_LEVEL_CRITICAL, ISSUE_LEVEL_WARNING, ISSUE_LEVEL_INFO]

DEFAULT_PASS_MSG = "PASS"  # nosec

DIRECTORIES_TO_IGNORE = [
    "etc"
]

REQUIRED_MANIFEST_PROPERTIES = [
    "id", "name", "description", "publisher", "version", "icon", "notice",
    "categories", "changelog", "readme", "requirements", "environment-name"
]

REQUIRED_CONNECTOR_SPEC_PROPERTIES = [
    "id", "name", "author", "version", "notice", "current_changes",
    "types", "functions", "settings", "runtime", "categories"
]

REQUIRED_CHANGELOG_PROPERTIES = [
    "date", "text", "version"
]

TEST_FN_ID = "test"

VALID_CHANGELOG_DATE_FMT = "YYYY-MM-DD"

VALID_CATEGORIES = [
    "alerting_and_notifications",
    "application_development",
    "asset_management",
    "case_management",
    "cloud_security",
    "cloud_service_provider",
    "credential_management",
    "collaboration",
    "database",
    "endpoint_detection_response",
    "endpoint_management",
    "external_attack_surface",
    "iam",
    "network_firewall",
    "phishing",
    "remediation_management",
    "security_operations",
    "threat_intel",
    "ticketing",
    "utility",
    "vulnerability_management"
]

VALID_SETTING_TYPES = [
    "string", "boolean", "integer", "number", "array", "json"
]

ENV_NAME_SAMOS_FISSION = "samos-fission"
ENV_NAME_NOETIC_FISSION_PY311 = "noetic-fission-py311"
VALID_ENV_NAMES = [ENV_NAME_SAMOS_FISSION, ENV_NAME_NOETIC_FISSION_PY311]

DEFAULT_CURRENT_RUNTIME = "py311"
SUPPORTED_RUNTIMES = [DEFAULT_CURRENT_RUNTIME]

FN_RTN_TYPES_PROP_NAME = "x-samos-return-items"

OPEN_API_TYPES_TO_PYTHON = {
    "string": str,
    "integer": int,
    "boolean": bool,
    "number": (int, float),
    "array": list,
    "object": dict,
}

REGEX_PLAIN_TEXT = r'^[A-Za-z0-9 .,;:!?/\'"\-()\\\n]+$'

# -----TYPES------#

MAX_TYPES_TO_IMPORT = 1000
X_SAMOS_TYPE_NAME = "x-samos-type-name"

# -----REQUESTS------#

REQUESTS_TIMEOUT_SECONDS = 20
REQUEST_SUPPORTED_METHODS = ("GET", "POST", "PUT", "DELETE")
HEADER_NOETIC_TRACE_ID = "X-Noetic-Trace-Id"

# -----STRINGS------#

STATUS_OK = "ok"

# ------------------------ #
