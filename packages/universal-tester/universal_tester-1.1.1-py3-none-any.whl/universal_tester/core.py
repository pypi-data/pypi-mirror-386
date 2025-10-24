# -*- coding: utf-8 -*-
import os
import re
import sys
import zipfile
import tempfile
import shutil
import json
import yaml
import logging

# Import version from package
try:
    from universal_tester import __version__ as PACKAGE_VERSION
except ImportError:
    PACKAGE_VERSION = "1.1.0"
from pathlib import Path
from typing import List, Dict, Any, Optional
import asyncio
from datetime import datetime
from langchain_openai import AzureChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

# Create logger for this module
logger = logging.getLogger(__name__)

# Set debug mode based on environment variable
if os.getenv("DEBUG_MODE", "false").lower() == "true":
    logger.setLevel(logging.DEBUG)
    logger.debug("Debug mode enabled")

# Load system configuration for version management
def load_system_config():
    """Load system configuration from .env_system file"""
    config = {}
    try:
        with open('.env_system', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
    except FileNotFoundError:
        logger.warning(".env_system file not found, using default version")
    return config

# Load system configuration
SYSTEM_CONFIG = load_system_config()

# Application Version Information - use package version as primary source
APP_VERSION = PACKAGE_VERSION
APP_NAME = SYSTEM_CONFIG.get('PRODUCT_NAME', 'Universal Tester').replace('_', ' ').title()
APP_DESCRIPTION = SYSTEM_CONFIG.get('PRODUCT_DESCRIPTION', 'AI-powered application for automatic test case generation')
BUILD_DATE = SYSTEM_CONFIG.get('BUILD_DATE', datetime.now().strftime('%Y-%m-%d'))
AUTHOR = SYSTEM_CONFIG.get('AUTHOR', 'Senthil Kumar Thanapal')
CONTACT_NAMES = SYSTEM_CONFIG.get('CONTACT_NAMES', 'Support Team')
CONTACT_TYPE = SYSTEM_CONFIG.get('CONTACT_TYPE', 'Issues/Feedback')
SUPPORT_EMAIL = SYSTEM_CONFIG.get('SUPPORT_EMAIL', 'senthilthepro@hotmail.com')
SUPPORTED_JAVA_VERSIONS = ["Java 8+", "Java 11", "Java 17", "Java 21"]
SUPPORTED_KOTLIN_VERSIONS = ["Kotlin 1.8+", "Kotlin 1.9", "Kotlin 2.0"]
SUPPORTED_FRAMEWORKS = ["Spring Boot", "Spring Framework", "JPA/Hibernate", "Mockito", "JUnit 5", "MockK", "Kotest"]
SUPPORTED_LANGUAGES = ["Java", "Kotlin"]

def get_app_info() -> Dict[str, Any]:
    """Get comprehensive application information for UI display"""
    return {
        "name": os.getenv("APP_NAME_OVERRIDE", APP_NAME),
        "version": APP_VERSION,
        "description": os.getenv("APP_DESCRIPTION_OVERRIDE", APP_DESCRIPTION),
        "build_date": BUILD_DATE,
        "author": os.getenv("AUTHOR_OVERRIDE", AUTHOR),
        "contact_names": CONTACT_NAMES,
        "contact_type": CONTACT_TYPE,
        "support_email": SUPPORT_EMAIL,
        "supported_java_versions": SUPPORTED_JAVA_VERSIONS,
        "supported_kotlin_versions": SUPPORTED_KOTLIN_VERSIONS,
        "supported_frameworks": SUPPORTED_FRAMEWORKS,
        "supported_languages": SUPPORTED_LANGUAGES,
        "max_iterations": get_max_iterations(),
        "exclude_private_method_tests": is_private_method_testing_excluded(),
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "chainlit_version": "N/A (UI Separated)",
        "environment": os.getenv("APP_ENV", "development")
    }

def format_version_info() -> str:
    """Format version information for display in any UI"""
    info = get_app_info()
    
    # Use ASCII-safe characters for Windows console compatibility
    version_text = f"""
{info['name']} v{info['version']}
Author: {info['author']}

System Information:
- Build Date: {info['build_date']}
- Environment: {info['environment'].title()}
- Python: {info['python_version']}
- Max Iterations: {info['max_iterations']}
- Private Method Tests: {'Excluded' if info['exclude_private_method_tests'] else 'Included'}

Contact & Feedback:
- {info['contact_type']}: {info['contact_names']}
- Support: {info['support_email']}

Java Support:
- Versions: {', '.join(info['supported_java_versions'])}

Kotlin Support:
- Versions: {', '.join(info['supported_kotlin_versions'])}

Supported Frameworks:
- {', '.join(info['supported_frameworks'])}

Supported Languages:
- {', '.join(info['supported_languages'])}

---

"""
    return version_text

def get_version_string() -> str:
    """Get a simple version string for logging/display"""
    return f"{APP_NAME} v{APP_VERSION}"

def get_short_version_info() -> str:
    """Get condensed version info for status messages"""
    info = get_app_info()
    private_method_status = "No Private Tests" if info['exclude_private_method_tests'] else "With Private Tests"
    return f"🔧 {info['name']} v{info['version']} | {info['environment'].title()} | Max Iterations: {info['max_iterations']} | {private_method_status}"

def get_max_iterations() -> int:
    """
    Get max_iterations from environment variable with default value of 3
    
    Environment Variable: MAX_ITERATIONS
    - Controls the maximum number of LLM auto-fix iterations for validation issues
    - Default: 3
    - Valid range: 1-10 (values outside this range are clamped)
    
    Returns:
        int: The maximum number of iterations to perform
    """
    try:
        max_iter = int(os.getenv("MAX_ITERATIONS", "3"))
        # Ensure it's a reasonable value (between 1 and 10)
        if max_iter < 1:
            max_iter = 1
        elif max_iter > 10:
            max_iter = 10
        return max_iter
    except (ValueError, TypeError):
        return 3

def is_private_method_testing_excluded() -> bool:
    """
    Check if private method test generation should be excluded
    
    Environment Variable: EXCLUDE_PRIVATE_METHOD_TESTS
    - Controls whether to generate test cases for private methods
    - Default: false (private methods are tested via reflection)
    - When true: excludes private method testing entirely
    
    Returns:
        bool: True if private method testing should be excluded
    """
    try:
        exclude_setting = os.getenv("EXCLUDE_PRIVATE_METHOD_TESTS", "false").lower().strip()
        return exclude_setting in ['true', '1', 'yes', 'on', 'enabled']
    except Exception:
        return False

def is_incremental_test_generation_enabled() -> bool:
    """
    Check if incremental test generation is enabled
    
    Environment Variable: INCREMENTAL_TEST_GENERATION
    - Controls whether to create additional numbered test files when existing tests exist
    - Default: false (overwrite existing test files)
    - When true: check for existing test files and create numbered versions (Test2.java, Test3.java, etc.)
    
    Returns:
        bool: True if incremental test generation is enabled
    """
    try:
        incremental_setting = os.getenv("INCREMENTAL_TEST_GENERATION", "false").lower().strip()
        return incremental_setting in ['true', '1', 'yes', 'on', 'enabled']
    except Exception:
        return False

def get_development_focus_file() -> str:
    """
    Get the development focus file for testing specific Java classes
    
    Environment Variable: DEVELOPMENT_FOCUS_FILE
    - Controls which specific Java file to process during development
    - Default: None (process all files in normal mode)
    - When set: only process the specified file for faster development testing
    
    Returns:
        str: Filename to focus on or None for normal mode
    """
    try:
        focus_file = os.getenv("DEVELOPMENT_FOCUS_FILE", "").strip()
        if focus_file.lower() in ['none', 'null', 'false', '']:
            return None
        return focus_file
    except Exception:
        return None

"""
🔧 DEVELOPMENT TESTING CONFIGURATION

To focus on a specific Java file during development, use the .env file:

1. Open the .env file in the project root
2. Set DEVELOPMENT_FOCUS_FILE to your target file:
   
   Examples:
   DEVELOPMENT_FOCUS_FILE=StringHelper.java
   DEVELOPMENT_FOCUS_FILE=SecurityConfig.java
   DEVELOPMENT_FOCUS_FILE=UserService.java
   DEVELOPMENT_FOCUS_FILE=DataValidator.java
   
3. Set to empty or None for normal processing:
   DEVELOPMENT_FOCUS_FILE=
   # or
   DEVELOPMENT_FOCUS_FILE=None

4. Restart the application for changes to take effect

This approach allows you to change the focus file without modifying code!
This will skip all other files and focus testing on your specified file only.
"""

# Import prompts
from universal_tester.prompts.prompt_builder import PromptBuilder

# Import enhanced dynamic import detector
from universal_tester.detectors.enhanced_import_detector import DynamicImportDetector

# Import LLM-based Java validator
from universal_tester.llm.java_validator import LLMJavaValidator, validate_java_file_with_llm



# Development testing helper function
def get_dev_focus_files():
    """
    Helper function to easily see and manage development focus files
    
    Available Java files in your sample project:
    - StringHelper.java (Utility class with string operations)
    - SecurityConfig.java (Spring Security configuration)
    - UserService.java (Main service class)
    - DataValidator.java (Data validation logic)
    - EncryptionUtil.java (Encryption utilities)
    - FileUtils.java (File processing utilities)
    - ErrorHandler.java (Exception handling)
    - MessageProducer.java (Message producer)
    - ResponseMapper.java (Response mapping utility)
    
    Usage: Set DEVELOPMENT_FOCUS_FILE in .env to one of these files for focused testing
    """
    return {
        "utils": ["StringHelper.java", "EncryptionUtil.java", "FileUtils.java"],
        "services": ["UserService.java"],
        "validation": ["DataValidator.java", "InputValidator.java", "SchemaValidator.java"],
        "security": ["SecurityConfig.java"],
        "controllers": ["ErrorHandler.java"],
        "producers": ["MessageProducer.java"],
        "mappers": ["ResponseMapper.java"]
    }

# Initialize LLM with Azure OpenAI configuration
def get_llm():
    from universal_tester.llm.factory import LLMFactory
    return LLMFactory.create_llm(
        streaming=os.getenv("OPENAI_IS_STREAMING", "false").lower() == "true",
        temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.3")),
        request_timeout=int(os.getenv("OPENAI_REQUEST_TIMEOUT", "60")),
        max_retries=int(os.getenv("OPENAI_MAX_RETRIES", "2")),
    )
    return llm

def auto_fix_imports(java_code: str, missing_imports: List[Dict[str, Any]]) -> str:
    """Auto-fix missing imports in Java code by inserting them after the package declaration."""
    try:
        # Extract all current imports with improved regex
        import_lines = set(re.findall(r'import\s+([^;]+);', java_code))
        print(f"🔍 Found existing imports: {import_lines}")
        
        # Build new import statements for missing imports
        new_imports = []
        for imp in missing_imports:
            imp_str = imp.get('import', '') or imp.get('name', '')
            if imp_str:
                # Check if import already exists (case-insensitive and whitespace tolerant)
                already_exists = any(
                    imp_str.strip().lower() == existing.strip().lower() 
                    for existing in import_lines
                )
                if not already_exists:
                    new_imports.append(f"import {imp_str};")
                    print(f"✅ Adding missing import: {imp_str}")
                else:
                    print(f"⚠️ Import already exists, skipping: {imp_str}")
        
        if not new_imports:
            print("ℹ️ No new imports needed")
            return java_code  # Nothing to add
        # Find where to insert imports (after package, before first import/class)
        lines = java_code.split('\n')
        insert_idx = 0
        for i, line in enumerate(lines):
            if line.strip().startswith('package '):
                insert_idx = i + 1
                break
        # Find last import line if any
        for i, line in enumerate(lines):
            if line.strip().startswith('import '):
                insert_idx = i + 1
        # Insert new imports, avoiding duplicates
        for imp in new_imports:
            if imp not in lines:
                lines.insert(insert_idx, imp)
                insert_idx += 1
        return '\n'.join(lines)
    except Exception as e:
        logger.error(f"auto_fix_imports error: {e}")
        return java_code

def fix_loggerbean_usage(java_code: str) -> str:
    """Fix LoggerBean type conversion issues that cause compilation errors"""
    try:
        print("🔧 Applying LoggerBean type conversion fixes...")
        
        # Pattern 1: Fix setTransactionType with String to use Arrays.asList()
        pattern1 = r'\.setTransactionType\s*\(\s*"([^"]+)"\s*\)'
        replacement1 = r'.setTransactionType(Arrays.asList("\1"))'
        java_code = re.sub(pattern1, replacement1, java_code)
        
        # Pattern 2: Fix any List setter that incorrectly uses String
        list_setters = ['setTransactionType', 'setProductCategories', 'setOrderTypes']
        for setter in list_setters:
            pattern = rf'\.{setter}\s*\(\s*"([^"]+)"\s*\)'
            replacement = rf'.{setter}(Arrays.asList("\1"))'
            java_code = re.sub(pattern, replacement, java_code)
        
        # Pattern 3: Fix any String setter that incorrectly uses Arrays.asList()
        string_setters = ['setChannelId', 'setCorrelationId', 'setUserId', 'setOrderId']
        for setter in string_setters:
            pattern = rf'\.{setter}\s*\(\s*Arrays\.asList\s*\(\s*"([^"]+)"\s*\)\s*\)'
            replacement = rf'.{setter}("\1")'
            java_code = re.sub(pattern, replacement, java_code)
        
        # Pattern 4: Ensure Arrays import is present when Arrays.asList is used
        if 'Arrays.asList' in java_code and 'import java.util.Arrays;' not in java_code:
            # Find the package line and add import after it
            lines = java_code.split('\n')
            for i, line in enumerate(lines):
                if line.strip().startswith('package '):
                    lines.insert(i + 1, 'import java.util.Arrays;')
                    break
            java_code = '\n'.join(lines)
            print("✅ Added missing Arrays import for LoggerBean usage")
        
        # Pattern 5: Fix reflection calls with wrong parameter types
        # getDeclaredMethod with String vs List parameter type errors
        reflection_fixes = [
            (r'getDeclaredMethod\s*\(\s*"setTransactionType"\s*,\s*String\.class\s*\)', 'getDeclaredMethod("setTransactionType", List.class)'),
            (r'getDeclaredMethod\s*\(\s*"setChannelId"\s*,\s*List\.class\s*\)', 'getDeclaredMethod("setChannelId", String.class)'),
        ]
        
        for pattern, replacement in reflection_fixes:
            java_code = re.sub(pattern, replacement, java_code)
        
        print("✅ LoggerBean type conversion fixes applied")
        return java_code
        
    except Exception as e:
        logger.error(f"Error fixing LoggerBean usage: {str(e)}")
        return java_code

async def validate_generated_test_with_llm(test_content: str, original_class_name: str, llm=None) -> Dict[str, Any]:
    """Validate generated test code using LLM for import and compilation issues"""
    try:
        validator = LLMJavaValidator(llm=llm)
        validation_result = await validator.validate_java_imports_and_compilation(test_content)
        
        # Add context about the original class
        validation_result['original_class'] = original_class_name
        validation_result['test_type'] = 'generated_junit_test'
        
        return validation_result
        
    except Exception as e:
        return {
            'validation_status': 'ERROR',
            'critical_issues': [{
                'type': 'VALIDATION_ERROR',
                'severity': 'CRITICAL',
                'line_number': 0,
                'message': f"LLM validation failed: {str(e)}",
                'suggestion': "Check LLM configuration and try again",
                'code_snippet': ''
            }],
            'missing_imports': [],
            'unused_imports': [],
            'compilation_errors': [],
            'recommendations': [],
            'overall_assessment': f"Validation failed: {str(e)}",
            'original_class': original_class_name,
            'test_type': 'generated_junit_test',
            'llm_validation': False
        }

async def auto_fix_validation_issues_with_llm(java_code: str, validation_result: Dict[str, Any], llm, max_iterations: int = None) -> str:
    """
    Iteratively fix validation issues using LLM according to the specified workflow:
    1. Collect all issues from the validation report
    2. For each issue, construct a prompt describing the problem, code snippet, and suggested fix
    3. Send this prompt to the LLM to generate a corrected version
    4. Apply the LLM's suggested fix to the code
    5. Re-validate the fixed code and repeat if issues remain
    6. Track the best result (iteration with minimal issues) and return it
    
    Args:
        java_code: The Java code to fix
        validation_result: The validation result containing issues to fix
        llm: The language model instance
        max_iterations: Maximum number of fix iterations. If None, reads from MAX_ITERATIONS env var (default: 3)
    
    Returns:
        The best fixed Java code after all iterations
    """
    try:
        # Use environment variable if max_iterations not provided
        if max_iterations is None:
            max_iterations = get_max_iterations()
        
        current_code = java_code
        iteration = 0
        
        # Track the best iteration with minimal issues
        best_iteration = {
            'code': java_code,
            'validation_result': validation_result,
            'iteration_number': 0,
            'total_issues': float('inf')  # Start with infinity so first iteration is always better
        }
        
        # Save original validation for comparison
        original_validation_result = validation_result.copy()
        
        def calculate_total_issues(validation_result):
            """Calculate total issue count for comparison"""
            critical_count = len(validation_result.get('critical_issues', []))
            missing_imports_count = len(validation_result.get('missing_imports', []))
            compilation_count = len(validation_result.get('compilation_errors', []))
            unused_imports_count = len(validation_result.get('unused_imports', []))
            
            # Weight critical issues and compilation errors more heavily
            weighted_total = (critical_count * 10) + (compilation_count * 8) + (missing_imports_count * 5) + (unused_imports_count * 1)
            return weighted_total
        
        # Calculate initial issue count
        initial_issues = calculate_total_issues(validation_result)
        best_iteration['total_issues'] = initial_issues
        
        logger.info(f"Starting auto-fix with {initial_issues} weighted issues (Critical: {len(validation_result.get('critical_issues', []))}, Missing Imports: {len(validation_result.get('missing_imports', []))}, Compilation: {len(validation_result.get('compilation_errors', []))}, Unused: {len(validation_result.get('unused_imports', []))})")
        
        while iteration < max_iterations:
            iteration += 1
            logger.info(f"Auto-fix iteration {iteration}/{max_iterations}")
            
            # Step 1: Collect all issues from the validation report
            all_issues = []
            
            # Collect critical issues
            critical_issues = validation_result.get('critical_issues', [])
            all_issues.extend(critical_issues)
            
            # Collect missing imports
            missing_imports = validation_result.get('missing_imports', [])
            for imp in missing_imports:
                all_issues.append({
                    'type': 'MISSING_IMPORT',
                    'severity': 'HIGH',
                    'message': f"Missing import: {imp.get('import', imp.get('name', 'unknown'))}",
                    'suggestion': f"Add import statement: import {imp.get('import', imp.get('name', 'unknown'))};",
                    'import_name': imp.get('import', imp.get('name', 'unknown'))
                })
            
            # Collect compilation errors
            compilation_errors = validation_result.get('compilation_errors', [])
            all_issues.extend(compilation_errors)
            
            # Collect unused imports (lower priority)
            unused_imports = validation_result.get('unused_imports', [])
            for imp in unused_imports:
                all_issues.append({
                    'type': 'UNUSED_IMPORT',
                    'severity': 'LOW',
                    'message': f"Unused import: {imp}",
                    'suggestion': f"Remove unused import: import {imp};",
                    'import_name': imp
                })
            
            # If no issues found, break the loop
            if not all_issues:
                print(f"✅ No more issues found after {iteration-1} iterations")
                break
            
            print(f"🔍 Found {len(all_issues)} issues to fix in iteration {iteration}")
            
            # Step 2: Construct prompt for each issue and ask LLM to fix
            issues_summary = []
            for i, issue in enumerate(all_issues[:10], 1):  # Limit to top 10 issues per iteration
                issue_type = issue.get('type', 'UNKNOWN')
                severity = issue.get('severity', 'MEDIUM')
                message = issue.get('message', 'No message')
                suggestion = issue.get('suggestion', 'No suggestion')
                
                issues_summary.append(f"{i}. [{issue_type}] {message}\n   Suggested fix: {suggestion}")
            
            # Step 3: Send prompt to LLM for code correction
            fix_prompt = f"""
You are a Java code expert. Please fix the following validation issues in this Java test code.

**Issues to Fix:**
{chr(10).join(issues_summary)}

**Current Java Code:**
```java
{current_code}
```

**CRITICAL VOID METHOD RULES:**
- VOID METHODS NEVER RETURN VALUES - DO NOT use when().thenReturn() with void methods
- FOR VOID METHODS: Use doNothing().when(mock).voidMethod() or doThrow().when(mock).voidMethod()
- FOR RETURN METHODS: Use when(mock.method()).thenReturn(value) or when(mock.method()).thenThrow(exception)
- VOID METHOD VERIFICATION: Always use verify(mock).voidMethod() to ensure void methods were called

**CRITICAL LOGGERBEAN TYPE CONVERSION RULES:**
- setTransactionType() expects List<String> - use Arrays.asList("TYPE") NOT "TYPE"
- setChannelId() expects String - use "WEB_APP" NOT Arrays.asList("WEB_APP")
- setCorrelationId() expects String - use "12345" NOT Arrays.asList("12345")
- setUserId() expects String - use "user123" NOT Arrays.asList("user123")
- ALWAYS add import java.util.Arrays; when using Arrays.asList()
- NEVER mix String and List<String> types in LoggerBean setters

**Instructions:**
1. Fix ALL the listed issues in the code
2. For missing imports, add them after the package declaration
3. For unused imports, remove them
4. For compilation errors, fix the syntax/logic issues
5. For void method mocking errors, use doNothing().when() instead of when().thenReturn()
6. For LoggerBean type errors, use correct parameter types (String vs List<String>)
7. Add import java.util.Arrays; when using Arrays.asList() with LoggerBean
8. Maintain the original test logic and structure
9. Return ONLY the corrected Java code without any explanations
10. Do not add comments about the fixes

Please provide the corrected Java code:
"""

            try:
                messages = [
                    SystemMessage(content="You are a Java expert. Fix the validation issues in the provided code. CRITICAL: For void methods, use doNothing().when().voidMethod() - NEVER use when().thenReturn() with void methods. CRITICAL LoggerBean rules: setTransactionType() expects List<String> use Arrays.asList(), setChannelId() expects String. Return only the corrected Java code without explanations."),
                    HumanMessage(content=fix_prompt)
                ]
                
                response = await llm.ainvoke(messages)
                
                fixed_code = response.content.strip()
                
                # Clean up the response (remove markdown if present)
                if fixed_code.startswith('```java'):
                    fixed_code = fixed_code.replace('```java', '').replace('```', '').strip()
                elif fixed_code.startswith('```'):
                    fixed_code = fixed_code.replace('```', '').strip()
                
                # Step 4: Apply the LLM's suggested fix
                current_code = fixed_code
                print(f"🔧 Applied LLM fixes for iteration {iteration}")
                
                # Step 4.5: Apply LoggerBean type conversion fixes
                current_code = fix_loggerbean_usage(current_code)
                
                # Step 5: Re-validate the fixed code
                validator = LLMJavaValidator(llm=llm)
                validation_result = await validator.validate_java_imports_and_compilation(current_code)
                
                # Calculate current iteration issues
                current_issues = calculate_total_issues(validation_result)
                
                # Check if we've improved
                remaining_critical = len(validation_result.get('critical_issues', []))
                remaining_missing = len(validation_result.get('missing_imports', []))
                remaining_compilation = len(validation_result.get('compilation_errors', []))
                remaining_unused = len(validation_result.get('unused_imports', []))
                
                print(f"📊 After iteration {iteration}: {current_issues} weighted issues (Critical: {remaining_critical}, Missing: {remaining_missing}, Compilation: {remaining_compilation}, Unused: {remaining_unused})")
                
                # Update best iteration if current is better
                if current_issues < best_iteration['total_issues']:
                    best_iteration = {
                        'code': current_code,
                        'validation_result': validation_result,
                        'iteration_number': iteration,
                        'total_issues': current_issues
                    }
                    print(f"🏆 New best iteration found: Iteration {iteration} with {current_issues} weighted issues")
                else:
                    print(f"📉 No improvement: Current {current_issues} vs Best {best_iteration['total_issues']} (Iteration {best_iteration['iteration_number']})")
                
                # If validation passes or only minor issues remain, break
                if validation_result.get('validation_status') == 'PASS':
                    print(f"✅ Validation passed after {iteration} iterations!")
                    break
                elif remaining_critical == 0 and remaining_missing == 0 and remaining_compilation == 0:
                    print(f"✅ All major issues fixed after {iteration} iterations!")
                    break
                    
            except Exception as e:
                print(f"⚠️ Error in LLM auto-fix iteration {iteration}: {str(e)}")
                break
        
        # Return the best iteration result
        final_critical = len(best_iteration['validation_result'].get('critical_issues', []))
        final_missing = len(best_iteration['validation_result'].get('missing_imports', []))
        final_compilation = len(best_iteration['validation_result'].get('compilation_errors', []))
        final_unused = len(best_iteration['validation_result'].get('unused_imports', []))
        
        # Get initial counts from original validation
        initial_critical = len(original_validation_result.get('critical_issues', []))
        initial_missing = len(original_validation_result.get('missing_imports', []))
        initial_compilation = len(original_validation_result.get('compilation_errors', []))
        initial_unused = len(original_validation_result.get('unused_imports', []))
        
        if best_iteration['iteration_number'] > 0:
            print(f"🎯 Returning best result from iteration {best_iteration['iteration_number']} with {best_iteration['total_issues']} weighted issues")
            print(f"📈 Improvement summary:")
            print(f"   Critical: {initial_critical} → {final_critical} (Δ{final_critical - initial_critical})")
            print(f"   Missing Imports: {initial_missing} → {final_missing} (Δ{final_missing - initial_missing})")
            print(f"   Compilation: {initial_compilation} → {final_compilation} (Δ{final_compilation - initial_compilation})")
            print(f"   Unused Imports: {initial_unused} → {final_unused} (Δ{final_unused - initial_unused})")
        else:
            print(f"🎯 Returning original code (no improvements found)")
        
        return best_iteration['code']
        
    except Exception as e:
        print(f"❌ Error in auto_fix_validation_issues_with_llm: {str(e)}")
        return java_code  # Return original code if fixing fails

def remove_embedded_class_definitions(content: str, current_class: str = "Unknown") -> str:
    """Remove any embedded class definitions from test content (architectural fix)"""
    try:
        lines = content.split('\n')
        cleaned_lines = []
        inside_embedded_class = False
        brace_count = 0
        removed_embedded_class = False
        
        for i, line in enumerate(lines):
            stripped_line = line.strip()
            
            # Detect start of embedded class definition (not test class)
            if (stripped_line.startswith('@Configuration') or 
                stripped_line.startswith('@EnableWebSecurity') or
                stripped_line.startswith('@Service') or
                stripped_line.startswith('@Component') or
                stripped_line.startswith('@Repository') or
                stripped_line.startswith('@Controller')):
                # Check if next few lines contain a class definition that's not a test class
                for j in range(i+1, min(i+5, len(lines))):
                    next_line = lines[j].strip()
                    if (re.match(r'class\s+(\w+)', next_line) and 
                        not next_line.endswith('Test {') and 
                        not 'Test' in next_line):
                        inside_embedded_class = True
                        removed_embedded_class = True
                        print(f"🚨 FIXED: Removing embedded class definition starting at line {i+1}")
                        break
            
            # Detect class definition that's not a test class
            if (re.match(r'(public\s+)?class\s+(\w+)', stripped_line) and 
                not stripped_line.endswith('Test {') and 
                not 'Test' in stripped_line and
                not inside_embedded_class):
                inside_embedded_class = True
                removed_embedded_class = True
                print(f"🚨 FIXED: Removing embedded class definition: {stripped_line}")
            
            if inside_embedded_class:
                # Count braces to know when class definition ends
                brace_count += stripped_line.count('{') - stripped_line.count('}')
                
                # Skip this line as it's part of embedded class
                if brace_count <= 0:
                    inside_embedded_class = False
                    brace_count = 0
                continue
            
            cleaned_lines.append(line)
        
        if removed_embedded_class:
            print(f"🔧 Removed embedded class definitions from test file for {current_class}")
            return '\n'.join(cleaned_lines)
        
        return content
        
    except Exception as e:
        print(f"⚠️ Error removing embedded class definitions: {str(e)}")
        return content

# Function-based Java Analysis Tools
def analyze_java_code(java_code: str) -> Dict[str, Any]:
    """Analyze Java code and return structured information with enhanced dynamic import detection"""
    try:
        # Initialize the enhanced dynamic import detector
        import_detector = DynamicImportDetector()
        
        # Extract package name
        package_match = re.search(r'package\s+([^;]+);', java_code)
        package_name = package_match.group(1) if package_match else ""
        
        # Extract class name
        class_match = re.search(r'public\s+class\s+(\w+)', java_code)
        class_name = class_match.group(1) if class_match else "UnknownClass"
        
        # Extract imports
        imports = re.findall(r'import\s+([^;]+);', java_code)
        
        # Extract methods with more details - separate public and private methods
        method_pattern = r'(public|private|protected)\s+(?:static\s+)?(?:final\s+)?(\w+(?:<[^>]+>)?)\s+(\w+)\s*\(([^)]*)\)\s*(?:throws\s+[^{]+)?\s*\{'
        all_methods = re.findall(method_pattern, java_code)
        
        # Enhanced method analysis - extract return types and parameters more accurately
        detailed_methods = []
        for visibility, return_type, name, parameters in all_methods:
            if name not in ['equals', 'hashCode', 'toString']:
                # Clean parameter string and extract parameter info
                clean_params = parameters.strip() if parameters else ""
                param_list = []
                if clean_params:
                    for param in clean_params.split(','):
                        param = param.strip()
                        if param:
                            # Extract parameter type and name
                            param_parts = param.split()
                            if len(param_parts) >= 2:
                                param_type = ' '.join(param_parts[:-1])
                                param_name = param_parts[-1]
                                param_list.append({'type': param_type, 'name': param_name})
                
                detailed_methods.append({
                    'visibility': visibility,
                    'return_type': return_type,
                    'name': name,
                    'parameters': clean_params,
                    'parameter_list': param_list,
                    'signature': f"{visibility} {return_type} {name}({clean_params})",
                    'is_getter': name.startswith('get') and len(param_list) == 0 and return_type != 'void',
                    'is_setter': name.startswith('set') and len(param_list) == 1 and return_type == 'void',
                    'is_boolean_getter': name.startswith('is') and len(param_list) == 0 and return_type.lower() in ['boolean', 'bool']
                })
        
        # Add method validation guidance
        available_getters = [m['name'] for m in detailed_methods if m['is_getter'] or m['is_boolean_getter']]
        available_setters = [m['name'] for m in detailed_methods if m['is_setter']]
        
        # Use enhanced dynamic import detection
        import_detection_result = import_detector.detect_imports(java_code)
        detected_imports = import_detection_result['detected_imports']
        
        # Get contextual imports based on class name
        contextual_imports = import_detector.get_contextual_imports(java_code, class_name)
        
        # Add project-specific imports from the source code
        project_specific_imports = []
        application_classes = []  # Track application classes to avoid framework conflicts
        
        for imp in imports:
            # Include non-standard Java imports (exclude java.*, javax.*, jakarta.* and common test frameworks)
            if not any(imp.startswith(prefix) for prefix in [
                'java.', 'javax.', 'jakarta.', 'org.junit', 'org.mockito', 'org.springframework.test'
            ]):
                # Track application classes vs framework classes
                if package_name and imp.startswith(package_name):
                    # This is an application class from the same project
                    class_name_from_import = imp.split('.')[-1]
                    application_classes.append(class_name_from_import)
                    project_specific_imports.append(imp)
                elif any(keyword in imp.lower() for keyword in [
                    'apache.commons', 'fasterxml.jackson', 'google.guava', 'slf4j', 'logback', 'lombok'
                ]) or '.' in imp and not imp.startswith('org.springframework.'):
                    # Include third-party libraries but avoid Spring framework conflicts
                    project_specific_imports.append(imp)
                # Include any custom project imports (non-standard packages) 
                elif not imp.startswith(('org.springframework', 'org.apache.logging', 'org.slf4j')):
                    project_specific_imports.append(imp)
        
        # Filter out conflicting framework imports
        filtered_detected_imports = []
        for detected_imp in detected_imports:
            detected_class = detected_imp.split('.')[-1]
            # Don't suggest framework imports if application class exists
            if detected_class not in application_classes:
                filtered_detected_imports.append(detected_imp)
            else:
                print(f"🚨 Filtering out framework import {detected_imp} - application class {detected_class} exists")
        
        # Combine all imports for test generation (use filtered list)
        all_test_imports = list(set(filtered_detected_imports + contextual_imports + project_specific_imports))
        
        # Extract constructors separately
        constructor_pattern = r'(public|private|protected)\s+(' + re.escape(class_name) + r')\s*\(([^)]*)\)\s*(?:throws\s+[^{]+)?\s*\{'
        constructors = re.findall(constructor_pattern, java_code)
        
        # Extract exception classes from imports for better constructor understanding
        exception_imports = [imp for imp in imports if 'Exception' in imp]
        
        # Add guidance for common exception constructors based on imports
        exception_constructor_hints = []
        for exc_import in exception_imports:
            exc_name = exc_import.split('.')[-1]
            if 'RestApiHandlerException' in exc_name:
                exception_constructor_hints.append(f"RestApiHandlerException(int statusCode, String message, HttpHeaders headers, LoggerBean loggerContext)")
            elif 'NotFoundException' in exc_name:
                exception_constructor_hints.append(f"NotFoundException(int statusCode, String errorCode, String message, LoggerBean loggerContext)")
            elif 'UnknownBackendException' in exc_name:
                exception_constructor_hints.append(f"UnknownBackendException(int statusCode, String message, LoggerBean loggerContext)")
            elif 'BadRequestException' in exc_name:
                exception_constructor_hints.append(f"BadRequestException(String errorCode, String message, LoggerBean loggerContext)")
        
        # Separate public/protected methods (direct testing) from private methods (reflection testing)
        public_methods = []
        private_methods = []
        constructor_info = []
        
        # Check if private method testing should be excluded
        exclude_private_methods = is_private_method_testing_excluded()
        
        if exclude_private_methods:
            print(f"🚫 Private method testing excluded for {class_name} via EXCLUDE_PRIVATE_METHOD_TESTS environment variable")
        
        for method in detailed_methods:
            if method['visibility'] in ['public', 'protected']:
                public_methods.append(method)
            elif method['visibility'] == 'private' and not exclude_private_methods:
                private_methods.append(method)
        
        # Process constructors
        for constructor in constructors:
            visibility, name, parameters = constructor
            constructor_info.append({
                'visibility': visibility,
                'name': name,
                'parameters': parameters,
                'signature': f"{visibility} {name}({parameters})"
            })
        
        # Add exception constructor hints to constructor info
        for hint in exception_constructor_hints:
            constructor_info.append({
                'visibility': 'public',
                'name': hint.split('(')[0],
                'parameters': hint.split('(')[1].rstrip(')'),
                'signature': hint,
                'is_exception': True
            })
        
        # Extract fields
        field_pattern = r'(private|protected|public)\s+(?:static\s+)?(?:final\s+)?(\w+(?:<[^>]+>)?)\s+(\w+)\s*[=;]'
        fields = re.findall(field_pattern, java_code)
        
        # Detect dependencies and frameworks
        frameworks = []
        if 'Spring' in java_code or '@Service' in java_code or '@Component' in java_code:
            frameworks.append('Spring')
        if 'JPA' in java_code or '@Entity' in java_code:
            frameworks.append('JPA')
        if 'javax.servlet' in java_code or 'jakarta.servlet' in java_code:
            frameworks.append('Servlet')
        
        # Calculate complexity
        complexity_indicators = len(re.findall(r'\bif\b|\bfor\b|\bwhile\b|\bswitch\b|\btry\b', java_code))
        
        # Add import detection metadata
        import_metadata = {
            'total_detected_imports': len(detected_imports),
            'rules_matched': import_detection_result['total_rules_matched'],
            'categories_detected': list(import_detection_result['category_counts'].keys()),
            'detection_confidence': min(100, (import_detection_result['total_rules_matched'] / max(1, complexity_indicators)) * 10)
        }
        
        return {
            'language': 'java',
            'class_type': 'class',  # Add class_type for consistency with Kotlin
            'package': package_name,
            'class_name': class_name,
            'imports': imports,
            'detected_imports': filtered_detected_imports,  # Use filtered list
            'contextual_imports': contextual_imports,
            'project_specific_imports': project_specific_imports,
            'application_classes': application_classes,  # Add application classes tracking
            'all_test_imports': all_test_imports,
            'import_metadata': import_metadata,
            'methods': public_methods,
            'private_methods': private_methods,
            'constructors': constructor_info,
            'available_getters': available_getters,
            'available_setters': available_setters,
            'fields': [{'visibility': f[0], 'type': f[1], 'name': f[2]} for f in fields],
            'frameworks': frameworks,
            'complexity_score': complexity_indicators,
            'content': java_code
        }
    except Exception as e:
        return {'error': f"Error analyzing Java code: {str(e)}"}

def analyze_kotlin_code(kotlin_code: str) -> Dict[str, Any]:
    """Analyze Kotlin code and return structured information"""
    try:
        # Extract package name (Kotlin uses same package syntax as Java)
        package_match = re.search(r'package\s+([^\s\n]+)', kotlin_code)
        package_name = package_match.group(1) if package_match else ""
        
        # Extract class/object name (Kotlin has multiple class types)
        class_patterns = [
            r'class\s+(\w+)',
            r'data\s+class\s+(\w+)',
            r'sealed\s+class\s+(\w+)',
            r'object\s+(\w+)',
            r'interface\s+(\w+)',
            r'enum\s+class\s+(\w+)'
        ]
        
        class_name = "UnknownClass"
        class_type = "class"
        for pattern in class_patterns:
            match = re.search(pattern, kotlin_code)
            if match:
                class_name = match.group(1)
                if 'data class' in pattern:
                    class_type = "data_class"
                elif 'sealed class' in pattern:
                    class_type = "sealed_class"
                elif 'object' in pattern:
                    class_type = "object"
                elif 'interface' in pattern:
                    class_type = "interface"
                elif 'enum class' in pattern:
                    class_type = "enum_class"
                break
        
        # Extract imports (same as Java)
        imports = re.findall(r'import\s+([^\s\n]+)', kotlin_code)
        
        # Extract Kotlin functions (methods)
        # Kotlin function patterns: fun functionName(), suspend fun, inline fun, etc.
        function_patterns = [
            r'(private|public|protected|internal)?\s*(?:(suspend|inline|infix|operator)\s+)?fun\s+(\w+)\s*\(([^)]*)\)\s*:\s*(\w+(?:<[^>]*>)?|\w+\??)',  # With return type
            r'(private|public|protected|internal)?\s*(?:(suspend|inline|infix|operator)\s+)?fun\s+(\w+)\s*\(([^)]*)\)\s*\{',  # Unit return (no explicit type)
        ]
        
        detailed_methods = []
        for pattern in function_patterns:
            functions = re.findall(pattern, kotlin_code)
            for func in functions:
                if len(func) >= 4:
                    visibility = func[0] if func[0] else 'public'  # Kotlin is public by default
                    modifiers = func[1] if func[1] else ''
                    name = func[2]
                    parameters = func[3]
                    return_type = func[4] if len(func) > 4 and func[4] else 'Unit'
                    
                    if name not in ['equals', 'hashCode', 'toString']:
                        # Parse parameters
                        clean_params = parameters.strip() if parameters else ""
                        param_list = []
                        if clean_params:
                            for param in clean_params.split(','):
                                param = param.strip()
                                if param and ':' in param:
                                    # Kotlin parameter format: name: Type
                                    param_parts = param.split(':')
                                    if len(param_parts) >= 2:
                                        param_name = param_parts[0].strip()
                                        param_type = param_parts[1].strip()
                                        param_list.append({'type': param_type, 'name': param_name})
                        
                        detailed_methods.append({
                            'visibility': visibility,
                            'modifiers': modifiers,
                            'return_type': return_type,
                            'name': name,
                            'parameters': clean_params,
                            'parameter_list': param_list,
                            'signature': f"{visibility} {modifiers} fun {name}({clean_params}): {return_type}".strip(),
                            'is_suspend': 'suspend' in modifiers,
                            'is_inline': 'inline' in modifiers,
                            'is_extension': '.' in name,  # Extension functions have . in name pattern
                            'is_getter': name.startswith('get') and len(param_list) == 0 and return_type != 'Unit',
                            'is_setter': name.startswith('set') and len(param_list) == 1 and return_type == 'Unit',
                        })
        
        # Extract Kotlin properties (val/var)
        property_pattern = r'(private|public|protected|internal)?\s*(val|var)\s+(\w+)\s*:\s*(\w+(?:<[^>]*>)?|\w+\??)'
        properties = re.findall(property_pattern, kotlin_code)
        
        # Separate public/internal functions from private functions
        public_methods = []
        private_methods = []
        
        exclude_private_methods = is_private_method_testing_excluded()
        
        if exclude_private_methods:
            print(f"🚫 Private method testing excluded for {class_name} via EXCLUDE_PRIVATE_METHOD_TESTS environment variable")
        
        for method in detailed_methods:
            if method['visibility'] in ['public', 'protected', 'internal', '']:  # Empty string means public in Kotlin
                public_methods.append(method)
            elif method['visibility'] == 'private' and not exclude_private_methods:
                private_methods.append(method)
        
        # Extract constructors (primary and secondary)
        constructor_info = []
        
        # Primary constructor
        primary_constructor_pattern = rf'class\s+{re.escape(class_name)}\s*\(([^)]*)\)'
        primary_match = re.search(primary_constructor_pattern, kotlin_code)
        if primary_match:
            params = primary_match.group(1)
            constructor_info.append({
                'visibility': 'public',
                'name': class_name,
                'parameters': params,
                'signature': f"constructor({params})",
                'is_primary': True
            })
        
        # Secondary constructors
        secondary_constructor_pattern = r'constructor\s*\(([^)]*)\)'
        secondary_constructors = re.findall(secondary_constructor_pattern, kotlin_code)
        for params in secondary_constructors:
            constructor_info.append({
                'visibility': 'public',
                'name': class_name,
                'parameters': params,
                'signature': f"constructor({params})",
                'is_primary': False
            })
        
        # Detect Kotlin-specific frameworks
        frameworks = []
        if 'Spring' in kotlin_code or '@Service' in kotlin_code or '@Component' in kotlin_code:
            frameworks.append('Spring')
        if '@Entity' in kotlin_code or 'JPA' in kotlin_code:
            frameworks.append('JPA')
        if 'coroutines' in kotlin_code.lower() or 'suspend' in kotlin_code:
            frameworks.append('Coroutines')
        if 'ktor' in kotlin_code.lower():
            frameworks.append('Ktor')
        
        # Calculate complexity (similar to Java but include Kotlin-specific constructs)
        complexity_indicators = len(re.findall(r'\bif\b|\bfor\b|\bwhile\b|\bwhen\b|\btry\b|\bsuspend\b', kotlin_code))
        
        return {
            'language': 'kotlin',
            'class_type': class_type,
            'package': package_name,
            'class_name': class_name,
            'imports': imports,
            'methods': public_methods,
            'private_methods': private_methods,
            'constructors': constructor_info,
            'properties': [{'visibility': p[0] or 'public', 'mutability': p[1], 'name': p[2], 'type': p[3]} for p in properties],
            'frameworks': frameworks,
            'complexity_score': complexity_indicators,
            'content': kotlin_code,
            'detected_imports': [],  # TODO: Implement Kotlin import detection
            'contextual_imports': [],  # TODO: Implement Kotlin contextual imports
            'all_test_imports': [],   # TODO: Implement Kotlin test imports
        }
    except Exception as e:
        return {'error': f"Error analyzing Kotlin code: {str(e)}"}

def analyze_source_code(file_path: str, content: str) -> Dict[str, Any]:
    """Analyze source code based on file extension"""
    if file_path.endswith('.java'):
        return analyze_java_code(content)
    elif file_path.endswith('.kt'):
        return analyze_kotlin_code(content)
    else:
        return {'error': f"Unsupported file type: {file_path}"}
        
# Legacy compatibility - keep the old common_test_imports for backward compatibility
def get_legacy_common_imports():
    """Get legacy common test imports for backward compatibility"""
    return [
        'java.util.Enumeration',
        'java.util.Collections',
        'java.util.Iterator',
        'java.lang.reflect.Method',
        'java.lang.reflect.Field',
        'java.util.concurrent.CompletableFuture',
        'java.time.LocalDateTime',
        'java.time.Instant',
        'java.io.ByteArrayInputStream',
        'java.io.InputStream',
        'java.io.InputStreamReader',
        'java.io.IOException',
        'java.util.stream.Stream',
        'java.util.stream.Collectors',
        'java.util.Optional',
        'java.util.concurrent.TimeUnit',
        'java.util.regex.Pattern',
        'java.net.URL',
        'java.net.URI'
    ]

def analyze_java_code_with_incremental_support(java_code: str, output_dir: str, original_file_path: str, extract_dir: str = None) -> Dict[str, Any]:
    """Analyze Java code and filter methods based on existing test coverage for incremental generation
    
    Args:
        java_code: Java source code to analyze
        output_dir: Output directory where test files would be saved
        original_file_path: Original Java file path
        extract_dir: Extracted ZIP directory to check for existing test files
        
    Returns:
        Analysis result with filtered methods if incremental generation is enabled
    """
    # Perform standard analysis
    analysis = analyze_java_code(java_code)
    
    # If incremental generation is not enabled, return standard analysis
    if not is_incremental_test_generation_enabled():
        return analysis
    
    # If analysis failed, return as-is
    if 'error' in analysis:
        return analysis
    
    try:
        # Determine what the test file path would be in output directory
        rel_path = Path(original_file_path)
        path_parts = list(rel_path.parts)
        
        # Convert src/main/java to src/test/java
        if 'src' in path_parts and 'main' in path_parts:
            main_index = path_parts.index('main')
            path_parts[main_index] = 'test'
        elif 'src' in path_parts:
            src_index = path_parts.index('src')
            path_parts.insert(src_index + 1, 'test')
            path_parts.insert(src_index + 2, 'java')
        
        # Create test file name
        file_name = path_parts[-1]
        test_file_name = file_name.replace('.java', 'Test.java') if not file_name.endswith('Test.java') else file_name
        path_parts[-1] = test_file_name
        
        # Create potential test file path in output directory
        test_file_path = os.path.join(output_dir, *path_parts[path_parts.index('src'):])
        
        # Check for existing test files in output directory
        existing_test_files = find_existing_test_files(test_file_path)
        
        # CRITICAL FIX: Also check for existing test files in the extracted ZIP directory
        existing_test_files_from_zip = []
        if extract_dir:
            print(f"🔍 ===== INCREMENTAL ANALYSIS DEBUG =====")
            print(f"🔍 Looking for existing test files in ZIP:")
            print(f"   Original file: {original_file_path}")
            print(f"   Extract dir: {extract_dir}")
            print(f"   Extract dir exists: {os.path.exists(extract_dir)}")
            
            # Extract the class name from the original file path
            original_file_name = os.path.basename(original_file_path)
            class_name = original_file_name.replace('.java', '')
            expected_test_file_name = f"{class_name}Test.java"
            
            print(f"   Class name: {class_name}")
            print(f"   Expected test file name: {expected_test_file_name}")
            
            # Search for existing test files with this pattern in the entire extracted directory
            found_files_count = 0
            for root, dirs, files in os.walk(extract_dir):
                for file in files:
                    if file == expected_test_file_name:
                        found_test_file = os.path.join(root, file)
                        existing_test_files_from_zip.append(found_test_file)
                        found_files_count += 1
                        print(f"   ✅ Found existing test file: {found_test_file}")
                        
                        # Verify the file is readable and extract test methods
                        try:
                            test_methods = extract_test_methods_from_file(found_test_file)
                            print(f"   📊 Test methods in existing file: {len(test_methods)}")
                            for i, method in enumerate(test_methods, 1):
                                print(f"      {i}. {method}")
                        except Exception as e:
                            print(f"   ⚠️ Error reading test file: {e}")
                        
                        # Also look for numbered versions (Test2.java, Test3.java, etc.)
                        dir_path = os.path.dirname(found_test_file)
                        counter = 2
                        while counter <= 10:  # Check up to Test10.java
                            numbered_test_file = os.path.join(dir_path, f"{class_name}Test{counter}.java")
                            if os.path.exists(numbered_test_file):
                                print(f"   ✅ Found numbered test file: {numbered_test_file}")
                                existing_test_files_from_zip.append(numbered_test_file)
                                counter += 1
                            else:
                                break
            
            if found_files_count == 0:
                print(f"   ❌ No existing test files found with name: {expected_test_file_name}")
                print(f"   🔍 All test files in extract directory:")
                test_files_found = []
                for root, dirs, files in os.walk(extract_dir):
                    for file in files:
                        if file.endswith('.java') and 'Test' in file:
                            test_files_found.append(os.path.join(root, file))
                
                if test_files_found:
                    for test_file in test_files_found[:10]:  # Show first 10
                        print(f"      {test_file}")
                else:
                    print(f"      No test files found at all!")
            
            print(f"   📊 Total existing test files found in ZIP: {len(existing_test_files_from_zip)}")
            print(f"🔍 ===== END INCREMENTAL DEBUG =====")
            
            # Combine existing files from both sources
            all_existing_files = existing_test_files + existing_test_files_from_zip
            # Remove duplicates while preserving order
            seen = set()
            existing_test_files = []
            for file_path in all_existing_files:
                if file_path not in seen:
                    existing_test_files.append(file_path)
                    seen.add(file_path)
        
        if existing_test_files:
            print(f"🔍 Incremental analysis: Found {len(existing_test_files)} existing test file(s)")
            for i, existing_file in enumerate(existing_test_files, 1):
                print(f"   {i}. {existing_file}")
            
            # Store original method counts before filtering
            original_method_count = len(analysis.get('methods', []))
            original_private_method_count = len(analysis.get('private_methods', []))
            
            # Filter methods based on existing coverage
            print(f"🔍 BEFORE FILTERING - Original methods:")
            for i, method in enumerate(analysis.get('methods', []), 1):
                print(f"  {i}. {method.get('name', 'unknown')} ({method.get('visibility', 'unknown')})")
            
            uncovered_methods = get_uncovered_methods(analysis.get('methods', []), existing_test_files)
            uncovered_private_methods = get_uncovered_methods(analysis.get('private_methods', []), existing_test_files)
            
            print(f"🎯 AFTER FILTERING - Methods for incremental testing: {len(uncovered_methods)} public, {len(uncovered_private_methods)} private")
            print(f"🔍 Uncovered public methods:")
            for i, method in enumerate(uncovered_methods, 1):
                print(f"  {i}. {method.get('name', 'unknown')} ({method.get('visibility', 'unknown')})")
            
            print(f"🔍 Uncovered private methods:")
            for i, method in enumerate(uncovered_private_methods, 1):
                print(f"  {i}. {method.get('name', 'unknown')} ({method.get('visibility', 'unknown')})")
            
            # Update analysis with filtered methods
            analysis['methods'] = uncovered_methods
            analysis['private_methods'] = uncovered_private_methods
            analysis['incremental_info'] = {
                'existing_test_files': len(existing_test_files),
                'original_method_count': original_method_count,
                'original_private_method_count': original_private_method_count,
                'filtered_method_count': len(uncovered_methods),
                'filtered_private_method_count': len(uncovered_private_methods),
                'existing_test_files_list': existing_test_files
            }
        else:
            print(f"🆕 No existing test files found - generating complete test suite")
            analysis['incremental_info'] = {
                'existing_test_files': 0,
                'original_method_count': len(analysis.get('methods', [])),
                'original_private_method_count': len(analysis.get('private_methods', [])),
                'filtered_method_count': len(analysis.get('methods', [])),
                'filtered_private_method_count': len(analysis.get('private_methods', [])),
                'existing_test_files_list': []
            }
        
        # FINAL DEBUG: Confirm what methods are being returned for LLM generation
        final_public_methods = len(analysis.get('methods', []))
        final_private_methods = len(analysis.get('private_methods', []))
        incremental_enabled = is_incremental_test_generation_enabled()
        
        print(f"🎯 ===== FINAL INCREMENTAL ANALYSIS SUMMARY =====")
        print(f"🎯 Incremental generation enabled: {incremental_enabled}")
        print(f"🎯 Final methods for LLM: {final_public_methods} public, {final_private_methods} private")
        print(f"🎯 Expected behavior:")
        if incremental_enabled and len(existing_test_files) > 0:
            print(f"   - Should generate ONLY uncovered methods (not all methods)")
            print(f"   - Should create Test2.java with {final_public_methods + final_private_methods} methods")
            print(f"   - Should copy existing test files to output")
        else:
            print(f"   - Should generate complete test suite")
        print(f"🎯 ===== END FINAL SUMMARY =====")
        
        return analysis
        
    except Exception as e:
        print(f"⚠️ Warning: Error in incremental analysis: {str(e)}")
        print(f"⚠️ Falling back to standard analysis")
        return analysis

def analyze_kotlin_code_with_incremental_support(kotlin_code: str, output_dir: str, original_file_path: str, extract_dir: str = None) -> Dict[str, Any]:
    """Analyze Kotlin code and filter methods based on existing test coverage for incremental generation
    
    Args:
        kotlin_code: Kotlin source code to analyze
        output_dir: Output directory where test files would be saved
        original_file_path: Original Kotlin file path
        extract_dir: Extracted ZIP directory to check for existing test files
        
    Returns:
        Analysis result with filtered methods if incremental generation is enabled
    """
    # Perform standard Kotlin analysis
    analysis = analyze_kotlin_code(kotlin_code)
    
    try:
        if not is_incremental_test_generation_enabled():
            print(f"🔄 Incremental generation DISABLED - generating complete test suite")
            return analysis
        
        print(f"🔄 Incremental generation ENABLED - checking for existing tests")
        
        # Get the path structure for generating test file
        path_parts = original_file_path.replace('\\', '/').split('/')
        
        # Create potential test file path in output directory
        test_file_path = os.path.join(output_dir, *path_parts[path_parts.index('src'):])
        
        # Check for existing test files in output directory
        existing_test_files = find_existing_test_files(test_file_path)
        
        # Also check for existing test files in the extracted ZIP directory
        existing_test_files_from_zip = []
        if extract_dir:
            print(f"🔍 ===== KOTLIN INCREMENTAL ANALYSIS DEBUG =====")
            print(f"🔍 Looking for existing Kotlin test files in ZIP:")
            print(f"   Original file: {original_file_path}")
            print(f"   Extract dir: {extract_dir}")
            
            # Extract the class name from the original file path
            original_file_name = os.path.basename(original_file_path)
            class_name = original_file_name.replace('.kt', '')
            expected_test_file_name = f"{class_name}Test.kt"
            
            print(f"   Class name: {class_name}")
            print(f"   Expected test file name: {expected_test_file_name}")
            
            # Search for existing test files with this pattern in the entire extracted directory
            for root, dirs, files in os.walk(extract_dir):
                for file in files:
                    if file == expected_test_file_name:
                        found_test_file = os.path.join(root, file)
                        existing_test_files_from_zip.append(found_test_file)
                        print(f"  ✅ Found existing Kotlin test file: {found_test_file}")
        
        # Combine existing test files from both sources
        all_existing_test_files = existing_test_files + existing_test_files_from_zip
        
        if all_existing_test_files:
            print(f"🔍 Found {len(all_existing_test_files)} existing Kotlin test file(s)")
            
            # Filter methods that are already covered
            uncovered_methods = filter_uncovered_methods(analysis.get('methods', []), all_existing_test_files)
            uncovered_private_methods = filter_uncovered_methods(analysis.get('private_methods', []), all_existing_test_files)
            
            # Update analysis with filtered methods
            analysis['methods'] = uncovered_methods
            analysis['private_methods'] = uncovered_private_methods
            analysis['incremental_info'] = {
                'existing_test_files': len(all_existing_test_files),
                'original_method_count': len(analysis.get('methods', [])),
                'original_private_method_count': len(analysis.get('private_methods', [])),
                'filtered_method_count': len(uncovered_methods),
                'filtered_private_method_count': len(uncovered_private_methods),
                'existing_test_files_list': all_existing_test_files
            }
        else:
            print(f"🆕 No existing Kotlin test files found - generating complete test suite")
            analysis['incremental_info'] = {
                'existing_test_files': 0,
                'original_method_count': len(analysis.get('methods', [])),
                'original_private_method_count': len(analysis.get('private_methods', [])),
                'filtered_method_count': len(analysis.get('methods', [])),
                'filtered_private_method_count': len(analysis.get('private_methods', [])),
                'existing_test_files_list': []
            }
        
        return analysis
        
    except Exception as e:
        print(f"⚠️ Warning: Error in Kotlin incremental analysis: {str(e)}")
        print(f"⚠️ Falling back to standard Kotlin analysis")
        return analysis

def create_test_strategy(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Generate testing strategy based on class analysis"""
    try:
        strategies = []
        
        # Determine test patterns based on class characteristics
        if any('Service' in imp or 'Repository' in imp for imp in analysis.get('imports', [])):
            strategies.append("Service Layer Testing - Use mocks for dependencies")
        
        if any('Controller' in imp for imp in analysis.get('imports', [])):
            strategies.append("Controller Testing - Use MockMvc for web layer testing")
        
        # Framework-based strategies
        frameworks = analysis.get('frameworks', [])
        if 'Spring' in frameworks:
            strategies.append("Spring Testing - Use @MockBean and @TestConfiguration")
        if 'JPA' in frameworks:
            strategies.append("JPA Testing - Use @DataJpaTest for repository tests")
        if 'Servlet' in frameworks:
            strategies.append("Servlet Testing - Use MockHttpServletRequest/Response")
        
        # Method-specific strategies for public/protected methods
        method_strategies = []
        for method in analysis.get('methods', []):
            method_name = method.get('name', '')
            return_type = method.get('return_type', '')
            
            if return_type == 'void':
                method_strategies.append(f"{method_name}: Verify behavior and side effects")
            elif 'boolean' in return_type.lower():
                method_strategies.append(f"{method_name}: Test true/false scenarios")
            elif any(collection in return_type for collection in ['List', 'Set', 'Collection', 'Map']):
                method_strategies.append(f"{method_name}: Test empty, single, and multiple item scenarios")
            elif 'String' in return_type:
                method_strategies.append(f"{method_name}: Test null, empty, and valid string scenarios")
            else:
                method_strategies.append(f"{method_name}: Test return value variations and edge cases")
        
        # Private method strategies (using reflection) - only if not excluded
        private_method_strategies = []
        exclude_private_methods = is_private_method_testing_excluded()
        
        if not exclude_private_methods:
            for method in analysis.get('private_methods', []):
                method_name = method.get('name', '')
                return_type = method.get('return_type', '')
                private_method_strategies.append(f"{method_name}: Test via reflection (complex logic only)")
        else:
            # Add a note about excluded private methods
            private_method_strategies.append("Private method testing excluded via EXCLUDE_PRIVATE_METHOD_TESTS environment variable")
        
        # Edge case strategies
        edge_cases = [
            "Null parameter testing",
            "Empty string/collection testing", 
            "Boundary value testing",
            "Exception scenario testing"
        ]
        
        complexity_score = analysis.get('complexity_score', 0)
        if complexity_score > 5:
            edge_cases.extend([
                "Complex logic path testing",
                "State transition testing",
                "Performance testing for complex operations"
            ])
        
        if complexity_score > 10:
            edge_cases.append("Integration testing recommended")
        
        return {
            'testing_approaches': strategies,
            'method_strategies': method_strategies,
            'private_method_strategies': private_method_strategies,
            'edge_cases': edge_cases,
            'recommended_annotations': ['@Test', '@BeforeEach', '@AfterEach', '@Mock', '@InjectMocks'],
            'mocking_strategy': 'Use Mockito for external dependencies',
            'complexity_level': 'High' if complexity_score > 10 else 'Medium' if complexity_score > 5 else 'Low'
        }
    except Exception as e:
        return {'error': f"Error creating test strategy: {str(e)}"}

def find_project_root(extract_dir: str) -> str:
    """Find the actual project root directory within the extracted folder"""
    print(f"🔍 === FINDING PROJECT ROOT ===")
    print(f"🔍 Extract directory: {extract_dir}")
    
    # Check if files are directly in extract_dir
    direct_files = []
    direct_dirs = []
    
    if os.path.exists(extract_dir):
        for item in os.listdir(extract_dir):
            item_path = os.path.join(extract_dir, item)
            if os.path.isfile(item_path):
                direct_files.append(item)
            else:
                direct_dirs.append(item)
    
    print(f"🔍 Direct files: {direct_files}")
    print(f"🔍 Direct directories: {direct_dirs}")
    
    # Look for src/ directory to identify project root
    # Check direct level first
    if 'src' in direct_dirs:
        print(f"✅ Found project root at: {extract_dir}")
        return extract_dir
    
    # Check one level deeper
    for dir_name in direct_dirs:
        subdir_path = os.path.join(extract_dir, dir_name)
        if os.path.exists(subdir_path):
            subdir_contents = os.listdir(subdir_path)
            print(f"🔍 Checking subdirectory {dir_name}: {subdir_contents}")
            
            if 'src' in subdir_contents:
                print(f"✅ Found project root at: {subdir_path}")
                return subdir_path
    
    # If no src/ found, return the first subdirectory if there's only one
    if len(direct_dirs) == 1 and len(direct_files) == 0:
        potential_root = os.path.join(extract_dir, direct_dirs[0])
        print(f"✅ Using single subdirectory as project root: {potential_root}")
        return potential_root
    
    # Fallback to original extract_dir
    print(f"⚠️ Using fallback project root: {extract_dir}")
    return extract_dir

def extract_swagger_files(extract_dir: str) -> Dict[str, str]:
    """Extract Swagger/OpenAPI files ONLY from swagger/ folder"""
    swagger_files = {}
    
    print(f"🔍 === SWAGGER FILE DETECTION DEBUG ===")
    
    # Find the actual project root
    project_root = find_project_root(extract_dir)
    print(f"🔍 Project root: {project_root}")
    
    swagger_dir = os.path.join(project_root, "swagger")
    print(f"🔍 Swagger directory path: {swagger_dir}")
    print(f"🔍 Swagger directory exists: {os.path.exists(swagger_dir)}")
    
    if not os.path.exists(swagger_dir):
        print("❌ Swagger directory not found")
        return swagger_files
    
    print(f"🔍 Swagger directory contents: {os.listdir(swagger_dir)}")
    
    # Only search in swagger/ folder
    swagger_extensions = ['.json', '.yml', '.yaml']
    
    for root, dirs, files in os.walk(swagger_dir):
        print(f"🔍 Walking swagger directory: {root}")
        print(f"🔍 Files: {files}")
        
        for file in files:
            file_lower = file.lower()
            print(f"🔍 Checking swagger file: {file}")
            
            # Check if it's a potential swagger file by extension
            if any(file_lower.endswith(ext) for ext in swagger_extensions):
                file_path = os.path.join(root, file)
                print(f"🔍 Reading swagger file: {file_path}")
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        print(f"🔍 File size: {len(content)} characters")
                        
                        # Basic validation - any JSON/YAML file in swagger/ folder is considered swagger
                        if len(content.strip()) > 0:
                            swagger_files[file] = content
                            print(f"✅ FOUND SWAGGER FILE: {file}")
                        else:
                            print(f"❌ Empty file: {file}")
                            
                except Exception as e:
                    print(f"⚠️ Could not read swagger file {file}: {e}")
    
    print(f"🔍 === SWAGGER DETECTION COMPLETE ===")
    print(f"🔍 Total swagger files found: {len(swagger_files)}")
    return swagger_files

def extract_test_data_files(extract_dir: str) -> Dict[str, str]:
    """Extract test data files ONLY from test-data/ folder and src/test/resources"""
    test_data_files = {}
    
    print(f"🔍 === TEST DATA FILE DETECTION DEBUG ===")
    
    # Find the actual project root
    project_root = find_project_root(extract_dir)
    print(f"🔍 Project root: {project_root}")
    
    # ONLY search in these specific directories
    test_data_dirs = [
        "test-data",
        "src/test/resources"
    ]
    
    print(f"🔍 Searching ONLY in specific test data directories: {test_data_dirs}")
    
    for test_dir in test_data_dirs:
        test_data_path = os.path.join(project_root, test_dir)
        exists = os.path.exists(test_data_path)
        print(f"🔍 {test_dir}: {test_data_path} - Exists: {exists}")
        
        if exists:
            print(f"🔍 Contents: {os.listdir(test_data_path)}")
            
            for root, dirs, files in os.walk(test_data_path):
                print(f"🔍 Walking test data directory: {root}")
                print(f"🔍 Files: {files}")
                
                for file in files:
                    file_lower = file.lower()
                    print(f"🔍 Checking test data file: {file}")
                    
                    # EXCLUDE Java files explicitly
                    if file_lower.endswith('.java'):
                        print(f"❌ Skipping Java file: {file}")
                        continue
                    
                    # Only include files that are likely test data
                    test_data_extensions = ['.json', '.xml', '.txt', '.log', '.csv', '.yml', '.yaml']
                    test_data_keywords = ['request', 'response', 'trace', 'log', 'sample', 'splunk', 'data']
                    
                    # Check by extension or keywords in filename
                    is_test_data = (
                        any(file_lower.endswith(ext) for ext in test_data_extensions) or
                        any(keyword in file_lower for keyword in test_data_keywords)
                    )
                    
                    if is_test_data:
                        file_path = os.path.join(root, file)
                        print(f"🔍 Reading test data file: {file_path}")
                        
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                relative_path = os.path.relpath(file_path, extract_dir)
                                test_data_files[relative_path] = content
                                print(f"✅ FOUND TEST DATA FILE: {relative_path}")
                        except UnicodeDecodeError:
                            try:
                                with open(file_path, 'r', encoding='latin-1') as f:
                                    content = f.read()
                                    relative_path = os.path.relpath(file_path, extract_dir)
                                    test_data_files[relative_path] = content
                                    print(f"✅ FOUND TEST DATA FILE (latin-1): {relative_path}")
                            except Exception as e:
                                print(f"⚠️ Could not read {file}: {e}")
                        except Exception as e:
                            print(f"⚠️ Could not read {file}: {e}")
                    else:
                        print(f"❌ Not a test data file: {file}")
    
    print(f"🔍 === TEST DATA DETECTION COMPLETE ===")
    print(f"🔍 Total test data files found: {len(test_data_files)}")
    print(f"🔍 Files found: {list(test_data_files.keys())}")
    return test_data_files

def extract_configuration_files(extract_dir: str) -> Dict[str, str]:
    """Extract configuration files ONLY from src/main/resources and src/test/resources"""
    config_files = {}
    
    print(f"🔍 === CONFIGURATION FILE DETECTION DEBUG ===")
    
    # Find the actual project root
    project_root = find_project_root(extract_dir)
    print(f"🔍 Project root: {project_root}")
    
    # Common configuration file patterns
    config_patterns = {
        'application.properties': 'properties',
        'application.yml': 'yaml',
        'application.yaml': 'yaml',
        'application-test.properties': 'test_properties',
        'application-test.yml': 'test_yaml',
        'application-dev.properties': 'dev_properties',
        'application-prod.properties': 'prod_properties'
    }
    
    # ONLY search in resources directories
    resources_dirs = [
        "src/main/resources",
        "src/test/resources"
    ]
    
    print(f"🔍 Searching for config files in: {resources_dirs}")
    
    for resources_dir in resources_dirs:
        resources_path = os.path.join(project_root, resources_dir)
        if os.path.exists(resources_path):
            print(f"🔍 Searching config directory: {resources_path}")
            
            for root, dirs, files in os.walk(resources_path):
                print(f"🔍 Walking: {root}")
                print(f"🔍 Files: {files}")
                
                for file in files:
                    if file in config_patterns:
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                config_files[config_patterns[file]] = f.read()
                                print(f"✅ Found config file: {file}")
                        except Exception as e:
                            print(f"⚠️ Could not read config file {file}: {e}")
        else:
            print(f"❌ Resources directory not found: {resources_path}")
    
    print(f"🔍 === CONFIGURATION DETECTION COMPLETE ===")
    print(f"🔍 Total config files found: {len(config_files)}")
    return config_files

async def prompt_for_missing_files(missing_swagger: bool, missing_test_data: bool, message_sender=None, user_prompter=None) -> Dict[str, bool]:
    """Prompt user for missing files and get their decision - UI agnostic version"""
    
    async def send_message(content):
        if message_sender:
            await message_sender(content)
        else:
            print(content)
    
    if not missing_swagger and not missing_test_data:
        return {'proceed': True, 'use_enhanced': True}
    
    prompt_message = PromptBuilder.build_missing_files_prompt(missing_swagger, missing_test_data)
    
    await send_message(prompt_message)
    
    # If no user prompter provided, default to proceed
    if not user_prompter:
        await send_message("✅ No user input available, proceeding with standard enhanced testing...")
        return {'proceed': True, 'use_enhanced': False}
    
    # Wait for user response with better error handling
    try:
        user_response = await user_prompter(
            "Please choose your option (proceed/upload new):",
            timeout=120
        )
        
        # Fix the NoneType error here
        if user_response and hasattr(user_response, 'content') and user_response.content:
            response_text = user_response.content.lower().strip()
        elif user_response and isinstance(user_response, dict) and 'content' in user_response:
            response_text = user_response['content'].lower().strip()
        else:
            response_text = 'proceed'  # Default fallback
        
        if response_text in ['proceed', 'continue', 'yes', 'ok']:
            await send_message("✅ Proceeding with standard enhanced testing...")
            return {'proceed': True, 'use_enhanced': False}
        elif response_text in ['upload new', 'new', 'upload']:
            await send_message("Upload new file selected.")
            return {'proceed': False, 'use_enhanced': False}
        else:
            await send_message("✅ Defaulting to standard enhanced testing...")
            return {'proceed': True, 'use_enhanced': False}
            
    except Exception as e:
        await send_message(f"⚠️ Error getting user response: {e}. Proceeding with standard testing...")
        return {'proceed': True, 'use_enhanced': False}

async def generate_enhanced_junit_test_with_files(
    analysis_or_class_info: Dict[str, Any],  # Can be either new analysis format or old class_info format
    swagger_files: Dict[str, str] = None,
    test_data_files: Dict[str, str] = None,
    config_files: Dict[str, str] = None,
    output_dir: str = None,
    original_file_path: str = None,
    extract_dir: str = None
) -> str:
    """Generate JUnit test with optional user-provided Swagger and test data files"""
    
    try:
        llm = get_llm()
        
        # Handle both new analysis format and old class_info format
        if 'content' in analysis_or_class_info:
            # Old class_info format
            class_info = analysis_or_class_info
            source_content = class_info['content']
        else:
            # New analysis format - need to read the content from the file
            class_info = {
                'class_name': analysis_or_class_info.get('class_name', 'Unknown'),
                'content': read_source_file(original_file_path) if original_file_path else '',
                'methods': analysis_or_class_info.get('methods', [])
            }
            source_content = class_info['content']
        
        # Perform analysis with incremental support if parameters are provided
        if output_dir and original_file_path and is_incremental_test_generation_enabled():
            # Determine language from file extension
            if original_file_path.endswith('.kt'):
                analysis = analyze_kotlin_code_with_incremental_support(
                    source_content, output_dir, original_file_path, extract_dir
                )
            else:
                analysis = analyze_java_code_with_incremental_support(
                    source_content, output_dir, original_file_path, extract_dir
                )
            
            # Check if incremental generation resulted in no methods to test
            if (len(analysis.get('methods', [])) == 0 and 
                len(analysis.get('private_methods', [])) == 0 and
                analysis.get('incremental_info', {}).get('existing_test_files', 0) > 0):
                return f"""// Incremental generation: All methods are already covered in existing test files.
// No additional test methods needed.
// Existing test files: {analysis.get('incremental_info', {}).get('existing_test_files', 0)}

package {analysis.get('package', 'com.example.test')};

public class {class_info.get('class_name', 'Unknown')}Test_AllMethodsCovered {{
    // All test methods are already covered in existing test files
    // No additional tests generated
}}"""
        else:
            # Standard analysis
            if original_file_path and original_file_path.endswith('.kt'):
                analysis = analyze_kotlin_code(source_content)
            else:
                analysis = analyze_java_code(source_content)
        
        if 'error' in analysis:
            return f"Analysis failed: {analysis['error']}"
        
        strategy = create_test_strategy(analysis)
        if 'error' in strategy:
            return f"Strategy creation failed: {strategy['error']}"
        
        # Build context with available files
        file_context = ""
        
        # Swagger context (only if user provided files)
        if swagger_files:
            file_context += "\n📋 **Available Swagger/OpenAPI Schemas:**\n"
            for filename, content in swagger_files.items():
                file_context += f"• {filename} - Use for schema validation testing\n"
                # Add a snippet of the schema for context
                try:
                    if filename.endswith('.json'):
                        schema_data = json.loads(content)
                        if 'paths' in schema_data:
                            paths = list(schema_data['paths'].keys())[:3]
                            file_context += f"  - Contains API paths: {paths}\n"
                        if 'components' in schema_data and 'schemas' in schema_data['components']:
                            schemas = list(schema_data['components']['schemas'].keys())[:3]
                            file_context += f"  - Contains schemas: {schemas}\n"
                except:
                    pass
        
        # Test data context (only if user provided files)
        if test_data_files:
            file_context += "\n📊 **Available Test Data Files:**\n"
            for filename, content in test_data_files.items():
                file_context += f"• {filename} - Use for realistic testing scenarios\n"
                # Add a snippet for context
                if content.strip().startswith('{'):
                    try:
                        data = json.loads(content)
                        if isinstance(data, dict) and len(data) > 0:
                            first_key = list(data.keys())[0]
                            file_context += f"  - Sample data includes: {first_key}\n"
                    except:
                        pass
        
        # Configuration context
        config_context = ""
        if config_files:
            config_context = "\n🔧 **Available Configuration:**\n"
            for config_type, content in config_files.items():
                relevant_props = extract_relevant_properties(content, analysis.get('class_name', ''))
                if relevant_props:
                    config_context += f"**{config_type.replace('_', ' ').title()}:**\n```properties\n{relevant_props}\n```\n"
        
        # Build enhanced prompt using PromptBuilder
        # CRITICAL FIX: Ensure LLM only receives filtered methods for incremental generation
        if (output_dir and original_file_path and is_incremental_test_generation_enabled() and 
            analysis.get('incremental_info', {}).get('existing_test_files', 0) > 0):
            
            # For incremental generation, create a modified class_info with only uncovered methods
            filtered_class_info = class_info.copy()
            filtered_class_info['filtered_for_incremental'] = True
            filtered_class_info['original_methods_count'] = analysis.get('incremental_info', {}).get('original_method_count', 0)
            filtered_class_info['original_private_methods_count'] = analysis.get('incremental_info', {}).get('original_private_method_count', 0)
            filtered_class_info['filtered_methods_count'] = len(analysis.get('methods', []))
            filtered_class_info['filtered_private_methods_count'] = len(analysis.get('private_methods', []))
            
            print(f"🎯 ===== INCREMENTAL LLM GENERATION =====")
            print(f"🎯 Original methods: {filtered_class_info['original_methods_count']} public, {filtered_class_info['original_private_methods_count']} private")
            print(f"🎯 Filtered methods for LLM: {filtered_class_info['filtered_methods_count']} public, {filtered_class_info['filtered_private_methods_count']} private")
            print(f"🎯 Methods in analysis object:")
            for i, method in enumerate(analysis.get('methods', []), 1):
                print(f"   {i}. {method.get('name', 'unknown')} ({method.get('visibility', 'unknown')} {method.get('return_type', 'unknown')})")
            print(f"🎯 Private methods in analysis object:")
            for i, method in enumerate(analysis.get('private_methods', []), 1):
                print(f"   {i}. {method.get('name', 'unknown')} ({method.get('visibility', 'unknown')} {method.get('return_type', 'unknown')})")
            print(f"🎯 Expected: LLM should generate tests ONLY for {filtered_class_info['filtered_methods_count'] + filtered_class_info['filtered_private_methods_count']} uncovered methods")
            
            # Create incremental-specific strategy
            incremental_strategy = strategy.copy()
            incremental_strategy['generation_mode'] = 'incremental'
            incremental_strategy['target_methods'] = analysis.get('methods', [])
            incremental_strategy['target_private_methods'] = analysis.get('private_methods', [])
            incremental_strategy['incremental_info'] = analysis.get('incremental_info', {})
            
            # Add specific instructions for incremental generation
            incremental_context = f"""
🎯 INCREMENTAL TEST GENERATION MODE:
- Generate tests ONLY for the {len(analysis.get('methods', []))} uncovered public methods and {len(analysis.get('private_methods', []))} uncovered private methods listed below
- DO NOT generate tests for methods that already have test coverage
- This is incremental generation - focus only on the uncovered methods
- Expected output: Test class with {len(analysis.get('methods', [])) + len(analysis.get('private_methods', []))} test methods

🎯 UNCOVERED METHODS TO TEST:
Public methods requiring tests:
{chr(10).join([f"• {m.get('name', '')} ({m.get('return_type', '')})" for m in analysis.get('methods', [])])}

Private methods requiring tests:
{chr(10).join([f"• {m.get('name', '')} ({m.get('return_type', '')})" for m in analysis.get('private_methods', [])])}
"""
            
            print(f"🎯 ===== SENDING TO LLM =====")
            
            # Determine language for prompt selection
            language = 'kotlin' if original_file_path and original_file_path.endswith('.kt') else 'java'
            
            enhanced_prompt = PromptBuilder.build_enhanced_prompt_with_files(
                analysis, incremental_strategy, filtered_class_info, file_context + incremental_context, config_context, language
            )
        else:
            # Standard generation
            language = 'kotlin' if original_file_path and original_file_path.endswith('.kt') else 'java'
            enhanced_prompt = PromptBuilder.build_enhanced_prompt_with_files(
                analysis, strategy, class_info, file_context, config_context, language
            )
        
        # CRITICAL: Add explicit import instruction for the application class
        current_package = analysis.get('package', '')
        current_class = analysis.get('class_name', '')
        if current_package and current_class:
            import_instruction = f"\n🚨 **CRITICAL CLASS IMPORT REQUIREMENT:**\n"
            if language == 'kotlin':
                import_instruction += f"- MUST import: import {current_package}.{current_class}\n"
            else:
                import_instruction += f"- MUST import: import {current_package}.{current_class};\n"
            import_instruction += f"- DO NOT use generic packages like com.example\n"
            import_instruction += f"- The actual class is located at: {current_package}.{current_class}\n"
            enhanced_prompt = enhanced_prompt.replace(
                "CRITICAL TESTING RULES:", 
                f"{import_instruction}\nCRITICAL TESTING RULES:"
            )
        
        system_prompt = PromptBuilder.get_system_prompt()

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=enhanced_prompt)
        ]
        
        # Debug level logging for final prompts
        logger.debug(f"\n=== FINAL PROMPTS FOR {current_class} ===")
        logger.debug(f"System Prompt Length: {len(system_prompt)} chars")
        logger.debug(f"Enhanced Prompt Length: {len(enhanced_prompt)} chars")
        logger.debug(f"Total Prompt Size: {len(system_prompt) + len(enhanced_prompt)} chars")
        logger.debug("\n=== SYSTEM PROMPT (FULL) ===")
        logger.debug(system_prompt)
        logger.debug("\n=== ENHANCED PROMPT (FULL) ===")
        logger.debug(enhanced_prompt)
        logger.debug("\n=== SENDING TO LLM NOW ===")
        
        # CRITICAL DEBUG: Verify methods being sent to LLM
        print(f"🎯 ===== FINAL PRE-LLM VERIFICATION =====")
        print(f"🎯 Analysis methods going to LLM: {len(analysis.get('methods', []))} public, {len(analysis.get('private_methods', []))} private")
        print(f"🎯 Class info: {class_info.get('class_name', 'Unknown')}")
        print(f"🎯 Incremental enabled: {is_incremental_test_generation_enabled()}")
        if analysis.get('incremental_info'):
            inc_info = analysis['incremental_info']
            print(f"🎯 Incremental info - Existing files: {inc_info.get('existing_test_files', 0)}")
            print(f"🎯 Incremental info - Original methods: {inc_info.get('original_method_count', 0)} public, {inc_info.get('original_private_method_count', 0)} private")
            print(f"🎯 Incremental info - Filtered methods: {inc_info.get('filtered_method_count', 0)} public, {inc_info.get('filtered_private_method_count', 0)} private")
        print(f"🎯 ===== INVOKING LLM NOW =====")
        
        response = await llm.ainvoke(messages)
        
        # Clean up any potential markdown or explanations that might slip through
        content = response.content.strip()
        
        # CRITICAL DEBUG: Show what LLM actually generated
        print(f"🎯 ===== LLM RESPONSE DEBUG =====")
        print(f"🎯 Raw response length: {len(content)} characters")
        print(f"🎯 Response starts with: {repr(content[:100])}")
        print(f"🎯 Response ends with: {repr(content[-100:])}")
        print(f"🎯 Contains @Test: {'@Test' in content}")
        print(f"🎯 Contains 'void': {'void' in content}")
        print(f"🎯 Contains 'public': {'public' in content}")
        print(f"🎯 Number of lines: {len(content.split(chr(10)))}")
        
        # Show first 20 lines for debugging
        lines_preview = content.split('\n')[:20]
        print(f"🎯 First 20 lines of LLM response:")
        for i, line in enumerate(lines_preview, 1):
            print(f"   {i:2d}: {line}")
        print(f"🎯 ===== END LLM RESPONSE DEBUG =====")
        
        # Remove markdown code blocks if present
        if content.startswith('```java'):
            content = content.replace('```java', '').replace('```', '').strip()
        elif content.startswith('```'):
            content = content.replace('```', '').strip()
        
        # Remove any explanatory text before the package declaration
        lines = content.split('\n')
        java_start = -1
        for i, line in enumerate(lines):
            if line.strip().startswith('package '):
                java_start = i
                break
        
        if java_start >= 0:
            content = '\n'.join(lines[java_start:])
        
        # CRITICAL: Remove any embedded class definitions (architectural fix)
        content = remove_embedded_class_definitions(content, class_info.get('class_name', 'Unknown'))
        
        # CRITICAL: Apply LoggerBean type conversion fixes upfront
        content = fix_loggerbean_usage(content)
        
        # Add LLM validation of the generated test
        try:
            validation_result = await validate_generated_test_with_llm(
                content, 
                class_info.get('class_name', 'Unknown'), 
                llm=llm
            )
            
            # CRITICAL: Check for application vs framework class import conflicts
            analysis = analyze_java_code(class_info['content'])
            application_classes = analysis.get('application_classes', [])
            current_class = class_info.get('class_name', 'Unknown')
            
            # CRITICAL: Remove any embedded class definitions (architectural fix)
            content = remove_embedded_class_definitions(content, current_class)
            
            # Post-process to fix import conflicts
            lines = content.split('\n')
            fixed_lines = []
            removed_imports = []
            needs_app_import = True
            
            for line in lines:
                if line.strip().startswith('import ') and line.strip().endswith(';'):
                    import_statement = line.strip()
                    imported_class = import_statement.split('.')[-1].replace(';', '')
                    
                    # Check if this is the correct application class import
                    if imported_class == current_class and current_package and current_package in import_statement:
                        needs_app_import = False
                        fixed_lines.append(line)
                        print(f"✅ FOUND: Correct application class import: {import_statement}")
                        continue
                    
                    # Check if this is a generic/wrong import for our class
                    if imported_class == current_class and ('com.example' in import_statement or current_package not in import_statement):
                        removed_imports.append(import_statement)
                        fixed_lines.append(f"// Removed incorrect import: {import_statement}")
                        print(f"🚨 FIXED: Removed incorrect generic import: {import_statement}")
                        continue
                    
                    # Check if this import conflicts with application class
                    if imported_class == current_class and 'org.springframework' in import_statement:
                        removed_imports.append(import_statement)
                        fixed_lines.append(f"// Removed conflicting framework import: {import_statement}")
                        print(f"🚨 FIXED: Removed framework import conflict: {import_statement}")
                        continue
                    elif imported_class in application_classes and ('org.springframework' in import_statement or 'org.apache' in import_statement):
                        removed_imports.append(import_statement)
                        fixed_lines.append(f"// Removed conflicting framework import: {import_statement}")
                        print(f"🚨 FIXED: Removed framework import conflict for application class: {import_statement}")
                        continue
                
                fixed_lines.append(line)
            
            # Add the correct application class import if missing
            if needs_app_import and current_package and current_class:
                correct_import = f"import {current_package}.{current_class};"
                # Find where to insert the import (after other imports)
                insert_idx = 0
                for i, line in enumerate(fixed_lines):
                    if line.strip().startswith('import ') and line.strip().endswith(';'):
                        insert_idx = i + 1
                
                fixed_lines.insert(insert_idx, correct_import)
                print(f"✅ ADDED: Correct application class import: {correct_import}")
            
            if removed_imports or needs_app_import:
                content = '\n'.join(fixed_lines)
                print(f"🔧 Fixed {len(removed_imports)} import conflicts and ensured correct app import for {current_class}")
                
                # Re-validate after fixing conflicts
                validation_result = await validate_generated_test_with_llm(
                    content, 
                    class_info.get('class_name', 'Unknown'), 
                    llm=llm
                )
            
            # If there are critical issues, try to auto-fix them using LLM
            if validation_result.get('validation_status') == 'FAIL' and validation_result.get('critical_issues'):
                print(f"🔧 LLM auto-fixing validation issues for {class_info.get('class_name', 'Unknown')}")
                content = await auto_fix_validation_issues_with_llm(content, validation_result, llm)
                # Re-validate after auto-fix
                validation_result = await validate_generated_test_with_llm(
                    content, 
                    class_info.get('class_name', 'Unknown'), 
                    llm=llm
                )
            # Store validation result for reporting
            if not hasattr(class_info, 'validation_result'):
                class_info['validation_result'] = validation_result
        except Exception as e:
            print(f"⚠️ LLM validation failed for {class_info.get('class_name', 'Unknown')}: {str(e)}")
            class_info['validation_result'] = {
                'validation_status': 'ERROR',
                'overall_assessment': f"Validation failed: {str(e)}",
                'llm_validation': False
            }
        return content.strip()
        
    except Exception as e:
        return f"Error generating enhanced test with files: {str(e)}"

def extract_relevant_properties(properties_content: str, class_name: str) -> str:
    """Extract properties relevant to the specific class"""
    relevant_lines = []
    
    # Generic property patterns based on class name
    class_name_lower = class_name.lower()
    
    # Extract class name components for pattern matching
    patterns = [class_name_lower]
    
    # Add common patterns based on class naming conventions
    if 'controller' in class_name_lower:
        patterns.extend(['controller', 'web', 'api', 'endpoint'])
    elif 'service' in class_name_lower:
        patterns.extend(['service', 'business', 'logic'])
    elif 'dao' in class_name_lower or 'repository' in class_name_lower:
        patterns.extend(['dao', 'database', 'repository', 'datasource'])
    elif 'validator' in class_name_lower:
        patterns.extend(['validation', 'validate', 'schema'])
    elif 'util' in class_name_lower:
        patterns.extend(['util', 'utility', 'helper'])
    
    for line in properties_content.split('\n'):
        line = line.strip()
        if line and not line.startswith('#'):
            for pattern in patterns:
                if pattern in line.lower():
                    relevant_lines.append(line)
                    break
    
    return '\n'.join(relevant_lines[:15])  # Limit to first 15 relevant properties

# Utility Functions for File Operations
def extract_java_files(zip_path: str, extract_dir: str) -> List[str]:
    """Extract Java files from zip and return list of Java file paths"""
    java_files = []
    
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
    
    for root, dirs, files in os.walk(extract_dir):
        for file in files:
            if file.endswith('.java'):
                java_files.append(os.path.join(root, file))
    
    return java_files

def extract_source_files(zip_path: str, extract_dir: str) -> Dict[str, List[str]]:
    """Extract source files (Java and Kotlin) from zip and return categorized file paths"""
    source_files = {
        'java': [],
        'kotlin': [],
        'all': []
    }
    
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
    
    for root, dirs, files in os.walk(extract_dir):
        for file in files:
            file_path = os.path.join(root, file)
            if file.endswith('.java'):
                source_files['java'].append(file_path)
                source_files['all'].append(file_path)
            elif file.endswith('.kt'):
                source_files['kotlin'].append(file_path)
                source_files['all'].append(file_path)
    
    return source_files

def read_source_file(file_path: str) -> str:
    """Read content from a source file (Java or Kotlin)"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except UnicodeDecodeError:
        # Try with different encoding if UTF-8 fails
        with open(file_path, 'r', encoding='latin1') as file:
            return file.read()

def read_java_file(file_path: str) -> str:
    """Read Java file content"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        with open(file_path, 'r', encoding='latin-1') as f:
            return f.read()

def find_existing_test_files(test_base_path: str) -> List[str]:
    """Find existing test files that match the base test file pattern
    
    Args:
        test_base_path: Base test file path (e.g., /path/to/UserServiceTest.java)
        
    Returns:
        List of existing test file paths sorted by number
    """
    existing_files = []
    if not os.path.exists(test_base_path):
        return existing_files
    
    # Add the base test file if it exists
    existing_files.append(test_base_path)
    
    # Look for numbered versions (Test2.java, Test3.java, etc.)
    dir_path = os.path.dirname(test_base_path)
    base_name = os.path.basename(test_base_path)
    
    # Extract class name and extension
    if base_name.endswith('Test.java'):
        class_base = base_name[:-9]  # Remove 'Test.java'
        extension = 'Test.java'
    else:
        class_base = base_name[:-5]  # Remove '.java'
        extension = '.java'
    
    # Check for numbered versions
    counter = 2
    while counter <= 50:  # Limit to prevent infinite loops
        numbered_file = os.path.join(dir_path, f"{class_base}Test{counter}.java")
        if os.path.exists(numbered_file):
            existing_files.append(numbered_file)
            counter += 1
        else:
            break
    
    return existing_files

def extract_test_methods_from_file(test_file_path: str) -> List[str]:
    """Extract test method names from an existing test file
    
    Args:
        test_file_path: Path to the test file
        
    Returns:
        List of test method names found in the file
    """
    test_methods = []
    
    try:
        test_content = read_java_file(test_file_path)
        
        # Find test methods - look for @Test annotation followed by method
        # Handle cases where @Test and method declaration are on different lines
        # and visibility modifier might be missing (package-private)
        test_method_pattern = r'@Test.*?(?:(?:public|private|protected)\s+)?(?:\w+\s+)?(\w+)\s*\([^)]*\)\s*(?:throws\s+[^{]+)?\s*\{'
        matches = re.findall(test_method_pattern, test_content, re.DOTALL)
        
        # Filter out obvious non-test methods (constructors, etc.)
        filtered_matches = []
        for match in matches:
            if (match.startswith('test') or 
                match.lower().startswith('test') or 
                'test' in match.lower()):
                filtered_matches.append(match)
        
        test_methods.extend(filtered_matches)
        
        # Also look for parameterized tests
        param_test_pattern = r'@ParameterizedTest.*?(?:(?:public|private|protected)\s+)?(?:\w+\s+)?(\w+)\s*\([^)]*\)\s*(?:throws\s+[^{]+)?\s*\{'
        param_matches = re.findall(param_test_pattern, test_content, re.DOTALL)
        
        # Filter parameterized test methods
        filtered_param_matches = []
        for match in param_matches:
            if (match.startswith('test') or 
                match.lower().startswith('test') or 
                'test' in match.lower()):
                filtered_param_matches.append(match)
        
        test_methods.extend(filtered_param_matches)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_methods = []
        for method in test_methods:
            if method not in seen:
                seen.add(method)
                unique_methods.append(method)
        
        return unique_methods
        
    except Exception as e:
        print(f"⚠️ Warning: Could not parse test methods from {test_file_path}: {str(e)}")
        return []

def get_uncovered_methods(class_methods: List[Dict[str, Any]], existing_test_files: List[str]) -> List[Dict[str, Any]]:
    """Determine which methods from the class are not covered by existing tests
    
    Args:
        class_methods: List of method dictionaries from analyze_java_code
        existing_test_files: List of existing test file paths
        
    Returns:
        List of uncovered method dictionaries
    """
    if not existing_test_files:
        return class_methods  # No existing tests, all methods are uncovered
    
    # Extract all test method names from existing files
    all_test_methods = []
    for test_file in existing_test_files:
        test_methods = extract_test_methods_from_file(test_file)
        all_test_methods.extend(test_methods)
    
    # Convert to lowercase for case-insensitive comparison and create variations
    test_method_variations = set()
    for test_method in all_test_methods:
        test_method_lower = test_method.lower()
        test_method_variations.add(test_method_lower)
        
        # Remove common test prefixes/suffixes for comparison
        if test_method_lower.startswith('test'):
            test_method_variations.add(test_method_lower[4:])
        if test_method_lower.endswith('test'):
            test_method_variations.add(test_method_lower[:-4])
    
    # Find uncovered methods
    uncovered_methods = []
    for method in class_methods:
        method_name = method.get('name', '').lower()
        
        print(f"🔍 Checking coverage for method: {method_name}")
        
        # Check if this method is likely covered by existing tests
        is_covered = False
        matching_tests = []
        
        for test_variation in test_method_variations:
            # More strict matching - require significant overlap
            if len(method_name) < 3 or len(test_variation) < 3:
                continue  # Skip very short names to avoid false matches
            
            # Direct name match (most reliable)
            if method_name == test_variation:
                is_covered = True
                matching_tests.append(f"exact: {test_variation}")
                break
            
            # Method name contained in test name (with sufficient length)
            if (len(method_name) >= 4 and method_name in test_variation and 
                len(method_name) / len(test_variation) >= 0.4):  # At least 40% of test name
                is_covered = True
                matching_tests.append(f"method_in_test: {test_variation}")
                break
            
            # Test name contained in method name (less common, but possible)
            if (len(test_variation) >= 4 and test_variation in method_name and 
                len(test_variation) / len(method_name) >= 0.4):  # At least 40% of method name
                is_covered = True
                matching_tests.append(f"test_in_method: {test_variation}")
                break
            
            # Fuzzy match for very similar names (without underscores)
            method_clean = method_name.replace('_', '').replace('-', '')
            test_clean = test_variation.replace('_', '').replace('-', '')
            
            if len(method_clean) >= 4 and len(test_clean) >= 4:
                # Check if one is contained in the other with good ratio
                if (method_clean in test_clean and len(method_clean) / len(test_clean) >= 0.5) or \
                   (test_clean in method_clean and len(test_clean) / len(method_clean) >= 0.5):
                    is_covered = True
                    matching_tests.append(f"fuzzy: {test_variation}")
                    break
        
        status = "✅ COVERED" if is_covered else "❌ NOT COVERED"
        print(f"  → {status}")
        if matching_tests:
            print(f"    Matched by: {', '.join(matching_tests)}")
        
        if not is_covered:
            uncovered_methods.append(method)
    
    return uncovered_methods

def get_next_test_file_name(test_base_path: str, existing_files: List[str]) -> str:
    """Generate the next available test file name
    
    Args:
        test_base_path: Base test file path
        existing_files: List of existing test files
        
    Returns:
        Next available test file path
    """
    if not existing_files:
        return test_base_path
    
    # Extract base name and directory
    dir_path = os.path.dirname(test_base_path)
    base_name = os.path.basename(test_base_path)
    
    # Extract class name
    if base_name.endswith('Test.java'):
        class_base = base_name[:-9]  # Remove 'Test.java'
    else:
        class_base = base_name[:-5]  # Remove '.java'
    
    # Find the next available number
    next_number = len(existing_files) + 1
    return os.path.join(dir_path, f"{class_base}Test{next_number}.java")

def extract_class_info(java_content: str) -> Dict[str, Any]:
    """Extract basic class information from Java content"""
    package_match = re.search(r'package\s+([^;]+);', java_content)
    package_name = package_match.group(1) if package_match else ""
    
    class_match = re.search(r'public\s+class\s+(\w+)', java_content)
    class_name = class_match.group(1) if class_match else "UnknownClass"
    
    imports = re.findall(r'import\s+([^;]+);', java_content)
    
    # Enhanced method pattern to handle multiline method signatures
    # This pattern uses DOTALL flag to match across lines and handles various method signature formats
    method_pattern = r'(public|private|protected)\s+(?:static\s+)?(?:synchronized\s+)?(?:final\s+)?(?:<[^>]*>\s+)?(\w+(?:<[^>]*>)?(?:\[\])*)\s+(\w+)\s*\([^{]*?\)\s*(?:throws\s+[^{]+)?\s*\{'
    methods = re.findall(method_pattern, java_content, re.DOTALL)
    
    # Extract method names, filtering out common Object methods
    method_names = []
    for method in methods:
        method_name = method[2] if len(method) >= 3 else method[1]
        if method_name not in ['equals', 'hashCode', 'toString', 'clone', 'finalize']:
            method_names.append(method_name)
    
    print(f"🔍 DEBUG - Extracted methods for {class_name}: {method_names}")
    
    return {
        'package': package_name,
        'class_name': class_name,
        'imports': imports,
        'methods': method_names,
        'content': java_content
    }

def save_test_file(test_content: str, original_file_path: str, output_dir: str, extract_dir: str = None) -> str:
    """Save generated test to appropriate directory structure"""
    rel_path = Path(original_file_path)
    
    # Convert src/main/java or src/main/kotlin to src/test/java or src/test/kotlin
    path_parts = list(rel_path.parts)
    if 'src' in path_parts and 'main' in path_parts:
        main_index = path_parts.index('main')
        path_parts[main_index] = 'test'
    elif 'src' in path_parts:
        src_index = path_parts.index('src')
        path_parts.insert(src_index + 1, 'test')
        # Determine language subdirectory
        if original_file_path.endswith('.kt'):
            path_parts.insert(src_index + 2, 'kotlin')
        else:
            path_parts.insert(src_index + 2, 'java')
    
    # Create test file name
    file_name = path_parts[-1]
    if original_file_path.endswith('.kt'):
        test_file_name = file_name.replace('.kt', 'Test.kt') if not file_name.endswith('Test.kt') else file_name
    else:
        test_file_name = file_name.replace('.java', 'Test.java') if not file_name.endswith('Test.java') else file_name
    path_parts[-1] = test_file_name
    
    # Create output path
    test_file_path = os.path.join(output_dir, *path_parts[path_parts.index('src'):])
    
    # Handle incremental test generation if enabled
    if is_incremental_test_generation_enabled():
        test_file_path = handle_incremental_test_generation(test_file_path, test_content, extract_dir)
    else:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(test_file_path), exist_ok=True)
        
        # Save test file (overwrite if exists)
        with open(test_file_path, 'w', encoding='utf-8') as f:
            f.write(test_content)
    
    return test_file_path

def handle_incremental_test_generation(test_file_path: str, test_content: str, extract_dir: str = None) -> str:
    """Handle incremental test generation logic
    
    Args:
        test_file_path: Original test file path
        test_content: Generated test content
        extract_dir: Extracted ZIP directory to check for existing test files
        
    Returns:
        Final test file path used
    """
    # Check if existing test files exist in output directory
    existing_files = find_existing_test_files(test_file_path)
    
    # CRITICAL FIX: Also check for existing test files in the extracted ZIP directory
    existing_files_from_zip = []
    if extract_dir:
        print(f"🔍 Looking for existing test files in ZIP (handle_incremental):")
        print(f"   Test file path: {test_file_path}")
        print(f"   Extract dir: {extract_dir}")
        
        # Extract the expected test file name from the test_file_path
        test_file_name = os.path.basename(test_file_path)
        print(f"   Looking for test file: {test_file_name}")
        
        # Search for existing test files with this exact name in the entire extracted directory
        for root, dirs, files in os.walk(extract_dir):
            for file in files:
                if file == test_file_name:
                    found_test_file = os.path.join(root, file)
                    print(f"   ✅ Found existing test file: {found_test_file}")
                    existing_files_from_zip.append(found_test_file)
                    
                    # Also look for numbered versions (Test2.java, Test3.java, etc.)
                    dir_path = os.path.dirname(found_test_file)
                    # Extract class name to look for numbered versions
                    if test_file_name.endswith('Test.java'):
                        class_name = test_file_name[:-9]  # Remove 'Test.java'
                        counter = 2
                        while counter <= 10:  # Check up to Test10.java
                            numbered_test_file = os.path.join(dir_path, f"{class_name}Test{counter}.java")
                            if os.path.exists(numbered_test_file):
                                print(f"   ✅ Found numbered test file: {numbered_test_file}")
                                existing_files_from_zip.append(numbered_test_file)
                                counter += 1
                            else:
                                break
        
        print(f"   Found {len(existing_files_from_zip)} existing test files in ZIP")
        
        # Combine existing files from both sources
        all_existing_files = existing_files + existing_files_from_zip
        # Remove duplicates while preserving order
        seen = set()
        existing_files = []
        for file_path in all_existing_files:
            if file_path not in seen:
                existing_files.append(file_path)
                seen.add(file_path)
    
    if not existing_files:
        # No existing test files, save normally
        os.makedirs(os.path.dirname(test_file_path), exist_ok=True)
        with open(test_file_path, 'w', encoding='utf-8') as f:
            f.write(test_content)
        return test_file_path
    
    print(f"🔍 Found {len(existing_files)} existing test file(s) for incremental generation:")
    for i, existing_file in enumerate(existing_files, 1):
        print(f"  {i}. {os.path.basename(existing_file)}")
    
    # Get all test methods from existing files
    all_existing_test_methods = []
    for existing_file in existing_files:
        test_methods = extract_test_methods_from_file(existing_file)
        all_existing_test_methods.extend(test_methods)
        print(f"  📝 {os.path.basename(existing_file)}: {len(test_methods)} test methods")
    
    print(f"📊 Total existing test methods: {len(all_existing_test_methods)}")
    
    # Extract test methods from the new generated content
    new_test_methods = extract_test_methods_from_content(test_content)
    print(f"🆕 New generated test methods: {len(new_test_methods)}")
    
    # Find uncovered test methods
    uncovered_test_methods = find_uncovered_test_methods(new_test_methods, all_existing_test_methods)
    
    if not uncovered_test_methods:
        print("✅ All test methods are already covered in existing test files.")
        print("📋 Copying existing test files to output directory...")
        
        # Copy all existing test files to output directory to preserve them
        copied_files = []
        for existing_file in existing_files:
            try:
                # Read the existing test file content
                existing_content = read_java_file(existing_file)
                
                # Create output path for the existing file
                output_path = test_file_path
                if len(existing_files) > 1:
                    # If multiple existing files, use numbered naming
                    base_name = os.path.basename(test_file_path)
                    if base_name.endswith('Test.java'):
                        class_name = base_name[:-9]  # Remove 'Test.java'
                        file_number = existing_files.index(existing_file) + 1
                        if file_number == 1:
                            output_path = test_file_path  # First file keeps original name
                        else:
                            dir_path = os.path.dirname(test_file_path)
                            output_path = os.path.join(dir_path, f"{class_name}Test{file_number}.java")
                
                # Ensure output directory exists
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
                # Copy the existing test file content to output
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(existing_content)
                
                copied_files.append(output_path)
                print(f"  ✅ Copied: {os.path.basename(existing_file)} → {os.path.basename(output_path)}")
                
            except Exception as e:
                print(f"  ⚠️ Error copying {existing_file}: {str(e)}")
        
        print(f"💾 Successfully copied {len(copied_files)} existing test file(s) to output")
        return copied_files[0] if copied_files else test_file_path  # Return first copied file path
    
    print(f"🎯 Found {len(uncovered_test_methods)} uncovered test methods:")
    for method in uncovered_test_methods:
        print(f"  • {method}")
    
    # First, copy all existing test files to output directory
    print(f"📋 Copying {len(existing_files)} existing test file(s) to output directory...")
    copied_files = []
    output_base_dir = os.path.dirname(test_file_path)
    
    for existing_file in existing_files:
        try:
            # Read existing file content
            with open(existing_file, 'r', encoding='utf-8') as f:
                existing_content = f.read()
            
            # Create output path with same name
            existing_filename = os.path.basename(existing_file)
            output_path = os.path.join(output_base_dir, existing_filename)
            
            # Ensure output directory exists
            os.makedirs(output_base_dir, exist_ok=True)
            
            # Write existing file to output
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(existing_content)
            
            copied_files.append(output_path)
            print(f"  ✅ Copied: {existing_filename} → output directory")
            
        except Exception as e:
            print(f"  ⚠️ Error copying {existing_file}: {str(e)}")
    
    print(f"💾 Successfully copied {len(copied_files)} existing test file(s) to output")
    
    # Generate new test file with only uncovered methods
    filtered_test_content = filter_test_content_for_uncovered_methods(test_content, uncovered_test_methods)
    
    # Get next available file name
    next_test_file = get_next_test_file_name(test_file_path, existing_files)
    
    # Update class name in the filtered content to match the new file name
    filtered_test_content = update_test_class_name_in_content(filtered_test_content, next_test_file)
    
    # Save the incremental test file
    os.makedirs(os.path.dirname(next_test_file), exist_ok=True)
    with open(next_test_file, 'w', encoding='utf-8') as f:
        f.write(filtered_test_content)
    
    print(f"💾 Created incremental test file: {os.path.basename(next_test_file)}")
    return next_test_file

def extract_test_methods_from_content(test_content: str) -> List[str]:
    """Extract test method names from test content"""
    print(f"🔍 === EXTRACTING TEST METHODS FROM GENERATED CONTENT ===")
    print(f"Content length: {len(test_content)} characters")
    
    test_methods = []
    
    # ENHANCED DEBUG: Show structure analysis
    lines = test_content.split('\n')
    print(f"🔍 CONTENT ANALYSIS:")
    print(f"   Total lines: {len(lines)}")
    print(f"   Lines with @Test: {len([l for l in lines if '@Test' in l])}")
    print(f"   Lines with 'void': {len([l for l in lines if ' void ' in l])}")
    print(f"   Lines with 'public': {len([l for l in lines if 'public' in l])}")
    print(f"   Lines with '()': {len([l for l in lines if '()' in l])}")
    
    # Pattern 1: @Test annotation followed by method (most flexible)
    test_method_pattern = r'@Test\s*(?:\([^)]*\))?\s*(?:@\w+\s*(?:\([^)]*\))?\s*)*\s*(?:public|private|protected)?\s+(?:static\s+)?(?:void|[\w<>\[\]]+)\s+(\w+)\s*\('
    matches = re.findall(test_method_pattern, test_content, re.DOTALL | re.MULTILINE)
    test_methods.extend(matches)
    print(f"Found {len(matches)} @Test methods: {matches}")
    
    # Pattern 2: Look for parameterized tests
    param_test_pattern = r'@ParameterizedTest\s*(?:\([^)]*\))?\s*(?:@\w+\s*(?:\([^)]*\))?\s*)*\s*(?:public|private|protected)?\s+(?:static\s+)?(?:void|[\w<>\[\]]+)\s+(\w+)\s*\('
    param_matches = re.findall(param_test_pattern, test_content, re.DOTALL | re.MULTILINE)
    test_methods.extend(param_matches)
    print(f"Found {len(param_matches)} @ParameterizedTest methods: {param_matches}")
    
    # Pattern 3: More aggressive - find any method that might be a test by position
    # Look for @Test followed by anything, then capture the method name
    aggressive_test_pattern = r'@Test[^{]*?(\w+)\s*\('
    aggressive_matches = re.findall(aggressive_test_pattern, test_content, re.DOTALL)
    for match in aggressive_matches:
        if match not in test_methods and not match in ['Test', 'class', 'import']:
            test_methods.append(match)
    print(f"Found {len(aggressive_matches)} methods via aggressive @Test pattern: {aggressive_matches}")
    
    # Pattern 4: Look for test methods that might not have explicit @Test annotations visible
    # This catches methods that start with "test" prefix
    method_pattern = r'(?:public|private|protected)\s+(?:static\s+)?(?:void|[\w<>\[\]]+)\s+(test\w+)\s*\('
    method_matches = re.findall(method_pattern, test_content, re.IGNORECASE)
    for match in method_matches:
        if match not in test_methods:
            test_methods.append(match)
    print(f"Found {len(method_matches)} methods with 'test' prefix: {method_matches}")
    
    # Pattern 5: Find void methods in test class (likely test methods)
    void_method_pattern = r'(?:public|private|protected)\s+void\s+(\w+)\s*\('
    void_matches = re.findall(void_method_pattern, test_content)
    for match in void_matches:
        if match not in test_methods and match not in ['setUp', 'tearDown', 'beforeEach', 'afterEach']:
            test_methods.append(match)
    print(f"Found {len(void_matches)} void methods (potential tests): {void_matches}")
    
    # Debug: Show sample of test content if no methods found or very few found
    if len(test_methods) < 2:  # Expect at least 2 test methods for the 2 uncovered methods
        print(f"⚠️ FOUND ONLY {len(test_methods)} TEST METHODS! Expected at least 2. Analyzing content:")
        
        # Show lines that might contain test methods
        print(f"🔍 Lines containing test-related keywords:")
        for i, line in enumerate(lines, 1):
            if any(keyword in line.lower() for keyword in ['@test', 'public void', 'test', '@', 'void', 'assert']):
                print(f"   Line {i:3d}: {line.strip()}")
        
        # Show content around class declaration
        print(f"\n🔍 Content structure analysis:")
        in_class = False
        method_count = 0
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if 'class ' in stripped and 'Test' in stripped:
                in_class = True
                print(f"   Line {i:3d}: [CLASS START] {stripped}")
            elif in_class and (stripped.startswith('public ') or stripped.startswith('private ') or stripped.startswith('protected ')):
                method_count += 1
                print(f"   Line {i:3d}: [METHOD {method_count}] {stripped}")
            elif stripped == '}' and in_class:
                print(f"   Line {i:3d}: [CLASS END] {stripped}")
                break
        
        # Show content preview
        print(f"\n🔍 Content preview (first 1000 chars):")
        print(test_content[:1000])
        print(f"...")
        print(f"🔍 Content preview (last 500 chars):")
        print(test_content[-500:])
    
    print(f"🎯 Total unique test methods found: {len(test_methods)}")
    for i, method in enumerate(test_methods, 1):
        print(f"  {i}. {method}")
    
    print(f"🔍 === END TEST METHOD EXTRACTION ===")
    return test_methods

def find_uncovered_test_methods(new_methods: List[str], existing_methods: List[str]) -> List[str]:
    """Find test methods that are not covered by existing tests"""
    # Convert to lowercase for case-insensitive comparison
    existing_lower = {method.lower() for method in existing_methods}
    
    uncovered = []
    for method in new_methods:
        method_lower = method.lower()
        
        # Check direct match
        if method_lower in existing_lower:
            continue
            
        # Check for partial matches (more flexible comparison)
        is_covered = False
        for existing_method in existing_lower:
            if (method_lower in existing_method or 
                existing_method in method_lower or
                method_lower.replace('_', '') in existing_method.replace('_', '') or
                existing_method.replace('_', '') in method_lower.replace('_', '')):
                is_covered = True
                break
        
        if not is_covered:
            uncovered.append(method)
    
    return uncovered

def filter_test_content_for_uncovered_methods(test_content: str, uncovered_methods: List[str]) -> str:
    """Filter test content to include only uncovered test methods"""
    if not uncovered_methods:
        return ""
    
    print(f"🔍 === FILTERING TEST CONTENT FOR UNCOVERED METHODS ===")
    print(f"Uncovered methods to include: {uncovered_methods}")
    
    lines = test_content.split('\n')
    filtered_lines = []
    
    # State tracking
    i = 0
    in_class = False
    class_brace_count = 0
    
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Always include package declarations, imports, and empty lines
        if (stripped.startswith('package ') or 
            stripped.startswith('import ') or 
            stripped == ''):
            filtered_lines.append(line)
            i += 1
            continue
        
        # Include class-level annotations and class declaration
        if (stripped.startswith('@ExtendWith') or
            stripped.startswith('@TestInstance') or
            stripped.startswith('@SpringBootTest') or
            stripped.startswith('public class ') or
            stripped.startswith('class ')):
            filtered_lines.append(line)
            if 'class ' in stripped:
                in_class = True
                class_brace_count = 0
            i += 1
            continue
        
        # Track class braces
        if in_class:
            class_brace_count += line.count('{')
            class_brace_count -= line.count('}')
            
            # If we've exited the class, add the closing brace and stop
            if class_brace_count < 0:
                filtered_lines.append(line)
                break
        
        # Include class-level fields and annotations
        if (in_class and not in_method_context(stripped) and
            (stripped.startswith('@Mock') or
             stripped.startswith('@InjectMocks') or
             stripped.startswith('@Autowired') or
             stripped.startswith('@Value') or
             stripped.startswith('private ') or
             stripped.startswith('protected ') or
             stripped.startswith('public '))):
            filtered_lines.append(line)
            i += 1
            continue
        
        # Handle @Test annotations and test methods
        if (stripped.startswith('@Test') or 
            stripped.startswith('@ParameterizedTest') or
            stripped.startswith('@RepeatedTest')):
            
            # Look ahead to find the method name
            method_name = None
            for j in range(i, min(i + 10, len(lines))):
                # Find method declaration
                method_patterns = [
                    r'(?:public|private|protected)?\s*(?:static\s+)?void\s+(\w+)\s*\(',
                    r'(?:public|private|protected)?\s*(?:static\s+)?\w+\s+(\w+)\s*\(',
                    r'void\s+(\w+)\s*\('
                ]
                
                for pattern in method_patterns:
                    match = re.search(pattern, lines[j])
                    if match:
                        method_name = match.group(1)
                        break
                if method_name:
                    break
            
            # Check if this method should be included
            if method_name and method_name in uncovered_methods:
                print(f"  ✅ Including uncovered method: {method_name}")
                
                # Include the @Test annotation and the complete method
                filtered_lines.append(line)
                i += 1
                
                # Include all lines until we find the complete method
                method_brace_count = 0
                method_started = False
                
                while i < len(lines):
                    method_line = lines[i]
                    filtered_lines.append(method_line)
                    
                    # Track method braces
                    if '{' in method_line:
                        method_brace_count += method_line.count('{')
                        method_started = True
                    if '}' in method_line:
                        method_brace_count -= method_line.count('}')
                        if method_started and method_brace_count <= 0:
                            # End of method reached
                            i += 1
                            break
                    i += 1
                continue
            else:
                # Skip this method - it's already covered
                if method_name:
                    print(f"  ⏭️ Skipping covered method: {method_name}")
                
                # Skip the @Test annotation and the entire method
                i += 1
                method_brace_count = 0
                method_started = False
                
                while i < len(lines):
                    method_line = lines[i]
                    
                    # Track method braces to skip the entire method
                    if '{' in method_line:
                        method_brace_count += method_line.count('{')
                        method_started = True
                    if '}' in method_line:
                        method_brace_count -= method_line.count('}')
                        if method_started and method_brace_count <= 0:
                            # End of method reached
                            i += 1
                            break
                    i += 1
                continue
        
        # Handle @BeforeEach, @AfterEach, etc. - include these setup methods
        if (stripped.startswith('@BeforeEach') or
            stripped.startswith('@AfterEach') or
            stripped.startswith('@BeforeAll') or
            stripped.startswith('@AfterAll')):
            
            # Include the annotation and the complete setup method
            filtered_lines.append(line)
            i += 1
            
            # Include all lines until we find the complete method
            method_brace_count = 0
            method_started = False
            
            while i < len(lines):
                setup_line = lines[i]
                filtered_lines.append(setup_line)
                
                # Track method braces
                if '{' in setup_line:
                    method_brace_count += setup_line.count('{')
                    method_started = True
                if '}' in setup_line:
                    method_brace_count -= setup_line.count('}')
                    if method_started and method_brace_count <= 0:
                        # End of method reached
                        i += 1
                        break
                i += 1
            continue
        
        # Include comments and other content inside the class
        if (in_class and 
            (stripped.startswith('//') or
             stripped.startswith('/*') or
             stripped.startswith('*') or
             stripped == '')):
            filtered_lines.append(line)
        
        i += 1
    
    # Ensure the class is properly closed
    if in_class and class_brace_count >= 0:
        filtered_lines.append('}')
    
    result = '\n'.join(filtered_lines)
    print(f"🎯 Filtered content length: {len(result)} characters")
    print(f"🔍 === END FILTERING ===")
    return result

def in_method_context(line_stripped: str) -> bool:
    """Helper function to check if we're in a method context"""
    return (line_stripped.startswith('@Test') or
            line_stripped.startswith('@ParameterizedTest') or
            line_stripped.startswith('@RepeatedTest') or
            line_stripped.startswith('@BeforeEach') or
            line_stripped.startswith('@AfterEach') or
            line_stripped.startswith('@BeforeAll') or
            line_stripped.startswith('@AfterAll'))

def update_test_class_name_in_content(test_content: str, new_file_path: str) -> str:
    """Update the test class name in content to match the new file name"""
    new_file_name = os.path.basename(new_file_path)
    new_class_name = new_file_name.replace('.java', '')
    
    # Replace class declaration
    test_content = re.sub(
        r'public class \w+Test\d*',
        f'public class {new_class_name}',
        test_content
    )
    
    # Replace class declaration without 'public' keyword
    test_content = re.sub(
        r'class \w+Test\d*',
        f'class {new_class_name}',
        test_content
    )
    
    return test_content

def create_output_zip(test_dir: str, output_zip_path: str):
    """Create zip file with generated test cases"""
    with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(test_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, test_dir)
                zipf.write(file_path, arcname)


# Initialize session tracking
def initialize_session(session_id: str = None):
    """Initialize session for test generation"""
    if not session_id:
        from datetime import datetime
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    print(f"🔢 Session initialized: {session_id}")
    return session_id

def create_output_filename_with_session(session_id: str = None, custom_output_dir: str = None) -> tuple:
    """
    Create output filename with session ID and timestamp, and ensure output folder exists
    
    Args:
        session_id: Optional session ID for filename
        custom_output_dir: Optional custom output directory path
    
    Returns:
        tuple: (output_folder_path, zip_filename, full_zip_path)
    """
    # Use custom output directory or default
    if custom_output_dir:
        # If custom_output_dir is a file path (ends with .zip), use its directory
        if custom_output_dir.lower().endswith('.zip'):
            output_folder = os.path.dirname(custom_output_dir)
            if not output_folder:
                output_folder = "."
            custom_filename = os.path.basename(custom_output_dir)
        else:
            output_folder = custom_output_dir
            custom_filename = None
    else:
        output_folder = "enhanced_junit_tests_output"
        custom_filename = None
    
    os.makedirs(output_folder, exist_ok=True)
    
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Get or generate session ID
    if not session_id:
        try:
            # Try to get Chainlit session ID
            session_id = "cl_session" if 'cl' in globals() and hasattr(globals()['cl'], 'context') else None
        except:
            session_id = None
    
    # Fallback to generic session if no ID available
    if not session_id:
        session_id = "session"
    
    # Create filename
    if custom_filename:
        zip_filename = custom_filename
    else:
        zip_filename = f"enhanced_junit_tests_output_{session_id}_{timestamp}.zip"
    
    full_zip_path = os.path.join(output_folder, zip_filename)
    
    return output_folder, zip_filename, full_zip_path

def cleanup_old_output_files(output_folder: str, keep_count: int = 10):
    """
    Clean up old output files, keeping only the most recent ones
    
    Args:
        output_folder: Path to the output folder
        keep_count: Number of most recent files to keep (default: 10)
    """
    try:
        if not os.path.exists(output_folder):
            return
        
        # Get all ZIP files in the output folder
        zip_files = []
        for file in os.listdir(output_folder):
            if file.endswith('.zip') and file.startswith('enhanced_junit_tests_output_'):
                file_path = os.path.join(output_folder, file)
                if os.path.isfile(file_path):
                    zip_files.append((file_path, os.path.getmtime(file_path)))
        
        # Sort by modification time (newest first)
        zip_files.sort(key=lambda x: x[1], reverse=True)
        
        # Remove old files if we have more than keep_count
        if len(zip_files) > keep_count:
            files_to_remove = zip_files[keep_count:]
            for file_path, _ in files_to_remove:
                try:
                    os.remove(file_path)
                    print(f"🗑️ Cleaned up old output file: {os.path.basename(file_path)}")
                except Exception as e:
                    print(f"⚠️ Could not remove old file {file_path}: {e}")
    except Exception as e:
        print(f"⚠️ Error during cleanup: {e}")

# Enhanced ZIP processing with file detection and user prompts
async def process_java_zip_enhanced_core(zip_element, message_sender=None, custom_output_dir=None):
    """Enhanced ZIP processing with comprehensive debugging - UI agnostic version"""
    
    async def send_message(content):
        """Send message through provided sender or print to console"""
        if message_sender:
            await message_sender(content)
        else:
            print(content)
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            extract_dir = os.path.join(temp_dir, "extracted")
            output_dir = os.path.join(temp_dir, "junit_tests")
            
            # Save and extract ZIP
            zip_path = os.path.join(temp_dir, zip_element.name)
            with open(zip_path, "wb") as f:
                f.write(zip_element.content)
            
            await send_message(
                "🔄 **Enhanced File Detection Started!**\n\n"
                "✅ Extracting files...\n"
                "📁 Creating output folder: `enhanced_junit_tests_output/`\n"
                "🔍 Scanning for Swagger/OpenAPI files...\n"
                "📊 Looking for test data files...\n"
                "⚙️ Detecting configuration files..."
            )
            
            # Extract Java files first
            java_files = extract_java_files(zip_path, extract_dir)
            main_java_files = [f for f in java_files if '/test/' not in f.replace('\\', '/')]            
            
            # Extract all source files (Java and Kotlin)
            source_files = extract_source_files(zip_path, extract_dir)
            main_java_files = [f for f in source_files['java'] if '/test/' not in f.replace('\\', '/')]
            main_kotlin_files = [f for f in source_files['kotlin'] if '/test/' not in f.replace('\\', '/')]
            all_main_files = main_java_files + main_kotlin_files
            
            print(f"🔍 DEBUG - Total Java files found: {len(source_files['java'])}")
            print(f"🔍 DEBUG - Total Kotlin files found: {len(source_files['kotlin'])}")
            print(f"🔍 DEBUG - Main Java files (excluding test): {len(main_java_files)}")
            print(f"🔍 DEBUG - Main Kotlin files (excluding test): {len(main_kotlin_files)}")
            print(f"🔍 DEBUG - Total main source files: {len(all_main_files)}")
            
            for i, source_file in enumerate(all_main_files[:10]):  # Show first 10 files
                file_name = source_file.split('\\')[-1] if '\\' in source_file else source_file.split('/')[-1]
                file_type = "Kotlin" if source_file.endswith('.kt') else "Java"
                print(f"🔍 DEBUG - {file_type} file {i+1}: {file_name}")
            if len(all_main_files) > 10:
                print(f"🔍 DEBUG - ... and {len(all_main_files) - 10} more files")
            
            # ADD DEBUG OUTPUT
            debug_directory_structure(extract_dir)
            
            # Extract other file types with enhanced debugging
            print("\n🔍 Starting Swagger file detection...")
            swagger_files = extract_swagger_files(extract_dir)
            
            print("\n🔍 Starting test data file detection...")
            test_data_files = extract_test_data_files(extract_dir)
            
            print("\n🔍 Starting configuration file detection...")
            config_files = extract_configuration_files(extract_dir)
            
            # Report findings with debug info
            findings_summary = f"""
📊 **File Detection Summary with Debug Info:**
- **Java classes:** {len(main_java_files)}
- **Kotlin classes:** {len(main_kotlin_files)}
- **Total source files:** {len(all_main_files)}
- **Swagger/OpenAPI files:** {len(swagger_files)} {'✅' if swagger_files else '❌'}
- **Test data files:** {len(test_data_files)} {'✅' if test_data_files else '❌'}
- **Configuration files:** {len(config_files)} {'✅' if config_files else '❌'}

**Language Distribution:**
- Java: {len(main_java_files)} files ({len(main_java_files)/max(1, len(all_main_files))*100:.1f}%)
- Kotlin: {len(main_kotlin_files)} files ({len(main_kotlin_files)/max(1, len(all_main_files))*100:.1f}%)

🔍 **Debug Information:**
- Extract directory: `{extract_dir}`
- Directory exists: {os.path.exists(extract_dir)}
- Total files extracted: {sum(len(files) for _, _, files in os.walk(extract_dir))}
"""
            
            if swagger_files:
                findings_summary += f"\n🔍 **Found Swagger Files:**\n"
                for filename in swagger_files.keys():
                    findings_summary += f"• {filename}\n"
            else:
                findings_summary += f"\n❌ **No Swagger files found. Searched locations:**\n"
                swagger_dir = os.path.join(extract_dir, "swagger")
                findings_summary += f"• {swagger_dir} (exists: {os.path.exists(swagger_dir)})\n"
                if os.path.exists(swagger_dir):
                    contents = os.listdir(swagger_dir)
                    findings_summary += f"• Contents: {contents}\n"
            
            if test_data_files:
                findings_summary += f"\n📊 **Found Test Data Files:**\n"
                for filename in list(test_data_files.keys())[:5]:
                    findings_summary += f"• {filename}\n"
                if len(test_data_files) > 5:
                    findings_summary += f"• ... and {len(test_data_files) - 5} more files\n"
            else:
                findings_summary += f"\n❌ **No test data files found. Searched locations:**\n"
                test_data_dir = os.path.join(extract_dir, "test-data")
                findings_summary += f"• {test_data_dir} (exists: {os.path.exists(test_data_dir)})\n"
                if os.path.exists(test_data_dir):
                    contents = os.listdir(test_data_dir)
                    findings_summary += f"• Contents: {contents}\n"
            
            await send_message(findings_summary)
            
            # Continue with the rest of the processing...
            # [Rest of the function remains the same]
            
            # Check for missing optional files and prompt user
            missing_swagger = len(swagger_files) == 0
            missing_test_data = len(test_data_files) == 0
            
            if missing_swagger or missing_test_data:
                decision = await prompt_for_missing_files(missing_swagger, missing_test_data, send_message)
                
                if not decision['proceed']:
                    return  # User chose to upload new file
            else:
                await send_message(
                    "✅ **All enhancement files found!** Proceeding with full file integration..."
                )
            
            # Process with enhanced file integration
            await send_message(
                "🧪 **Starting Enhanced Test Generation...**\n\n"
                f"• Using Swagger files: {'Yes (' + str(len(swagger_files)) + ' files)' if swagger_files else 'No'}\n"
                f"• Using test data: {'Yes (' + str(len(test_data_files)) + ' files)' if test_data_files else 'No'}\n"
                f"• Using configuration: {'Yes (' + str(len(config_files)) + ' files)' if config_files else 'No'}\n\n"
                "🚀 Generating production-ready tests with file integration..."
            )
            
            generated_tests = []
            
            # Development phase: Get focus file from environment configuration
            DEV_FOCUS_FILE = get_development_focus_file()  # Read from DEVELOPMENT_FOCUS_FILE environment variable
            # DEV_FOCUS_FILE = None  # NORMAL MODE: Process all files in the project (set DEVELOPMENT_FOCUS_FILE to empty/None in .env)
            
            # Process each source file (Java and Kotlin) with all available files
            for i, source_file in enumerate(all_main_files, 1):
                try:
                    # Development phase filtering: Skip files that don't match focus file
                    if DEV_FOCUS_FILE:
                        file_name = os.path.basename(source_file)
                        if file_name != DEV_FOCUS_FILE:
                            print(f"🔍 DEV MODE: Skipping {file_name} (focusing on {DEV_FOCUS_FILE})")
                            continue
                        else:
                            print(f"🎯 DEV MODE: Processing focus file {file_name}")
                            await send_message(
                                f"🎯 **Development Mode Active**\n\n"
                                f"Focusing on: **{DEV_FOCUS_FILE}**\n"
                                f"Skipping other files for faster development testing..."
                            )
                    
                    # Read source file content
                    source_content = read_source_file(source_file)
                    
                    # Analyze based on file type
                    analysis = analyze_source_code(source_file, source_content)
                    
                    if 'error' in analysis:
                        file_name = source_file.split('\\')[-1] if '\\' in source_file else source_file.split('/')[-1]
                        print(f"⚠️ Error analyzing {file_name}: {analysis['error']}")
                        continue
                    
                    if not analysis.get('methods', []):
                        file_name = source_file.split('\\')[-1] if '\\' in source_file else source_file.split('/')[-1]
                        print(f"⚠️ DEBUG - Skipping {file_name} ({analysis.get('class_name', 'Unknown')}) - No methods detected")
                        continue
                    
                    language = analysis.get('language', 'unknown')
                    class_name = analysis.get('class_name', 'Unknown')
                    
                    if i % 3 == 0 or i == len(all_main_files):
                        await send_message(
                            f"🧪 Generating file-integrated tests... ({i}/{len(all_main_files)})\n"
                            f"📝 Processing: {class_name} ({language.title()}) with user-provided files"
                        )
                    
                    # Generate enhanced test with user-provided files only
                    test_content = await generate_enhanced_junit_test_with_files(
                        analysis,  # Use the analysis dict instead of class_info
                        swagger_files=swagger_files if swagger_files else None,
                        test_data_files=test_data_files if test_data_files else None,
                        config_files=config_files if config_files else None,
                        output_dir=output_dir,
                        original_file_path=source_file,  # Use source_file instead of java_file
                        extract_dir=extract_dir
                    )
                    
                    # Save test file
                    test_file_path = save_test_file(test_content, source_file, output_dir, extract_dir)
                    
                    generated_tests.append({
                        'original_class': class_name,
                        'test_file': test_file_path,
                        'methods_tested': len(analysis.get('methods', [])),
                        'has_swagger': bool(swagger_files),
                        'has_test_data': bool(test_data_files),
                        'has_config': bool(config_files),
                        'complexity': analysis.get('complexity_score', 0),
                        'frameworks': analysis.get('frameworks', []),
                        'language': language,
                        'validation_result': analysis.get('validation_result', {})
                    })
                    
                except Exception as e:
                    file_name = source_file.split('\\')[-1] if '\\' in source_file else source_file.split('/')[-1]
                    await send_message(f"⚠️ Error processing {file_name}: {str(e)}")
                    continue
            
            if not generated_tests:
                await send_message(
                    "❌ No test cases could be generated. Please check if your Java files contain valid classes with methods."
                )
                return
            
            # Collect validation issues for reporting
            validation_issues = []
            for test in generated_tests:
                validation = test.get('validation_result', {})
                critical_issues = validation.get('critical_issues', [])
                if critical_issues:
                    for issue in critical_issues:
                        validation_issues.append({
                            'class': test.get('original_class', ''),
                            'file': test.get('test_file', ''),
                            'issue': issue
                        })
            
            # DEBUG: Check what files are in output directory before ZIP creation
            print(f"🔍 === FINAL OUTPUT DIRECTORY DEBUG ===")
            print(f"Output directory: {output_dir}")
            
            if os.path.exists(output_dir):
                print(f"📁 Files in output directory before ZIP creation:")
                total_files = 0
                for root, dirs, files in os.walk(output_dir):
                    for file in files:
                        if file.endswith(('.java', '.kt')):  # Include both Java and Kotlin test files
                            file_path = os.path.join(root, file)
                            rel_path = os.path.relpath(file_path, output_dir)
                            file_size = os.path.getsize(file_path)
                            file_ext = 'Java' if file.endswith('.java') else 'Kotlin'
                            print(f"  ✅ {rel_path} ({file_size} bytes) [{file_ext}]")
                            total_files += 1
                
                print(f"📊 Total test files found: {total_files}")
                
                if is_incremental_test_generation_enabled():
                    print(f"🔧 Incremental generation was ENABLED during this run")
                    
                    # Check for test files with incremental numbering (Test2, Test3, etc.)
                    incremental_files = []
                    for root, dirs, files in os.walk(output_dir):
                        for file in files:
                            if re.search(r'Test\d+\.java$|Test\d+\.kt$', file):
                                file_path = os.path.join(root, file)
                                rel_path = os.path.relpath(file_path, output_dir)
                                file_size = os.path.getsize(file_path)
                                incremental_files.append((rel_path, file_size))
                    
                    print(f"🎯 Incremental test files found: {len(incremental_files)}")
                    for rel_path, file_size in incremental_files:
                        print(f"  📄 {rel_path} ({file_size} bytes)")
                        
                    if len(incremental_files) == 0:
                        print(f"⚠️ WARNING: No incremental files found, may indicate no existing tests were present!")
                    elif len(incremental_files) >= 1:
                        print(f"✅ SUCCESS: Incremental test files generated successfully!")
                else:
                    print(f"❌ Incremental generation was DISABLED during this run")
            else:
                print(f"❌ Output directory does not exist!")
            
            print(f"🔍 === END OUTPUT DIRECTORY DEBUG ===")
            
            # Create enhanced output ZIP with session ID and timestamp
            output_folder, zip_filename, permanent_zip_path = create_output_filename_with_session(
                session_id=None, 
                custom_output_dir=custom_output_dir
            )
            output_zip_path = os.path.join(temp_dir, "enhanced_junit_tests.zip")
            create_output_zip(output_dir, output_zip_path)
            
            # Copy to permanent location with enhanced filename
            shutil.copy2(output_zip_path, permanent_zip_path)
            
            # Clean up old output files (keep last 10)
            cleanup_old_output_files(output_folder, keep_count=10)
            
            # Return the file path and data for UI to handle
            return {
                'zip_path': permanent_zip_path,
                'zip_filename': zip_filename,
                'generated_tests': generated_tests,
                'validation_issues': validation_issues
            }
            
    except Exception as e:
        error_msg = f"❌ **Error in enhanced processing:** {str(e)}"
        await send_message(error_msg)
        return None

# Standard processing function (fallback)
async def generate_junit_test_enhanced(class_info: Dict[str, Any]) -> str:
    """Generate JUnit test using enhanced functional approach with LangChain - NO COMMENTS"""
    try:
        llm = get_llm()
        
        # Step 1: Analyze the code
        analysis = analyze_java_code(class_info['content'])
        if 'error' in analysis:
            return f"Analysis failed: {analysis['error']}"
        
        # Step 2: Create strategy
        strategy = create_test_strategy(analysis)
        if 'error' in strategy:
            return f"Strategy creation failed: {strategy['error']}"
        
        # Step 3: Generate enhanced prompt using PromptBuilder
        enhanced_prompt = PromptBuilder.build_standard_prompt(analysis, strategy, class_info)
        
        system_prompt = PromptBuilder.get_system_prompt(analysis.get('frameworks', []))

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=enhanced_prompt)
        ]
        
        response = await llm.ainvoke(messages)
        
        # Clean up any potential markdown or explanations
        content = response.content.strip()
        
        # Remove markdown code blocks if present
        if content.startswith('```java'):
            content = content.replace('```java', '').replace('```', '').strip()
        elif content.startswith('```'):
            content = content.replace('```', '').strip()
        
        # Remove any explanatory text before the package declaration
        lines = content.split('\n')
        java_start = -1
        for i, line in enumerate(lines):
            if line.strip().startswith('package '):
                java_start = i
                break
        
        if java_start >= 0:
            content = '\n'.join(lines[java_start:])
        
        # CRITICAL: Remove any embedded class definitions (architectural fix)
        content = remove_embedded_class_definitions(content, class_info.get('class_name', 'Unknown'))
        
        # CRITICAL: Apply LoggerBean type conversion fixes upfront
        content = fix_loggerbean_usage(content)
        
        # Add LLM validation of the generated test
        try:
            validation_result = await validate_generated_test_with_llm(
                content, 
                class_info.get('class_name', 'Unknown'), 
                llm=llm
            )
            
            # If there are critical issues, try to auto-fix them
            if validation_result.get('validation_status') == 'FAIL' and validation_result.get('missing_imports'):
                print(f"🔧 Auto-fixing missing imports for {class_info.get('class_name', 'Unknown')}")
                content = auto_fix_imports(content, validation_result.get('missing_imports', []))
                
                # Re-validate after auto-fix
                validation_result = await validate_generated_test_with_llm(
                    content, 
                    class_info.get('class_name', 'Unknown'), 
                    llm=llm
                )
            
            # Store validation result for reporting
            if not hasattr(class_info, 'validation_result'):
                class_info['validation_result'] = validation_result
                
        except Exception as e:
            print(f"⚠️ LLM validation failed for {class_info.get('class_name', 'Unknown')}: {str(e)}")
            class_info['validation_result'] = {
                'validation_status': 'ERROR',
                'overall_assessment': f"Validation failed: {str(e)}",
                'llm_validation': False
            }
        
        return content.strip()
        
    except Exception as e:
        return f"Error generating enhanced JUnit test: {str(e)}"



