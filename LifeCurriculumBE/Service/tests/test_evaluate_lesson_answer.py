import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
from fastapi import HTTPException
from pydantic import ValidationError

from app.apis.programs.evaluate_lesson_answer import (
    EvaluateAnswerRequest, 
    EvaluateAnswerResponse,
    build_evaluation_prompt,
    evaluate_lesson_answer
)
from app.models.lesson import Lesson, ConversationTurn, InteractionSpec
from app.models.enums import ResponseType, ContextType
from app.models.openai_models import TextGenerationResponse


class TestEvaluateAnswerRequest:
    """Test EvaluateAnswerRequest validation"""
    
    def test_valid_request(self):
        """Test valid request creation"""
        request = EvaluateAnswerRequest(user_answer="This is my thoughtful answer")
        assert request.user_answer == "This is my thoughtful answer"
    
    def test_empty_answer_validation(self):
        """Test empty answer validation"""
        with pytest.raises(ValidationError):
            EvaluateAnswerRequest(user_answer="")
    
    def test_whitespace_only_answer_validation(self):
        """Test whitespace-only answer validation"""
        with pytest.raises(ValueError, match="Answer cannot be empty"):
            EvaluateAnswerRequest(user_answer="   \n\t  ")
    
    def test_answer_trimming(self):
        """Test answer trimming"""
        request = EvaluateAnswerRequest(user_answer="  trimmed answer  ")
        assert request.user_answer == "trimmed answer"
    
    def test_max_length_validation(self):
        """Test maximum length validation"""
        long_answer = "x" * 2001  # Exceeds 2000 char limit
        with pytest.raises(ValueError):
            EvaluateAnswerRequest(user_answer=long_answer)


class TestBuildEvaluationPrompt:
    """Test prompt building logic"""
    
    def test_build_prompt_with_full_lesson(self):
        """Test prompt building with complete lesson data"""
        # Create test lesson with conversation and interaction
        conversation_chunks = [
            ConversationTurn(speaker="Host A", text="Welcome to today's lesson on spending habits."),
            ConversationTurn(speaker="Host B", text="Let's explore how emotions influence our purchases.")
        ]
        
        primary_interaction = InteractionSpec(
            type=ResponseType.REFLECTION_PROMPT,
            prompt="Reflect on your recent spending patterns"
        )
        
        lesson = Lesson(
            id="test-lesson-id",
            program_id="test-program-id", 
            day_number=1,
            title="Spending Habits",
            description="Learn about spending patterns",
            audio_section_title="Understanding Spending",
            conversation_chunks=conversation_chunks,
            primary_interaction=primary_interaction,
            context=ContextType.HOME
        )
        
        user_answer = "I notice I spend more when stressed"
        prompt = build_evaluation_prompt(lesson, user_answer)
        
        # Verify prompt includes all key components
        assert "Spending Habits" in prompt
        assert "Learn about spending patterns" in prompt
        assert "home" in prompt.lower()
        assert "Host A: Welcome to today's lesson" in prompt
        assert "Host B: Let's explore how emotions" in prompt
        assert "Reflect on your recent spending patterns" in prompt
        assert "I notice I spend more when stressed" in prompt
        assert "educational feedback" in prompt.lower()
        assert "acknowledges what the user did well" in prompt.lower()
    
    def test_build_prompt_without_conversation(self):
        """Test prompt building with lesson missing conversation"""
        primary_interaction = InteractionSpec(
            type=ResponseType.REFLECTION_PROMPT,
            prompt="Reflect on your habits"
        )
        
        lesson = Lesson(
            id="test-lesson-id",
            program_id="test-program-id",
            day_number=1,
            title="Test Lesson",
            description="Test description",
            audio_section_title="Test Audio",
            conversation_chunks=[],
            primary_interaction=primary_interaction,
            context=ContextType.HOME
        )
        
        user_answer = "Test answer"
        prompt = build_evaluation_prompt(lesson, user_answer)
        
        # Should still work with empty conversation
        assert "Test Lesson" in prompt
        assert "Reflect on your habits" in prompt
        assert "Test answer" in prompt
        assert "LESSON CONVERSATION:\n\n" in prompt  # Empty conversation section
    
    def test_build_prompt_without_primary_interaction(self):
        """Test prompt building with lesson missing primary interaction"""
        lesson = Lesson(
            id="test-lesson-id",
            program_id="test-program-id",
            day_number=1,
            title="Test Lesson",
            description="Test description", 
            audio_section_title="Test Audio",
            conversation_chunks=[],
            primary_interaction=None,
            context=ContextType.HOME
        )
        
        user_answer = "Test answer"
        prompt = build_evaluation_prompt(lesson, user_answer)
        
        # Should work with empty interaction prompt
        assert "Test Lesson" in prompt
        assert "EXERCISE PROMPT:\n\n" in prompt  # Empty prompt section


