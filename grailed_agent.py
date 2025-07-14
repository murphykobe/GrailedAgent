#!/usr/bin/env python3
"""
Grailed Listing Agent with State-Aware Browser Automation
Fixes the critical issue of not tracking browser state/page context
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded .env file")
except ImportError:
    print("⚠️  python-dotenv not installed, using system environment variables only")

# Configure logging
logging.basicConfig(
    format="%(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler()]
)
logging.getLogger("strands").setLevel(logging.INFO)

try:
    from strands import Agent, tool
    from strands_tools import file_read, file_write
    print("✅ Successfully imported Strands Agents SDK")
except ImportError as e:
    print(f"❌ Error importing Strands Agents SDK: {e}")
    print("Please install: pip install strands-agents strands-agents-tools")
    sys.exit(1)

# Import additional libraries for custom image handling with Gemini
import base64

# Import MCP for Playwright browser automation
try:
    from mcp import StdioServerParameters, stdio_client
    from strands.tools.mcp import MCPClient
    print("✅ Successfully imported MCP tools")
except ImportError as e:
    print(f"❌ Error importing MCP tools: {e}")
    sys.exit(1)

@tool
def gemini_image_reader(image_path: str) -> str:
    """
    Read and encode JPG image for Gemini API using base64 format.
    This is specifically designed to work with Gemini's OpenAI-compatible endpoint.
    """
    try:
        # Expand the path
        expanded_path = Path(image_path).expanduser().resolve()
        
        if not expanded_path.exists():
            return f"Error: Image file not found: {image_path}"
        
        # Validate JPG format
        if not expanded_path.suffix.lower() in ['.jpg', '.jpeg']:
            raise ValueError(f"Invalid image format: {expanded_path.suffix}. Only JPG/JPEG files are supported.")
        
        # Read and encode the image
        with open(expanded_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        
        # Return the data URL format that Gemini expects
        data_url = f"data:image/jpeg;base64,{base64_image}"
        
        return f"Image successfully loaded from {image_path}. Data URL ready for Gemini API."
        
    except Exception as e:
        return f"Error reading image {image_path}: {str(e)}"

@tool
def expand_image_paths(image_paths: List[str]) -> List[str]:
    """Expand and validate image file paths"""
    expanded_paths = []
    for path in image_paths:
        expanded_path = Path(path).expanduser().resolve()
        if expanded_path.exists():
            expanded_paths.append(str(expanded_path))
        else:
            print(f"⚠️  Warning: Image file not found: {path}")
            expanded_paths.append(str(expanded_path))  # Include anyway for debugging
    return expanded_paths

@tool
def validate_grailed_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and normalize Grailed-specific metadata"""
    required_fields = [
        "department", "category", "sub_category", "designer", "item_name",
        "size", "color", "condition", "price", "description", "image_paths"
    ]
    
    validated = {}
    for field in required_fields:
        if field in metadata:
            validated[field] = metadata[field]
        else:
            print(f"⚠️  Missing required field: {field}")
    
    # Validate image paths are JPG format
    if "image_paths" in metadata:
        for image_path in metadata["image_paths"]:
            path = Path(image_path)
            if not path.suffix.lower() in ['.jpg', '.jpeg']:
                raise ValueError(f"Invalid image format: {path.suffix}. Only JPG/JPEG files are supported for Gemini API.")
    
    # Add optional fields
    optional_fields = ["accept_offers", "smart_pricing", "country_of_origin"]
    for field in optional_fields:
        if field in metadata:
            validated[field] = metadata[field]
    
    return validated

@tool
def detect_current_page_state() -> str:
    """
    Detect what page/state the browser is currently in using text-based analysis.
    This is CRITICAL for state-aware automation.
    """
    return """
CRITICAL: Use browser_snapshot to detect current page state by analyzing:

1. **Homepage/Landing Page**:
   - URL contains just "grailed.com" or "grailed.com/"
   - Look for: a[data-testid="desktop-sell"] (sell button)
   - Page title contains "Grailed"
   - Navigation elements present

2. **Login Modal/Popup State**:
   - Look for: div[role="dialog"], .modal, .login-popup
   - Login form elements: input[type="email"], input[type="password"]
   - "Sign In" or "Log In" buttons/text
   - Modal overlay blocking main content

3. **Sell/Create Listing Page**:
   - URL contains "/sell" or "/create" or "/listing"
   - Form elements: select[name="department"], input[name="title"]
   - "Create Listing" or "Sell Item" text
   - Product form fields visible

4. **Profile/Account Page**:
   - URL contains "/users/" or "/profile"
   - User avatar or account settings visible
   - User-specific content and navigation

5. **Other/Unknown Page**:
   - Check URL and page title
   - Look for navigation elements
   - Analyze page content structure

Use browser_snapshot to get page accessibility tree and content.
Parse URL, elements, page title, and text content to determine state.
Return the detected state clearly: "homepage", "login_popup", "sell_page", "profile", or "unknown".
"""

