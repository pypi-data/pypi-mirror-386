# Universal Tester - AI-Powered Test Generation

[![PyPI version](https://badge.fury.io/py/universal-tester.svg)](https://pypi.org/project/universal-tester/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

**Automatically generate high-quality JUnit tests for Java and Kotlin projects using AI - with complete code privacy using local LLMs.**

Universal Tester leverages Large Language Models (LLMs) to understand your code and create comprehensive test suites with proper mocking, assertions, and edge case coverage. It comes with both a **Command-Line Interface (CLI)** and a **Web UI** for maximum flexibility.

## 🔒 Unique Security Feature

## 🔒 Unique Security Feature

**Your Code Never Leaves Your Machine!**

Unlike other AI testing tools that send your code to cloud services, Universal Tester supports **Ollama** - a runtime platform that lets you run powerful open-source LLMs (Llama, Mistral, CodeLlama, etc.) entirely on your own computer.

**Why This Matters:**
- ✅ **Complete Privacy**: Your proprietary source code stays on your machine
- ✅ **100% Offline**: No internet required for test generation
- ✅ **Enterprise-Safe**: Complies with strict corporate security policies
- ✅ **Zero Trust Architecture**: No cloud providers can access your code
- ✅ **FREE**: No API costs - unlimited test generation at no charge
- ✅ **Compliance-Ready**: Meets requirements for regulated industries (healthcare, finance, government)

**You Have Options**: While Ollama provides maximum security through local LLM execution, you can also use Azure OpenAI or Google Gemini if your team prefers cloud-based models.

- ✅ **100% Offline Operation** with Ollama
- ✅ **No Cloud Uploads** - Your code stays on your machine
- ✅ **Enterprise-Safe** - Perfect for proprietary and sensitive codebases
- ✅ **FREE** - No API costs with local models
- ✅ **Your Choice** - Also supports Azure OpenAI and Google Gemini if preferred

---

## 🚀 Features

- ✅ **🔐 Local LLM Support (Ollama)**: Run any open-source LLM locally - your code never leaves your machine
- ✅ **Multi-LLM Support**: Azure OpenAI, Google Gemini, or Ollama (run LLMs locally/offline)
- ✅ **Smart Import Detection**: Automatic dependency analysis and import management
- ✅ **Two Interfaces**: CLI for automation, Web UI for interactive use
- ✅ **Java & Kotlin**: Full support for both languages
- ✅ **Multiple Frameworks**: JUnit 5, Mockito, MockK, Kotest
- ✅ **Spring Boot Ready**: Special handling for Spring annotations and dependency injection
- ✅ **Incremental Testing**: Generate tests for specific files or entire projects
- ✅ **Context-Aware**: Understands your code structure and dependencies
- ✅ **No Vendor Lock-in**: Switch between LLM providers anytime

---

## 📦 Installation

### Prerequisites

- **Python 3.8+** (Tested and certified on **Python 3.13.5**)
  - ⚠️ **Important**: Requires Python 3.8 or higher to avoid compatibility issues
  - ✅ **Certified on**: Python 3.13.5
  - 📋 **Compatible with**: Python 3.8, 3.9, 3.10, 3.11, 3.12, 3.13+ (based on dependencies)
- pip (Python package manager)
- LLM API access (Azure OpenAI, Google Gemini, or Ollama)

### Recommended: Use Virtual Environment

We strongly recommend using a virtual environment to avoid dependency conflicts:

```bash
# Create virtual environment
python -m venv universal-tester-env

# Activate on Windows
universal-tester-env\Scripts\activate

# Activate on Linux/Mac
source universal-tester-env/bin/activate

# Install universal-tester
pip install universal-tester
```

### Install from PyPI

```bash
pip install universal-tester
```

**That's it!** Both CLI and Web UI are included.

### Verify Installation

```bash
universal-tester --version
```

---

## 🎯 Quick Start

### 1. Configure Your LLM Provider

Copy `.env.example` to `.env` and configure:

```bash
# Ollama (FREE - Recommended for local development)
LLM_PROVIDER=ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b

# OR Azure OpenAI
LLM_PROVIDER=azure_openai
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4

# OR Google Gemini
LLM_PROVIDER=google
GOOGLE_API_KEY=your-google-api-key
GOOGLE_MODEL=gemini-2.0-flash:generateContent
```

### 2. Generate Tests (CLI)

```bash
# Generate tests from a ZIP file
universal-tester --input /path/to/your-project.zip

# With custom output directory
universal-tester -i project.zip -o ./generated-tests
```

### 3. Or Use the Web UI

```bash
# Launch the web interface
universal-tester-ui
```

Then upload your ZIP file and click "Generate Tests"!

---

## 💡 Usage Examples

### CLI Examples

**Basic test generation:**
```bash
universal-tester --input myproject.zip
```

**Kotlin with MockK:**
```bash
universal-tester --input kotlin-app.zip --language kotlin --framework mockk
```

**Use specific LLM provider:**
```bash
universal-tester --input project.zip --llm-provider google
```

**Verbose mode:**
```bash
universal-tester --input project.zip --verbose
```

### Web UI

1. Start the UI: `universal-tester-ui`
2. Open `http://localhost:8000` in your browser
3. Upload your Java/Kotlin project (ZIP format)
4. Click "Generate Tests"
5. Download the generated test files

---

## 🎨 What Tests Look Like

**Input: `UserService.java`**
```java
@Service
public class UserService {
    @Autowired
    private UserRepository userRepository;
    
    public User findById(Long id) {
        return userRepository.findById(id)
            .orElseThrow(() -> new UserNotFoundException(id));
    }
}
```

**Generated: `UserServiceTest.java`**
```java
@ExtendWith(MockitoExtension.class)
class UserServiceTest {
    @Mock
    private UserRepository userRepository;
    
    @InjectMocks
    private UserService userService;
    
    @Test
    void findById_WhenUserExists_ReturnsUser() {
        // Arrange
        Long userId = 1L;
        User expectedUser = new User(userId, "John Doe");
        when(userRepository.findById(userId)).thenReturn(Optional.of(expectedUser));
        
        // Act
        User result = userService.findById(userId);
        
        // Assert
        assertNotNull(result);
        assertEquals(expectedUser.getId(), result.getId());
        assertEquals(expectedUser.getName(), result.getName());
        verify(userRepository).findById(userId);
    }
    
    @Test
    void findById_WhenUserNotFound_ThrowsException() {
        // Arrange
        Long userId = 999L;
        when(userRepository.findById(userId)).thenReturn(Optional.empty());
        
        // Act & Assert
        assertThrows(UserNotFoundException.class, () -> userService.findById(userId));
        verify(userRepository).findById(userId);
    }
}
```

---

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `LLM_PROVIDER` | LLM provider: `azure`, `google`, or `ollama` | ✅ Yes |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API key | If using Azure |
| `AZURE_OPENAI_ENDPOINT` | Azure endpoint URL | If using Azure |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | Azure deployment name | If using Azure |
| `GOOGLE_API_KEY` | Google Gemini API key | If using Google |
| `OLLAMA_BASE_URL` | Ollama server URL | If using Ollama |
| `OLLAMA_MODEL` | Ollama model name | If using Ollama |

### CLI Options

```bash
universal-tester [OPTIONS]

Options:
  -i, --input PATH       Input ZIP file path (required)
  -o, --output PATH      Output directory (default: ./generated_tests)
  --llm-provider TEXT    LLM provider override (azure/google/ollama)
  --language TEXT        Source language (java/kotlin)
  --framework TEXT       Test framework (junit/mockito/mockk/kotest)
  -v, --verbose          Enable verbose logging
  --version              Show version
  --help                 Show help message
```

---

## 📚 Documentation

- **[Complete User Guide](USER_GUIDE.md)** - Detailed documentation
- **[LLM Provider Setup](USER_GUIDE.md#llm-provider-setup)** - Configure Azure, Google, or Ollama
- **[Troubleshooting](USER_GUIDE.md#troubleshooting)** - Common issues and solutions
- **[FAQ](USER_GUIDE.md#faq)** - Frequently asked questions

---

## 🎯 Use Cases

### For Developers
- Quickly create test scaffolding for new code
- Improve test coverage on legacy code
- Learn testing best practices from generated examples
- Speed up TDD workflow

### For Teams
- Standardize test patterns across the codebase
- Onboard new team members with consistent test examples
- Reduce time spent writing boilerplate tests
- Focus on complex business logic testing

### For CI/CD
- Integrate into build pipelines
- Generate tests automatically on code commits
- Maintain test coverage metrics
- Automate test creation for new features

---

## 🌟 Why Universal Tester?

| Feature | Universal Tester | Manual Testing | Other Tools |
|---------|-----------------|----------------|-------------|
| Speed | ⚡ Seconds | 🐌 Hours | ⚡ Fast |
| Quality | ✅ AI-powered | 👤 Variable | ⚠️ Template-based |
| Customization | ✅ Flexible | ✅ Full control | ❌ Limited |
| LLM Choice | ✅ 3 providers | N/A | ❌ Usually locked |
| UI + CLI | ✅ Both | N/A | ⚠️ Usually one |
| Cost | 💰 Free + LLM API | 💰💰 Developer time | 💰💰💰 Expensive |

---

## 🔒 Privacy & Security

- **Your code stays yours**: Code is only sent to your chosen LLM provider
- **Use Ollama for local processing**: 100% offline operation available
- **No data storage**: We don't store or log your code
- **Open source**: Audit the code yourself (Apache 2.0 License)

---

## 🛠️ Requirements

- Python 3.8 or higher
- Access to an LLM provider:
  - **Azure OpenAI** (paid)
  - **Google Gemini** (paid, but has free tier)
  - **Ollama** (free, runs locally)

---

## 📊 Project Structure

```
universal-tester/
├── universal_tester/
│   ├── core.py                    # Main test generation logic
│   ├── cli.py                     # Command-line interface
│   ├── llm/
│   │   ├── factory.py             # Multi-LLM support
│   │   ├── health_check.py        # LLM health monitoring
│   │   └── java_validator.py     # Code validation
│   ├── detectors/
│   │   ├── enhanced_import_detector.py  # Java import detection
│   │   └── kotlin_import_detector.py    # Kotlin import detection
│   ├── prompts/
│   │   ├── prompt_builder.py      # LLM prompt construction
│   │   ├── system_prompts.py      # System-level prompts
│   │   └── ui_messages.py         # UI messages
│   └── ui/
│       ├── chainlit_ui.py         # Web UI implementation
│       └── main.py                # UI entry point
├── USER_GUIDE.md                  # Complete documentation
└── README.md                      # This file
```

---

## 🤝 Contributing

Contributions are welcome! Here's how:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

---

## 📝 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

**Note on Commercial Use**: While the software is open source under Apache 2.0, commercial use requires a separate license. Contact senthilthepro@hotmail.com for commercial licensing.

**Patent Notice**: The author reserves all patent rights related to the concepts and methods embodied in this software.

---

## 🙏 Acknowledgments

- Built with [LangChain](https://langchain.com/)
- UI powered by [Chainlit](https://chainlit.io/)
- Inspired by the need for better automated testing tools

---

## 📧 Contact & Support

- **Author**: Senthil Kumar Thanapal
- **Email**: senthilthepro@hotmail.com
- **PyPI Package**: https://pypi.org/project/universal-tester/

---

## 🚀 Quick Links

- [PyPI Package](https://pypi.org/project/universal-tester/)
- [User Guide](USER_GUIDE.md)
- Documentation included in package

---

**Made with ❤️ for the testing community**

*Star ⭐ this repo if you find it useful!*
