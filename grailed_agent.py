#!/usr/bin/env python3
"""
Grailed Listing Agent using Strands Agents SDK

This agent automates the creation of listings on Grailed.com using:
- AI-powered image analysis for metadata generation
- Browser automation via MCP Playwright server
- Sequential processing with error handling
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(
    format="%(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler()]
)
logging.getLogger("strands").setLevel(logging.INFO)

try:
    from strands import Agent, tool
    from strands_tools import file_read, file_write, image_reader
    print("✅ Successfully imported Strands Agents SDK")
except ImportError as e:
    print(f"❌ Error importing Strands Agents SDK: {e}")
    print("Please install: pip install strands-agents strands-agents-tools")
    sys.exit(1)

# Import MCP for Playwright browser automation
try:
    from mcp import StdioServerParameters, stdio_client
    from strands.tools.mcp import MCPClient
    print("✅ Successfully imported MCP tools")
except ImportError as e:
    print(f"❌ Error importing MCP tools: {e}")
    print("Please install: pip install mcp")
    sys.exit(1)


@tool
def expand_image_paths(image_paths: List[str]) -> List[str]:
    """
    Expand user home directory paths and validate image files exist.
    
    Args:
        image_paths: List of image file paths (may contain ~ for home directory)
        
    Returns:
        List of expanded absolute paths for existing image files
    """
    expanded_paths = []
    for path_str in image_paths:
        expanded_path = os.path.expanduser(path_str)
        abs_path = Path(expanded_path).resolve()
        
        if abs_path.exists() and abs_path.is_file():
            expanded_paths.append(str(abs_path))
        else:
            print(f"⚠️  Warning: Image file not found: {path_str}")
    
    return expanded_paths


@tool
def validate_grailed_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and normalize Grailed listing metadata.
    
    Args:
        metadata: Dictionary containing listing metadata
        
    Returns:
        Dictionary with validation results and normalized data
    """
    
    # Valid options for Grailed
    valid_departments = ['Menswear', 'Womenswear']
    valid_conditions = ['Brand New', 'Like New', 'Gently Used', 'Used', 'Very Worn']
    valid_colors = ['Black', 'White', 'Grey', 'Navy', 'Blue', 'Red', 'Green', 
                   'Brown', 'Beige', 'Pink', 'Purple', 'Yellow', 'Orange', 
                   'Multicolor', 'Indigo']
    
    errors = []
    warnings = []
    normalized = metadata.copy()
    
    # Validate department
    if 'department' in metadata:
        if metadata['department'] not in valid_departments:
            errors.append(f"Invalid department: {metadata['department']}")
    
    # Validate condition
    if 'condition' in metadata:
        condition = metadata['condition']
        # Handle case variations
        condition_title = condition.title()
        if condition_title in valid_conditions:
            normalized['condition'] = condition_title
        else:
            errors.append(f"Invalid condition: {condition}")
    
    # Validate color
    if 'color' in metadata:
        color = metadata['color']
        if color not in valid_colors:
            # Try to find close match
            color_lower = color.lower()
            for valid_color in valid_colors:
                if valid_color.lower() in color_lower or color_lower in valid_color.lower():
                    normalized['color'] = valid_color
                    warnings.append(f"Mapped color '{color}' to '{valid_color}'")
                    break
            else:
                warnings.append(f"Unusual color: {color}")
    
    return {
        'normalized_metadata': normalized,
        'errors': errors,
        'warnings': warnings,
        'is_valid': len(errors) == 0
    }


