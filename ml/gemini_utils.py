import google.generativeai as genai
import os
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeminiClient:
    """
    A robust client for Google Gemini API with automatic model fallback.
    Prioritizes newer/faster models and falls back to others on failure.
    """
    
    # Priority list of models to try
    # 2.5 Flash is the latest and fastest audio/multimodal
    # 2.0 Flash is the previous stable version
    # 1.5 Pro is the robust high-intelligence model
    # 1.5 Flash is the cost-effective fallback
    FALLBACK_MODELS = [
        "gemini-2.5-flash", 
        "gemini-2.0-flash", 
        "gemini-1.5-pro", 
        "gemini-1.5-flash"
    ]

    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not found. AI features will be disabled.")
        else:
            genai.configure(api_key=self.api_key)

    def generate_content(self, contents, generation_config=None):
        """
        Synchronous content generation with fallback.
        Used for non-async contexts like report analysis.
        """
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is missing.")

        last_exception = None

        for model_name in self.FALLBACK_MODELS:
            try:
                logger.info(f"Attempting generation with model: {model_name}")
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(contents, generation_config=generation_config)
                return response
            except Exception as e:
                logger.warning(f"Model {model_name} failed: {e}. Trying next...")
                last_exception = e
                # Setup specific error handling for ResourceExhausted or similar
                if "429" in str(e) or "ResourceExhausted" in str(e):
                    continue # Definitely try next for quota issues
                # For other errors, we might still want to try fallback depending on severity
                continue
        
        logger.error("All Gemini models failed.")
        raise last_exception or Exception("All Gemini models failed.")

    async def generate_content_async(self, contents, generation_config=None):
        """
        Asynchronous content generation with fallback.
        Used for async contexts like chatbot.
        """
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is missing.")

        last_exception = None

        for model_name in self.FALLBACK_MODELS:
            try:
                logger.info(f"Attempting async generation with model: {model_name}")
                model = genai.GenerativeModel(model_name)
                response = await model.generate_content_async(contents, generation_config=generation_config)
                return response
            except Exception as e:
                logger.warning(f"Model {model_name} failed: {e}. Trying next...")
                last_exception = e
                continue
        
        logger.error("All Gemini models failed.")
        raise last_exception or Exception("All Gemini models failed.")

# Singleton instance for easy import
_client = None

def get_gemini_client(api_key=None):
    global _client
    # If a specific key is provided, always create a new client (or update)
    if api_key:
        return GeminiClient(api_key)
    # Otherwise use shared instance
    if _client is None:
        _client = GeminiClient()
    return _client
