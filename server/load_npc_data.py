import os
import json
from pymongo import MongoClient, UpdateOne
from bson import ObjectId
from slugify import slugify # Using python-slugify

# Assuming your script is in the 'server' directory
# and character data is in 'server/app/data'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'app', 'data')
WORLD_DATA_FILES = ['world_events.json', 'world_locations.json', 'world_religions.json']


# --- Utility Functions ---
def generate_deterministic_id(name, data_source="generated"):
    """Generates a deterministic _id based on the character's name and source."""
    slug_name = slugify(name, separator='_')
    slug_source = slugify(data_source, separator='_')
    return f"{slug_source}_{slug_name}" if data_source else slug_name

def is_valid_objectid(value):
    """Checks if a value is a valid MongoDB ObjectId string."""
    try:
        ObjectId(value)
        return True
    except Exception:
        return False

def determine_id_for_character(item_data, filename_source, is_world_item=False): # Renamed function
    """
    Determines the _id for a character (PC/NPC) or world item.
    Priority:
    1. Valid 'id' in item_data (if not world_item).
    2. Valid '_id' in item_data.
    3. Generate a deterministic ID based on name and filename.
    """
    if is_world_item:
        # For world items, prioritize existing _id (string or ObjectId)
        if '_id' in item_data and item_data['_id']:
            if isinstance(item_data['_id'], ObjectId): return item_data['_id']
            # Allow string _id for world items, could be custom or from another system
            elif isinstance(item_data['_id'], str): 
                # If it can be a valid ObjectId, convert it, otherwise use as string
                return ObjectId(item_data['_id']) if is_valid_objectid(item_data['_id']) else item_data['_id']
        if 'name' in item_data and item_data['name']:
            return generate_deterministic_id(item_data['name'], data_source=os.path.splitext(filename_source)[0])
        # Fallback for world items without a name or _id
        return generate_deterministic_id(f"unnamed_world_item_{ObjectId()}", data_source=os.path.splitext(filename_source)[0])

    # For PCs/NPCs
    if 'id' in item_data and item_data['id'] and is_valid_objectid(item_data['id']): # Often from user uploads with 'id'
        return ObjectId(item_data['id'])
    if '_id' in item_data and item_data['_id']: # Prioritize existing '_id'
        if isinstance(item_data['_id'], ObjectId): return item_data['_id']
        if isinstance(item_data['_id'], str):
            # If it can be a valid ObjectId, convert it, otherwise use as string (e.g. previously generated slug)
            return ObjectId(item_data['_id']) if is_valid_objectid(item_data['_id']) else item_data['_id']

    # Fallback to generating a new deterministic ID
    name_for_id = item_data.get('name', f"unnamed_character_{filename_source.split('.')[0]}_{ObjectId()}") # Added ObjectId to ensure uniqueness if name is missing
    return generate_deterministic_id(name_for_id, data_source=os.path.splitext(filename_source)[0])


