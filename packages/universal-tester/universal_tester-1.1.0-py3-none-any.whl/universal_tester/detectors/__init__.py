"""
Import and dependency detection for Java and Kotlin projects.
"""

from universal_tester.detectors.enhanced_import_detector import DynamicImportDetector
from universal_tester.detectors.kotlin_import_detector import KotlinImportDetector

# Alias for backward compatibility
EnhancedImportDetector = DynamicImportDetector

__all__ = [
    "DynamicImportDetector",
    "EnhancedImportDetector",
    "KotlinImportDetector",
]