@tool
def navigate_to_sell_page() -> str:
    """
    Navigate to the sell page with proper state checking.
    This ensures we're on the right page before proceeding.
    """
    return """
STEP-BY-STEP NAVIGATION TO SELL PAGE:

1. **Check Current State First**:
   - Use detect_current_page_state() to see where we are
   - Use browser_snapshot to analyze page content and URL

2. **If on Homepage**:
   - Look for sell button: a[data-testid="desktop-sell"]
   - Click the sell button
   - Wait 2-3 seconds for navigation
   - Check for login popup immediately after click

3. **If Login Popup Appears**:
   - Use prompt_user_login() to handle popup
   - After user completes login, check state again
   - Navigate to sell page if not already there

4. **If Already on Sell Page**:
   - Verify form elements are present
   - Proceed with listing creation

5. **If on Unknown Page**:
   - Navigate to https://www.grailed.com first
   - Then follow homepage flow

6. **State Verification**:
   - After each navigation step, use browser_snapshot to confirm success
   - Parse the accessibility tree to verify expected elements are present
   - Check URL and page content match expected sell page pattern

ALWAYS verify you're on the sell page before trying to fill forms!
"""

@tool
def verify_sell_page_ready() -> str:
    """
    Verify that we're on the sell page and form is ready for input.
    This prevents trying to fill forms on wrong pages.
    """
    return """
VERIFY SELL PAGE IS READY:

Use browser_snapshot to check these elements and confirm sell page is loaded and ready:

1. **URL Check**: 
   - URL should contain "/sell" or similar
   - Parse URL from browser_snapshot accessibility tree

2. **Form Elements Present**:
   - Department dropdown: select[name="department"] or similar
   - Title/Name input: input[name="title"] or input[name="name"]
   - Price input: input[name="price"] or input[type="number"]
   - Description textarea: textarea[name="description"]
   - Image upload area or file input elements

3. **Page Title and Content**:
   - Should contain "Sell" or "Create Listing" text
   - Page structure should match sell page layout

4. **No Overlays/Modals**:
   - Ensure no login popups or other modals are blocking the form
   - Check for overlay elements: .modal, .popup, div[role="dialog"]
   - Verify main form content is accessible

5. **Form Readiness**:
   - All required form fields should be present and interactable
   - No loading states or disabled elements blocking interaction
   - Form should be ready for data input

Use browser_snapshot to analyze page accessibility tree and content.
Return "READY" if sell page is ready, or describe what's missing/wrong.
"""

@tool
def prompt_user_login() -> str:
    """Prompt user to complete login manually when popup appears"""
    print("\n" + "="*60)
    print("🔐 LOGIN POPUP DETECTED")
    print("="*60)
    print("A login popup has appeared on the page.")
    print("Please complete the following steps:")
    print("1. Look at the browser window")
    print("2. Complete the login process in the popup")
    print("3. Wait for the popup to close and return to the main page")
    print("4. Come back here and press Enter to continue")
    print("="*60)
    
    try:
        input("Press Enter after you have completed login in the popup...")
        return "User confirmed login popup completed"
    except KeyboardInterrupt:
        return "User cancelled login process"

@tool 
def prompt_user_confirmation(message: str) -> str:
    """Prompt user for confirmation with a custom message"""
    print(f"\n📋 {message}")
    try:
        response = input("Press Enter to continue or 'q' to quit: ").strip().lower()
        if response == 'q':
            return "User chose to quit"
        return "User confirmed to continue"
    except KeyboardInterrupt:
        return "User cancelled"