def debug_directory_structure(extract_dir: str):
    """Debug function to show complete directory structure with file type identification"""
    print(f"\n🔍 === COMPLETE DIRECTORY STRUCTURE DEBUG ===")
    print(f"🔍 Root directory: {extract_dir}")
    
    if not os.path.exists(extract_dir):
        print(f"❌ Directory does not exist!")
        return
    
    # Find project root
    project_root = find_project_root(extract_dir)
    print(f"🔍 Detected project root: {project_root}")
    
    java_files = []
    swagger_files = []
    test_data_files = []
    config_files = []
    other_files = []
    
    for root, dirs, files in os.walk(extract_dir):
        level = root.replace(extract_dir, '').count(os.sep)
        indent = ' ' * 2 * level
        print(f"{indent}📁 {os.path.basename(root)}/")
        subindent = ' ' * 2 * (level + 1)
        
        for file in files:
            file_path = os.path.join(root, file)
            relative_path = os.path.relpath(file_path, extract_dir)
            file_size = os.path.getsize(file_path)
            
            # Classify files based on project root
            relative_to_project = os.path.relpath(file_path, project_root) if project_root != extract_dir else relative_path
            
            if file.endswith('.java'):
                java_files.append(relative_path)
                file_type = "☕ JAVA"
            elif 'swagger' in relative_to_project and file.lower().endswith(('.json', '.yml', '.yaml')):
                swagger_files.append(relative_path)
                file_type = "📋 SWAGGER"
            elif ('test-data' in relative_to_project or 'src/test/resources' in relative_to_project) and not file.endswith('.java'):
                test_data_files.append(relative_path)
                file_type = "📊 TEST-DATA"
            elif ('src/main/resources' in relative_to_project or 'src/test/resources' in relative_to_project) and 'application' in file:
                config_files.append(relative_path)
                file_type = "⚙️ CONFIG"
            else:
                other_files.append(relative_path)
                file_type = "📄 OTHER"
            
            print(f"{subindent}{file_type} {file} ({file_size} bytes)")
    
    print(f"\n🔍 === FILE CLASSIFICATION SUMMARY ===")
    print(f"🔍 Project root detected: {project_root}")
    print(f"☕ Java files: {len(java_files)}")
    print(f"📋 Swagger files: {len(swagger_files)}")
    print(f"📊 Test data files: {len(test_data_files)}")
    print(f"⚙️ Config files: {len(config_files)}")
    print(f"📄 Other files: {len(other_files)}")
    
    print(f"\n🔍 Swagger files found:")
    for f in swagger_files:
        print(f"  • {f}")
    
    print(f"\n🔍 Test data files found:")
    for f in test_data_files:
        print(f"  • {f}")
    
    print("🔍 === END DIRECTORY STRUCTURE ===\n")
