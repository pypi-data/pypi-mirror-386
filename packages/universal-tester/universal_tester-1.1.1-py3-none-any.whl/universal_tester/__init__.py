"""
Universal Tester - AI-powered test generation for Java and Kotlin projects

This package provides core functionality for automatically generating unit tests
using Large Language Models (LLMs).
"""

__version__ = "1.1.0"
__author__ = "Senthil Kumar Thanapal"
__email__ = "senthilthepro@hotmail.com"

# Core functionality
from universal_tester.core import (
    get_app_info,
    format_version_info,
    get_short_version_info,
    process_java_zip_enhanced_core,
)

# LLM functionality
from universal_tester.llm.factory import LLMFactory
from universal_tester.llm.health_check import (
    print_llm_status,
    get_llm_status_dict,
    test_llm_connectivity,
)

# Detectors
from universal_tester.detectors import (
    EnhancedImportDetector,
    DynamicImportDetector,
    KotlinImportDetector,
)

__all__ = [
    # Version info
    "__version__",
    "__author__",
    "__email__",
    # Core functions
    "get_app_info",
    "format_version_info",
    "get_short_version_info",
    "process_java_zip_enhanced_core",
    # LLM
    "LLMFactory",
    "print_llm_status",
    "get_llm_status_dict",
    "test_llm_connectivity",
    # Detectors
    "EnhancedImportDetector",
    "DynamicImportDetector",
    "KotlinImportDetector",
]
