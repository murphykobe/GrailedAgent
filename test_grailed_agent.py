#!/usr/bin/env python3
"""
Test version of Grailed Listing Agent using Strands Agents SDK
This version demonstrates the structure without requiring API keys
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

try:
    from strands import Agent, tool
    from strands_tools import file_read, file_write
    print("✅ Successfully imported Strands Agents SDK")
except ImportError as e:
    print(f"❌ Error importing Strands Agents SDK: {e}")
    print("Please install: pip install strands-agents strands-agents-tools")
    sys.exit(1)


@tool
def validate_listings_file(file_path: str) -> Dict[str, Any]:
    """
    Validate a Grailed listings JSON file.
    
    Args:
        file_path: Path to the listings.json file
        
    Returns:
        Dictionary with validation results
    """
    try:
        # Check if file exists
        if not Path(file_path).exists():
            return {
                "valid": False,
                "error": f"File not found: {file_path}",
                "items": []
            }
        
        # Load and parse JSON
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            return {
                "valid": False,
                "error": "JSON file must contain a list of items",
                "items": []
            }
        
        # Validate each item
        validation_results = []
        for i, item in enumerate(data):
            item_result = {
                "index": i,
                "valid": True,
                "errors": [],
                "warnings": [],
                "missing_metadata": []
            }
            
            # Check required fields
            required_fields = ["image_paths", "price"]
            for field in required_fields:
                if field not in item:
                    item_result["errors"].append(f"Missing required field: {field}")
                    item_result["valid"] = False
            
            # Check image paths
            if "image_paths" in item:
                for img_path in item["image_paths"]:
                    expanded_path = os.path.expanduser(img_path)
                    if not Path(expanded_path).exists():
                        item_result["warnings"].append(f"Image file not found: {img_path}")
            
            # Check for missing metadata
            metadata_fields = [
                "department", "category", "sub_category", "designer",
                "item_name", "size", "color", "condition", "description"
            ]
            for field in metadata_fields:
                if field not in item or item[field] is None:
                    item_result["missing_metadata"].append(field)
            
            validation_results.append(item_result)
        
        # Overall validation
        all_valid = all(item["valid"] for item in validation_results)
        total_errors = sum(len(item["errors"]) for item in validation_results)
        total_warnings = sum(len(item["warnings"]) for item in validation_results)
        
        return {
            "valid": all_valid,
            "total_items": len(data),
            "total_errors": total_errors,
            "total_warnings": total_warnings,
            "items": validation_results
        }
        
    except json.JSONDecodeError as e:
        return {
            "valid": False,
            "error": f"Invalid JSON: {str(e)}",
            "items": []
        }
    except Exception as e:
        return {
            "valid": False,
            "error": f"Validation error: {str(e)}",
            "items": []
        }


@tool
def analyze_listing_requirements(file_path: str) -> Dict[str, Any]:
    """
    Analyze what's needed for Grailed listings.
    
    Args:
        file_path: Path to the listings.json file
        
    Returns:
        Analysis of listing requirements
    """
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        analysis = {
            "total_items": len(data),
            "items_needing_metadata": 0,
            "items_ready": 0,
            "common_missing_fields": {},
            "recommendations": []
        }
        
        metadata_fields = [
            "department", "category", "sub_category", "designer",
            "item_name", "size", "color", "condition", "description"
        ]
        
        for item in data:
            missing_fields = []
            for field in metadata_fields:
                if field not in item or item[field] is None:
                    missing_fields.append(field)
                    analysis["common_missing_fields"][field] = analysis["common_missing_fields"].get(field, 0) + 1
            
            if missing_fields:
                analysis["items_needing_metadata"] += 1
            else:
                analysis["items_ready"] += 1
        
        # Generate recommendations
        if analysis["items_needing_metadata"] > 0:
            analysis["recommendations"].append(
                f"Run image analysis on {analysis['items_needing_metadata']} items to generate missing metadata"
            )
        
        if analysis["items_ready"] > 0:
            analysis["recommendations"].append(
                f"{analysis['items_ready']} items are ready for listing creation"
            )
        
        most_missing = max(analysis["common_missing_fields"].items(), key=lambda x: x[1]) if analysis["common_missing_fields"] else None
        if most_missing:
            analysis["recommendations"].append(
                f"Most commonly missing field: {most_missing[0]} (missing in {most_missing[1]} items)"
            )
        
        return analysis
        
    except Exception as e:
        return {
            "error": f"Analysis failed: {str(e)}"
        }


def create_test_agent() -> Agent:
    """Create a test agent for demonstration."""
    
    # Use a simple system prompt for testing
    system_prompt = """You are a Grailed Listing Agent assistant. You help users prepare and validate their Grailed listings.

You have access to tools for:
- Reading and writing files
- Validating listings data
- Analyzing listing requirements

When users ask you to validate or analyze listings, use the appropriate tools and provide helpful, detailed feedback.

Be helpful and provide actionable recommendations for improving their listings."""

    # Create agent with basic tools (no API key required for this demo)
    agent = Agent(
        model="us.anthropic.claude-3-5-sonnet-20241022-v2:0",  # This will fail gracefully
        tools=[file_read, file_write, validate_listings_file, analyze_listing_requirements],
        system_prompt=system_prompt
    )
    
    return agent


def main():
    """Main function for testing."""
    
    print("🧪 Testing Grailed Listing Agent Structure")
    print("="*50)
    
    # Test the validation tool directly
    print("\n📋 Testing validation tool...")
    result = validate_listings_file("listings.json")
    
    print(f"Validation result: {result}")
    
    # Test the analysis tool
    print("\n📊 Testing analysis tool...")
    analysis = analyze_listing_requirements("listings.json")
    
    print(f"Analysis result: {analysis}")
    
    print("\n✅ Strands Agent structure is working!")
    print("\nTo use with real API:")
    print("1. Set ANTHROPIC_API_KEY in .env file")
    print("2. Run: python grailed_agent.py validate listings.json")


if __name__ == "__main__":
    main()
