#!/usr/bin/env python3
"""
Setup script for Grailed Listing Agent using Strands Agents SDK
"""

import os
import subprocess
import sys
from pathlib import Path

def check_python_version():
    """Check Python version compatibility."""
    if sys.version_info < (3, 9):
        print("❌ Python 3.9 or higher is required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")
    return True

def install_strands_agents():
    """Install Strands Agents SDK."""
    print("\n📦 Installing Strands Agents SDK...")
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements_strands.txt"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Strands Agents SDK installed successfully")
            return True
        else:
            print(f"❌ Failed to install Strands Agents SDK: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error installing Strands Agents SDK: {str(e)}")
        return False

def check_node_js():
    """Check if Node.js is available for MCP Playwright server."""
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Node.js {result.stdout.strip()}")
            return True
        else:
            print("❌ Node.js not found")
            return False
    except FileNotFoundError:
        print("❌ Node.js not found")
        print("   Please install Node.js from https://nodejs.org/")
        return False

def setup_playwright_mcp():
    """Setup Playwright MCP server for browser automation."""
    print("\n🎭 Setting up Playwright MCP server...")
    
    try:
        # Install Playwright MCP server globally
        result = subprocess.run([
            "npm", "install", "-g", "@modelcontextprotocol/server-playwright"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Playwright MCP server installed")
        else:
            print(f"❌ Failed to install Playwright MCP server: {result.stderr}")
            return False
        
        # Install Playwright browsers
        result = subprocess.run([
            "npx", "playwright", "install", "chromium"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Playwright browsers installed")
        else:
            print(f"⚠️  Warning: Failed to install browsers: {result.stderr}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting up Playwright MCP: {str(e)}")
        return False

def create_env_file():
    """Create environment configuration file."""
    env_file = Path(".env")
    
    if not env_file.exists():
        print("\n📝 Creating .env configuration file...")
        
        env_content = """# AI Model Configuration
# Choose your model provider: bedrock, anthropic, litellm
AI_MODEL_PROVIDER=bedrock

# For Bedrock (default) - ensure you have AWS credentials configured
# AWS_PROFILE=default
# AWS_REGION=us-west-2

# For direct Anthropic API (if AI_MODEL_PROVIDER=anthropic)
# ANTHROPIC_API_KEY=your_anthropic_api_key_here

# For LiteLLM (OpenAI, etc.) - if AI_MODEL_PROVIDER=litellm  
# OPENAI_API_KEY=your_openai_api_key_here

# Grailed Configuration
GRAILED_BASE_URL=https://www.grailed.com

# Logging Level
LOG_LEVEL=INFO
"""
        
        env_file.write_text(env_content)
        print("✅ Created .env file")
    else:
        print("✅ .env file already exists")

def test_strands_import():
    """Test Strands Agents import."""
    print("\n🧪 Testing Strands Agents import...")
    
    try:
        import strands
        from strands import Agent
        from strands_tools import file_read, file_write
        print("✅ Strands Agents SDK imports working")
        return True
    except ImportError as e:
        print(f"❌ Strands Agents import failed: {e}")
        return False

def test_mcp_import():
    """Test MCP import."""
    print("🧪 Testing MCP import...")
    
    try:
        from mcp import StdioServerParameters, stdio_client
        from strands.tools.mcp import MCPClient
        print("✅ MCP imports working")
        return True
    except ImportError as e:
        print(f"❌ MCP import failed: {e}")
        return False

def create_example_listings():
    """Create example listings.json file."""
    listings_file = Path("listings.json")
    
    if not listings_file.exists():
        print("\n📄 Creating example listings.json...")
        
        example_data = [
            {
                "image_paths": [
                    "~/path/to/your/item1_front.jpg",
                    "~/path/to/your/item1_back.jpg"
                ],
                "price": 120.0,
                "accept_offers": True,
                "smart_pricing": True,
                "floor_price": 90.0,
                "country_of_origin": "USA"
            },
            {
                "image_paths": [
                    "~/path/to/your/item2_1.jpg",
                    "~/path/to/your/item2_2.jpg"
                ],
                "price": 85.0,
                "accept_offers": False,
                "smart_pricing": False,
                "country_of_origin": "Japan"
            }
        ]
        
        import json
        with open(listings_file, 'w') as f:
            json.dump(example_data, f, indent=2)
        
        print("✅ Created example listings.json")
    else:
        print("✅ listings.json already exists")

def main():
    """Main setup function."""
    print("🚀 Setting up Grailed Listing Agent with Strands Agents SDK")
    print("="*60)
    
    success = True
    
    # Check Python version
    if not check_python_version():
        success = False
    
    # Install Strands Agents
    if success and not install_strands_agents():
        success = False
    
    # Check Node.js for MCP
    if success and not check_node_js():
        print("⚠️  Node.js not found - browser automation will not work")
        print("   Install Node.js from https://nodejs.org/ to enable browser features")
        success = False
    
    # Setup Playwright MCP
    if success and not setup_playwright_mcp():
        print("⚠️  Playwright MCP setup failed - browser automation may not work")
    
    # Create configuration files
    create_env_file()
    create_example_listings()
    
    # Test imports
    if success and not test_strands_import():
        success = False
    
    if success and not test_mcp_import():
        print("⚠️  MCP imports failed - browser automation may not work")
    
    print("\n" + "="*60)
    
    if success:
        print("✅ Setup completed successfully!")
        print("\n📋 Next steps:")
        print("1. Configure your model provider in .env file:")
        print("   - For Bedrock: Ensure AWS credentials are configured")
        print("   - For Anthropic: Add ANTHROPIC_API_KEY to .env")
        print("   - For OpenAI: Add OPENAI_API_KEY to .env")
        print("2. Update listings.json with your actual item data and image paths")
        print("3. Test the agent:")
        print("   python grailed_agent.py validate listings.json")
        print("   python grailed_agent.py analyze listings.json")
        print("   python grailed_agent.py run listings.json --dry-run")
    else:
        print("❌ Setup completed with errors")
        print("Please resolve the issues above before using the agent")
        sys.exit(1)

if __name__ == "__main__":
    main()
