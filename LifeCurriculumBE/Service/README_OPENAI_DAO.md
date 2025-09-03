# OpenAI DAO Documentation

This document describes the OpenAI Data Access Object (DAO) implementation for the LifeCurriculum service.

## Overview

The OpenAI DAO provides a clean, async interface for interacting with OpenAI's APIs, including:
- Text generation using Chat Completion API
- Text-to-Speech (TTS) using Speech API
- Audio-enabled text generation using GPT-4 Audio models
- Audio transcription using Whisper API
- Combined audio input/output processing

## Configuration

### Environment Variables

Add the following to your `.env` file:

```env
# OpenAI Configuration
OPENAI_API_KEY=your-api-key-here
OPENAI_DEFAULT_MODEL=gpt-4o-audio-preview
OPENAI_TEXT_MODEL=gpt-4o
OPENAI_TTS_MODEL=tts-1
OPENAI_DEFAULT_VOICE=alloy
OPENAI_DEFAULT_AUDIO_FORMAT=wav
OPENAI_TEMPERATURE=0.7
```

### Available Voices
- `alloy` - Neutral, balanced
- `echo` - Clear, expressive 
- `fable` - Warm, engaging
- `onyx` - Deep, authoritative
- `nova` - Bright, energetic
- `shimmer` - Soft, gentle

### Supported Audio Formats
- `wav` - Uncompressed (default)
- `mp3` - Compressed, smaller files
- `opus` - Low latency streaming
- `aac` - High quality compression
- `flac` - Lossless compression

## Usage Examples

### Basic Text Generation

```python
from app.daos.openai_dao import OpenAIDAO
from app.models.openai_models import TextGenerationRequest

dao = OpenAIDAO()

messages = [
    {"role": "user", "content": "Explain quantum computing in simple terms."}
]

request = TextGenerationRequest(messages=messages)
result = await dao.generate_text(request)
print(f"Response: {result.text}")
print(f"Model: {result.model}")
print(f"Token usage: {result.usage}")
```

### Text-to-Speech

```python
from app.models.openai_models import TTSRequest

text = "Hello, this is a test of the text-to-speech functionality."

request = TTSRequest(text=text)
result = await dao.generate_audio_tts(request)

# Save audio to file
with open("speech.wav", "wb") as f:
    f.write(result.audio_data)
```

### Audio-Enabled Text Generation

```python
from app.models.openai_models import AudioTextGenerationRequest

messages = [
    {"role": "user", "content": "Tell me about dolphins and include audio."}
]

request = AudioTextGenerationRequest(messages=messages)
result = await dao.generate_text_with_audio_response(request)
print(f"Text: {result.text}")

if result.audio_data:
    with open("response.wav", "wb") as f:
        f.write(result.audio_data)
```

### Custom Parameters

```python
from app.models.openai_models import TextGenerationRequest, TTSRequest

# Text generation with custom settings
request = TextGenerationRequest(
    messages=messages,
    model="gpt-4",
    temperature=0.9,  # More creative
    max_tokens=150    # Shorter response
)
result = await dao.generate_text(request)

# TTS with custom voice and format
tts_request = TTSRequest(
    text="Custom voice test",
    voice="nova",
    response_format="mp3"
)
tts_result = await dao.generate_audio_tts(tts_request)
```

### Audio Transcription

```python
import base64
from app.models.openai_models import AudioTranscriptionRequest

# Load and encode audio file
with open("audio.wav", "rb") as f:
    audio_bytes = f.read()
audio_data = base64.b64encode(audio_bytes).decode()

request = AudioTranscriptionRequest(
    audio_data=audio_data,
    audio_format="wav",
    language="en"  # Optional language hint
)
result = await dao.transcribe_audio(request)
print(f"Transcription: {result.text}")
```

### Processing Audio with Text Query

```python
# Analyze audio with a specific question
result = await dao.process_audio_input_with_text_query(
    text_query="What is the speaker talking about?",
    audio_data=audio_data,
    audio_format="wav"
)

print(f"Analysis: {result.text}")
if result.audio_data:
    # Save audio response
    with open("analysis_response.wav", "wb") as f:
        f.write(result.audio_data)
```

## API Reference

### Methods

