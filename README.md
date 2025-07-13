# Grailed Listing Agent - State-Aware Browser Automation

An intelligent agent built with **Strands Agents SDK** for automating Grailed.com listing creation using AI-powered image analysis and **state-aware browser automation** via MCP (Model Context Protocol).

## 🤖 Architecture

This implementation uses:
- **Strands Agents SDK** - For AI agent orchestration and tool integration
- **MCP Playwright Server** - For browser automation via Model Context Protocol
- **State-Aware Automation** - Always knows what page it's on before taking actions
- **Multi-Model Support** - Claude, Bedrock, or LiteLLM for image analysis
- **Custom Tools** - For Grailed-specific validation and processing

## 📁 Project Structure

```
GrailedListingAgent/
├── grailed_agent.py           # Main Strands Agent implementation
├── test_grailed_agent.py      # Test version (no API keys needed)
├── setup_strands.py           # Setup script for dependencies
├── requirements.txt           # Python dependencies
├── .env                       # Environment configuration
├── listings.json              # Your listing data
└── README.md                  # This file
```

## 🚀 Quick Start

### 1. Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run setup script (installs MCP Playwright server)
python setup_strands.py

# Configure your API key in .env file
# Edit .env with your API key
```

### 2. Configure Environment

Edit `.env` file:

```env
# Choose your AI model provider
AI_MODEL_PROVIDER=anthropic
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Alternative: Use AWS Bedrock
# AI_MODEL_PROVIDER=bedrock
# AWS_PROFILE=default
# AWS_REGION=us-west-2
```

### 3. Usage

```bash
# Validate your listings file
python grailed_agent.py validate listings.json

# Analyze images and generate metadata
python grailed_agent.py analyze listings.json

# Create listings (dry run first)
python grailed_agent.py run listings.json --dry-run

# Create actual listings
python grailed_agent.py run listings.json
```

## 🧠 How It Works

### State-Aware Agent Architecture

The Grailed Listing Agent is a **State-Aware Strands Agent** that:

1. **Always Checks Page State** before taking any browser actions
2. **Uses AI Models** for image analysis and reasoning
3. **Integrates Custom Tools** via `@tool` decorators for state tracking
4. **Follows Intelligent Workflows** with proper navigation verification
5. **Handles Browser Automation** via MCP Playwright with state awareness
6. **Provides Error Recovery** with graceful degradation and state checking

### State-Aware Workflow Process

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Load & Parse  │───▶│  Image Analysis  │───▶│ State Detection │
│  listings.json  │    │   (AI Vision)    │    │ & Page Checking │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Validate Data   │    │ Generate Meta    │    │ Navigate with   │
│ & File Paths    │    │ & Get Approval   │    │ State Tracking  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                                                         ▼
                                               ┌─────────────────┐
                                               │ Fill Forms &    │
                                               │ Upload Images   │
                                               │ (State-Verified)│
                                               └─────────────────┘
```

### Key Components

#### 1. Strands Agent with State-Aware Custom Tools
```python
@tool
def detect_current_page_state() -> str:
    """Detect what page/state the browser is currently in"""

@tool
def navigate_to_sell_page() -> str:
    """Navigate to sell page with proper state checking"""

@tool
def verify_sell_page_ready() -> str:
    """Verify that we're on the sell page and form is ready"""

@tool
def expand_image_paths(image_paths: List[str]) -> List[str]:
    """Expand and validate image file paths"""

@tool  
def validate_grailed_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Validate Grailed-specific metadata"""

# Agent with comprehensive system prompt for state awareness
agent = Agent(
    model=AnthropicModel(...),
    tools=[file_read, file_write, image_reader, state_tools, validation_tools],
    system_prompt=state_aware_system_prompt
)
```

#### 2. MCP Integration for Browser Automation
```python
playwright_client = MCPClient(lambda: stdio_client(
    StdioServerParameters(
        command="npx",
        args=["@modelcontextprotocol/server-playwright"]
    )
))
```

#### 3. State-Aware Intelligent Workflows
The agent follows sophisticated workflows with state verification:
- **Phase 1**: Metadata generation from images
- **Phase 2**: State-aware browser navigation and login handling  
- **Phase 3**: Form filling with page verification
- **Phase 4**: Error handling and recovery with state checking