# --- Main Loading Logic ---
def load_character_data(): # Renamed function
    print("Starting Character Data Loader (PCs, NPCs, World Items)...")
    mongo_uri = os.getenv('MONGO_URI', "mongodb://localhost:27017/ttrpg_app_db")
    db_name = mongo_uri.split('/')[-1].split('?')[0]

    print(f"Connecting to MongoDB: {mongo_uri}")
    client = MongoClient(mongo_uri)
    db = client[db_name]
    
    # Single collection for PCs and NPCs, differentiated by 'type' field
    characters_collection = db.npcs # Collection name is still 'npcs'
    world_events_collection = db.world_events
    world_locations_collection = db.world_locations
    world_religions_collection = db.world_religions

    print(f"Connected to DB '{db_name}'. Target collection for PCs/NPCs: '{characters_collection.name}'.")

    json_files = [f for f in os.listdir(DATA_DIR) if f.endswith('.json')]
    print(f"Found JSON files: {', '.join(json_files)}")
    print("Processing files...\n")

    summary = {
        "files_processed": 0, "total_records": 0, "inserted": 0, 
        "updated": 0, "no_change": 0, "skipped": 0, "errors": 0
    }

    for filename in json_files:
        filepath = os.path.join(DATA_DIR, filename)
        summary["files_processed"] += 1
        file_stats = {"inserted": 0, "updated": 0, "no_change": 0, "skipped": 0, "errors": 0}
        print(f"--- Processing: {filename} ---")

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                raw_file_data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error reading/parsing {filename}: {e}. Skipping.")
            summary["errors"] += 1; file_stats["errors"] +=1; continue
        except Exception as e:
            print(f"An unexpected error occurred with {filename}: {e}. Skipping.")
            summary["errors"] += 1; file_stats["errors"] +=1; continue

        is_world_file = filename in WORLD_DATA_FILES
        current_collection = characters_collection
        current_collection_name_for_log = characters_collection.name 

        if filename == 'world_events.json':
            current_collection = world_events_collection
            current_collection_name_for_log = world_events_collection.name
        elif filename == 'world_locations.json':
            current_collection = world_locations_collection
            current_collection_name_for_log = world_locations_collection.name
        elif filename == 'world_religions.json':
            current_collection = world_religions_collection
            current_collection_name_for_log = world_religions_collection.name
        
        data_to_process_list = raw_file_data if isinstance(raw_file_data, list) else [raw_file_data]
        
        if not data_to_process_list:
            print(f"No data found in {filename}. Skipping.")
            continue

        print(f"Found {len(data_to_process_list)} item(s) in {filename}.")
        summary["total_records"] += len(data_to_process_list)
        operations = []

        for item_data_from_json in data_to_process_list:
            if not isinstance(item_data_from_json, dict):
                print(f"Warning [{filename}]: Found an item that is not a dictionary: {type(item_data_from_json)}. Skipping item.")
                file_stats["skipped"] +=1; summary["skipped"] +=1; continue
            
            data_for_db = item_data_from_json.copy() # Work with a copy
            item_name_for_log = data_for_db.get('name', 'Unnamed Item')
            
            original_type_in_json = data_for_db.get('type')
            print(f"    DEBUG [{filename} / {item_name_for_log}]: 'type' field as read from JSON: '{original_type_in_json}'")

            if not is_world_file: # This block is for PCs and NPCs, processed into the 'characters_collection' (db.npcs)
                if str(original_type_in_json).lower() == "pc": # Case-insensitive check for "pc"
                    data_for_db['type'] = "pc"
                    print(f"    DEBUG [{filename} / {item_name_for_log}]: Identified as PC. 'type' field set to 'pc'.")
                elif str(original_type_in_json).lower() == "npc": # Case-insensitive check for "npc"
                    data_for_db['type'] = "npc"
                    print(f"    DEBUG [{filename} / {item_name_for_log}]: Identified as NPC. 'type' field set to 'npc'.")
                else:
                    # If type is missing or something else (e.g. None, empty string, other values), default to 'npc'
                    print(f"    DEBUG [{filename} / {item_name_for_log}]: 'type' is missing or not 'pc'/'npc' (was: '{original_type_in_json}'). Defaulting character to 'npc'.")
                    data_for_db['type'] = 'npc'
            # For world files, 'type' might mean something else (e.g., event type, location type).
            # It will be preserved as is from the JSON if present, or remain absent if not in JSON.
            # No defaulting to 'pc' or 'npc' for world items.

            db_id = determine_id_for_character(data_for_db, filename, is_world_item=is_world_file)
            
            # Clean up 'id' field if it was a temporary one from some systems and we're using '_id'
            if 'id' in data_for_db and data_for_db['id'] != str(db_id) and is_valid_objectid(data_for_db['id']):
                 if isinstance(db_id, ObjectId) and ObjectId(data_for_db['id']) == db_id:
                    pass 
                 else:
                    del data_for_db['id']
            
            final_type_for_log = data_for_db.get('type', 'ITEM' if is_world_file else 'UNKNOWN_CHAR_TYPE').upper()
            print(f"    Info [{filename}]: Preparing {final_type_for_log} '{item_name_for_log}' with _id '{str(db_id)}' for collection '{current_collection_name_for_log}'")

            operations.append(
                UpdateOne({"_id": db_id}, {"$set": data_for_db}, upsert=True)
            )

        if operations:
            try:
                result = current_collection.bulk_write(operations, ordered=False)
                file_stats["inserted"] = result.upserted_count
                file_stats["updated"] = result.modified_count
                file_stats["no_change"] = result.matched_count - result.modified_count if result.matched_count > result.modified_count else 0
                summary["inserted"] += file_stats["inserted"]
                summary["updated"] += file_stats["updated"]
                summary["no_change"] += file_stats["no_change"]
            except Exception as e:
                print(f"Error during bulk write for {filename} into {current_collection_name_for_log}: {e}")
                summary["errors"] += len(operations); file_stats["errors"] += len(operations)
        
        print(f"Finished {filename}: {file_stats['inserted']} ins, {file_stats['updated']} upd, {file_stats['skipped']} skip, {file_stats['no_change']} no-chg, {file_stats['errors']} err.")
        print("-" * 20)

    print("\n--- Overall Load Summary ---")
    for key, val in summary.items(): print(f"{key.replace('_', ' ').capitalize()}: {val}")
    print("Load complete.")

if __name__ == '__main__':
    load_character_data()