# Universal Tester - Core Library

This folder contains the **core library** that will be published to PyPI.

## 📦 What's Inside

This is the pip-installable package that provides:
- Core test generation engine
- LLM provider abstractions  
- Import detectors for Java/Kotlin
- Prompt templates
- Basic CLI interface

## 🚀 Publishing to PyPI

```powershell
# Validate structure
python validate_package.py

# Build the package
.\build_package.ps1

# Publish to TestPyPI (test first)
python publish_package.py --test

# Publish to PyPI (production)
python publish_package.py
```

## 📚 Documentation

- `README_PYPI.md` - Package README for PyPI page
- `PYPI_PUBLISHING_GUIDE.md` - Complete publishing guide
- `QUICKSTART.md` - Quick reference
- `READY_TO_PUBLISH.md` - Publishing checklist

## 🎯 After Publishing

Users can install with:
```bash
pip install universal-tester
```

And use in their code:
```python
from universal_tester import LLMFactory, process_java_zip_enhanced_core
```

## 📁 Structure

```
universal-tester-lib/
├── src/
│   └── universal_tester/     # Main package
│       ├── core.py           # Test generation engine
│       ├── cli.py            # CLI entry point
│       ├── llm/              # LLM providers
│       ├── detectors/        # Import detection
│       └── prompts/          # Prompt templates
├── pyproject.toml            # Package metadata
├── build_package.py          # Build script
├── publish_package.py        # Publish script
└── README_PYPI.md           # PyPI README
```

## 🔗 Related

See `../universal-tester-app/` for the Chainlit UI application that uses this library.
