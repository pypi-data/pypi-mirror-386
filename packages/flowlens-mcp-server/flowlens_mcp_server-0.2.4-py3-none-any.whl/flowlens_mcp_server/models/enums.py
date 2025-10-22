from enum import Enum

class RequestType(Enum):
    GET = "GET"
    POST = "POST"
    PATCH = "PATCH"
    PUT = "PUT"
    DELETE = "DELETE"
    
class ProcessingStatus(Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    
class RecordingType(Enum):
    WEBM = "WEBM"
    RRWEB = "RRWEB"
    
class TimelineEventType(Enum):
    NETWORK_REQUEST = "network_request"
    NETWORK_RESPONSE = "network_response"
    NETWORK_REQUEST_WITH_RESPONSE = "network_request_with_response"
    NETWORK_REQUEST_PENDING = "network_request_pending"
    LOCAL_STORAGE = "local_storage"
    SESSION_STORAGE = "session_storage"
    DOM_ACTION = "dom_action"
    NAVIGATION = "navigation"
    CONSOLE_WARNING = "console_warn"
    CONSOLE_ERROR = "console_error"
    JAVASCRIPT_ERROR = "javascript_error"
    WEBSOCKET_CREATED = "websocket_created"
    WEBSOCKET_HANDSHAKE_REQUEST = "websocket_handshake_request"
    WEBSOCKET_HANDSHAKE_RESPONSE = "websocket_handshake_response"
    WEBSOCKET_FRAME_SENT = "websocket_frame_sent"
    WEBSOCKET_FRAME_RECEIVED = "websocket_frame_received"
    WEBSOCKET_CLOSED = "websocket_closed"
    

class ActionType(Enum):
    DEBUGGER_REQUEST = "debugger_request"
    DEBUGGER_RESPONSE = "debugger_response"
    DEBUGGER_REQUEST_WITH_RESPONSE = "debugger_request_with_response"
    DEBUGGER_REQUEST_PENDING = "debugger_request_pending"
    CLICK = "click"
    KEYDOWN_SESSION = "keydown_session"
    GET = "get"
    SET = "set"
    CLEAR = "clear"
    REMOVE = "remove"
    HISTORY_CHANGE = "history_change"
    WARNING_LOGGED = "warning_logged"
    ERROR_LOGGED = "error_logged"
    ERROR_CAPTURED = "error_captured"
    CONNECTION_OPENED = "connection_opened"
    HANDSHAKE_REQUEST = "handshake_request"
    HANDSHAKE_RESPONSE = "handshake_response"
    MESSAGE_SENT = "message_sent"
    MESSAGE_RECEIVED = "message_received"
    CONNECTION_CLOSED = "connection_closed"
    UNKNOWN = "unknown"