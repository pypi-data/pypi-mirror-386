# Contributing to VSCode Copilot Controller

Thank you for your interest in contributing! This project aims to provide reliable automation for VSCode Copilot chat interactions.

## Development Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/autoocto/vscode-copilot-controller.git
   cd vscode-copilot-controller
   ```

2. **Install in development mode**:
   ```bash
   pip install -e ".[dev,gui]"
   ```

3. **Install Tesseract OCR** (required for functionality):
   - Windows: Download from [GitHub releases](https://github.com/UB-Mannheim/tesseract/wiki)
   - macOS: `brew install tesseract`
   - Linux: `sudo apt-get install tesseract-ocr`

## Running Tests

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=vscode_copilot_controller

# Run linting
flake8 vscode_copilot_controller
black --check vscode_copilot_controller
mypy vscode_copilot_controller
```

## Code Style

- Use [Black](https://black.readthedocs.io/) for code formatting
- Follow [PEP 8](https://pep8.org/) style guidelines
- Add type hints for new functions
- Include docstrings for public functions

## Testing Your Changes

1. **Test with real VSCode**: Make sure VSCode with Copilot is open and test your changes
2. **Test OCR detection**: Verify that button/text detection still works
3. **Test automation**: Ensure clicking and message sending functions work
4. **Test different themes**: Test with VSCode high contrast themes

## Submitting Changes

1. **Create a feature branch**: `git checkout -b feature/your-feature-name`
2. **Make your changes** with appropriate tests
3. **Ensure tests pass**: Run the full test suite
4. **Update documentation** if needed
5. **Submit a pull request** with a clear description

## Issue Reporting

When reporting issues, please include:

- VSCode version and theme
- Operating system
- Tesseract version (`tesseract --version`)
- Copilot chat panel layout/position
- Screenshots if relevant
- Error messages and logs

## Feature Requests

We welcome feature requests! Please describe:

- The use case or problem you're trying to solve
- How you envision the feature working
- Any alternative solutions you've considered

## Areas for Contribution

- **Detector improvements**: Better OCR detection for different themes/layouts
- **Cross-platform support**: Testing and fixes for macOS/Linux
- **Documentation**: Examples, tutorials, API documentation
- **Testing**: Unit tests, integration tests, edge case handling
- **Performance**: Optimization of OCR and screenshot operations

## Code of Conduct

Please be respectful and constructive in all interactions. This project aims to be welcoming to contributors of all skill levels.