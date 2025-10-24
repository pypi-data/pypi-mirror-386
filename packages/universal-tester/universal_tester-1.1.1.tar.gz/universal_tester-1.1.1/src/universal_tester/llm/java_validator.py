#!/usr/bin/env python3
"""
LLM-based Java import and compilation validation system
"""
import os
import re
from typing import List, Dict, Any, Optional
from langchain.schema import HumanMessage, SystemMessage
import asyncio
from dotenv import load_dotenv
from universal_tester.llm.factory import LLMFactory

# Load environment variables from .env file
load_dotenv()

class LLMJavaValidator:
    """LLM-powered Java code validation for imports and compilation issues"""
    
    def __init__(self, llm=None):
        self.llm = llm
    
    def get_llm(self):
        """Get LLM instance"""
        if self.llm:
            return self.llm
        
        self.llm = LLMFactory.create_llm(
            temperature=0.1,  # Low temperature for precise validation
            request_timeout=int(os.getenv("OPENAI_REQUEST_TIMEOUT", "30")),
            max_retries=int(os.getenv("OPENAI_MAX_RETRIES", "2")),
            streaming=False
        )
        return self.llm
    
    async def validate_java_imports_and_compilation(self, java_code: str) -> Dict[str, Any]:
        """Validate Java code for import issues and compilation errors using LLM"""
        
        system_prompt = """You are an expert Java compiler and import validator. Your task is to analyze Java code and identify:

1. **IMPORT ISSUES:**
   - Missing imports for classes/annotations used in the code
   - Unused imports that can be removed
   - Incorrect import statements
   - Conflicting imports (same class name from different packages)

2. **COMPILATION ERRORS:**
   - Syntax errors
   - Missing dependencies
   - Incorrect annotations usage
   - Method signature issues
   - Type mismatches
   - Missing method implementations

3. **BEST PRACTICES:**
   - Static import recommendations
   - Import organization suggestions
   - Dependency management advice

**Response Format:**
```json
{
  "validation_status": "PASS|FAIL|WARNING",
  "critical_issues": [
    {
      "type": "MISSING_IMPORT|UNUSED_IMPORT|SYNTAX_ERROR|TYPE_MISMATCH|OTHER",
      "severity": "CRITICAL|WARNING|INFO",
      "line_number": 0,
      "message": "Description of the issue",
      "suggestion": "How to fix it",
      "code_snippet": "Relevant code causing the issue"
    }
  ],
  "missing_imports": [
    {
      "class_name": "ClassName",
      "suggested_import": "full.package.ClassName",
      "reason": "Used in code but not imported",
      "line_usage": 42
    }
  ],
  "unused_imports": [
    {
      "import_statement": "import full.package.UnusedClass;",
      "line_number": 5,
      "reason": "Imported but never used"
    }
  ],
  "compilation_errors": [
    {
      "error_type": "SYNTAX|TYPE|METHOD|ANNOTATION",
      "line_number": 0,
      "message": "Error description",
      "suggestion": "How to fix"
    }
  ],
  "recommendations": [
    {
      "type": "STATIC_IMPORT|ORGANIZATION|DEPENDENCY",
      "message": "Recommendation description",
      "example": "Example code if applicable"
    }
  ],
  "overall_assessment": "Summary of the code quality and compilation readiness"
}
```

**Important Guidelines:**
- Focus on actual compilation issues, not style preferences
- Be specific about line numbers when possible
- Provide concrete import suggestions with full package names
- Consider common Java testing frameworks (JUnit 5, Mockito, AssertJ)
- Identify Spring Framework annotation usage
- Check for servlet API usage
- Validate reflection API usage
- Only report real issues, not potential ones"""

        user_prompt = f"""Please validate the following Java code for import issues and compilation errors:

```java
{java_code}
```

Analyze this code thoroughly and provide a comprehensive validation report focusing on:
1. Missing imports for all classes, annotations, and utilities used
2. Unused imports that should be removed
3. Compilation errors that would prevent the code from building
4. Best practice recommendations for imports and dependencies

Pay special attention to:
- JUnit 5 annotations (@Test, @BeforeEach, @Mock, @InjectMocks)
- Mockito framework usage
- AssertJ assertions
- Spring Framework annotations
- Servlet API classes
- Java reflection APIs
- Collection framework usage
- Stream API usage
- Exception handling

Return a valid JSON response with detailed analysis."""

        try:
            llm = self.get_llm()
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = await llm.ainvoke(messages)
            
            # Try to parse JSON response
            import json
            try:
                # Clean up response content
                content = response.content.strip()
                if content.startswith('```json'):
                    content = content.replace('```json', '').replace('```', '').strip()
                elif content.startswith('```'):
                    content = content.replace('```', '').strip()
                
                validation_result = json.loads(content)
                validation_result['llm_validation'] = True
                validation_result['validation_timestamp'] = __import__('datetime').datetime.now().isoformat()
                
                return validation_result
                
            except json.JSONDecodeError as e:
                # Fallback: parse response manually
                return {
                    'validation_status': 'WARNING',
                    'critical_issues': [],
                    'missing_imports': [],
                    'unused_imports': [],
                    'compilation_errors': [],
                    'recommendations': [],
                    'overall_assessment': f"LLM validation response could not be parsed as JSON: {str(e)}",
                    'raw_response': response.content,
                    'llm_validation': True,
                    'validation_timestamp': __import__('datetime').datetime.now().isoformat()
                }
                
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
                'overall_assessment': f"Validation failed due to error: {str(e)}",
                'llm_validation': False,
                'validation_timestamp': __import__('datetime').datetime.now().isoformat()
            }
    
    async def validate_setter_type_safety(self, java_code: str) -> Dict[str, Any]:
        """Specifically validate setter method calls for type safety issues"""
        
        system_prompt = """You are a Java type safety expert. Analyze the provided test code for TYPE MISMATCH ERRORS, specifically:

🚨 **CRITICAL TYPE SAFETY ISSUES TO DETECT:**

1. **STRING vs LIST<STRING> MISMATCHES:**
   - setTransactionType("SALE") ← WRONG if method expects List<String>
   - setTransactionType(Arrays.asList("SALE")) ← CORRECT
   - setItems("item") ← WRONG if method expects List<String>
   - setItems(List.of("item")) ← CORRECT

2. **REFLECTION METHOD SIGNATURE MISMATCHES:**
   - getDeclaredMethod("method", String.class) ← Check if method actually takes String
   - getDeclaredMethod("method", List.class) ← Check if method actually takes List

3. **MOCK PARAMETER TYPE MISMATCHES:**
   - when(mock.method(anyString())) ← For String parameters
   - when(mock.method(anyList())) ← For List parameters

**ANALYSIS REQUIREMENTS:**
- Identify exact line numbers with type mismatches
- Provide specific fixes for each issue
- Focus on setter methods and their expected parameter types
- Check reflection calls for correct parameter types

Return JSON with structure:
{
  "type_safety_status": "PASS|ISSUES_FOUND",
  "type_mismatches": [
    {
      "line_number": 123,
      "method_call": "loggerContext.setTransactionType(\"SALE\")",
      "issue": "String passed to method expecting List<String>",
      "fix": "loggerContext.setTransactionType(Arrays.asList(\"SALE\"))",
      "required_import": "java.util.Arrays"
    }
  ],
  "reflection_issues": [
    {
      "line_number": 456,
      "method_call": "getDeclaredMethod(\"updateMethod\", String.class)",
      "issue": "Parameter type mismatch in reflection call",
      "fix": "getDeclaredMethod(\"updateMethod\", List.class)"
    }
  ],
  "mock_issues": [
    {
      "line_number": 789,
      "method_call": "when(mock.method(anyString()))",
      "issue": "Mock parameter type doesn't match actual method signature",
      "fix": "when(mock.method(anyList()))"
    }
  ]
}"""

        user_prompt = f"""
Analyze this Java test code for type safety issues:

```java
{java_code}
```

Focus on:
1. Setter method calls with wrong parameter types
2. Reflection getDeclaredMethod calls with incorrect parameter types  
3. Mock method calls with mismatched parameter types
4. String vs List<String> conversion issues

Provide detailed analysis with line numbers and specific fixes.
"""

        try:
            llm = self.get_llm()
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = await llm.ainvoke(messages)
            
            # Parse the LLM response
            response_text = response.content.strip()
            
            # Extract JSON from response if wrapped in markdown
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                json_str = response_text[start:end].strip()
            elif "{" in response_text and "}" in response_text:
                start = response_text.find("{")
                end = response_text.rfind("}") + 1
                json_str = response_text[start:end]
            else:
                json_str = response_text
            
            try:
                import json
                result = json.loads(json_str)
                
                # Ensure required fields exist
                if 'type_safety_status' not in result:
                    result['type_safety_status'] = 'ISSUES_FOUND' if (
                        result.get('type_mismatches') or 
                        result.get('reflection_issues') or 
                        result.get('mock_issues')
                    ) else 'PASS'
                
                return result
                
            except json.JSONDecodeError:
                # Fallback parsing from text response
                return self._parse_type_safety_response(response_text)
                
        except Exception as e:
            return {
                'type_safety_status': 'ERROR',
                'error': f"Type safety validation failed: {str(e)}",
                'type_mismatches': [],
                'reflection_issues': [],
                'mock_issues': []
            }

    def _parse_type_safety_response(self, response_text: str) -> Dict[str, Any]:
        """Fallback parser for type safety response"""
        result = {
            'type_safety_status': 'PASS',
            'type_mismatches': [],
            'reflection_issues': [],
            'mock_issues': []
        }
        
        # Look for common patterns in the response
        lines = response_text.split('\n')
        current_issue = {}
        
        for line in lines:
            line = line.strip()
            
            # Look for type mismatch patterns
            if 'setTransactionType' in line and 'String' in line and 'List' in line:
                result['type_mismatches'].append({
                    'line_number': 0,
                    'method_call': 'setTransactionType',
                    'issue': 'String passed to method expecting List<String>',
                    'fix': 'Use Arrays.asList() or List.of()',
                    'required_import': 'java.util.Arrays'
                })
                result['type_safety_status'] = 'ISSUES_FOUND'
            
            # Look for reflection issues
            if 'getDeclaredMethod' in line and ('String.class' in line or 'List.class' in line):
                result['reflection_issues'].append({
                    'line_number': 0,
                    'method_call': line,
                    'issue': 'Potential parameter type mismatch in reflection call',
                    'fix': 'Verify parameter types match actual method signature'
                })
                result['type_safety_status'] = 'ISSUES_FOUND'
        
        return result

    def format_validation_report(self, validation_result: Dict[str, Any]) -> str:
        """Format validation result into readable report"""
        
        status = validation_result.get('validation_status', 'UNKNOWN')
        
        # Status emoji
        status_emoji = {
            'PASS': '✅',
            'WARNING': '⚠️',
            'FAIL': '❌',
            'ERROR': '🔥'
        }.get(status, '❓')
        
        report = f"""
🔍 **LLM JAVA VALIDATION REPORT** {status_emoji}
{'=' * 60}

**Status:** {status_emoji} {status}
**Timestamp:** {validation_result.get('validation_timestamp', 'N/A')}

"""
        
        # Critical Issues
        critical_issues = validation_result.get('critical_issues', [])
        if critical_issues:
            report += f"🚨 **CRITICAL ISSUES ({len(critical_issues)}):**\n"
            for issue in critical_issues:
                severity_emoji = {'CRITICAL': '🚨', 'WARNING': '⚠️', 'INFO': 'ℹ️'}.get(issue.get('severity', 'INFO'), 'ℹ️')
                report += f"   {severity_emoji} **{issue.get('type', 'UNKNOWN')}** (Line {issue.get('line_number', '?')})\n"
                report += f"      • {issue.get('message', 'No message')}\n"
                if issue.get('suggestion'):
                    report += f"      • **Fix:** {issue.get('suggestion')}\n"
                if issue.get('code_snippet'):
                    report += f"      • **Code:** `{issue.get('code_snippet')}`\n"
                report += "\n"
        
        # Missing Imports
        missing_imports = validation_result.get('missing_imports', [])
        if missing_imports:
            report += f"📦 **MISSING IMPORTS ({len(missing_imports)}):**\n"
            for imp in missing_imports:
                report += f"   • `{imp.get('suggested_import', 'Unknown')}` - {imp.get('reason', 'No reason')}\n"
                if imp.get('line_usage'):
                    report += f"     Used at line {imp.get('line_usage')}\n"
            report += "\n"
        
        # Unused Imports
        unused_imports = validation_result.get('unused_imports', [])
        if unused_imports:
            report += f"🗑️ **UNUSED IMPORTS ({len(unused_imports)}):**\n"
            for imp in unused_imports:
                report += f"   • `{imp.get('import_statement', 'Unknown')}` (Line {imp.get('line_number', '?')})\n"
                report += f"     {imp.get('reason', 'No reason')}\n"
            report += "\n"
        
        # Compilation Errors
        compilation_errors = validation_result.get('compilation_errors', [])
        if compilation_errors:
            report += f"⚠️ **COMPILATION ERRORS ({len(compilation_errors)}):**\n"
            for error in compilation_errors:
                report += f"   • **{error.get('error_type', 'UNKNOWN')}** (Line {error.get('line_number', '?')})\n"
                report += f"     {error.get('message', 'No message')}\n"
                if error.get('suggestion'):
                    report += f"     **Fix:** {error.get('suggestion')}\n"
            report += "\n"
        
        # Recommendations
        recommendations = validation_result.get('recommendations', [])
        if recommendations:
            report += f"💡 **RECOMMENDATIONS ({len(recommendations)}):**\n"
            for rec in recommendations:
                report += f"   • **{rec.get('type', 'GENERAL')}:** {rec.get('message', 'No message')}\n"
                if rec.get('example'):
                    report += f"     **Example:** `{rec.get('example')}`\n"
            report += "\n"
        
        # Overall Assessment
        overall = validation_result.get('overall_assessment', 'No assessment available')
        report += f"📋 **OVERALL ASSESSMENT:**\n{overall}\n"
        
        # No issues found
        if not critical_issues and not missing_imports and not unused_imports and not compilation_errors:
            report += f"\n🎉 **EXCELLENT!** No critical issues found. Code appears to be compilation-ready!\n"
        
        return report

