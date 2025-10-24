#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM Health Check Module for Universal Tester
Validates LLM connectivity and displays model information
"""

import os
import sys
from typing import Dict, Any, Optional
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)


def get_llm_config() -> Dict[str, Any]:
    """Get LLM configuration from environment variables"""
    config = {
        'provider': os.getenv('LLM_PROVIDER', 'azure').lower().replace('_', ''),
        'model': os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME', 'Not configured'),
        'api_version': os.getenv('AZURE_OPENAI_API_VERSION', 'Not configured'),
        'endpoint': os.getenv('AZURE_OPENAI_ENDPOINT', 'Not configured'),
        'api_key_set': bool(os.getenv('OPENAI_API_KEY_DEV') or os.getenv('AZURE_OPENAI_API_KEY')),
        'temperature': os.getenv('LLM_TEMPERATURE', '0.0'),
        'max_tokens': os.getenv('LLM_MAX_TOKENS', '16000'),
    }
    
    # Handle different providers
    if 'openai' in config['provider'] and 'azure' not in config['provider']:
        config['model'] = os.getenv('OPENAI_MODEL', 'gpt-4')
        config['endpoint'] = 'api.openai.com'
    elif config['provider'] == 'ollama':
        config['model'] = os.getenv('OLLAMA_MODEL', 'llama2')
        config['endpoint'] = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
    
    return config


def test_llm_connectivity() -> Dict[str, Any]:
    """Test LLM connectivity and return status"""
    config = get_llm_config()
    result = {
        'success': False,
        'provider': config['provider'],
        'model': config['model'],
        'endpoint': config['endpoint'],
        'error': None,
        'response_time': None,
        'message': ''
    }
    
    try:
        # Check if API key is configured
        if not config['api_key_set']:
            result['error'] = 'API key not configured'
            result['message'] = '❌ API key not found in environment variables'
            return result
        
        # Test connectivity based on provider
        if 'azure' in config['provider']:
            result.update(_test_azure_openai(config))
        elif 'openai' in config['provider']:
            result.update(_test_openai(config))
        elif 'ollama' in config['provider']:
            result.update(_test_ollama(config))
        else:
            result['error'] = f"Unsupported provider: {config['provider']}"
            result['message'] = f"❌ Unsupported LLM provider: {config['provider']}"
            
    except Exception as e:
        result['error'] = str(e)
        result['message'] = f"❌ Connection test failed: {str(e)}"
        logger.error(f"LLM connectivity test failed: {e}")
    
    return result


def _test_azure_openai(config: Dict[str, Any]) -> Dict[str, Any]:
    """Test Azure OpenAI connectivity"""
    import time
    from langchain_openai import AzureChatOpenAI
    from langchain.schema import HumanMessage
    
    result = {}
    start_time = time.time()
    
    try:
        # Initialize Azure OpenAI client
        llm = AzureChatOpenAI(
            deployment_name=config['model'],
            openai_api_version=config['api_version'],
            azure_endpoint=config['endpoint'],
            openai_api_key=os.getenv('OPENAI_API_KEY_DEV') or os.getenv('AZURE_OPENAI_API_KEY'),
            temperature=0.0,
            max_tokens=100
        )
        
        # Send a simple test message
        response = llm.invoke([HumanMessage(content="Hello, respond with just 'OK'")])
        
        result['response_time'] = round(time.time() - start_time, 2)
        result['success'] = True
        result['message'] = f"✅ Azure OpenAI connected successfully ({result['response_time']}s)"
        
    except Exception as e:
        result['success'] = False
        error_msg = str(e)
        result['error'] = error_msg
        
        # Add specific hints for common errors
        if '401' in error_msg or 'Unauthorized' in error_msg or 'PermissionDenied' in error_msg:
            result['message'] = f"❌ Azure OpenAI authentication failed: API key invalid or expired"
        elif '404' in error_msg or 'NotFound' in error_msg:
            result['message'] = f"❌ Azure OpenAI deployment not found: Check model/deployment name"
        elif 'timeout' in error_msg.lower():
            result['message'] = f"❌ Azure OpenAI connection timeout: Check network connectivity"
        else:
            result['message'] = f"❌ Azure OpenAI connection failed: {error_msg}"
        
        result['response_time'] = round(time.time() - start_time, 2)
    
    return result


def _test_openai(config: Dict[str, Any]) -> Dict[str, Any]:
    """Test OpenAI connectivity"""
    import time
    from langchain_openai import ChatOpenAI
    from langchain.schema import HumanMessage
    
    result = {}
    start_time = time.time()
    
    try:
        llm = ChatOpenAI(
            model=config['model'],
            openai_api_key=os.getenv('OPENAI_API_KEY_DEV') or os.getenv('OPENAI_API_KEY'),
            temperature=0.0,
            max_tokens=100
        )
        
        response = llm.invoke([HumanMessage(content="Hello, respond with just 'OK'")])
        
        result['response_time'] = round(time.time() - start_time, 2)
        result['success'] = True
        result['message'] = f"✅ OpenAI connected successfully ({result['response_time']}s)"
        
    except Exception as e:
        result['success'] = False
        result['error'] = str(e)
        result['message'] = f"❌ OpenAI connection failed: {str(e)}"
        result['response_time'] = round(time.time() - start_time, 2)
    
    return result


def _test_ollama(config: Dict[str, Any]) -> Dict[str, Any]:
    """Test Ollama connectivity"""
    import time
    import requests
    
    result = {}
    start_time = time.time()
    
    try:
        # Test Ollama API endpoint
        response = requests.get(f"{config['endpoint']}/api/tags", timeout=5)
        response.raise_for_status()
        
        result['response_time'] = round(time.time() - start_time, 2)
        result['success'] = True
        result['message'] = f"✅ Ollama connected successfully ({result['response_time']}s)"
        
    except Exception as e:
        result['success'] = False
        result['error'] = str(e)
        result['message'] = f"❌ Ollama connection failed: {str(e)}"
        result['response_time'] = round(time.time() - start_time, 2)
    
    return result


def format_llm_status() -> str:
    """Format LLM status information for display"""
    config = get_llm_config()
    status = test_llm_connectivity()
    
    output = f"""