def create_grailed_agent() -> Agent:
    """Create and configure the Grailed Listing Agent."""
    
    # Setup MCP Playwright client for browser automation (optional)
    playwright_tools = []
    try:
        # Try different MCP server names
        server_commands = [
            ["npx", "@modelcontextprotocol/server-playwright"],
            ["npx", "mcp-server-playwright"],
            ["playwright-mcp-server"]
        ]
        
        for command in server_commands:
            try:
                playwright_client = MCPClient(lambda: stdio_client(
                    StdioServerParameters(
                        command=command[0],
                        args=command[1:] if len(command) > 1 else []
                    )
                ))
                
                with playwright_client:
                    playwright_tools = playwright_client.list_tools_sync()
                    print(f"✅ Loaded {len(playwright_tools)} Playwright tools via MCP")
                    break
            except Exception:
                continue
    
    except Exception as e:
        print(f"⚠️  Warning: Could not load Playwright MCP tools: {e}")
        print("   Browser automation will be limited. You can still use image analysis features.")
    
    # Configure model with better error handling
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
        except Exception as e:
            print(f"❌ Failed to setup Anthropic model: {e}")
            print("   Please set ANTHROPIC_API_KEY in your environment")
            raise
    else:
        # Try Bedrock as fallback
        try:
            model = "us.anthropic.claude-3-5-sonnet-20241022-v2:0"
            print("✅ Using Bedrock Claude model (ensure AWS credentials are configured)")
        except Exception as e:
            print(f"❌ Failed to setup Bedrock model: {e}")
            raise
    
    # Create the agent with comprehensive system prompt
    system_prompt = """You are a Grailed Listing Agent, an expert at automating the creation of fashion listings on Grailed.com.

## Your Capabilities:
1. **Image Analysis**: Analyze fashion product images to extract metadata
2. **Browser Automation**: Navigate Grailed.com and fill listing forms via Playwright MCP
3. **Data Validation**: Ensure listing data meets Grailed's requirements
4. **Sequential Processing**: Handle multiple items with error recovery

## Workflow Process:

### Phase 1: Metadata Generation & Validation
- Use file_read to load listings.json
- For items missing metadata, use image_reader to analyze product images
- Generate missing fields: department, category, sub_category, designer, item_name, size, color, condition, description
- Use validate_grailed_metadata to ensure data quality
- Present generated metadata for user approval
- Use file_write to save approved metadata back to listings.json

### Phase 2: Browser Navigation & Authentication
- Use Playwright MCP tools to launch browser and navigate to https://www.grailed.com
- Click sell button using selector: a[data-testid="desktop-sell"]
- Detect if login is required by checking for login indicators
- If login needed, guide user through manual login process
- Verify successful navigation to listing creation page

### Phase 3: Form Filling & Submission
For each item with complete metadata:
- Fill department/category dropdown: page.getByRole('textbox').filter({ hasText: 'Department / Category' })
- Select appropriate department: page.getByRole('menuitem', { name: 'Menswear' }) or 'Womenswear'
- Choose subcategory: page.getByRole('menuitem', { name: sub_category })
- Handle designer field: page.getByRole('textbox', { name: 'Search and add a Designer' })
  - For collaborations like "Brain Dead x A.P.C", select main designer first, then add collaboration
- Set size: page.locator('select[name="size"]').selectOption(size)
- Fill item name: page.getByRole('textbox', { name: 'Item name' })
- Select color: page.getByRole('textbox').filter({ hasText: 'Select a Color' })
- Set condition: page.locator('select[name="condition"]').selectOption(condition)
- Fill description: page.getByRole('textbox', { name: 'Add details about condition,' })
- Set price and options (accept_offers, smart_pricing, floor_price)
- Upload images using file input
- Publish listing: button[data-testid="publish-button"]

### Phase 4: Error Handling & Recovery
- Skip items with errors and continue processing
- Provide detailed error messages and suggestions
- Save progress after each successful operation
- Handle network timeouts and page loading issues gracefully

## Key Guidelines:
- Always validate image paths using expand_image_paths before processing
- Use validate_grailed_metadata to ensure data quality
- Handle designer collaborations properly (main designer + collaboration)
- Wait for page elements to load before interacting
- Provide clear status updates and progress information
- Skip failed items and continue with remaining ones
- Be helpful and provide actionable error messages

## Grailed-Specific Knowledge:
- Departments: Menswear, Womenswear
- Common categories: Outerwear, Tops, Bottoms, Footwear
- Subcategories: Denim Jackets, Straight Jeans, Button Up Shirts, etc.
- Conditions: Brand New, Like New, Gently Used, Used, Very Worn
- Colors: Black, White, Grey, Navy, Blue, Red, Green, Brown, Beige, Pink, Purple, Yellow, Orange, Multicolor, Indigo
- Handle collaborations like "Brain Dead x A.P.C" by selecting main brand first

You are helpful, efficient, and focused on creating high-quality Grailed listings."""

    # Create agent with all available tools
    all_tools = [
        file_read, file_write, image_reader,
        expand_image_paths, validate_grailed_metadata
    ] + playwright_tools
    
    agent = Agent(
        model=model,
        tools=all_tools,
        system_prompt=system_prompt
    )
    
    return agent


