"""
Session Manager for handling OpenAI API interactions to generate learning curricula
"""
from typing import Dict, Any

from app.config import get_settings
from app.logger import get_logger
from app.daos.openai_dao import OpenAIDAO
from app.models.openai_models import TextGenerationRequest, TextGenerationResponse

logger = get_logger(__name__)


class SessionManager:
    """
    Manages learning session creation by coordinating with OpenAI APIs
    to generate personalized curricula based on user requests.
    """
    
    def __init__(self):
        """Initialize SessionManager with required dependencies"""
        logger.debug("Initializing SessionManager")
        self.settings = get_settings()
        self.openai_dao = OpenAIDAO()
        logger.info("SessionManager initialized successfully")
        
    async def create_session(self, prompt: str) -> str:
        """
        Create a learning session by generating a 5-lesson curriculum based on user prompt.
        
        Args:
            prompt (str): The user's learning request describing what they want to learn
            
        Raises:
            Exception: If there's an error generating the curriculum or communicating with OpenAI
            
        Returns:
            str: The generated curriculum text
        """
        logger.info(f"Starting session creation for prompt: '{prompt[:100]}...' (length: {len(prompt)} characters)")
        
        try:
            logger.debug(f"Using system prompt from configuration")
            
            # Prepare the messages for OpenAI API
            messages = [
                {"role": "system", "content": self.settings.curriculum_system_prompt},
                {"role": "user", "content": f"Create a 5-lesson curriculum for learning: {prompt}"}
            ]
            
            logger.debug(f"Prepared {len(messages)} messages for OpenAI API")
            
            # Create the request object
            request = TextGenerationRequest(
                messages=messages,
                temperature=0.7,  # Balanced creativity and consistency
                max_tokens=2000   # Sufficient for detailed curriculum
            )
            
            logger.debug(f"Created TextGenerationRequest with temperature={request.temperature}, max_tokens={request.max_tokens}")
            
            # Call OpenAI API via DAO
            logger.info("Calling OpenAI DAO to generate curriculum text")
            response: TextGenerationResponse = await self.openai_dao.generate_text(request)
            
            # Log successful completion with details
            logger.info(f"Successfully generated curriculum for prompt. Model: {response.model}")
            
            if response.usage:
                logger.debug(f"Token usage details: {response.usage}")
            
            logger.info(f"Generated curriculum length: {len(response.text)} characters")
            
            # Return the generated curriculum
            return response.text
                
        except Exception as e:
            logger.error(f"Failed to create learning session for prompt '{prompt[:50]}...': {str(e)}")
            raise
