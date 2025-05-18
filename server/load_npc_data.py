# server/load_npc_data.py
import os
import json
from pymongo import MongoClient, errors # type: ignore
from dotenv import load_dotenv
import glob # To find all json files

# Determine the base directory of the server
SERVER_DIR = os.path.dirname(os.path.abspath(__file__))

# Load environment variables from .env file in the server directory
dotenv_path = os.path.join(SERVER_DIR, '.env')
load_dotenv(dotenv_path)

# --- Configuration ---
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/ttrpg_app_db')
DATABASE_NAME = MONGO_URI.split('/')[-1].split('?')[0] 
NPC_COLLECTION_NAME = 'npcs'  # Collection where NPCs will be stored
# Directory containing the NPC JSON files
NPC_DATA_DIR_PATH = os.path.join(SERVER_DIR, 'app', 'data') 

def process_npc_data(npc_raw_data, npc_collection, file_name="Unknown File"):
    """
    Processes a single raw NPC data object (dictionary) and loads it into MongoDB.
    Returns a tuple: (was_inserted, was_updated, was_skipped)
    """
    inserted, updated, skipped = 0, 0, 0

    if not isinstance(npc_raw_data, dict):
        print(f"Warning [{file_name}]: Item is not a valid NPC object (dictionary). Skipping: {str(npc_raw_data)[:100]}")
        return 0, 0, 1

    # Ensure there's an _id.
    # Prioritize '_id', then 'id', then generate from 'name' or a default.
    if '_id' in npc_raw_data:
        npc_id = npc_raw_data['_id']
    elif 'id' in npc_raw_data:
        npc_id = npc_raw_data['id']
        print(f"Info [{file_name}]: NPC '{npc_raw_data.get('name', 'Unnamed')}' using 'id' field as '_id': {npc_id}")
    else:
        # Use a more robust way to generate an ID if name is missing or generic
        base_name_for_id = npc_raw_data.get('name', f'npc_from_{os.path.splitext(file_name)[0]}').lower().replace(' ', '_').replace('-', '_')
        # Attempt to make it somewhat unique if multiple NPCs have same name in same file
        # This is still not foolproof for global uniqueness without a proper sequence or UUID
        temp_id_candidate = base_name_for_id
        # In a real scenario, you might query DB to ensure uniqueness or use UUIDs
        npc_id = temp_id_candidate 
        print(f"Warning [{file_name}]: NPC '{npc_raw_data.get('name', 'Unnamed')}' missing '_id' and 'id'. Generated _id: '{npc_id}'")
    
    # --- CRUCIAL: Field Mapping ---
    # You MUST customize this section if your JSON files have different field names
    # for common attributes like name, appearance, personality traits, etc.
    # This example assumes common field names or uses .get() with fallbacks.
    npc_doc = {
        '_id': npc_id, # Ensure this is unique across all NPCs from all files
        'name': npc_raw_data.get('name', 'Unnamed NPC'),
        'appearance': npc_raw_data.get('appearance', 'No description available.'),
        'personality_traits': npc_raw_data.get('personality_traits', []),
        'source_file': file_name # Track which file the NPC came from
        # Add any other fields from your JSON files that you want to store.
        # Example:
        # 'race': npc_raw_data.get('race'),
        # 'class': npc_raw_data.get('class'),
        # 'stats': npc_raw_data.get('stats', {}),
        # 'notes': npc_raw_data.get('notes', '')
    }
    # Remove None values if you don't want to store keys with None
    # npc_doc = {k: v for k, v in npc_doc.items() if v is not None}

    try:
        result = npc_collection.update_one(
            {'_id': npc_doc['_id']},
            {'$set': npc_doc},
            upsert=True
        )
        if result.upserted_id:
            inserted = 1
        elif result.matched_count > 0 and result.modified_count > 0:
            updated = 1
        # If matched_count > 0 and modified_count == 0, data was identical.
            
    except errors.PyMongoError as e:
        print(f"MongoDB error for NPC with _id '{npc_doc['_id']}' from {file_name}: {e}. Skipping.")
        skipped = 1
    except Exception as e:
        print(f"Unexpected error for NPC with _id '{npc_doc['_id']}' from {file_name}: {e}. Skipping.")
        skipped = 1
    
    return inserted, updated, skipped

