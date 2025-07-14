# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Essential Commands

**Development Environment:**
- Always use the virtual environment: `./venv/bin/python` instead of `python`
- Python 3.11 is required

**Core Agent Commands:**
```bash
# Validate listings data
./venv/bin/python grailed_agent.py validate listings.json

# Analyze images and generate metadata  
./venv/bin/python grailed_agent.py analyze listings.json

# Test automation workflow (dry-run)
./venv/bin/python grailed_agent.py run listings.json --dry-run

# Execute live automation
./venv/bin/python grailed_agent.py run listings.json
```

**Setup and Dependencies:**
```bash
# Install all dependencies
pip install -r requirements.txt

# Setup MCP Playwright browser automation
python setup_strands.py

# Test without API keys (development)
./venv/bin/python test_grailed_agent.py
```

## Architecture Overview

This is a **State-Aware AI Agent** built with the Strands Agents SDK for automating Grailed.com listing creation. The architecture consists of three main layers:

### 1. Agent Layer (`grailed_agent.py`)
- **Strands Agent**: Central orchestrator with AI model integration
- **Custom Tools**: State-aware browser automation tools (`@tool` decorators)
- **Multi-Model Support**: Anthropic Claude, AWS Bedrock, or Google Gemini
- **State Management**: Always knows current browser state before actions

### 2. Browser Automation Layer  
- **MCP Integration**: Uses Model Context Protocol for browser control
- **Playwright Server**: Handles actual browser interactions via `@playwright/mcp`
- **Text-Based State Detection**: Uses `browser_snapshot` (accessibility tree) instead of screenshots
- **State-Aware Navigation**: Verifies page state before every action

### 3. Custom Tool System
Critical custom tools that enable state-aware automation:

```python
@tool
def detect_current_page_state() -> str:
    # Analyzes browser_snapshot to determine current page (homepage, login, sell page, etc.)

@tool 
def verify_sell_page_ready() -> str:
    # Confirms form elements are present before filling

@tool
def navigate_to_sell_page() -> str:
    # Handles navigation with state verification at each step

@tool
def gemini_image_reader(image_path: str) -> str:
    # Custom image processing for Gemini API (base64 encoding)
```

## Model Provider Configuration

The agent supports multiple AI providers via environment variables:

**Google Gemini (Current Setup):**
```env
AI_MODEL_PROVIDER=gemini
GEMINI_API_KEY=your_key
GEMINI_MODEL_ID=gemini-2.5-flash
```

**Anthropic Claude:**
```env
AI_MODEL_PROVIDER=anthropic
ANTHROPIC_API_KEY=your_key
```

**AWS Bedrock:**
```env
AI_MODEL_PROVIDER=bedrock
AWS_PROFILE=default
AWS_REGION=us-west-2
```

## Key Implementation Details

### State-Aware Automation Philosophy
Unlike traditional browser automation, this agent:
1. **Always checks current state** via `browser_snapshot` before actions
2. **Verifies navigation success** after each page transition  
3. **Handles dynamic content** with proper wait strategies
4. **Recovers from errors** by re-detecting state and retrying

### Gemini API Compatibility
The codebase includes special handling for Gemini's OpenAI-compatible endpoint:
- Custom `gemini_image_reader` tool for base64 image encoding
- Removed `browser_take_screenshot` usage (incompatible with Gemini)
- Uses text-based `browser_snapshot` for state detection instead

### MCP Browser Automation
Browser control is handled through Model Context Protocol:
- Playwright MCP server provides browser tools
- Agent uses `browser_snapshot` (accessibility tree) for state detection
- Form interactions use semantic selectors (`data-testid`, roles)

### Fully Automated Workflow
The agent processes all listings without user confirmation:
- Loads listings from JSON file
- Navigates to Grailed.com automatically  
- Fills forms and uploads images for each item
- Only prompts for login if popup appears (`prompt_user_login`)

## Testing and Development

**Environment Setup:**
- Use `./venv/bin/python` for all Python commands
- MCP Playwright server must be installed via `setup_strands.py`
- Chrome/Chromium browser required for automation

**Dry-Run Testing:**
Always test with `--dry-run` flag before live execution to simulate the workflow without actual form submission.

**Image Path Requirements:**
- Only JPG/JPEG images supported (enforced by validation)
- Paths in `listings.json` must point to actual files on the system
- Images are processed locally and uploaded via browser automation

**Common Issues:**
- Quota limits with Gemini free tier (429 errors)
- MCP server connection issues (run `setup_strands.py`)
- Browser state detection failures (agent will retry with state checking)

## Critical Development Notes

- **Never commit API keys** - they're in `.env` file (gitignored)
- **Test thoroughly before commits** - browser automation can be fragile
- **State-aware tools are essential** - modifying them affects core functionality
- **Virtual environment is required** - dependencies are isolated in `./venv/`