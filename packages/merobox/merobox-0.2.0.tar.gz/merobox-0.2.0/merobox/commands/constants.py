"""
Constants and configuration values used across the merobox codebase.
"""

# API Endpoints
JSONRPC_ENDPOINT = "/jsonrpc"
ADMIN_API_BASE = "/admin-api"
ADMIN_API_APPLICATIONS = f"{ADMIN_API_BASE}/applications"
ADMIN_API_CONTEXTS = f"{ADMIN_API_BASE}/contexts"
ADMIN_API_CONTEXTS_INVITE = f"{ADMIN_API_BASE}/contexts/invite"
ADMIN_API_CONTEXTS_JOIN = f"{ADMIN_API_BASE}/contexts/join"
ADMIN_API_IDENTITY_CONTEXT = f"{ADMIN_API_BASE}/identity/context"
ADMIN_API_HEALTH = f"{ADMIN_API_BASE}/health"
ADMIN_API_NODE_INFO = f"{ADMIN_API_BASE}/node-info"

# Default values
DEFAULT_RPC_PORT = 2528
DEFAULT_P2P_PORT = 2428
DEFAULT_CHAIN_ID = "testnet-1"
DEFAULT_PROTOCOL = "near"
DEFAULT_TIMEOUT = 30
DEFAULT_WAIT_TIMEOUT = 60

# Retry and timeout configuration
DEFAULT_RETRY_ATTEMPTS = 3
DEFAULT_RETRY_DELAY = 1.0  # seconds
DEFAULT_RETRY_BACKOFF = 2.0  # exponential backoff multiplier
DEFAULT_CONNECTION_TIMEOUT = 10.0  # seconds
DEFAULT_READ_TIMEOUT = 30.0  # seconds

# Docker configuration
DEFAULT_IMAGE = "ghcr.io/calimero-network/merod:edge"
DEFAULT_NODE_PREFIX = "calimero-node"
DEFAULT_DATA_DIR_PREFIX = "data"

# Response field names (from API responses)
FIELD_APPLICATION_ID = "applicationId"
FIELD_CONTEXT_ID = "contextId"
FIELD_MEMBER_PUBLIC_KEY = "memberPublicKey"
FIELD_PUBLIC_KEY = "publicKey"
FIELD_IDENTITY_ID = "id"
FIELD_INVITATION = "invitation"
FIELD_RESULT = "result"
FIELD_OUTPUT = "output"
FIELD_DATA = "data"
FIELD_SUCCESS = "success"
FIELD_ERROR = "error"

# Workflow step types
STEP_INSTALL_APPLICATION = "install_application"
STEP_CREATE_CONTEXT = "create_context"
STEP_CREATE_IDENTITY = "create_identity"
STEP_INVITE_IDENTITY = "invite_identity"
STEP_JOIN_CONTEXT = "join_context"
STEP_CALL = "call"
STEP_WAIT = "wait"
STEP_REPEAT = "repeat"
STEP_GET_PROPOSAL = "get_proposal"
STEP_LIST_PROPOSALS = "list_proposals"
STEP_GET_PROPOSAL_APPROVERS = "get_proposal_approvers"

# Protocol types
PROTOCOL_NEAR = "near"
PROTOCOL_ETHEREUM = "ethereum"
PROTOCOL_ICP = "icp"
PROTOCOL_STARKNET = "starknet"
PROTOCOL_STELLAR = "stellar"

# Network types
NETWORK_MAINNET = "mainnet"
NETWORK_TESTNET = "testnet"
NETWORK_LOCAL = "local"

# Valid protocol networks mapping
VALID_NETWORKS = {
    PROTOCOL_ETHEREUM: [NETWORK_MAINNET, "sepolia", "goerli", NETWORK_LOCAL],
    PROTOCOL_ICP: [NETWORK_MAINNET, NETWORK_TESTNET, NETWORK_LOCAL],
    PROTOCOL_NEAR: [NETWORK_MAINNET, NETWORK_TESTNET, NETWORK_LOCAL],
    PROTOCOL_STARKNET: [NETWORK_MAINNET, "sepolia", "goerli", NETWORK_LOCAL],
    PROTOCOL_STELLAR: [NETWORK_MAINNET, NETWORK_TESTNET, NETWORK_LOCAL],
}

# Container data directory patterns
CONTAINER_DATA_DIR_PATTERNS = [
    "data/{prefix}-{node_num}-{chain_id}",
    "data/{node_name}",
]

# JSON-RPC method names
JSONRPC_METHOD_EXECUTE = "execute"

# Default metadata
DEFAULT_METADATA = b""

# Error messages
ERROR_NODE_NOT_RUNNING = "Node {node} is not running"
ERROR_NODE_NOT_FOUND = "Node {node} not found"
ERROR_INVALID_URL = "Invalid URL: {url}"
ERROR_INVALID_PORT = "Port must be between 1 and 65535"
ERROR_FILE_NOT_FOUND = "File not found: {path}"
ERROR_CONTAINER_DATA_DIR_NOT_FOUND = "Container data directory not found: {dir}"
