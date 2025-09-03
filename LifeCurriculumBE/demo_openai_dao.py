#!/usr/bin/env python3
"""
Demo script showing how to use the OpenAI DAO
"""
import asyncio
import base64
import os
import sys

# Add the Service directory to the path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'Service'))

from app.daos.openai_dao import OpenAIDAO
from app.models.openai_models import (
    TextGenerationRequest,
    TTSRequest,
    AudioTextGenerationRequest
)


async def demo_text_generation():
    """Demo basic text generation"""
    print("=== Text Generation Demo ===")
    
    try:
        dao = OpenAIDAO()
        
        # Simple text generation
        messages = [
            {"role": "user", "content": "Explain what a golden retriever is in one paragraph."}
        ]
        
        request = TextGenerationRequest(messages=messages)
        result = await dao.generate_text(request)
        print(f"Generated Text: {result.text}")
        print(f"Model Used: {result.model}")
        print(f"Token Usage: {result.usage}")
        print()
        
    except Exception as e:
        print(f"Error in text generation: {e}")
        print()


async def demo_tts():
    """Demo text-to-speech"""
    print("=== Text-to-Speech Demo ===")
    
    try:
        dao = OpenAIDAO()
        
        text = "Hello! This is a demonstration of OpenAI's text-to-speech capabilities."
        
        request = TTSRequest(text=text)
        result = await dao.generate_audio_tts(request)
        print(f"Generated audio with format: {result.format}")
        print(f"Audio data size: {len(result.audio_data)} bytes")
        
        # Save audio to file
        with open("demo_tts_output.wav", "wb") as f:
            f.write(result.audio_data)
        print("Audio saved to demo_tts_output.wav")
        print()
        
    except Exception as e:
        print(f"Error in TTS: {e}")
        print()


async def demo_audio_text_generation():
    """Demo audio-enabled text generation"""
    print("=== Audio-Enabled Text Generation Demo ===")
    
    try:
        dao = OpenAIDAO()
        
        messages = [
            {"role": "user", "content": "Tell me a fun fact about golden retrievers and respond with audio."}
        ]
        
        request = AudioTextGenerationRequest(messages=messages)
        result = await dao.generate_text_with_audio_response(request)
        print(f"Generated Text: {result.text}")
        print(f"Model Used: {result.model}")
        
        if result.audio_data:
            print(f"Audio format: {result.audio_format}")
            print(f"Audio data size: {len(result.audio_data)} bytes")
            
            # Save audio to file
            with open("demo_audio_response.wav", "wb") as f:
                f.write(result.audio_data)
            print("Audio response saved to demo_audio_response.wav")
        else:
            print("No audio data in response")
        print()
        
    except Exception as e:
        print(f"Error in audio text generation: {e}")
        print()


async def demo_custom_parameters():
    """Demo using custom parameters"""
    print("=== Custom Parameters Demo ===")
    
    try:
        dao = OpenAIDAO()
        
        # Text generation with custom parameters
        messages = [
            {"role": "user", "content": "Write a haiku about dogs."}
        ]
        
        request = TextGenerationRequest(
            messages=messages,
            model="gpt-4",  # Specify model
            temperature=0.9,  # More creative
            max_tokens=100   # Limit response length
        )
        result = await dao.generate_text(request)
        
        print(f"Haiku: {result.text}")
        print(f"Model: {result.model}")
        print()
        
        # TTS with custom voice
        tts_request = TTSRequest(
            text=result.text,
            voice="nova",  # Different voice
            response_format="mp3"  # Different format
        )
        tts_result = await dao.generate_audio_tts(tts_request)
        
        print(f"TTS with nova voice, format: {tts_result.format}")
        with open("demo_haiku.mp3", "wb") as f:
            f.write(tts_result.audio_data)
        print("Haiku audio saved to demo_haiku.mp3")
        print()
        
    except Exception as e:
        print(f"Error in custom parameters demo: {e}")
        print()


async def main():
    """Run all demos"""
    print("OpenAI DAO Demo")
    print("=" * 50)
    print("Make sure to set your OPENAI_API_KEY in your .env file!")
    print("=" * 50)
    print()
    
    # Check if API key is likely configured
    try:
        dao = OpenAIDAO()
        print("✓ OpenAI DAO initialized successfully")
        print()
    except ValueError as e:
        print(f"✗ Configuration Error: {e}")
        print("Please set OPENAI_API_KEY in your .env file")
        return
    except Exception as e:
        print(f"✗ Initialization Error: {e}")
        return
    
    # Run demos
    await demo_text_generation()
    await demo_tts()
    await demo_audio_text_generation()
    await demo_custom_parameters()
    
    print("=" * 50)
    print("Demo completed! Check the generated audio files:")
    print("- demo_tts_output.wav")
    print("- demo_audio_response.wav")
    print("- demo_haiku.mp3")


if __name__ == "__main__":
    asyncio.run(main())
