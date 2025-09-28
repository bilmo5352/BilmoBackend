#!/usr/bin/env python3
"""
Convert Existing JSON Files to New MongoDB Format
This script reads existing JSON files and saves them in the new unified format
"""

import json
import os
import glob
from datetime import datetime
from unified_mongodb_manager import UnifiedMongoDBManager
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def convert_json_to_unified_format(json_file_path):
    """Convert existing JSON file to new unified format"""
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Check if it's already in the new format
        if 'success' in data and 'results' in data:
            logger.info(f"✅ File '{json_file_path}' is already in unified format")
            return data
        
        # Convert old format to new format
        unified_data = {
            "success": True,
            "query": extract_query_from_filename(json_file_path),
            "total_results": 0,
            "results": []
        }
        
        # Handle different JSON structures
        if isinstance(data, list):
            # If data is a list of results
            for item in data:
                if isinstance(item, dict) and 'site' in item:
                    unified_data["results"].append(item)
                    unified_data["total_results"] += item.get('total_products', 0)
        elif isinstance(data, dict):
            # If data is a single result object
            if 'site' in data:
                unified_data["results"].append(data)
                unified_data["total_results"] += data.get('total_products', 0)
            elif 'results' in data:
                # If it has a results key
                unified_data["results"] = data.get('results', [])
                unified_data["total_results"] = sum(result.get('total_products', 0) for result in unified_data["results"])
        
        logger.info(f"✅ Converted '{json_file_path}' to unified format")
        return unified_data
        
    except Exception as e:
        logger.error(f"❌ Failed to convert '{json_file_path}': {e}")
        return None

def extract_query_from_filename(filename):
    """Extract search query from filename"""
    basename = os.path.basename(filename)
    
    # Remove common prefixes and suffixes
    query = basename.replace('unified_search_', '').replace('amazon_products_', '').replace('_detailed_products_quick.json', '').replace('.json', '')
    
    # Handle date patterns
    import re
    query = re.sub(r'_\d{8}_\d{6}$', '', query)
    
    return query if query else 'unknown'

def main():
    """Main function to convert and upload JSON files"""
    print("🔄 Converting existing JSON files to new MongoDB format...")
    
    # Initialize MongoDB manager
    manager = UnifiedMongoDBManager()
    if not manager.connect():
        print("❌ Failed to connect to MongoDB")
        return
    
    # Find all JSON files
    json_patterns = [
        "unified_search_*.json",
        "amazon_products_*.json",
        "*_search_*.json"
    ]
    
    converted_files = []
    failed_files = []
    
    for pattern in json_patterns:
        json_files = glob.glob(pattern)
        for file_path in json_files:
            print(f"\n📄 Processing: {file_path}")
            
            # Convert to unified format
            unified_data = convert_json_to_unified_format(file_path)
            if unified_data:
                # Save to MongoDB
                result_id = manager.save_unified_search_result(unified_data)
                if result_id:
                    converted_files.append(file_path)
                    print(f"✅ Saved to MongoDB with ID: {result_id}")
                else:
                    failed_files.append(file_path)
                    print(f"❌ Failed to save to MongoDB")
            else:
                failed_files.append(file_path)
                print(f"❌ Failed to convert file")
    
    # Show summary
    print(f"\n📊 Conversion Summary:")
    print(f"✅ Successfully converted: {len(converted_files)} files")
    print(f"❌ Failed conversions: {len(failed_files)} files")
    
    if converted_files:
        print(f"\n✅ Converted files:")
        for file in converted_files:
            print(f"  - {file}")
    
    if failed_files:
        print(f"\n❌ Failed files:")
        for file in failed_files:
            print(f"  - {file}")
    
    # Show database stats
    print(f"\n📊 Database Statistics:")
    stats = manager.get_database_stats()
    if stats:
        print(f"Total documents: {stats['collection_stats'].get('unified_search_results', 0)}")
    
    manager.close()
    print("\n✅ Conversion completed!")

if __name__ == "__main__":
    main()