@tool
def wait_and_retry(action_description: str, max_retries: int = 3) -> str:
    """
    Helper tool for retrying actions with waits.
    Useful for handling dynamic page loading.
    """
    return f"""
RETRY STRATEGY for: {action_description}

1. Wait 2-3 seconds for page to stabilize
2. Check current page state with detect_current_page_state()
3. Take screenshot to see current state
4. Attempt the action
5. If action fails, wait another 2-3 seconds and retry
6. Maximum {max_retries} retries before reporting failure

Use this pattern for:
- Clicking buttons that trigger navigation
- Waiting for form elements to appear
- Handling dynamic content loading
"""

def setup_playwright_client():
    """Setup MCP Playwright client with Chrome browser and return the client and tools"""
    print("🤖 Setting up MCP Playwright client with Chrome browser...")
    
    # Try different MCP server names with Chrome configuration
    server_commands = [
            ["npx", "@playwright/mcp@latest"]
    ]
    
    for command in server_commands:
        try:
            print(f"🔄 Trying MCP server with Chrome: {' '.join(command)}")
            playwright_client = MCPClient(lambda: stdio_client(
                StdioServerParameters(
                    command=command[0],
                    args=command[1:] if len(command) > 1 else []
                )
            ))
            
            # Test the client connection
            with playwright_client:
                playwright_tools = playwright_client.list_tools_sync()
                print(f"✅ Loaded {len(playwright_tools)} Playwright tools via MCP (Chrome)")
                return playwright_client, playwright_tools
                
        except Exception as e:
            print(f"❌ Failed with {' '.join(command)}: {str(e)[:100]}...")
            continue
    
    # Fallback to default browser if Chrome-specific commands fail
    print("🔄 Falling back to default browser configuration...")
    fallback_commands = [
        ["npx", "@automatalabs/mcp-server-playwright"],
        ["npx", "@modelcontextprotocol/server-playwright"]
    ]
    
    for command in fallback_commands:
        try:
            print(f"🔄 Trying fallback MCP server: {' '.join(command)}")
            playwright_client = MCPClient(lambda: stdio_client(
                StdioServerParameters(
                    command=command[0],
                    args=command[1:] if len(command) > 1 else []
                )
            ))
            
            # Test the client connection
            with playwright_client:
                playwright_tools = playwright_client.list_tools_sync()
                print(f"✅ Loaded {len(playwright_tools)} Playwright tools via MCP (default browser)")
                return playwright_client, playwright_tools
                
        except Exception as e:
            print(f"❌ Failed with {' '.join(command)}: {str(e)[:100]}...")
            continue
    
    print("⚠️  Warning: Could not load Playwright MCP tools")
    print("   Browser automation will be limited. You can still use image analysis features.")
    return None, []

def setup_model():
    """Setup the AI model (Bedrock, Anthropic, or Gemini)"""
    model_provider = os.getenv("AI_MODEL_PROVIDER", "anthropic")
    
    if model_provider == "anthropic":
        try:
            from strands.models.anthropic import AnthropicModel
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not found in environment")
            
            model = AnthropicModel(
                client_args={"api_key": api_key},
                model_id="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                params={"temperature": 0.1}
            )
            print("✅ Using Anthropic Claude model")
            return model
        except Exception as e:
            print(f"❌ Failed to setup Anthropic model: {e}")
            print("   Please set ANTHROPIC_API_KEY in your environment")
            raise
    elif model_provider == "bedrock":
        try:
            from strands.models.bedrock import BedrockModel
            aws_profile = os.getenv("AWS_PROFILE", "default")
            aws_region = os.getenv("AWS_REGION", "us-east-1")
            
            model = BedrockModel(
                model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
                region_name=aws_region,
                profile_name=aws_profile,
                max_tokens=8192,
                params={"temperature": 0.1}
            )
            print(f"✅ Using Bedrock Claude 3 Sonnet model (region: {aws_region}, profile: {aws_profile})")
            return model
        except Exception as e:
            print(f"❌ Failed to setup Bedrock model: {e}")
            print("   Please ensure AWS credentials are configured")
            raise
    elif model_provider == "gemini":
        try:
            from strands.models.openai import OpenAIModel
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY not found in environment")
            
            model = OpenAIModel(
                client_args={
                    "api_key": api_key,
                    "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/"
                },
                model_id=os.getenv("GEMINI_MODEL_ID", "gemini-2.5-pro"),
                max_tokens=int(os.getenv("GEMINI_MAX_TOKENS", "4000")),
                params={"temperature": float(os.getenv("GEMINI_TEMPERATURE", "0.1"))}
            )
            model_name = os.getenv("GEMINI_MODEL_ID", "gemini-2.5-pro")
            print(f"✅ Using Google {model_name} model via OpenAI-compatible endpoint")
            return model
        except Exception as e:
            print(f"❌ Failed to setup Gemini model: {e}")
            print("   Please set GEMINI_API_KEY in your environment")
            raise
    else:
        raise ValueError(f"Unsupported AI_MODEL_PROVIDER: {model_provider}. Supported: anthropic, bedrock, gemini")

