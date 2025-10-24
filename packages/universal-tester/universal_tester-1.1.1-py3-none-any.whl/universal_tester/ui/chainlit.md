# Welcome to Universal Tester! 🚀

**AI-Powered Test Generation for Java & Kotlin**

Universal Tester automatically generates high-quality JUnit tests for your projects using advanced AI. Upload your code and let the AI create comprehensive test suites with proper mocking, assertions, and edge case coverage.

## 🔒 Your Code Stays Private!

**Unique Security Feature:** Universal Tester supports **Ollama** - a platform that lets you run any open-source LLM (Llama 3.1, Mistral, CodeLlama, DeepSeek, etc.) entirely on your machine. Your proprietary source code never leaves your computer, ensuring complete confidentiality and compliance with strict security policies.

- ✅ **100% Offline Operation** - No cloud uploads
- ✅ **Enterprise-Safe** - Perfect for sensitive codebases
- ✅ **FREE** - Run free open-source LLMs, no API costs
- ✅ **Your Choice** - Also supports Azure OpenAI and Google Gemini

---

## ✨ Features

- **🔐 Local LLM Support (Ollama)**: Run any open-source LLM locally - your code never leaves your machine
- **Multi-LLM Support**: Works with Azure OpenAI, Google Gemini, or Ollama (local open-source LLMs)
- **Smart Import Detection**: Automatic dependency analysis and import management
- **Java & Kotlin**: Full support for both languages with Spring Boot integration
- **Multiple Frameworks**: JUnit 5, Mockito, MockK, Kotest
- **Incremental Testing**: Generate tests for specific files or entire projects
- **Context-Aware**: Understands your code structure and generates relevant tests

---

## 🚀 Quick Start

1. **Upload Your Project**: Click the upload button and select your Java/Kotlin project ZIP file
2. **AI Analysis**: The AI will analyze your code structure, dependencies, and methods
3. **Generate Tests**: Receive comprehensive test files with proper assertions and mocks
4. **Download**: Get your generated tests and integrate them into your project

---

## ⚙️ Configuration

Make sure you have configured your LLM provider in the `.env` file:

```bash
# For Ollama (FREE - Local)
LLM_PROVIDER=ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b

# For Azure OpenAI
LLM_PROVIDER=azure_openai
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/

# For Google Gemini
LLM_PROVIDER=google
GOOGLE_API_KEY=your-google-api-key
```

---

## 📋 Supported Languages & Frameworks

**Languages:**
- Java 8+, 11, 17, 21
- Kotlin 1.8+, 1.9, 2.0

**Frameworks:**
- Spring Boot, Spring Framework
- JPA/Hibernate
- JUnit 5, Mockito
- MockK, Kotest

---

## 📄 License

**Apache License 2.0**

Copyright © 2025 Senthil Kumar Thanapal

This software is open source under Apache 2.0 license. For commercial use inquiries, contact: senthilthepro@hotmail.com

Patent rights reserved. See LICENSE file for details.

---

## 🔗 Resources

- **GitHub**: [github.com/senthilthepro/universal-tester](https://github.com/senthilthepro/universal-tester)
- **PyPI**: [pypi.org/project/universal-tester](https://pypi.org/project/universal-tester)
- **Documentation**: See USER_GUIDE.md in the repository
- **Support**: senthilthepro@hotmail.com

---

**Ready to start?** Upload your project ZIP file above! 🎯
