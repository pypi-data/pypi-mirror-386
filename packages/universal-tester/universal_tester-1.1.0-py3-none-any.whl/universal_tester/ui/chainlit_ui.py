# -*- coding: utf-8 -*-
"""
Chainlit UI Module for Universal Tester
Handles all Chainlit-specific UI interactions and event handlers
"""

import chainlit as cl
import os
import asyncio
from typing import Optional

# Import the core functionality from the main module
from universal_tester import (
    get_app_info,
    format_version_info, 
    get_short_version_info,
    process_java_zip_enhanced_core,
)
from universal_tester.prompts.prompt_builder import PromptBuilder

# Import LLM health check
from universal_tester.llm.health_check import format_llm_status, get_llm_status_dict

# Import UI messages
from universal_tester.prompts.ui_messages import (
    WELCOME_MESSAGE, 
    HELP_MESSAGE, 
    FILE_UPLOAD_MESSAGE,
    UPLOAD_NEW_MESSAGE,
    DEFAULT_RESPONSE_MESSAGE
)


class ChainlitUI:
    """Handles all Chainlit UI interactions"""
    
    @staticmethod
    @cl.on_chat_start
    async def start():
        """Initialize the chat session with enhanced file detection"""
        # Show version information first
        version_info = format_version_info()
        await cl.Message(content=version_info).send()
        
        # Show LLM connection status
        llm_status = format_llm_status()
        await cl.Message(content=llm_status).send()
        
        # Then show the welcome message
        await cl.Message(content=WELCOME_MESSAGE).send()
        
        # Show custom prompt configuration status
        prompt_status = PromptBuilder.get_custom_prompt_status()
        if prompt_status["custom_system_enabled"] or prompt_status["custom_addition_enabled"]:
            status_message = "🎯 **Custom Prompt Configuration Active:**\n\n"
            
            if prompt_status["custom_system_enabled"]:
                if prompt_status["has_custom_system"]:
                    status_message += f"✅ **Custom System Prompt:** Enabled\n"
                    status_message += f"   Preview: `{prompt_status['custom_system_preview']}`\n\n"
                else:
                    status_message += f"⚠️ **Custom System Prompt:** Enabled but empty\n\n"
            
            if prompt_status["custom_addition_enabled"]:
                if prompt_status["has_custom_addition"]:
                    status_message += f"✅ **Custom User Instructions:** Enabled\n"
                    status_message += f"   Preview: `{prompt_status['custom_addition_preview']}`\n\n"
                else:
                    status_message += f"⚠️ **Custom User Instructions:** Enabled but empty\n\n"
            
            status_message += "💡 **Tip:** Edit your `.env` file to customize these settings!"
            
            await cl.Message(content=status_message).send()
        
        # Wait for file upload
        files = None
        while files is None:
            files = await cl.AskFileMessage(
                content=FILE_UPLOAD_MESSAGE,
                accept=["application/zip", ".zip"],
                max_size_mb=100,
                timeout=300,
            ).send()

        file = files[0]
        
        # Validate file type
        if not file.name.lower().endswith(".zip"):
            await cl.Message(content="❌ Please upload a valid ZIP file containing Java source code.").send()
            return

        # Process with enhanced file integration
        version_header = get_short_version_info()
        await cl.Message(content=f"{version_header}\n\n🔄 **Processing your Java project with file integration:** `{file.name}`\n\nScanning for enhancement files...").send()
        
        # Create file element and process
        await ChainlitUI._process_uploaded_file(file)

    @staticmethod
    @cl.on_message
    async def main(message: cl.Message):
        """Handle chat messages with enhanced options"""
        if message.content and message.content.lower().strip() in ['use sample', 'sample', 'test sample']:
            await ChainlitUI._process_sample_project()
            return
        elif message.content and message.content.lower().strip() in ['upload new', 'new file', 'upload', 'new']:
            await cl.Message(content=UPLOAD_NEW_MESSAGE).send()
            return
        elif message.content and message.content.lower().strip() in ['help', '?']:
            await cl.Message(content=HELP_MESSAGE).send()
            return
        elif message.content and message.content.lower().strip() in ['version', 'info', 'about', 'v']:
            await ChainlitUI._show_version_info()
            return
        elif message.content and message.content.lower().strip() in ['custom prompts', 'custom prompt', 'prompts']:
            await ChainlitUI._show_custom_prompt_status()
            return
        
        # Default response
        await cl.Message(content=DEFAULT_RESPONSE_MESSAGE).send()

    @staticmethod
    async def _process_uploaded_file(file):
        """Process uploaded file through the UI"""
        # Create file element
        class FileElement:
            def __init__(self, file_path, file_name):
                self.name = file_name
                with open(file_path, 'rb') as f:
                    self.content = f.read()
                self.mime = "application/zip"
        
        file_element = FileElement(file.path, file.name)
        result = await process_java_zip_enhanced_core(
            file_element, 
            ChainlitUI._send_message,
            custom_output_dir=None
        )
        
        if result:
            # Create comprehensive summary with validation results
            enhanced_summary = f"""
✅ **Enhanced JUnit Test Generation Complete with LLM Validation!**

📁 **Output Location:**
- **File:** `{result['zip_filename']}`
- **Full path:** `{result['zip_path']}`
- **Note:** Old output files are automatically cleaned up (keeping last 10 files)

📊 **Test Generation Summary:**
- **Classes processed:** {len(result['generated_tests'])}
- **Test files generated:** {len(result['generated_tests'])}
- **Total methods tested:** {sum(test['methods_tested'] for test in result['generated_tests'])}

🔍 **LLM Validation Results:**"""
            
            # Add validation summary
            validation_stats = {'PASS': 0, 'WARNING': 0, 'FAIL': 0, 'ERROR': 0}
            for test in result['generated_tests']:
                validation = test.get('validation_result', {})
                status = validation.get('validation_status', 'ERROR')
                validation_stats[status] = validation_stats.get(status, 0) + 1
            
            enhanced_summary += f"""
- **✅ PASS:** {validation_stats['PASS']} tests
- **⚠️ WARNING:** {validation_stats['WARNING']} tests  
- **❌ FAIL:** {validation_stats['FAIL']} tests
- **🔥 ERROR:** {validation_stats['ERROR']} tests

🚀 **Enhanced Features Applied:**
- ✅ Real schema validation testing (user-provided Swagger/OpenAPI)
- ✅ Realistic test data scenarios (user-provided samples)
- ✅ Configuration property integration
- ✅ Framework-specific patterns
- ✅ **LLM-powered import & compilation validation**
- ✅ **Automated import fixing**
- ✅ Production-ready test code

📋 **Generated Test Classes:**
"""
            
            for test in result['generated_tests']:
                enhancements = []
                if test['has_swagger']:
                    enhancements.append("Schema validation")
                if test['has_test_data']:
                    enhancements.append("Real data testing")
                if test['has_config']:
                    enhancements.append("Config integration")
               
                if test.get('frameworks'):
                    enhancements.append(f"{'/'.join(test['frameworks'])} patterns")
                
                # Add validation status
                validation = test.get('validation_result', {})
                validation_status = validation.get('validation_status', 'ERROR')
                status_emoji = {'PASS': '✅', 'WARNING': '⚠️', 'FAIL': '❌', 'ERROR': '🔥'}.get(validation_status, '❓')
                
                enhancement_info = f" [{', '.join(enhancements)}]" if enhancements else ""
                enhanced_summary += f"\n• `{test['original_class']}Test.java` ({test['methods_tested']} methods){enhancement_info} {status_emoji}"
            
            # Add validation issues if any
            if result['validation_issues']:
                enhanced_summary += "\n\n❗ **Validation Issues Found:**\n"
                for issue in result['validation_issues']:
                    class_name = issue['class']
                    file_name = os.path.basename(issue['file'])
                    issue_data = issue['issue']
                    msg = issue_data.get('message', '')
                    suggestion = issue_data.get('suggestion', '')
                    line_number = issue_data.get('line_number', '')
                    code_snippet = issue_data.get('code_snippet', '')
                    enhanced_summary += f"- `{class_name}Test.java` (File: {file_name}, Line: {line_number})\n  - Issue: {msg}\n  - Suggestion: {suggestion}\n"
                    if code_snippet:
                        enhanced_summary += f"  - Code: `{code_snippet}`\n"
            
            enhanced_summary += f"""

📁 **Download your production-ready JUnit test suite below!**

**🎯 Next Steps:**
1. Extract the ZIP file to your test directory
2. Review the generated tests for domain-specific patterns
3. **Check validation reports** for any import/compilation issues
4. Run the tests to validate your implementation
5. Customize test data as needed for your specific use cases

**💡 Tip:** Tests include LLM-validated imports and compilation checks!
"""
            
            # Create file element for download
            zip_element = cl.File(
                name=result['zip_filename'],
                path=result['zip_path'],
                display="inline"
            )
            
            await cl.Message(
                content=enhanced_summary,
                elements=[zip_element]
            ).send()

    @staticmethod
    async def _process_sample_project():
        """Process the sample Java project for testing"""
        sample_zip_path = "sample-java-project.zip"
        
        if not os.path.exists(sample_zip_path):
            await cl.Message(
                content="❌ Sample project not found! The file 'sample-java-project.zip' is missing.\n\n"
                        "Please upload your own Java project ZIP file using the attachment button 📎"
            ).send()
            return
        
        # Read the sample ZIP file
        with open(sample_zip_path, "rb") as f:
            zip_content = f.read()
        
        # Create a mock element for processing
        class MockElement:
            def __init__(self, name, content):
                self.name = name
                self.content = content
                self.mime = "application/zip"
        
        mock_element = MockElement("sample-java-project.zip", zip_content)
        
        await cl.Message(
            content="🔄 Processing sample Java project: **sample-java-project.zip**"
        ).send()
        
        result = await process_java_zip_enhanced_core(
            mock_element, 
            ChainlitUI._send_message,
            custom_output_dir=None
        )
        
        if result:
            # Create file element for download
            zip_element = cl.File(
                name=result['zip_filename'],
                path=result['zip_path'],
                display="inline"
            )
            
            await cl.Message(
                content=f"✅ **Sample project processed successfully!**\n\n📁 **Download:** `{result['zip_filename']}`",
                elements=[zip_element]
            ).send()

    @staticmethod
    async def _show_version_info():
        """Show version and system information"""
        version_info = format_version_info()
        app_info = get_app_info()
        
        detailed_info = version_info + f"""
🔧 **Detailed System Information:**
• Chainlit Version: {app_info['chainlit_version']}
• Author: {app_info['author']}
• Description: {app_info['description']}

💡 **Available Commands:**
• `help` or `?` - Show help message
• `version` or `info` - Show this information
• `custom prompts` - View custom prompt configuration
• `upload new` - Upload a new file
• `sample` - Use sample project

"""
        await cl.Message(content=detailed_info).send()

    @staticmethod
    async def _show_custom_prompt_status():
        """Show custom prompt configuration status"""
        prompt_status = PromptBuilder.get_custom_prompt_status()
        
        status_message = "🎯 **Custom Prompt Configuration Status:**\n\n"
        
        # System prompt status
        if prompt_status["custom_system_enabled"]:
            if prompt_status["has_custom_system"]:
                status_message += f"✅ **Custom System Prompt:** Active\n"
                status_message += f"   Preview: `{prompt_status['custom_system_preview']}`\n\n"
            else:
                status_message += f"⚠️ **Custom System Prompt:** Enabled but empty (check .env file)\n\n"
        else:
            status_message += f"❌ **Custom System Prompt:** Disabled (using default)\n\n"
        
        # User addition status
        if prompt_status["custom_addition_enabled"]:
            if prompt_status["has_custom_addition"]:
                status_message += f"✅ **Custom User Instructions:** Active\n"
                status_message += f"   Preview: `{prompt_status['custom_addition_preview']}`\n\n"
            else:
                status_message += f"⚠️ **Custom User Instructions:** Enabled but empty (check .env file)\n\n"
        else:
            status_message += f"❌ **Custom User Instructions:** Disabled (using default)\n\n"
        
        # Configuration instructions
        if not prompt_status["custom_system_enabled"] and not prompt_status["custom_addition_enabled"]:
            status_message += "💡 **To enable custom prompts:**\n"
            status_message += "1. Edit your `.env` file\n"
            status_message += "2. Set `USE_CUSTOM_SYSTEM_PROMPT=true` and/or `USE_CUSTOM_USER_PROMPT_ADDITION=true`\n"
            status_message += "3. Add your custom prompt text\n"
            status_message += "4. Restart the application\n\n"
        
        status_message += "📖 **For detailed examples and usage guide, see:** `CUSTOM_PROMPTS.md`"
        
        await cl.Message(content=status_message).send()

    @staticmethod
    async def _send_message(content: str):
        """Helper method to send messages through Chainlit"""
        await cl.Message(content=content).send()


# Initialize the UI when this module is imported by chainlit
# The decorators will be automatically registered with chainlit
ui = ChainlitUI()