async def validate_java_file_with_llm(file_path: str, llm=None) -> Dict[str, Any]:
    """Validate a Java file using LLM and return detailed report"""
    
    if not os.path.exists(file_path):
        return {
            'validation_status': 'ERROR',
            'critical_issues': [{
                'type': 'FILE_NOT_FOUND',
                'severity': 'CRITICAL',
                'line_number': 0,
                'message': f"File not found: {file_path}",
                'suggestion': "Check file path and ensure file exists",
                'code_snippet': ''
            }],
            'missing_imports': [],
            'unused_imports': [],
            'compilation_errors': [],
            'recommendations': [],
            'overall_assessment': f"File not found: {file_path}",
            'llm_validation': False
        }
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            java_code = f.read()
    except Exception as e:
        return {
            'validation_status': 'ERROR',
            'critical_issues': [{
                'type': 'FILE_READ_ERROR',
                'severity': 'CRITICAL',
                'line_number': 0,
                'message': f"Could not read file: {str(e)}",
                'suggestion': "Check file permissions and encoding",
                'code_snippet': ''
            }],
            'missing_imports': [],
            'unused_imports': [],
            'compilation_errors': [],
            'recommendations': [],
            'overall_assessment': f"Could not read file: {str(e)}",
            'llm_validation': False
        }
    
    validator = LLMJavaValidator(llm=llm)
    return await validator.validate_java_imports_and_compilation(java_code)

if __name__ == "__main__":
    # This module is designed to be imported and used by app_langchain_v3_5.py
    # For testing, create a simple test case
    print("LLM Java Validator module loaded successfully!")
    print("This module provides LLM-powered Java code validation.")
    print("Import and use LLMJavaValidator class or validate_java_file_with_llm function.")