class TestEvaluateLessonAnswer:
    """Test main endpoint logic"""
    
    @pytest.fixture
    def sample_lesson_data(self):
        """Sample lesson data for testing"""
        return {
            "id": "test-lesson-id",
            "program_id": "test-program-id",
            "day_number": 1,
            "title": "Test Lesson",
            "description": "Test description",
            "audio_section_title": "Test Audio",
            "conversation_chunks": [
                {"speaker": "Host A", "text": "Test conversation"},
                {"speaker": "Host B", "text": "More test content"}
            ],
            "primary_interaction": {
                "type": "reflection_prompt",
                "prompt": "Test prompt"
            },
            "context": "home"
        }
    
    @pytest.fixture
    def mock_openai_response(self):
        """Mock OpenAI response"""
        return TextGenerationResponse(
            text="Great reflection! Your awareness of emotional spending triggers shows strong self-insight.",
            model="gpt-4"
        )
    
    @patch('app.apis.programs.evaluate_lesson_answer.get_lesson_by_uuid')
    @patch('app.apis.programs.evaluate_lesson_answer.dao')
    async def test_successful_evaluation(self, mock_dao, mock_get_lesson, sample_lesson_data, mock_openai_response):
        """Test successful answer evaluation"""
        # Setup mocks
        mock_get_lesson.return_value = ({}, sample_lesson_data)
        mock_dao.generate_text = AsyncMock(return_value=mock_openai_response)
        
        # Create request
        request = EvaluateAnswerRequest(user_answer="I tend to overspend when feeling stressed")
        
        # Call endpoint
        response = await evaluate_lesson_answer("test-lesson-id", request)
        
        # Verify response
        assert isinstance(response, EvaluateAnswerResponse)
        assert response.feedback == "Great reflection! Your awareness of emotional spending triggers shows strong self-insight."
        assert response.lesson_title == "Test Lesson"
        assert response.prompt_text == "Test prompt"
        assert response.model_used == "gpt-4"
        assert isinstance(response.evaluation_timestamp, datetime)
        
        # Verify OpenAI was called correctly
        mock_dao.generate_text.assert_called_once()
        call_args = mock_dao.generate_text.call_args[0][0]
        assert len(call_args.messages) == 1
        assert call_args.messages[0]["role"] == "user"
        assert "Test Lesson" in call_args.messages[0]["content"]
    
    @patch('app.apis.programs.evaluate_lesson_answer.get_lesson_by_uuid')
    async def test_lesson_not_found(self, mock_get_lesson):
        """Test lesson not found error"""
        mock_get_lesson.return_value = None
        
        request = EvaluateAnswerRequest(user_answer="Test answer")
        
        with pytest.raises(HTTPException) as exc_info:
            await evaluate_lesson_answer("nonexistent-lesson-id", request)
        
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Lesson not found"
    
    @patch('app.apis.programs.evaluate_lesson_answer.get_lesson_by_uuid')
    async def test_lesson_without_primary_interaction(self, mock_get_lesson):
        """Test lesson without primary interaction"""
        lesson_data = {
            "id": "test-lesson-id",
            "program_id": "test-program-id",
            "day_number": 1,
            "title": "Test Lesson",
            "description": "Test description",
            "audio_section_title": "Test Audio",
            "conversation_chunks": [],
            "primary_interaction": None,
            "context": "home"
        }
        
        mock_get_lesson.return_value = ({}, lesson_data)
        
        request = EvaluateAnswerRequest(user_answer="Test answer")
        
        with pytest.raises(HTTPException) as exc_info:
            await evaluate_lesson_answer("test-lesson-id", request)
        
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Lesson has no primary interaction to evaluate"
    
    @patch('app.apis.programs.evaluate_lesson_answer.get_lesson_by_uuid')
    async def test_invalid_lesson_data(self, mock_get_lesson):
        """Test invalid lesson data parsing"""
        invalid_lesson_data = {
            "id": "test-lesson-id",
            "program_id": "test-program-id",
            # Missing required fields
        }
        
        mock_get_lesson.return_value = ({}, invalid_lesson_data)
        
        request = EvaluateAnswerRequest(user_answer="Test answer")
        
        with pytest.raises(HTTPException) as exc_info:
            await evaluate_lesson_answer("test-lesson-id", request)
        
        assert exc_info.value.status_code == 500
        assert exc_info.value.detail == "Invalid lesson data"
    
    @patch('app.apis.programs.evaluate_lesson_answer.get_lesson_by_uuid')
    @patch('app.apis.programs.evaluate_lesson_answer.dao')
    async def test_openai_failure(self, mock_dao, mock_get_lesson, sample_lesson_data):
        """Test OpenAI API failure"""
        mock_get_lesson.return_value = ({}, sample_lesson_data)
        mock_dao.generate_text = AsyncMock(side_effect=Exception("OpenAI API error"))
        
        request = EvaluateAnswerRequest(user_answer="Test answer")
        
        with pytest.raises(HTTPException) as exc_info:
            await evaluate_lesson_answer("test-lesson-id", request)
        
        assert exc_info.value.status_code == 500
        assert exc_info.value.detail == "Failed to generate evaluation feedback"


class TestEndToEndIntegration:
    """Test complete workflow with real data structure"""
    
    def test_evaluation_response_serialization(self):
        """Test response model serialization"""
        response = EvaluateAnswerResponse(
            feedback="Test feedback",
            lesson_title="Test Lesson", 
            prompt_text="Test prompt",
            evaluation_timestamp=datetime(2024, 1, 1, 12, 0, 0),
            model_used="gpt-4"
        )
        
        # Should serialize to dict correctly
        data = response.model_dump()
        assert data["feedback"] == "Test feedback"
        assert data["lesson_title"] == "Test Lesson"
        assert data["prompt_text"] == "Test prompt"
        assert data["model_used"] == "gpt-4"
        assert isinstance(data["evaluation_timestamp"], datetime)


if __name__ == "__main__":
    pytest.main([__file__])
