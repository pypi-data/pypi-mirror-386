"""
LLM Factory module to handle different LLM providers
"""
import os
from typing import Optional
from langchain.chat_models.base import BaseChatModel
from langchain_openai import AzureChatOpenAI
from langchain_community.chat_models import ChatOllama
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class LLMFactory:
    """Factory class to create LLM instances based on provider configuration"""
    
    @staticmethod
    def create_llm(
        temperature: float = 0.3,
        request_timeout: int = 60,
        max_retries: int = 2,
        streaming: bool = False
    ) -> BaseChatModel:
        """
        Create an LLM instance based on the configured provider
        """
        provider = os.getenv("LLM_PROVIDER", "azure_openai").lower()
        
        if provider == "azure_openai":
            return LLMFactory._create_azure_openai(temperature, request_timeout, max_retries, streaming)
        elif provider == "google":
            return LLMFactory._create_google(temperature, request_timeout, max_retries)
        elif provider == "ollama":
            return LLMFactory._create_ollama(temperature)
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
    
    @staticmethod
    def _create_azure_openai(
        temperature: float,
        request_timeout: int,
        max_retries: int,
        streaming: bool
    ) -> BaseChatModel:
        """Create Azure OpenAI LLM instance"""
        api_key = os.getenv("OPENAI_API_KEY_DEV")
        if not api_key:
            raise ValueError("OPENAI_API_KEY_DEV environment variable is not set")
        
        azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        api_version = os.getenv("AZURE_OPENAI_API_VERSION")
        
        if not all([azure_deployment, azure_endpoint, api_version]):
            raise ValueError("Required Azure OpenAI configuration is missing")
        
        return AzureChatOpenAI(
            api_key=api_key,
            azure_deployment=azure_deployment,
            azure_endpoint=azure_endpoint,
            api_version=api_version,
            temperature=temperature,
            request_timeout=request_timeout,
            max_retries=max_retries,
            streaming=streaming
        )
    
    @staticmethod
    def _create_google(
        temperature: float,
        request_timeout: int,
        max_retries: int
    ) -> BaseChatModel:
        """Create Google Generative AI LLM instance"""
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
        except ImportError:
            raise ImportError(
                "Could not import langchain_google_genai. Please install it with "
                "'pip install langchain-google-genai' to use the Google provider."
            )

        api_key = os.getenv("GOOGLE_API_KEY")
        model = os.getenv("GOOGLE_MODEL", "gemini-pro")
        
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is not set")
        
        return ChatGoogleGenerativeAI(
            model=model,
            google_api_key=api_key,
            temperature=temperature,
            request_timeout=request_timeout,
            max_retries=max_retries
        )
    
    @staticmethod
    def _create_ollama(temperature: float) -> BaseChatModel:
        """Create Ollama LLM instance"""
        base_url = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        model = os.getenv("OLLAMA_MODEL", "llama2")
        
        return ChatOllama(
            base_url=base_url,
            model=model,
            temperature=temperature
        )