## 🛠️ Features

### State-Aware Browser Automation (NEW!)
- **Page State Detection**: Always knows what page the browser is on
- **Navigation Verification**: Confirms successful navigation before proceeding
- **Smart Login Handling**: Only prompts for login when popup actually appears
- **Form Readiness Checking**: Verifies form elements exist before filling
- **Error Recovery**: Graceful handling with state-based debugging

### AI-Powered Image Analysis
- Analyzes product images to extract metadata
- Generates department, category, designer, size, color, condition
- Handles complex scenarios like designer collaborations
- Provides confidence scoring and user approval workflow

### Intelligent Browser Automation
- Uses MCP Playwright for robust browser control
- Handles dynamic page loading and network delays
- Detects login requirements and guides user through process
- Supports complex form interactions (dropdowns, collaborations)

### Error Handling & Recovery
- Skip-on-error processing for batch operations
- Detailed error reporting and logging
- State persistence for interrupted workflows
- Graceful degradation when components fail

### User Experience
- Clear progress indicators and status updates
- Interactive approval workflows for AI-generated data
- Dry-run mode for testing without actual submission
- Comprehensive validation and error messages

## 📋 Listings JSON Schema

```json
[
  {
    "image_paths": ["~/path/to/image1.jpg", "~/path/to/image2.jpg"],
    "price": 120.0,
    "accept_offers": true,
    "smart_pricing": true,
    "floor_price": 90.0,
    "country_of_origin": "USA",
    
    // AI-generated fields (optional)
    "department": "Menswear",
    "category": "Outerwear", 
    "sub_category": "Denim Jackets",
    "designer": "Brain Dead x A.P.C",
    "item_name": "Brain Dead x A.P.C Denim Jacket",
    "size": "S",
    "color": "Indigo",
    "condition": "Gently Used",
    "description": "Detailed description..."
  }
]
```

## 🔧 Configuration

### Model Providers

#### Anthropic Claude (Recommended)
```env
AI_MODEL_PROVIDER=anthropic
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

#### AWS Bedrock
```env
AI_MODEL_PROVIDER=bedrock
AWS_PROFILE=default
AWS_REGION=us-west-2
```

#### OpenAI via LiteLLM
```bash
pip install 'strands-agents[litellm]'
```
```env
AI_MODEL_PROVIDER=litellm
OPENAI_API_KEY=your_openai_api_key_here
```

## 🚨 Important Notes

### MCP Playwright Setup
The agent requires the MCP Playwright server for browser automation:

```bash
# Install globally (done by setup script)
npm install -g @modelcontextprotocol/server-playwright

# Install browsers
npx playwright install chromium
```

### Grailed Selectors
The agent uses current Grailed.com selectors (as of 2024):
- Sell button: `a[data-testid="desktop-sell"]`
- Form elements: Various role-based and data-testid selectors
- These may change if Grailed updates their interface

### Rate Limiting
- Process items sequentially to avoid overwhelming Grailed
- Built-in delays between actions
- Respects Grailed's terms of service

## 🔍 Troubleshooting

### Common Issues

**"Strands Agents SDK not found"**
```bash
pip install strands-agents strands-agents-tools
```

**"MCP Playwright server failed"**
```bash
npm install -g @modelcontextprotocol/server-playwright
npx playwright install chromium
```

**"API key not found"**
- Check your `.env` file has the correct API key
- Ensure the environment variable name matches your provider

**"Browser automation failed"**
- Run setup script: `python setup_strands.py`
- Check Node.js is installed: `node --version`
- Verify Playwright MCP server is working

### Debug Mode
```bash
# Test without API keys
python test_grailed_agent.py

# Enable debug logging
python grailed_agent.py validate listings.json --debug
```

## 🤝 Contributing

This implementation follows the Strands Agents patterns:
- Agent-based architecture with tool integration
- MCP for external service communication
- Comprehensive error handling and logging
- User-friendly CLI interface

## 📄 License

MIT License - See LICENSE file for details.

## ⚠️ Disclaimer

This tool is for educational and personal use. Please ensure compliance with Grailed's Terms of Service and use responsibly.