#### `generate_text(messages, model=None, temperature=None, max_tokens=None)`
Generate text using OpenAI's Chat Completion API.

**Parameters:**
- `messages`: List of message dictionaries with 'role' and 'content'
- `model`: Model to use (defaults to configured text model)
- `temperature`: Sampling temperature 0.0-2.0 (defaults to configured value)
- `max_tokens`: Maximum tokens to generate

**Returns:** `TextGenerationResponse`

#### `generate_audio_tts(text, voice=None, model=None, response_format=None)`
Convert text to speech using OpenAI's TTS API.

**Parameters:**
- `text`: Text to convert to speech
- `voice`: Voice to use (defaults to configured voice)
- `model`: TTS model to use (defaults to configured TTS model)
- `response_format`: Audio format (defaults to configured format)

**Returns:** `TTSResponse`

#### `generate_text_with_audio_response(messages, voice=None, audio_format=None, model=None, temperature=None, max_tokens=None)`
Generate text with optional audio output using audio-capable models.

**Parameters:**
- `messages`: List of message dictionaries
- `voice`: Voice for audio output (defaults to configured voice)
- `audio_format`: Audio format (defaults to configured format)
- `model`: Model to use (defaults to configured audio model)
- `temperature`: Sampling temperature (defaults to configured value)
- `max_tokens`: Maximum tokens to generate

**Returns:** `AudioTextGenerationResponse`

#### `transcribe_audio(audio_data, audio_format, model=None, language=None)`
Transcribe audio using OpenAI's Whisper API.

**Parameters:**
- `audio_data`: Base64 encoded audio data
- `audio_format`: Audio format (wav, mp3, etc.)
- `model`: Model to use (defaults to whisper-1)
- `language`: Language hint for transcription

**Returns:** `AudioTranscriptionResponse`

#### `process_audio_input_with_text_query(text_query, audio_data, audio_format, response_voice=None, response_audio_format=None, model=None)`
Process audio input with a text query for comprehensive analysis.

**Parameters:**
- `text_query`: Text question about the audio
- `audio_data`: Base64 encoded audio data
- `audio_format`: Audio format
- `response_voice`: Voice for audio response
- `response_audio_format`: Format for audio response
- `model`: Model to use

**Returns:** `AudioTextGenerationResponse`

## Response Models

### `TextGenerationResponse`
- `text`: Generated text
- `model`: Model used
- `usage`: Token usage information (dict)

### `TTSResponse`
- `audio_data`: Audio data as bytes
- `format`: Audio format used

### `AudioTextGenerationResponse`
- `text`: Generated text
- `audio_data`: Audio data as bytes (optional)
- `audio_format`: Audio format (optional)
- `model`: Model used
- `usage`: Token usage information (dict)

### `AudioTranscriptionResponse`
- `text`: Transcribed text
- `language`: Detected/specified language
- `model`: Model used

## Error Handling

The DAO includes comprehensive error handling:
- **Configuration errors**: Missing API key, invalid settings
- **API errors**: Rate limits, invalid requests, network issues
- **HTTP errors**: Proper status code mapping for FastAPI integration

All errors are raised as `HTTPException` with appropriate status codes and descriptive messages.

## Testing

Run the test suite:

```bash
cd Service
python -m pytest tests/test_openai_dao.py -v
```

## Demo

Run the demo script to test all functionality:

```bash
python demo_openai_dao.py
```

Make sure your `.env` file is configured with a valid OpenAI API key first.

## Best Practices

1. **API Key Security**: Store API keys in environment variables, never in code
2. **Error Handling**: Always wrap DAO calls in try-catch blocks
3. **Resource Management**: Audio data can be large; consider streaming for large files
4. **Rate Limiting**: OpenAI has rate limits; implement retry logic if needed
5. **Cost Management**: Monitor token usage, especially with audio-enabled models
6. **Model Selection**: Use appropriate models for your use case (text vs audio-enabled)

## Cost Considerations

- **Text Generation**: Charged per token (input + output)
- **TTS**: Charged per character of input text
- **Audio Models**: Higher cost than text-only models
- **Whisper**: Charged per minute of audio

Monitor usage through OpenAI's dashboard and implement appropriate limits for your application.
