"""
Identify Snapshot Data Tool
Searches for specific values in snapshot-data.json to identify and analyze data.
Reads the current snapshot ID from runtime-files/current_snapshot.txt.
"""

import json
import re
import sys
from pathlib import Path
from typing import Any, List, Dict


def load_snapshot_data():
    """Load snapshot data from current snapshot"""
    # Read snapshot ID from current_snapshot.txt
    runtime_files_dir = Path(__file__).parent / "runtime-files"
    current_snapshot_file = runtime_files_dir / "current_snapshot.txt"
    
    if not current_snapshot_file.exists():
        print(f"Error: {current_snapshot_file} not found")
        return None, None
    
    # Parse snapshot_id from file
    with open(current_snapshot_file, 'r') as f:
        content = f.read().strip()
        if "snapshot_id = " in content:
            snapshot_id = content.split("snapshot_id = ")[1].strip()
        else:
            print(f"Error: Invalid format in {current_snapshot_file}")
            return None, None
    
    # Load snapshot-data.json from main folder (NOT from original-data)
    snapshot_dir = Path(__file__).parent.parent / "Snapshots" / snapshot_id
    snapshot_data_file = snapshot_dir / "snapshot-data.json"
    
    if not snapshot_data_file.exists():
        print(f"Error: {snapshot_data_file} not found")
        return None, None
    
    print(f"Loading snapshot: {snapshot_id}")
    
    with open(snapshot_data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return snapshot_id, data


def search_in_dict(obj: Any, search_value: str, path: str = "") -> List[Dict]:
    """Recursively search for a value in nested dictionary/list structures"""
    results = []
    
    if isinstance(obj, dict):
        for key, value in obj.items():
            current_path = f"{path}.{key}" if path else key
            
            # Check if the value matches
            if isinstance(value, str) and search_value.lower() in value.lower():
                results.append({
                    "path": current_path,
                    "key": key,
                    "value": value,
                    "parent": obj
                })
            elif isinstance(value, (int, float)) and str(search_value) == str(value):
                results.append({
                    "path": current_path,
                    "key": key,
                    "value": value,
                    "parent": obj
                })
            
            # Recurse into nested structures
            if isinstance(value, (dict, list)):
                results.extend(search_in_dict(value, search_value, current_path))
                
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            current_path = f"{path}[{idx}]"
            
            # Check if item matches
            if isinstance(item, str) and search_value.lower() in item.lower():
                results.append({
                    "path": current_path,
                    "index": idx,
                    "value": item,
                    "parent": obj
                })
            elif isinstance(item, (int, float)) and str(search_value) == str(item):
                results.append({
                    "path": current_path,
                    "index": idx,
                    "value": item,
                    "parent": obj
                })
            
            # Recurse into nested structures
            if isinstance(item, (dict, list)):
                results.extend(search_in_dict(item, search_value, current_path))
    
    return results


def search_by_id(data: Dict, search_id: str) -> List[Dict]:
    """Search specifically for an ID field"""
    print(f"\nSearching for ID: {search_id}")
    results = search_in_dict(data, search_id)
    return results


def display_results(results: List[Dict], search_value: str):
    """Display search results in a readable format"""
    if not results:
        print(f"\nNo results found for: {search_value}")
        return
    
    print(f"\nFound {len(results)} result(s):\n")
    
    for idx, result in enumerate(results, 1):
        print(f"Result #{idx}:")
        print(f"  Path: {result['path']}")
        print(f"  Value: {result['value']}")
        
        # Try to show parent context
        parent = result.get('parent')
        if isinstance(parent, dict) and len(parent) <= 20:
            print(f"  Context (parent object):")
            for k, v in list(parent.items())[:10]:
                value_str = str(v)[:100] if not isinstance(v, (dict, list)) else f"<{type(v).__name__}>"
                print(f"    {k}: {value_str}")
        
        print()


def find_references(data: Dict, target_value: str, result_path: str) -> Dict:
    """Find references to the target value in the data"""
    references = {
        "successor_demands": [],
        "predecessor_demands": [],
        "customer_orders": []
    }
    
    # Extract index from path (e.g., "demands[165]" -> 165)
    if "[" in result_path and "]" in result_path:
        try:
            index_str = result_path.split("[")[1].split("]")[0]
            target_index = int(index_str)
        except:
            target_index = None
    else:
        target_index = None
    
    # Search in demands for successors/predecessors
    if "demands" in data and isinstance(data["demands"], list):
        for idx, demand in enumerate(data["demands"]):
            if not isinstance(demand, dict):
                continue
            
            # Check if this demand has the target as successor
            successor = demand.get("successor", "").strip()
            if successor and target_value in successor:
                references["predecessor_demands"].append({
                    "index": idx,
                    "demandId": demand.get("demandId"),
                    "articleId": demand.get("articleId"),
                    "quantity": demand.get("quantity"),
                    "dueDate": demand.get("dueDate")
                })
            
            # Check if target demand has this as successor
            if target_index is not None and idx != target_index:
                target_demand = data["demands"][target_index] if target_index < len(data["demands"]) else {}
                target_successor = target_demand.get("successor", "").strip() if isinstance(target_demand, dict) else ""
                if target_successor:
                    demand_id = demand.get("demandId", "")
                    if demand_id and demand_id in target_successor:
                        references["successor_demands"].append({
                            "index": idx,
                            "demandId": demand_id,
                            "articleId": demand.get("articleId"),
                            "quantity": demand.get("quantity"),
                            "dueDate": demand.get("dueDate")
                        })
    
    # Search in customerOrderPositions
    if "customerOrderPositions" in data and isinstance(data["customerOrderPositions"], list):
        for idx, cop in enumerate(data["customerOrderPositions"]):
            if not isinstance(cop, dict):
                continue
            
            # Check if this customer order references the target demand
            cop_id = str(cop.get("id", ""))
            if target_value in cop_id or target_value in str(cop):
                references["customer_orders"].append({
                    "index": idx,
                    "esaromOrderNumber": cop.get("esaromOrderNumber"),
                    "customerName": cop.get("customerName"),
                    "articleId": cop.get("articleId"),
                    "quantity": cop.get("quantity"),
                    "dueDate": cop.get("dueDate")
                })
    
    return references


def get_article_context(data: Dict, article_id: Any) -> Dict:
    """Get context information about an article"""
    if "articles" not in data or not isinstance(data["articles"], list):
        return {}
    
    for article in data["articles"]:
        if not isinstance(article, dict):
            continue
        if str(article.get("id")) == str(article_id):
            return {
                "id": article.get("id"),
                "name": article.get("name"),
                "departmentName": article.get("departmentName"),
                "minBatchSize": article.get("minBatchSize"),
                "maxBatchSize": article.get("maxBatchSize")
            }
    
    return {}


def build_enriched_context(data: Dict, search_mode: str, search_value: str, results: List[Dict]) -> Dict:
    """Build enriched context with examples, patterns, and related entities for LLM"""
    enriched = {
        "field_examples": {},
        "format_patterns": {},
        "related_entities": {}
    }
    
    # Collect field examples from demands array (first 10 non-empty values)
    if "demands" in data and isinstance(data["demands"], list):
        field_examples = {}
        
        # Key fields to collect examples for
        key_fields = ["demandId", "articleId", "packaging", "successor", "dispatcherGroup"]
        
        for field in key_fields:
            examples = []
            for demand in data["demands"]:
                if isinstance(demand, dict) and field in demand:
                    value = demand.get(field)
                    if value and value != "" and value not in examples:
                        examples.append(value)
                        if len(examples) >= 10:
                            break
            if examples:
                field_examples[field] = examples
        
        enriched["field_examples"] = field_examples
        
        # Pattern analysis for the error field
        if search_mode == "empty_field":
            field_name = search_value
            pattern_data = {
                "field_name": field_name,
                "total_count": 0,
                "non_empty_count": 0,
                "sample_values": [],
                "length_range": {"min": None, "max": None},
                "detected_patterns": []
            }
            
            lengths = []
            for demand in data["demands"]:
                if isinstance(demand, dict) and field_name in demand:
                    pattern_data["total_count"] += 1
                    value = demand.get(field_name)
                    if value and str(value).strip():
                        pattern_data["non_empty_count"] += 1
                        str_value = str(value)
                        lengths.append(len(str_value))
                        if len(pattern_data["sample_values"]) < 5:
                            pattern_data["sample_values"].append(str_value)
            
            if lengths:
                pattern_data["length_range"]["min"] = min(lengths)
                pattern_data["length_range"]["max"] = max(lengths)
            
            # Simple pattern detection
            samples = pattern_data["sample_values"]
            if samples:
                # Check for common prefixes
                if all(s.startswith('D') for s in samples if len(s) > 0):
                    pattern_data["detected_patterns"].append("Starts with 'D'")
                # Check for underscore separator
                if all('_' in s for s in samples):
                    pattern_data["detected_patterns"].append("Contains underscore separator")
            
            enriched["format_patterns"][field_name] = pattern_data
        
        # Related entities
        related = {}
        
        # For error results, find demands with same articleId
        if results:
            article_ids = set()
            for r in results:
                parent = r.get("parent", {})
                if isinstance(parent, dict) and "articleId" in parent:
                    article_ids.add(parent.get("articleId"))
            
            if article_ids:
                demands_same_article = []
                for demand in data["demands"]:
                    if isinstance(demand, dict):
                        if demand.get("articleId") in article_ids:
                            demands_same_article.append({
                                "demandId": demand.get("demandId"),
                                "articleId": demand.get("articleId"),
                                "quantity": demand.get("quantity"),
                                "dueDate": demand.get("dueDate")
                            })
                            if len(demands_same_article) >= 5:
                                break
                
                if demands_same_article:
                    related["demands_same_article"] = demands_same_article
        
        # Collect all valid demand IDs for reference checking
        all_demand_ids = []
        for demand in data["demands"]:
            if isinstance(demand, dict) and "demandId" in demand:
                demand_id = demand.get("demandId")
                if demand_id and str(demand_id).strip():
                    all_demand_ids.append(str(demand_id))
        
        if all_demand_ids:
            related["all_valid_demand_ids"] = all_demand_ids[:20]  # First 20 for reference
        
        enriched["related_entities"] = related
    
    return enriched


def search_empty_field(obj: Any, field_name: str, path: str = "") -> List[Dict]:
    """Search for objects where a specific field is empty, null, or whitespace-only"""
    results = []
    
    if isinstance(obj, dict):
        # Check if this dict has the field and it's empty
        if field_name in obj:
            value = obj[field_name]
            is_empty = (
                value is None or 
                value == "" or 
                (isinstance(value, str) and value.strip() == "")
            )
            if is_empty:
                results.append({
                    "path": f"{path}.{field_name}" if path else field_name,
                    "key": field_name,
                    "value": value,
                    "parent": obj
                })
        
        # Recurse into nested structures
        for key, val in obj.items():
            current_path = f"{path}.{key}" if path else key
            if isinstance(val, (dict, list)):
                results.extend(search_empty_field(val, field_name, current_path))
                
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            current_path = f"{path}[{idx}]"
            if isinstance(item, (dict, list)):
                results.extend(search_empty_field(item, field_name, current_path))
    
    return results


def get_latest_iteration_dir(snapshot_dir: Path) -> Path:
    """Find the iteration folder with the highest number"""
    iteration_pattern = re.compile(r'^iteration-(\d+)$')
    max_iteration = 0
    
    for item in snapshot_dir.iterdir():
        if item.is_dir():
            match = iteration_pattern.match(item.name)
            if match:
                iteration_num = int(match.group(1))
                max_iteration = max(max_iteration, iteration_num)
    
    if max_iteration > 0:
        return snapshot_dir / f"iteration-{max_iteration}"
    return None


def main():
    """Main function"""
    # Check for command line arguments
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Search by value: python identify_snapshot.py <search_value>")
        print("  Search empty fields: python identify_snapshot.py --empty <field_name>")
        print("\nExamples:")
        print("  python identify_snapshot.py D830081_005")
        print("  python identify_snapshot.py --empty demandId")
        return
    
    # Check for empty field search mode
    if sys.argv[1] == "--empty":
        if len(sys.argv) < 3:
            print("Error: Field name required for --empty mode")
            print("Example: python identify_snapshot.py --empty demandId")
            return
        
        field_name = sys.argv[2]
        search_mode = "empty_field"
        search_value = field_name
        
        # Load snapshot data
        snapshot_id, data = load_snapshot_data()
        if data is None:
            return
        
        print(f"Snapshot data loaded successfully")
        print(f"\nSearching for empty '{field_name}' fields...")
        
        # Search for empty fields
        results = search_empty_field(data, field_name)
        
    else:
        # Regular value search mode
        search_value = sys.argv[1]
        search_mode = "value"
        
        # Load snapshot data
        snapshot_id, data = load_snapshot_data()
        if data is None:
            return
        
        print(f"Snapshot data loaded successfully")
        
        # Search for the value
        results = search_by_id(data, search_value)
    
    # Display results
    display_results(results, search_value)
    
    # Save enhanced results to file in snapshot directory
    if results:
        snapshot_dir = Path(__file__).parent.parent / "Snapshots" / snapshot_id
        output_file = snapshot_dir / "last_search_results.json"
        
        # Determine error type based on search mode and results
        if search_mode == "empty_field":
            error_type = "EMPTY_FIELD"
        else:
            error_type = "DUPLICATE_ID" if len(results) > 1 else "SINGLE_MATCH"
        
        # Prepare enhanced results for JSON
        json_results = []
        for r in results:
            parent = r.get("parent", {})
            path = r.get("path", "")
            
            # Get references
            references = find_references(data, search_value, path)
            
            # Get article context if parent has articleId
            article_context = {}
            if isinstance(parent, dict) and "articleId" in parent:
                article_context = get_article_context(data, parent.get("articleId"))
            
            json_results.append({
                "path": path,
                "value": r["value"],
                "original_object": parent if isinstance(parent, dict) else {},
                "references": references,
                "article_context": article_context
            })
        
        # Build context section
        context = {
            "total_demands_count": len(data.get("demands", [])) if "demands" in data else 0,
            "total_customer_orders": len(data.get("customerOrderPositions", [])) if "customerOrderPositions" in data else 0,
            "validation_rules": {
                "demandId_must_be_unique": True,
                "successor_must_reference_valid_demand": True
            }
        }
        
        # Build original_structure section (array of original objects as they appear in the file)
        original_structure = []
        for r in results:
            parent = r.get("parent", {})
            if isinstance(parent, dict) and parent:
                original_structure.append(parent)
        
        # Build enriched context for LLM
        enriched_context = build_enriched_context(data, search_mode, search_value, results)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "snapshot_id": snapshot_id,
                "search_mode": search_mode,
                "search_value": search_value,
                "error_type": error_type,
                "results_count": len(results),
                "original_structure": original_structure,
                "results": json_results,
                "context": context,
                "enriched_context": enriched_context
            }, f, indent=2, ensure_ascii=False)
        
        print(f"Enhanced results saved to: {output_file}")
        
        # Also save to latest iteration folder if it exists
        latest_iteration_dir = get_latest_iteration_dir(snapshot_dir)
        if latest_iteration_dir:
            iteration_output_file = latest_iteration_dir / "last_search_results.json"
            with open(iteration_output_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "snapshot_id": snapshot_id,
                    "search_mode": search_mode,
                    "search_value": search_value,
                    "error_type": error_type,
                    "results_count": len(results),
                    "original_structure": original_structure,
                    "results": json_results,
                    "context": context,
                    "enriched_context": enriched_context
                }, f, indent=2, ensure_ascii=False)
            print(f"Enhanced results also saved to: {iteration_output_file}")
        
        print(f"Error Type: {error_type}")
        print(f"Total demands in snapshot: {context['total_demands_count']}")


if __name__ == "__main__":
    main()