def create_agent_with_mcp(playwright_client, playwright_tools, model):
    """Create agent with MCP tools within the context manager"""
    
    # System prompt for the agent with STATE-AWARE automation
    system_prompt = """You are a STATE-AWARE Grailed Listing Agent that ALWAYS checks what page you're on before taking actions.

## CRITICAL STATE-AWARE WORKFLOW:

### ALWAYS START WITH STATE DETECTION:
Before ANY action, use detect_current_page_state() to understand where you are in the browser.

### Phase 1: Initial Navigation with State Tracking
1. Load listings data from JSON file
2. Use browser_navigate to go to https://www.grailed.com
3. **IMMEDIATELY**: Use detect_current_page_state() to confirm page loaded
4. Take screenshot for visual confirmation
5. Wait for page to fully stabilize

### Phase 2: State-Aware Navigation to Sell Page
1. **Check Current State**: Use detect_current_page_state()
2. **If on Homepage**: 
   - Look for sell button: a[data-testid="desktop-sell"]
   - Click sell button
   - **IMMEDIATELY AFTER CLICK**: Use detect_current_page_state() again
   - Check for login popup (div[role="dialog"], .modal, input[type="email"])
3. **If Login Popup Detected**:
   - Use prompt_user_login() to handle popup
   - **AFTER USER CONFIRMS LOGIN**: Use detect_current_page_state() to see where we are
   - If not on sell page, use navigate_to_sell_page()
4. **If Already on Sell Page**: Use verify_sell_page_ready() to confirm form is ready

### Phase 3: State-Verified Form Filling
1. **BEFORE FILLING ANY FORM**: Use verify_sell_page_ready()
2. **If NOT READY**: Use navigate_to_sell_page() to get to correct state
3. **If READY**: Proceed with form filling for each item:
   - Use prompt_user_confirmation() for each item
   - Fill department, category, designer, etc.
   - Upload images
   - Set price and options
   - Review and submit (or simulate in dry-run)

### Phase 4: Error Recovery with State Checking
- If any action fails, use detect_current_page_state() to understand why
- Take screenshot to visually debug the issue
- Use wait_and_retry() for actions that might need time to complete
- Always verify state before retrying failed actions

## CRITICAL RULES FOR STATE AWARENESS:

1. **NEVER ASSUME PAGE STATE**: Always check with detect_current_page_state()
2. **VERIFY BEFORE ACTION**: Use verify_sell_page_ready() before form filling
3. **CHECK AFTER NAVIGATION**: Always verify you ended up where expected
4. **HANDLE LOGIN PROPERLY**: Only use prompt_user_login() when popup actually detected
5. **VISUAL CONFIRMATION**: Take screenshots frequently for debugging
6. **WAIT FOR STABILITY**: Use wait_and_retry() for dynamic content

## STATE DETECTION PRIORITIES:
1. Use browser_snapshot to check current page content and URL
2. Look for page-specific elements (sell button, form fields, login modals)
3. Check page title and navigation elements
4. Take screenshot for visual confirmation
5. Report current state clearly before proceeding

## Available Tools:
- **State Tools**: detect_current_page_state, navigate_to_sell_page, verify_sell_page_ready
- **Browser Tools**: browser_navigate, browser_snapshot, browser_click, browser_type, browser_select_option
- **User Interaction**: prompt_user_login
- **Utility Tools**: wait_and_retry, expand_image_paths, validate_grailed_metadata
- **Data Tools**: file_read, file_write, gemini_image_reader

## SUCCESS CRITERIA:
- Always know what page you're on
- Never try to fill forms on wrong pages
- Handle login popups only when they actually appear
- Provide clear progress updates with state information
- Recover gracefully from navigation issues

Remember: STATE AWARENESS is the key to reliable browser automation!
"""

    # Combine all tools
    all_tools = [
        file_read, file_write, gemini_image_reader,
        expand_image_paths, validate_grailed_metadata,
        detect_current_page_state, navigate_to_sell_page, verify_sell_page_ready,
        prompt_user_login, wait_and_retry
    ] + playwright_tools
    
    # Create the agent
    agent = Agent(
        model=model,
        tools=all_tools,
        system_prompt=system_prompt
    )
    
    return agent