def main():
    """Main CLI interface for the Grailed Listing Agent."""
    
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Grailed Listing Agent using Strands Agents SDK",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python grailed_agent.py validate listings.json
  python grailed_agent.py analyze listings.json  
  python grailed_agent.py run listings.json --dry-run
  python grailed_agent.py run listings.json
        """
    )
    
    parser.add_argument("command", 
                       choices=["validate", "analyze", "run"],
                       help="Command to execute")
    parser.add_argument("file", 
                       help="Path to listings.json file")
    parser.add_argument("--dry-run", 
                       action="store_true",
                       help="Simulate actions without actual submission")
    parser.add_argument("--start-index", 
                       type=int, 
                       default=0,
                       help="Start processing from specific item index")
    parser.add_argument("--debug", 
                       action="store_true",
                       help="Enable debug logging")
    
    args = parser.parse_args()
    
    # Configure debug logging if requested
    if args.debug:
        logging.getLogger("strands").setLevel(logging.DEBUG)
    
    try:
        print("🤖 Initializing Grailed Listing Agent...")
        agent = create_grailed_agent()
        
        if args.command == "validate":
            print("✅ Validating listings file...")
            response = agent(f"""
Please validate the listings file '{args.file}':

1. Use file_read to load the JSON file
2. Check the structure and required fields
3. Use expand_image_paths to verify image files exist
4. Use validate_grailed_metadata for each item
5. Provide a detailed validation report

Focus on identifying any issues that would prevent successful listing creation.
""")
        
        elif args.command == "analyze":
            print("🔍 Analyzing images and generating metadata...")
            response = agent(f"""
Please analyze images and generate metadata for '{args.file}':

1. Use file_read to load the listings.json file
2. Identify items missing metadata fields
3. For each item needing analysis:
   - Use expand_image_paths to get valid image paths
   - Use image_reader to analyze the product images
   - Generate missing metadata (department, category, designer, etc.)
   - Use validate_grailed_metadata to ensure quality
4. Present generated metadata for user approval
5. Use file_write to save approved metadata back to the file

Generate accurate, Grailed-appropriate metadata for fashion items.
""")
        
        elif args.command == "run":
            mode = "DRY RUN" if args.dry_run else "LIVE"
            start_msg = f" starting from index {args.start_index}" if args.start_index > 0 else ""
            
            print(f"🚀 Creating Grailed listings in {mode} mode{start_msg}...")
            
            response = agent(f"""
Please create Grailed listings from '{args.file}' in {mode} mode{start_msg}:

1. Use file_read to load the listings data
2. Validate all items have complete metadata
3. Use Playwright MCP tools to:
   - Navigate to https://www.grailed.com
   - Click sell button: a[data-testid="desktop-sell"]
   - Handle login if required (guide user through manual login)
   - Navigate to listing creation page
4. For each item starting from index {args.start_index}:
   - Fill out the complete listing form
   - Upload images using expand_image_paths for valid paths
   - {"Simulate publishing (dry run)" if args.dry_run else "Publish the listing"}
5. Handle errors gracefully - skip failed items and continue
6. Provide detailed progress updates

{"This is a DRY RUN - simulate all browser actions without actually submitting listings." if args.dry_run else "This is LIVE MODE - create actual listings on Grailed.com."}

Process items sequentially and provide clear status updates.
""")
        
        print("\n" + "="*60)
        print("AGENT RESPONSE:")
        print("="*60)
        print(response)
        
    except KeyboardInterrupt:
        print("\n⚠️  Operation interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
