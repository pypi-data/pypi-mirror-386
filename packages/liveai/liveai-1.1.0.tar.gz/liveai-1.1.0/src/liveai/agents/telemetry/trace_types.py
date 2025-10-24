ATTR_SPEECH_ID = "la.speech_id"
ATTR_AGENT_LABEL = "la.agent_label"
ATTR_START_TIME = "la.start_time"
ATTR_END_TIME = "la.end_time"
ATTR_RETRY_COUNT = "la.retry_count"

# session start
ATTR_JOB_ID = "la.job_id"
ATTR_AGENT_NAME = "la.agent_name"
ATTR_ROOM_NAME = "la.room_name"
ATTR_SESSION_OPTIONS = "la.session_options"

# assistant turn
ATTR_USER_INPUT = "la.user_input"
ATTR_INSTRUCTIONS = "la.instructions"
ATTR_SPEECH_INTERRUPTED = "la.interrupted"

# llm node
ATTR_CHAT_CTX = "la.chat_ctx"
ATTR_FUNCTION_TOOLS = "la.function_tools"
ATTR_RESPONSE_TEXT = "la.response.text"
ATTR_RESPONSE_FUNCTION_CALLS = "la.response.function_calls"

# function tool
ATTR_FUNCTION_TOOL_NAME = "la.function_tool.name"
ATTR_FUNCTION_TOOL_ARGS = "la.function_tool.arguments"
ATTR_FUNCTION_TOOL_IS_ERROR = "la.function_tool.is_error"
ATTR_FUNCTION_TOOL_OUTPUT = "la.function_tool.output"

# tts node
ATTR_TTS_INPUT_TEXT = "la.input_text"
ATTR_TTS_STREAMING = "la.tts.streaming"
ATTR_TTS_LABEL = "la.tts.label"

# eou detection
ATTR_EOU_PROBABILITY = "la.eou.probability"
ATTR_EOU_UNLIKELY_THRESHOLD = "la.eou.unlikely_threshold"
ATTR_EOU_DELAY = "la.eou.endpointing_delay"
ATTR_EOU_LANGUAGE = "la.eou.language"
ATTR_USER_TRANSCRIPT = "la.user_transcript"
ATTR_TRANSCRIPT_CONFIDENCE = "la.transcript_confidence"
ATTR_TRANSCRIPTION_DELAY = "la.transcription_delay"
ATTR_END_OF_UTTERANCE_DELAY = "la.end_of_utterance_delay"

# metrics
ATTR_LLM_METRICS = "la.llm_metrics"
ATTR_TTS_METRICS = "la.tts_metrics"
ATTR_REALTIME_MODEL_METRICS = "la.realtime_model_metrics"

# OpenTelemetry GenAI attributes
# OpenTelemetry specification: https://opentelemetry.io/docs/specs/semconv/registry/attributes/gen-ai/
ATTR_GEN_AI_OPERATION_NAME = "gen_ai.operation.name"
ATTR_GEN_AI_REQUEST_MODEL = "gen_ai.request.model"
ATTR_GEN_AI_USAGE_INPUT_TOKENS = "gen_ai.usage.input_tokens"
ATTR_GEN_AI_USAGE_OUTPUT_TOKENS = "gen_ai.usage.output_tokens"

# Unofficial OpenTelemetry GenAI attributes, these are namespaces recognised by LangFuse
# https://langfuse.com/integrations/native/opentelemetry#usage
# but not yet in the official OpenTelemetry specification.
ATTR_GEN_AI_USAGE_INPUT_TEXT_TOKENS = "gen_ai.usage.input_text_tokens"
ATTR_GEN_AI_USAGE_INPUT_AUDIO_TOKENS = "gen_ai.usage.input_audio_tokens"
ATTR_GEN_AI_USAGE_INPUT_CACHED_TOKENS = "gen_ai.usage.input_cached_tokens"
ATTR_GEN_AI_USAGE_OUTPUT_TEXT_TOKENS = "gen_ai.usage.output_text_tokens"
ATTR_GEN_AI_USAGE_OUTPUT_AUDIO_TOKENS = "gen_ai.usage.output_audio_tokens"

# OpenTelemetry GenAI event names (for structured logging)
EVENT_GEN_AI_SYSTEM_MESSAGE = "gen_ai.system.message"
EVENT_GEN_AI_USER_MESSAGE = "gen_ai.user.message"
EVENT_GEN_AI_ASSISTANT_MESSAGE = "gen_ai.assistant.message"
EVENT_GEN_AI_TOOL_MESSAGE = "gen_ai.tool.message"
EVENT_GEN_AI_CHOICE = "gen_ai.choice"

# Exception attributes
ATTR_EXCEPTION_TRACE = "exception.stacktrace"
ATTR_EXCEPTION_TYPE = "exception.type"
ATTR_EXCEPTION_MESSAGE = "exception.message"

# Platform-specific attributes
ATTR_LANGFUSE_COMPLETION_START_TIME = "langfuse.observation.completion_start_time"
