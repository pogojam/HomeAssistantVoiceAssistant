"""Constants for OpenAI Realtime Assistant."""

DOMAIN = "openai_realtime_assistant"

# Configuration constants
CONF_MODEL = "model"
CONF_VOICE = "voice"
CONF_TEMPERATURE = "temperature"
CONF_SYSTEM_PROMPT = "system_prompt"
CONF_ENABLE_HOME_CONTROL = "enable_home_control"
CONF_CONVERSATION_TIMEOUT = "conversation_timeout"

# Default values
DEFAULT_MODEL = "gpt-4o-realtime-preview"
DEFAULT_VOICE = "alloy"
DEFAULT_TEMPERATURE = 0.7
DEFAULT_SYSTEM_PROMPT = "You are a helpful home assistant. You can control smart home devices and answer questions."
DEFAULT_CONVERSATION_TIMEOUT = 30

# OpenAI Realtime API constants
OPENAI_REALTIME_URL = "wss://api.openai.com/v1/realtime"
AUDIO_FORMAT = "pcm16"
SAMPLE_RATE = 16000
CHANNELS = 1

# Voice options
VOICE_OPTIONS = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]

# WebSocket event types
WS_EVENT_SESSION_CREATED = "session.created"
WS_EVENT_SESSION_UPDATED = "session.updated"
WS_EVENT_INPUT_AUDIO_BUFFER_APPEND = "input_audio_buffer.append"
WS_EVENT_INPUT_AUDIO_BUFFER_COMMIT = "input_audio_buffer.commit"
WS_EVENT_INPUT_AUDIO_BUFFER_CLEAR = "input_audio_buffer.clear"
WS_EVENT_CONVERSATION_ITEM_CREATE = "conversation.item.create"
WS_EVENT_RESPONSE_CREATE = "response.create"
WS_EVENT_RESPONSE_AUDIO_DELTA = "response.audio.delta"
WS_EVENT_RESPONSE_TEXT_DELTA = "response.text.delta"
WS_EVENT_RESPONSE_FUNCTION_CALL = "response.function_call_arguments"
WS_EVENT_ERROR = "error"

# Audio processing constants
AUDIO_CHUNK_SIZE = 1024
AUDIO_BUFFER_SIZE = 16384
VAD_THRESHOLD = 0.5