def run_with_mcp_context(command: str, filename: str, dry_run: bool = False):
    """Run the agent within the MCP context manager"""
    print("🤖 Initializing STATE-AWARE Grailed Listing Agent...")
    
    # Setup model
    model = setup_model()
    
    # Setup MCP Playwright client
    playwright_client, playwright_tools = setup_playwright_client()
    
    if playwright_client is None:
        print("⚠️  Running without browser automation capabilities")
        return "Browser automation not available"
    
    # Run within MCP context manager
    with playwright_client:
        print("✅ MCP Playwright client context active")
        
        # Create agent with MCP tools
        agent = create_agent_with_mcp(playwright_client, playwright_tools, model)
        
        # Run the command with specific instructions
        if command == "validate":
            print("✅ Validating listings file...")
            response = agent(f"Please validate the listings file: {filename}")
        elif command == "analyze":
            print("🔍 Analyzing images and generating metadata...")
            response = agent(f"Please analyze images and generate metadata for: {filename}")
        elif command == "run":
            mode = "DRY RUN" if dry_run else "LIVE"
            print(f"🚀 Creating Grailed listings in {mode} mode with STATE AWARENESS...")
            
            # Specific instructions for STATE-AWARE browser automation
            instructions = f"""
Create Grailed listings from {filename} in {'dry-run' if dry_run else 'live'} mode using STATE-AWARE automation.

IMPORTANT: This is a FULLY AUTOMATED workflow. Process ALL listings without requesting user confirmation for each item.

CRITICAL STATE-AWARE WORKFLOW:

1. **Load Data**: Read and validate listings from {filename}

2. **Initial Navigation with State Tracking**:
   - Navigate to https://www.grailed.com
   - Use detect_current_page_state() to confirm page loaded
   - Use browser_snapshot for state confirmation

3. **State-Aware Sell Page Navigation**:
   - Use detect_current_page_state() to see current page
   - If on homepage, click sell button
   - IMMEDIATELY after clicking: Use detect_current_page_state() again
   - Check for login popup and handle if present
   - Use navigate_to_sell_page() if needed to reach sell page

4. **Verify Ready State Before Form Filling**:
   - Use verify_sell_page_ready() to confirm form is ready
   - If not ready, troubleshoot and navigate properly
   - Only proceed when sell page is confirmed ready

5. **Process Each Item with State Awareness (FULLY AUTOMATED)**:
   - For each item in listings:
     - Verify still on sell page before filling forms
     - Fill all form fields with metadata automatically
     - Upload images using the provided image paths
     - Submit or simulate in dry-run mode
     - Check state after each major action
     - Continue to next item without user confirmation

6. **Error Recovery**:
   - If any action fails, use detect_current_page_state() to diagnose
   - Use browser_snapshot for debugging page state
   - Use wait_and_retry() for actions that need time
   - Always verify state before retrying

REMEMBER: Never assume page state - always check first!
"""
            
            response = agent(instructions)
        
        return response

def main():
    """Main entry point"""
    if len(sys.argv) < 3:
        print("Usage: python grailed_agent_state_aware.py <command> <filename> [--dry-run]")
        print("Commands: validate, analyze, run")
        sys.exit(1)
    
    command = sys.argv[1]
    filename = sys.argv[2]
    dry_run = "--dry-run" in sys.argv
    
    if command not in ["validate", "analyze", "run"]:
        print("❌ Invalid command. Use: validate, analyze, or run")
        sys.exit(1)
    
    try:
        response = run_with_mcp_context(command, filename, dry_run)
        print("=" * 60)
        print("AGENT RESPONSE:")
        print("=" * 60)
        print(response)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