def load_npcs_to_db():
    """
    Connects to MongoDB, finds all .json files in NPC_DATA_DIR_PATH,
    reads NPC data from them, and inserts/updates them into the collection.
    """
    try:
        print(f"Attempting to connect to MongoDB at: {MONGO_URI}")
        client = MongoClient(MONGO_URI)
        client.admin.command('ping') 
        db = client[DATABASE_NAME]
        npc_collection = db[NPC_COLLECTION_NAME]
        print(f"Successfully connected to database '{DATABASE_NAME}' and collection '{NPC_COLLECTION_NAME}'.")
    except errors.ConnectionFailure as e:
        print(f"Fatal: Could not connect to MongoDB. Error: {e}")
        return
    except Exception as e:
        print(f"Fatal: An unexpected error occurred during MongoDB connection: {e}")
        return

    total_npcs_processed_from_files = 0
    total_npcs_inserted = 0
    total_npcs_updated = 0
    total_npcs_skipped = 0

    if not os.path.isdir(NPC_DATA_DIR_PATH):
        print(f"Error: NPC data directory not found at {NPC_DATA_DIR_PATH}")
        return

    # Find all .json files in the specified directory
    json_files = glob.glob(os.path.join(NPC_DATA_DIR_PATH, '*.json'))

    if not json_files:
        print(f"No .json files found in {NPC_DATA_DIR_PATH}. Nothing to load.")
        return

    print(f"Found JSON files to process: {', '.join(os.path.basename(f) for f in json_files)}")
    print("Starting data import process for all files...")

    for json_file_path in json_files:
        file_name = os.path.basename(json_file_path)
        print(f"\n--- Processing file: {file_name} ---")
        
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data_from_file = json.load(f)
        except FileNotFoundError:
            print(f"Error: File {file_name} disappeared during processing. Skipping.")
            continue
        except json.JSONDecodeError as e:
            print(f"Error: Could not decode JSON from {file_name}. Check its format. Details: {e}. Skipping file.")
            continue
        except Exception as e:
            print(f"An error occurred while reading or parsing {file_name}: {e}. Skipping file.")
            continue

        npcs_in_current_file = []
        if isinstance(data_from_file, list):
            # File contains a list of NPCs
            npcs_in_current_file = data_from_file
            print(f"Found {len(npcs_in_current_file)} NPC entries (as a list) in {file_name}.")
        elif isinstance(data_from_file, dict):
            # File contains a single NPC object
            npcs_in_current_file = [data_from_file] # Treat as a list with one item
            print(f"Found 1 NPC entry (as a single object) in {file_name}.")
        else:
            print(f"Warning: Data in {file_name} is not a list or a single NPC object. Skipping file.")
            continue
        
        file_inserted, file_updated, file_skipped = 0, 0, 0
        for i, npc_raw in enumerate(npcs_in_current_file):
            total_npcs_processed_from_files +=1
            inserted, updated, skipped = process_npc_data(npc_raw, npc_collection, file_name)
            file_inserted += inserted
            file_updated += updated
            file_skipped += skipped
        
        print(f"Finished processing {file_name}: {file_inserted} inserted, {file_updated} updated, {file_skipped} skipped.")
        total_npcs_inserted += file_inserted
        total_npcs_updated += file_updated
        total_npcs_skipped += file_skipped

    print(f"\n--- Overall Load Summary ---")
    print(f"Total JSON files processed: {len(json_files)}")
    print(f"Total NPC records encountered in files: {total_npcs_processed_from_files}")
    print(f"Total NPCs successfully inserted into DB: {total_npcs_inserted}")
    print(f"Total NPCs successfully updated in DB: {total_npcs_updated}")
    print(f"Total NPCs skipped due to errors/format issues: {total_npcs_skipped}")
    print(f"Data loading process complete. Check collection '{NPC_COLLECTION_NAME}' in database '{DATABASE_NAME}'.")

    client.close()

if __name__ == '__main__':
    print("Starting NPC data loading script for all JSON files in app/data/ ...")
    load_npcs_to_db()
