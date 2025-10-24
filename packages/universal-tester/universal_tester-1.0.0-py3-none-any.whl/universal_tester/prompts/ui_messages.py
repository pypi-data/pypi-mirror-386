"""UI messages and user interaction prompts"""

WELCOME_MESSAGE = """
🧪 **Welcome to the Enhanced JUnit Test Generator with File Integration!**

This advanced tool generates production-ready JUnit 5 test cases with optional file integration.

**🚀 Enhanced Features:**
- ✅ **Intelligent Code Analysis** - Deep analysis of class structure and dependencies
- ✅ **Optional Swagger Integration** - Schema validation testing with your OpenAPI files
- ✅ **Test Data Integration** - Realistic testing with your traces and sample data
- ✅ **Configuration Awareness** - Property file integration for real environment testing
- ✅ **Framework Detection** - Specialized patterns for Spring, JPA, Servlet, etc.
- ✅ **Custom Prompts** - Personalize AI behavior via .env file configuration

**⚙️ Custom Prompt Configuration:**
You can customize the AI's behavior by editing the `.env` file:
- `CUSTOM_SYSTEM_PROMPT` - Override default AI instructions
- `CUSTOM_USER_PROMPT_ADDITION` - Add extra requirements to every test generation
- Set `USE_CUSTOM_SYSTEM_PROMPT=true` and `USE_CUSTOM_USER_PROMPT_ADDITION=true` to enable

**📁 Optional File Structure in your ZIP:**
```
your-project.zip
├── src/main/java/...        # Your Java source files (required)
├── swagger/                 # OpenAPI/Swagger files (optional)
│   ├── api-spec.json
│   └── your-file-name.yml
├── test-data/              # Test data files (optional)
│   ├── /
│   ├── traces/
│   ├── request-samples/
│   └── validation-samples/
└── src/main/resources/     # Configuration files (optional)
    └── application.properties
```

**🤔 Don't have these optional files?** No problem! The tool will:
- Generate comprehensive JUnit tests without them
- Use intelligent code analysis and framework detection
- Proceed with standard enhanced testing

**Ready to start?** Upload your Java project ZIP file below! 📁
"""

MISSING_FILES_PROMPT = """
🔍 **Optional Enhancement Files Not Found:**

{missing_items}

**Without these files, the test generation will:**
- ✅ Still generate comprehensive JUnit tests
- ✅ Use intelligent code analysis and strategies
- ✅ Include framework-specific patterns
- ❌ Miss schema validation testing (without Swagger)
- ❌ Miss realistic test data scenarios (without test data)

**📁 To include these files in future uploads:**
- Place Swagger/OpenAPI files in a `swagger/` folder
- Place test data files in folders like `test-data/`, `samples/`, or `traces/`

**🤔 How would you like to proceed?**

**Options:**
1. Type `proceed` - Continue with standard enhanced testing
2. Type `upload new` - Upload a new ZIP with the optional files

What's your choice?
"""

HELP_MESSAGE = """
🆘 **Enhanced Help - Available Commands:**

**📁 File Upload Features:**
- **Standard:** Upload ZIP with just Java files for intelligent testing
- **Enhanced:** Include `swagger/` folder for schema validation testing
- **Advanced:** Add `test-data/` folder for realistic test scenarios

**🎯 Custom Prompt Configuration:**
- Edit `.env` file to customize AI behavior
- `CUSTOM_SYSTEM_PROMPT` - Override default AI instructions
- `CUSTOM_USER_PROMPT_ADDITION` - Add extra requirements
- Set `USE_CUSTOM_SYSTEM_PROMPT=true` to enable system override
- Set `USE_CUSTOM_USER_PROMPT_ADDITION=true` to enable additions
- See `CUSTOM_PROMPTS.md` for detailed examples

**🧪 Sample Project:**
- Type: `use sample` - Test with the sample Java project

**🔄 Upload New File:**
- Type: `upload new` - Instructions for uploading a different file

**❓ Get Help:**
- Type: `help` or `?` - Show this help message
- Type: `version` or `info` - Show application version and system information
- Type: `custom prompts` - Show custom prompt configuration status

**📁 Optional Enhancement Folders:**
- `swagger/` - Place .json/.yml OpenAPI/Swagger files here
- `test-data/` - Place sample requests, responses, traces here
- `samples/` - Alternative location for test data
- `traces/` - Alternative location for log traces

**💡 Advanced Tips:**
- Swagger files enable schema validation testing
- Test data files create realistic test scenarios
- Configuration files enable property-based testing
- Tool works great even without optional files!
"""

FILE_UPLOAD_MESSAGE = """📁 **Please upload a ZIP file containing your Java source code:**

• **Required:** Java (.java) source files
• **Optional:** Swagger files in `swagger/` folder
• **Optional:** Test data files in `test-data/` or similar folders
• **Optional:** Configuration files in `src/main/resources/`
• **Maximum size:** 100MB

**Alternative:** Type **'use sample'** in the chat to test with the sample project."""

UPLOAD_NEW_MESSAGE = """🔄 **To upload a new ZIP file:**

1. Refresh the page
2. Start a new session
3. Upload your ZIP with optional files in the correct folders:
   - `swagger/` folder for Swagger/OpenAPI files
   - `test-data/` or `samples/` folder for test data files"""

DEFAULT_RESPONSE_MESSAGE = """🤖 **Enhanced JUnit Test Generator Ready!**

**Available commands:**
• `use sample` - Test with sample Java project
• `upload new` - Instructions for uploading with enhancements
• `help` - Show enhanced help and features

💡 **Pro Tip:** Include `swagger/` and `test-data/` folders in your ZIP for maximum enhancement!"""
