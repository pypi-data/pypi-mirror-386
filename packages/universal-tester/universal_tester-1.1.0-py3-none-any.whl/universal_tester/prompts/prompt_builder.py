"""Prompt building utilities with multi-language support"""

import os
from typing import Dict, Any, List
from .test_generation_prompts import ENHANCED_JUNIT_WITH_FILES_PROMPT, STANDARD_JUNIT_PROMPT
from .kotlin_test_generation_prompts import KOTLIN_JUNIT_TEST_PROMPT
from .system_prompts import JUNIT_TEST_SYSTEM_PROMPT, ENHANCED_SYSTEM_PROMPT

def _is_private_method_testing_excluded() -> bool:
    """Check if private method test generation should be excluded"""
    try:
        exclude_setting = os.getenv("EXCLUDE_PRIVATE_METHOD_TESTS", "false").lower().strip()
        return exclude_setting in ['true', '1', 'yes', 'on', 'enabled']
    except Exception:
        return False

class PromptBuilder:
    """Utility class for building prompts with dynamic content and language support"""
    
    @staticmethod
    def build_enhanced_prompt_with_files(
        analysis: Dict[str, Any],
        strategy: Dict[str, Any],
        class_info: Dict[str, Any],
        file_context: str = "",
        config_context: str = "",
        language: str = "java"
    ) -> str:
        """Build enhanced prompt with file integration and language support"""
        
        methods_list = "\n".join([
            f"• {m.get('name', '')}: {m.get('return_type', '')} - {m.get('visibility', '')}" 
            for m in analysis.get('methods', [])
        ])
        
        # Handle private methods based on exclusion setting
        exclude_private_methods = _is_private_method_testing_excluded()
        if exclude_private_methods:
            private_methods_list = "Private method testing excluded via EXCLUDE_PRIVATE_METHOD_TESTS environment variable"
        else:
            private_methods_list = "\n".join([
                f"• {m.get('name', '')}: {m.get('return_type', '')} - PRIVATE (use reflection if complex)" 
                for m in analysis.get('private_methods', [])
            ]) if analysis.get('private_methods') else "None found"
        
        # Add constructor information for proper parameter usage
        constructors_list = "\n".join([
            f"• {c.get('signature', '')}" 
            for c in analysis.get('constructors', [])
        ]) if analysis.get('constructors') else "Default constructor only"
        
        # Use dynamic import detection system - NO hardcoded imports
        detected_imports = analysis.get('detected_imports', [])
        contextual_imports = analysis.get('contextual_imports', [])
        project_imports = analysis.get('project_specific_imports', [])
        all_imports = analysis.get('all_test_imports', [])
        import_metadata = analysis.get('import_metadata', {})
        
        # Build dynamic import guidance
        import_guidance = ""
        if import_metadata:
            import_guidance += f"🔍 **DYNAMIC IMPORT DETECTION RESULTS:**\n"
            import_guidance += f"• Total imports automatically detected: {import_metadata.get('total_detected_imports', 0)}\n"
            import_guidance += f"• Pattern matching rules applied: {import_metadata.get('rules_matched', 0)}\n"
            import_guidance += f"• Categories detected: {', '.join(import_metadata.get('categories_detected', []))}\n"
            import_guidance += f"• Detection confidence: {import_metadata.get('detection_confidence', 0):.1f}%\n\n"
        
        # Show dynamically detected imports
        if detected_imports:
            import_guidance += "🎯 **DYNAMICALLY DETECTED IMPORTS (MUST INCLUDE ALL):**\n"
            for imp in detected_imports:
                import_guidance += f"• {imp}\n"
            import_guidance += "\n"
        
        # Show contextual imports
        if contextual_imports:
            unique_contextual = [imp for imp in contextual_imports if imp not in detected_imports]
            if unique_contextual:
                import_guidance += "🏗️ **CONTEXTUAL IMPORTS (Class-type specific):**\n"
                for imp in unique_contextual:
                    import_guidance += f"• {imp}\n"
                import_guidance += "\n"
        
        # Show project-specific imports
        if project_imports:
            import_guidance += "📦 **PROJECT-SPECIFIC IMPORTS (MUST INCLUDE ALL):**\n"
            for imp in project_imports:
                import_guidance += f"• {imp}\n"
            import_guidance += "\n"
        
        if not import_guidance:
            if language == "kotlin":
                import_guidance = "Standard Kotlin test imports with dynamically detected dependencies"
            else:
                import_guidance = "Standard JUnit imports with dynamically detected dependencies"
        
        # Add method validation guidance
        available_getters = analysis.get('available_getters', [])
        available_setters = analysis.get('available_setters', [])
        method_validation = f"""
Available Getters: {', '.join(available_getters) if available_getters else 'None detected'}
Available Setters: {', '.join(available_setters) if available_setters else 'None detected'}
CRITICAL: Only use methods that actually exist in the class!"""
        
        # Add method strategies for enhanced prompt
        method_strategies = "\n".join([f"• {s}" for s in strategy.get('method_strategies', [])])
        
        # Select the appropriate prompt template based on language
        if language == "kotlin":
            prompt_template = KOTLIN_JUNIT_TEST_PROMPT
        else:
            prompt_template = ENHANCED_JUNIT_WITH_FILES_PROMPT
        
        # Determine class type for Kotlin (required by Kotlin template)
        class_type = analysis.get('class_type', 'class')  # Default to 'class' if not specified
        if not class_type or class_type == 'Unknown':
            # Try to infer from class name patterns
            class_name = analysis.get('class_name', '')
            if 'Service' in class_name:
                class_type = 'service class'
            elif 'Controller' in class_name:
                class_type = 'controller class'
            elif 'Repository' in class_name:
                class_type = 'repository class'
            elif 'Config' in class_name or 'Configuration' in class_name:
                class_type = 'configuration class'
            else:
                class_type = 'class'
        
        # Build the enhanced prompt with all required fields
        format_kwargs = {
            'package': analysis.get('package', 'N/A'),
            'class_name': analysis.get('class_name', 'Unknown'),
            'class_type': class_type,
            'frameworks': ', '.join(analysis.get('frameworks', [])) or 'None detected',
            'complexity_score': analysis.get('complexity_score', 0),
            'method_count': len(analysis.get('methods', [])),
            'private_method_count': 0 if exclude_private_methods else len(analysis.get('private_methods', [])),
            'testing_approaches': ', '.join(strategy.get('testing_approaches', [])),
            'complexity_level': strategy.get('complexity_level', 'Low'),
            'mocking_strategy': strategy.get('mocking_strategy', 'Standard'),
            'file_context': file_context,
            'config_context': config_context,
            'methods_list': methods_list,
            'private_methods_list': private_methods_list,
            'constructors_list': constructors_list,
            'import_guidance': import_guidance,
            'method_validation': method_validation,
            'method_strategies': method_strategies,
            'java_content': class_info['content'] if language == "java" else "",
            'kotlin_content': class_info['content'] if language == "kotlin" else ""
        }
        
        # Filter out fields that the template doesn't actually need
        try:
            enhanced_prompt = prompt_template.format(**format_kwargs)
        except KeyError as e:
            # If template is missing a field, provide a default value
            missing_field = str(e).strip("'")
            format_kwargs[missing_field] = f"[{missing_field} not provided]"
            enhanced_prompt = prompt_template.format(**format_kwargs)
        
        # Apply custom user prompt enhancement if configured
        return PromptBuilder.enhance_user_prompt(enhanced_prompt)
    
    @staticmethod
    def build_standard_prompt(
        analysis: Dict[str, Any],
        strategy: Dict[str, Any],
        class_info: Dict[str, Any],
        language: str = "java"
    ) -> str:
        """Build standard enhanced prompt with language support"""
        
        methods_list = "\n".join([
            f"• {m.get('name', '')}: {m.get('return_type', '')} - {m.get('visibility', '')}" 
            for m in analysis.get('methods', [])
        ])
        
        # Handle private methods based on exclusion setting
        exclude_private_methods = _is_private_method_testing_excluded()
        if exclude_private_methods:
            private_methods_list = "Private method testing excluded via EXCLUDE_PRIVATE_METHOD_TESTS environment variable"
        else:
            private_methods_list = "\n".join([
                f"• {m.get('name', '')}: {m.get('return_type', '')} - PRIVATE (use reflection if complex)" 
                for m in analysis.get('private_methods', [])
            ]) if analysis.get('private_methods') else "None found"
        
        # Add constructor information for proper parameter usage
        constructors_list = "\n".join([
            f"• {c.get('signature', '')}" 
            for c in analysis.get('constructors', [])
        ]) if analysis.get('constructors') else "Default constructor only"
        
        # Add enhanced import guidance with detailed detection information
        detected_imports = analysis.get('detected_imports', [])
        contextual_imports = analysis.get('contextual_imports', [])
        project_imports = analysis.get('project_specific_imports', [])
        all_imports = analysis.get('all_test_imports', [])
        import_metadata = analysis.get('import_metadata', {})
        
        import_guidance = ""
        
        # Enhanced import guidance with detection metadata
        if import_metadata:
            import_guidance += f"🔍 **Dynamic Import Detection Results:**\n"
            import_guidance += f"• Total imports detected: {import_metadata.get('total_detected_imports', 0)}\n"
            import_guidance += f"• Pattern rules matched: {import_metadata.get('rules_matched', 0)}\n"
            import_guidance += f"• Categories detected: {', '.join(import_metadata.get('categories_detected', []))}\n"
            import_guidance += f"• Detection confidence: {import_metadata.get('detection_confidence', 0):.1f}%\n\n"
        
        if detected_imports:
            import_guidance += "🎯 **Dynamically Detected Imports (MUST INCLUDE):**\n" + "\n".join([f"• {imp}" for imp in detected_imports[:20]])  # Limit to first 20
            if len(detected_imports) > 20:
                import_guidance += f"\n• ... and {len(detected_imports) - 20} more imports\n"
        
        if contextual_imports:
            unique_contextual = [imp for imp in contextual_imports if imp not in detected_imports]
            if unique_contextual:
                import_guidance += "\n\n🏗️ **Contextual Imports (Class-specific):**\n" + "\n".join([f"• {imp}" for imp in unique_contextual[:10]])
        
        if project_imports:
            import_guidance += "\n\n📦 **Project-Specific Imports (MUST INCLUDE):**\n" + "\n".join([f"• {imp}" for imp in project_imports])
        
        if not import_guidance:
            if language == "kotlin":
                import_guidance = "Standard Kotlin test imports with basic utilities"
            else:
                import_guidance = "Standard JUnit imports with basic Java utilities"
        
        # Add method validation guidance
        available_getters = analysis.get('available_getters', [])
        available_setters = analysis.get('available_setters', [])
        method_validation = f"""
Available Getters: {', '.join(available_getters) if available_getters else 'None detected'}
Available Setters: {', '.join(available_setters) if available_setters else 'None detected'}
CRITICAL: Only use methods that actually exist in the class!"""
        
        method_strategies = "\n".join([f"• {s}" for s in strategy.get('method_strategies', [])])
        edge_cases = "\n".join([f"• {e}" for e in strategy.get('edge_cases', [])])
        framework_patterns = "\n".join([f"• {approach}" for approach in strategy.get('testing_approaches', [])])
        
        # Select the appropriate prompt template based on language
        if language == "kotlin":
            prompt_template = KOTLIN_JUNIT_TEST_PROMPT
        else:
            prompt_template = STANDARD_JUNIT_PROMPT
        
        # Determine class type for Kotlin (required by Kotlin template)
        class_type = analysis.get('class_type', 'class')  # Default to 'class' if not specified
        if not class_type or class_type == 'Unknown':
            # Try to infer from class name patterns
            class_name = analysis.get('class_name', '')
            if 'Service' in class_name:
                class_type = 'service class'
            elif 'Controller' in class_name:
                class_type = 'controller class'
            elif 'Repository' in class_name:
                class_type = 'repository class'
            elif 'Config' in class_name or 'Configuration' in class_name:
                class_type = 'configuration class'
            else:
                class_type = 'class'
        
        # Build the standard prompt
        standard_prompt = prompt_template.format(
            package=analysis.get('package', 'N/A'),
            class_name=analysis.get('class_name', 'Unknown'),
            class_type=class_type,
            frameworks=', '.join(analysis.get('frameworks', [])) or 'None detected',
            complexity_score=analysis.get('complexity_score', 0),
            method_count=len(analysis.get('methods', [])),
            private_method_count=0 if exclude_private_methods else len(analysis.get('private_methods', [])),
            field_count=len(analysis.get('fields', [])),
            testing_approaches=', '.join(strategy.get('testing_approaches', [])),
            complexity_level=strategy.get('complexity_level', 'Low'),
            mocking_strategy=strategy.get('mocking_strategy', 'Standard'),
            methods_list=methods_list,
            private_methods_list=private_methods_list,
            constructors_list=constructors_list,
            import_guidance=import_guidance,
            method_validation=method_validation,
            method_strategies=method_strategies,
            edge_cases=edge_cases,
            framework_patterns=framework_patterns,
            java_content=class_info['content'] if language == "java" else "",
            kotlin_content=class_info['content'] if language == "kotlin" else ""
        )
        
        # Apply custom user prompt enhancement if configured
        return PromptBuilder.enhance_user_prompt(standard_prompt)
    
    @staticmethod
    def get_custom_prompt_status() -> Dict[str, Any]:
        """Get the current status of custom prompt configurations"""
        use_custom_system = os.getenv("USE_CUSTOM_SYSTEM_PROMPT", "false").lower() == "true"
        use_custom_addition = os.getenv("USE_CUSTOM_USER_PROMPT_ADDITION", "false").lower() == "true"
        custom_system = os.getenv("CUSTOM_SYSTEM_PROMPT", "").strip()
        custom_addition = os.getenv("CUSTOM_USER_PROMPT_ADDITION", "").strip()
        
        return {
            "custom_system_enabled": use_custom_system,
            "custom_addition_enabled": use_custom_addition,
            "has_custom_system": bool(custom_system),
            "has_custom_addition": bool(custom_addition),
            "custom_system_preview": custom_system[:100] + "..." if len(custom_system) > 100 else custom_system,
            "custom_addition_preview": custom_addition[:100] + "..." if len(custom_addition) > 100 else custom_addition
        }
    
    @staticmethod
    def get_system_prompt(frameworks: List[str] = None) -> str:
        """Get appropriate system prompt with custom prompt support"""
        # Check if custom system prompt is enabled and provided
        use_custom = os.getenv("USE_CUSTOM_SYSTEM_PROMPT", "false").lower() == "true"
        custom_prompt = os.getenv("CUSTOM_SYSTEM_PROMPT", "").strip()
        
        if use_custom and custom_prompt:
            # Use custom system prompt
            base_prompt = custom_prompt
            if frameworks:
                # Append framework info to custom prompt
                framework_info = f"\n\nFrameworks detected in the project: {', '.join(frameworks)}"
                base_prompt += framework_info
            return base_prompt
        
        # Use default system prompts
        if frameworks:
            return ENHANCED_SYSTEM_PROMPT.format(frameworks=', '.join(frameworks))
        return JUNIT_TEST_SYSTEM_PROMPT
    
    @staticmethod
    def enhance_user_prompt(base_prompt: str) -> str:
        """Enhance user prompt with custom additions if configured"""
        # Check if custom user prompt addition is enabled
        use_custom_addition = os.getenv("USE_CUSTOM_USER_PROMPT_ADDITION", "false").lower() == "true"
        custom_addition = os.getenv("CUSTOM_USER_PROMPT_ADDITION", "").strip()
        
        if use_custom_addition and custom_addition:
            # Add custom instructions to the base prompt
            enhanced_prompt = f"{base_prompt}\n\n🎯 **ADDITIONAL CUSTOM INSTRUCTIONS:**\n{custom_addition}"
            return enhanced_prompt
        
        return base_prompt
    
    @staticmethod
    def build_missing_files_prompt(missing_swagger: bool, missing_test_data: bool) -> str:
        """Build prompt for missing files"""
        from .ui_messages import MISSING_FILES_PROMPT
        
        missing_items = []
        if missing_swagger:
            missing_items.append("📋 **Swagger/OpenAPI files** (in swagger/ folder)")
        if missing_test_data:
            missing_items.append("📊 **Test data files** (request/response traces, Splunk logs)")
        
        return MISSING_FILES_PROMPT.format(
            missing_items="\n".join(missing_items)
        )
