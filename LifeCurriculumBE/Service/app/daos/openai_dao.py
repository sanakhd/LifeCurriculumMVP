"""
OpenAI Data Access Object for text generation, TTS, and audio processing
"""
import base64
from typing import Optional, Dict, Any, List, Union
from openai import OpenAI
from fastapi import HTTPException

from app.config import get_settings
from app.logger import get_logger
from app.models.openai_models import (
    TextGenerationRequest,
    TextGenerationResponse,
    TTSRequest,
    TTSResponse,
    AudioTextGenerationRequest,
    AudioTextGenerationResponse,
    AudioTranscriptionRequest,
    AudioTranscriptionResponse
)

logger = get_logger(__name__)


class OpenAIDAO:
    """Standalone DAO for OpenAI API interactions"""
    
    def __init__(self):
        """Initialize OpenAI DAO with configuration"""
        logger.debug("Initializing OpenAI DAO")
        self.settings = get_settings()
        
        # Validate API key is present
        if not self.settings.openai_api_key:
            logger.error("OpenAI API key not configured")
            raise ValueError("OpenAI API key not configured. Please set OPENAI_API_KEY environment variable.")
        
        logger.debug("OpenAI API key found, initializing client")
        try:
            self.client = OpenAI(api_key=self.settings.openai_api_key)
            logger.info("OpenAI DAO initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to initialize OpenAI client")

    async def generate_text(
        self,
        request: TextGenerationRequest
    ) -> TextGenerationResponse:
        """
        Generate text using OpenAI Chat Completion API
        
        Args:
            request: TextGenerationRequest with messages and optional parameters
            
        Returns:
            TextGenerationResponse containing generated text and metadata
            
        Raises:
            HTTPException: On API errors or configuration issues
        """
        logger.info(f"Processing text generation request with {len(request.messages)} messages")
        
        try:
            # Use configured defaults if not provided in request
            model = request.model or self.settings.openai_text_model
            temperature = None #request.temperature if request.temperature is not None else self.settings.openai_temperature
            max_tokens = None #request.max_tokens or self.settings.openai_max_tokens
            
            logger.debug(f"Using model: {model}, temperature: {temperature}, max_tokens: {max_tokens}")
            
            # Prepare request parameters
            request_params = {
                "model": model,
                "messages": request.messages,
            }
            
            if max_tokens is not None:
                request_params["max_tokens"] = max_tokens
            
            logger.debug(f"Making OpenAI API call with parameters: {list(request_params.keys())}")
            
            # Make API call
            completion = self.client.chat.completions.create(**request_params)
            
            # Extract response
            response_text = completion.choices[0].message.content
            usage = completion.usage.dict() if completion.usage else None
            
            logger.info(f"Successfully generated text response using model: {completion.model}")
            
            if usage:
                logger.debug(f"Token usage: {usage}")
            
            logger.debug(f"Generated text length: {len(response_text) if response_text else 0} characters")
            
            return TextGenerationResponse(
                text=response_text,
                model=completion.model,
                usage=usage
            )
            
        except Exception as e:
            logger.error(f"OpenAI text generation error: {str(e)}")
            if hasattr(e, 'response') and hasattr(e.response, 'status_code'):
                logger.error(f"OpenAI API returned status code: {e.response.status_code}")
                raise HTTPException(status_code=e.response.status_code, detail=str(e))
            raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(e)}")

    async def generate_audio_tts(
        self,
        request: TTSRequest
    ) -> TTSResponse:
        """
        Generate audio from text using OpenAI TTS API
        
        Args:
            request: TTSRequest with text and optional parameters
            
        Returns:
            TTSResponse containing audio data and format
            
        Raises:
            HTTPException: On API errors or configuration issues
        """
        logger.info(f"Processing TTS request for text with length: {len(request.text)} characters")
        
        try:
            # Use configured defaults if not provided in request
            voice = request.voice or self.settings.openai_default_voice
            model = request.model or self.settings.openai_tts_model
            response_format = request.response_format or self.settings.openai_default_audio_format
            
            logger.debug(f"Using TTS model: {model}, voice: {voice}, format: {response_format}")
            
            # Make TTS API call
            logger.debug("Making OpenAI TTS API call")
            response = self.client.audio.speech.create(
                model=model,
                voice=voice,
                input=request.text,
                response_format=response_format
            )
            
            # Get audio bytes
            audio_bytes = response.content
            logger.info(f"Successfully generated audio with size: {len(audio_bytes)} bytes")
            
            return TTSResponse(
                audio_data=audio_bytes,
                format=response_format
            )
            
        except Exception as e:
            logger.error(f"OpenAI TTS error for text length {len(request.text)}: {str(e)}")
            if hasattr(e, 'response') and hasattr(e.response, 'status_code'):
                logger.error(f"OpenAI TTS API returned status code: {e.response.status_code}")
                raise HTTPException(status_code=e.response.status_code, detail=str(e))
            raise HTTPException(status_code=500, detail=f"OpenAI TTS API error: {str(e)}")

    async def generate_text_with_audio_response(
        self,
        request: AudioTextGenerationRequest
    ) -> AudioTextGenerationResponse:
        """
        Generate text response with audio output using OpenAI audio-capable models
        
        Args:
            request: AudioTextGenerationRequest with messages and optional parameters
            
        Returns:
            AudioTextGenerationResponse containing text and audio data
            
        Raises:
            HTTPException: On API errors or configuration issues
        """
        logger.info(f"Processing audio text generation request with {len(request.messages)} messages")
        
        try:
            # Use configured defaults if not provided in request
            voice = request.voice or self.settings.openai_default_voice
            audio_format = request.audio_format or self.settings.openai_default_audio_format
            model = request.model or self.settings.openai_default_model
            temperature = request.temperature if request.temperature is not None else self.settings.openai_temperature
            max_tokens = request.max_tokens or self.settings.openai_max_tokens
            
            logger.debug(f"Using audio model: {model}, voice: {voice}, format: {audio_format}, temperature: {temperature}")
            
            # Prepare request parameters for audio-enabled completion
            request_params = {
                "model": model,
                "modalities": ["text", "audio"],
                "audio": {"voice": voice, "format": audio_format},
                "messages": request.messages,
                "temperature": temperature,
            }
            
            if max_tokens is not None:
                request_params["max_tokens"] = max_tokens
            
            logger.debug("Making OpenAI audio-enabled API call")
            
            # Make API call
            completion = self.client.chat.completions.create(**request_params)
            
            # Extract response
            response_text = completion.choices[0].message.content
            usage = completion.usage.dict() if completion.usage else None
            
            # Extract audio if present
            audio_data = None
            if hasattr(completion.choices[0].message, 'audio') and completion.choices[0].message.audio:
                audio_base64 = completion.choices[0].message.audio.data
                audio_data = base64.b64decode(audio_base64)
                logger.info(f"Successfully generated text with audio response, audio size: {len(audio_data)} bytes")
            else:
                logger.info("Successfully generated text response (no audio data)")
            
            if usage:
                logger.debug(f"Audio generation token usage: {usage}")
            
            return AudioTextGenerationResponse(
                text=response_text,
                audio_data=audio_data,
                audio_format=audio_format if audio_data else None,
                model=completion.model,
                usage=usage
            )
            
        except Exception as e:
            logger.error(f"OpenAI audio text generation error: {str(e)}")
            if hasattr(e, 'response') and hasattr(e.response, 'status_code'):
                logger.error(f"OpenAI audio API returned status code: {e.response.status_code}")
                raise HTTPException(status_code=e.response.status_code, detail=str(e))
            raise HTTPException(status_code=500, detail=f"OpenAI audio API error: {str(e)}")

    async def transcribe_audio(
        self,
        request: AudioTranscriptionRequest
    ) -> AudioTranscriptionResponse:
        """
        Transcribe audio using OpenAI Whisper API
        
        Args:
            request: AudioTranscriptionRequest with audio data and optional parameters
            
        Returns:
            AudioTranscriptionResponse containing transcribed text
            
        Raises:
            HTTPException: On API errors or configuration issues
        """
        logger.info(f"Processing audio transcription request for format: {request.audio_format}")
        
        try:
            # Use default model if not provided in request
            model = request.model or "whisper-1"
            
            logger.debug(f"Using transcription model: {model}")
            
            # Decode audio data
            audio_bytes = base64.b64decode(request.audio_data)
            logger.debug(f"Decoded audio data, size: {len(audio_bytes)} bytes")
            
            # Create a temporary file-like object for the audio
            from io import BytesIO
            audio_file = BytesIO(audio_bytes)
            audio_file.name = f"audio.{request.audio_format}"
            
            # Prepare request parameters
            request_params = {
                "model": model,
                "file": audio_file,
            }
            
            if request.language:
                request_params["language"] = request.language
                logger.debug(f"Using specified language: {request.language}")
            
            logger.debug("Making OpenAI Whisper transcription API call")
            
            # Make transcription API call
            transcript = self.client.audio.transcriptions.create(**request_params)
            
            logger.info(f"Successfully transcribed audio, text length: {len(transcript.text)} characters")
            
            return AudioTranscriptionResponse(
                text=transcript.text,
                language=request.language,
                model=model
            )
            
        except Exception as e:
            logger.error(f"OpenAI transcription error for format {request.audio_format}: {str(e)}")
            if hasattr(e, 'response') and hasattr(e.response, 'status_code'):
                logger.error(f"OpenAI transcription API returned status code: {e.response.status_code}")
                raise HTTPException(status_code=e.response.status_code, detail=str(e))
            raise HTTPException(status_code=500, detail=f"OpenAI transcription API error: {str(e)}")

    async def process_audio_input_with_text_query(
        self,
        text_query: str,
        audio_data: str,
        audio_format: str,
        response_voice: Optional[str] = None,
        response_audio_format: Optional[str] = None,
        model: Optional[str] = None
    ) -> AudioTextGenerationResponse:
        """
        Process audio input alongside text query for comprehensive response
        
        Args:
            text_query: Text question/query about the audio
            audio_data: Base64 encoded audio data
            audio_format: Audio format (wav, mp3, etc.)
            response_voice: Voice for audio response
            response_audio_format: Format for audio response
            model: Model to use
            
        Returns:
            AudioTextGenerationResponse containing text and audio response
        """
        logger.info(f"Processing audio input with text query, format: {audio_format}, query length: {len(text_query)}")
        
        try:
            # Use configured defaults if not provided
            response_voice = response_voice or self.settings.openai_default_voice
            response_audio_format = response_audio_format or self.settings.openai_default_audio_format
            model = model or self.settings.openai_default_model
            
            logger.debug(f"Using response voice: {response_voice}, format: {response_audio_format}, model: {model}")
            
            # Build messages with both text and audio input
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": text_query
                        },
                        {
                            "type": "input_audio",
                            "input_audio": {
                                "data": audio_data,
                                "format": audio_format
                            }
                        }
                    ]
                }
            ]
            
            logger.debug("Created multimodal message with text and audio content")
            
            # Create AudioTextGenerationRequest
            audio_request = AudioTextGenerationRequest(
                messages=messages,
                voice=response_voice,
                audio_format=response_audio_format,
                model=model
            )
            
            logger.debug("Calling generate_text_with_audio_response for multimodal processing")
            
            # Generate response with audio output
            response = await self.generate_text_with_audio_response(audio_request)
            
            logger.info("Successfully processed audio input with text query")
            return response
            
        except Exception as e:
            logger.error(f"OpenAI audio processing error for query '{text_query[:50]}...': {str(e)}")
            raise HTTPException(status_code=500, detail=f"Audio processing error: {str(e)}")