🔌 **LLM Connection Status**

**Provider:** {config['provider'].upper()}
**Model:** {config['model']}
**Endpoint:** {config['endpoint']}
**API Version:** {config['api_version']}
**Temperature:** {config['temperature']}
**Max Tokens:** {config['max_tokens']}
**API Key:** {'✅ Configured' if config['api_key_set'] else '❌ Not configured'}

**Connection Test:**
{status['message']}
"""
    
    if status['response_time']:
        output += f"**Response Time:** {status['response_time']}s\n"
    
    if status['error'] and not status['success']:
        output += f"\n**Error Details:**\n{status['error']}\n"
        output += f"\n**Troubleshooting:**\n"
        output += f"1. Check your .env file for correct API keys\n"
        output += f"2. Verify endpoint URL is correct\n"
        output += f"3. Ensure network connectivity\n"
        output += f"4. Check API key permissions\n"
    
    return output


def print_llm_status():
    """Print LLM status to console"""
    print(format_llm_status())


def get_llm_status_dict() -> Dict[str, Any]:
    """Get LLM status as a dictionary for programmatic use"""
    config = get_llm_config()
    status = test_llm_connectivity()
    
    return {
        'config': config,
        'status': status,
        'is_healthy': status['success']
    }


if __name__ == "__main__":
    """Run health check when executed directly"""
    print("🔍 Universal Tester - LLM Health Check\n")
    print_llm_status()
    
    status = get_llm_status_dict()
    sys.exit(0 if status['is_healthy'] else 1)
