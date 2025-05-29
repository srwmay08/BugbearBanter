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

<<<<<<< HEAD
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
=======
    npc_id_source = "unknown"
    # Use name from Vuthausk's specific structure if it's him for ID gen before general mapping
    if file_name.lower() == 'vuthausk.json' and not is_soul_npc and 'character_details' in npc_raw_data:
         actual_name_for_id = npc_raw_data.get('character_details', {}).get('basic_information', {}).get('name', 'vuthausk')
         npc_name_for_id_gen = actual_name_for_id.lower().replace(' ', '_').replace('-', '_')
    else:
        npc_name_for_id_gen = npc_raw_data.get('name', 'unnamed').lower().replace(' ', '_').replace('-', '_')

    
    if '_id' in npc_raw_data and npc_raw_data['_id']:
        npc_id = npc_raw_data['_id']
        npc_id_source = "_id field"
    elif 'id' in npc_raw_data and npc_raw_data['id']:
        npc_id = npc_raw_data['id']
        npc_id_source = "id field"
    else:
        file_name_part = os.path.splitext(file_name)[0].lower().replace(' ', '_').replace('-', '_')
        base_id_prefix = f"{file_name_part}_soul_" if is_soul_npc else f"{file_name_part}_"
        
        temp_id = f"{base_id_prefix}{npc_name_for_id_gen}"
        
        if is_soul_npc and len(npc_name_for_id_gen) > 20: 
            npc_name_for_id_gen_short = npc_name_for_id_gen[:20]
            temp_id = f"{base_id_prefix}{npc_name_for_id_gen_short}"


        existing_doc = npc_collection.find_one({"_id": temp_id})
        if existing_doc and existing_doc.get('name') != npc_raw_data.get('name'): 
            npc_id = f"{temp_id}_{str(uuid.uuid4())[:4]}"
            print(f"Warning [{file_name}]: Generated _id '{temp_id}' might conflict for '{npc_raw_data.get('name', 'Unnamed')}'. Appended UUID part: '{npc_id}'")
        else:
            npc_id = temp_id

        npc_id_source = "generated"
    
    # --- Field Mapping ---
    name = npc_raw_data.get('name', 'Unnamed NPC')
    appearance = npc_raw_data.get('appearance', 'No description available.')
    
    # Refinement 4: Ensure personality_traits is a list
    personality_traits_raw = npc_raw_data.get('personality_traits', [])
    if isinstance(personality_traits_raw, str):
        personality_traits = [trait.strip() for trait in personality_traits_raw.split(',') if trait.strip()]
    elif isinstance(personality_traits_raw, list):
        personality_traits = personality_traits_raw
    else:
        personality_traits = []

    backstory = npc_raw_data.get('backstory', '')
    motivations = npc_raw_data.get('motivations', '')
    flaws = npc_raw_data.get('flaws', '')
    race = npc_raw_data.get('race')
    npc_class = npc_raw_data.get('class') 
    ideals = npc_raw_data.get('ideals', '')
    bonds = npc_raw_data.get('bonds', '')
    speech_patterns = npc_raw_data.get('speech_patterns', '')
    mannerisms = npc_raw_data.get('mannerisms', '')


    if file_name.lower() == 'vuthausk.json' and not is_soul_npc and 'character_details' in npc_raw_data:
        details = npc_raw_data.get('character_details', {})
        basic_info = details.get('basic_information', {})
        personality_backstory_info = details.get('personality_and_backstory', {}) # Corrected key

        name = basic_info.get('name', name)
        race = basic_info.get('race', race)
        npc_class = basic_info.get('class', npc_class) 
        
        appearance_parts = [basic_info.get('race', ''), basic_info.get('class', ''), f"Age: {basic_info.get('age', '')}"]
        appearance = ", ".join(filter(None, appearance_parts)) + f". Alignment: {basic_info.get('alignment', '')}"
        
        # Re-process personality_traits for Vuthausk if it's a string in his specific structure
        vuthausk_traits_raw = personality_backstory_info.get('personality_traits', personality_traits_raw)
        if isinstance(vuthausk_traits_raw, str):
            personality_traits = [trait.strip() for trait in vuthausk_traits_raw.split(',') if trait.strip()]
        elif isinstance(vuthausk_traits_raw, list): # If it was already a list or became one
             personality_traits = vuthausk_traits_raw
        # else: it keeps the general parsed one or empty list

        backstory = personality_backstory_info.get('backstory', backstory)
        motivations = personality_backstory_info.get('motivations', motivations)
        flaws = personality_backstory_info.get('flaws', flaws)
        ideals = personality_backstory_info.get('ideals', ideals)
        bonds = personality_backstory_info.get('bonds', bonds)
        speech_patterns = details.get('speech_and_mannerisms', {}).get('speech_patterns', speech_patterns)
        mannerisms = details.get('speech_and_mannerisms', {}).get('mannerisms', mannerisms)

    
    npc_doc = {
        '_id': npc_id,
        'name': name,
        'appearance': appearance,
        'personality_traits': personality_traits, # Should be a list now
        'backstory': backstory,
        'motivations': motivations,
        'flaws': flaws,
        'race': race,
        'class': npc_class, 
        'ideals': ideals,
        'bonds': bonds,
        'speech_patterns': speech_patterns,
        'mannerisms': mannerisms,
        'source_file': file_name,
        'is_soul_npc': is_soul_npc,
        'main_npc_id_if_soul': main_npc_id_for_soul if is_soul_npc else None,
        'memories': [] # Initialize memories array
    }
    # Clean out None values or empty strings/lists before insertion if desired, but ensure 'memories: []' stays
    npc_doc_cleaned = {k: v for k, v in npc_doc.items() if v is not None and v != '' and (isinstance(v, list) and len(v) > 0 or not isinstance(v, list) or k == 'memories')}
    if 'memories' not in npc_doc_cleaned: # Ensure memories is always present, even if empty
        npc_doc_cleaned['memories'] = []
>>>>>>> main

    for filename in json_files:
        filepath = os.path.join(DATA_DIR, filename)
        summary["files_processed"] += 1
        file_stats = {"inserted": 0, "updated": 0, "no_change": 0, "skipped": 0, "errors": 0}
        print(f"--- Processing: {filename} ---")

<<<<<<< HEAD
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
=======
    try:
        result = npc_collection.update_one(
            {'_id': npc_doc_cleaned['_id']},
            {'$set': npc_doc_cleaned},
            upsert=True
        )
        if result.upserted_id:
            inserted = 1
            print(f"Info [{file_name}]: Inserted NPC '{name}' with _id '{npc_doc_cleaned['_id']}' (source: {npc_id_source})")
        elif result.matched_count > 0:
            if result.modified_count > 0:
                updated = 1
                print(f"Info [{file_name}]: Updated NPC '{name}' with _id '{npc_doc_cleaned['_id']}'")
            else:
                matched_no_change = 1
        else:
            print(f"Warning [{file_name}]: NPC _id '{npc_doc_cleaned['_id']}' - No upsert/match. Result: {result.raw_result}")
            skipped = 1
            
    except errors.DuplicateKeyError:
        print(f"MongoDB DuplicateKeyError for _id '{npc_doc_cleaned['_id']}' from {file_name}. This might happen if an NPC with a generated ID was already processed from another file or run. Skipping.")
        skipped = 1
    except errors.PyMongoError as e:
        print(f"MongoDB error for _id '{npc_doc_cleaned['_id']}' from {file_name}: {e}. Skipping.")
        skipped = 1
    except Exception as e:
        print(f"Unexpected error processing NPC '{name}' from {file_name} with _id '{npc_doc_cleaned.get('_id', 'N/A')}': {e}. Skipping.")
        skipped = 1
    
    return inserted, updated, skipped, matched_no_change

def load_npcs_to_db():
    try:
        print(f"Connecting to MongoDB: {MONGO_URI}")
        client = MongoClient(MONGO_URI)
        client.admin.command('ping') 
        db = client[DATABASE_NAME]
        npc_collection = db[NPC_COLLECTION_NAME]
        print(f"Connected to DB '{DATABASE_NAME}', collection '{NPC_COLLECTION_NAME}'.")
    except Exception as e:
        print(f"Fatal: MongoDB connection error: {e}")
        return

    total_records_in_files, total_inserted, total_updated, total_skipped, total_matched_no_change = 0, 0, 0, 0, 0

    if not os.path.isdir(NPC_DATA_DIR_PATH):
        print(f"Error: NPC data directory not found: {NPC_DATA_DIR_PATH}")
        return

    json_files = glob.glob(os.path.join(NPC_DATA_DIR_PATH, '*.json'))
    # Filter out world data files from being processed by process_npc_data here
    # Assumes NPC files don't start with "world_"
    npc_json_files = [f for f in json_files if not os.path.basename(f).startswith('world_')]
    # world_data_files = [f for f in json_files if os.path.basename(f).startswith('world_')]


    if not npc_json_files:
        print(f"No NPC specific .json files found in {NPC_DATA_DIR_PATH} (excluding files starting with 'world_').")
        # Optionally, you can still proceed to load world_data_files if that's handled separately or if you adapt this script.
        # For now, this script focuses on NPC loading primarily.
        # return 
    else:
        print(f"Found NPC JSON files: {', '.join(os.path.basename(f) for f in npc_json_files)}")
        print("Processing NPC files...")

        for json_file_path in npc_json_files:
            file_name = os.path.basename(json_file_path)
            print(f"\n--- Processing NPC file: {file_name} ---")
            
            try:
                with open(json_file_path, 'r', encoding='utf-8') as f:
                    data_from_file = json.load(f)
            except Exception as e:
                print(f"Error reading/parsing {file_name}: {e}. Skipping.")
                continue

            npcs_to_process = []
            vuthausk_main_id_for_souls = None 

            if file_name.lower() == 'vuthausk.json' and isinstance(data_from_file, dict) and 'character_details' in data_from_file:
                print(f"Handling {file_name} (Vuthausk + souls).")
                npcs_to_process.append(data_from_file) 
                vuthausk_name_from_json = data_from_file.get('character_details', {}).get('basic_information', {}).get('name', 'vuthausk')
                vuthausk_main_id_for_souls = f"vuthausk_{vuthausk_name_from_json.lower().replace(' ', '_').replace('-', '_')}"

                souls_list = data_from_file.get('character_details', {}).get('in_game_details', {}).get(VUTHAUSK_SOULS_KEY, [])
                if isinstance(souls_list, list) and souls_list:
                    print(f"Found {len(souls_list)} souls in {file_name}.")
                    for soul_str in souls_list:
                        if isinstance(soul_str, str) and soul_str.strip():
                            soul_name_parts = soul_str.split(' - ')
                            soul_name = soul_name_parts[0].strip() if soul_name_parts else "Unnamed Soul"
                            soul_desc = soul_name_parts[1].strip() if len(soul_name_parts) > 1 else soul_str
                            soul_npc_data = {
                                'name': soul_name,
                                'appearance': f"A past life soul: {soul_desc}",
                                'personality_traits': ["Past Life Influence"], # Stored as list
                            }
                            npcs_to_process.append(soul_npc_data)
                else:
                    print(f"No souls list found or empty in {file_name} under key '{VUTHAUSK_SOULS_KEY}'.")

            elif isinstance(data_from_file, list):
                npcs_to_process = data_from_file
                print(f"Found {len(npcs_to_process)} NPCs (list) in {file_name}.")
            elif isinstance(data_from_file, dict):
                npcs_to_process = [data_from_file]
                print(f"Found 1 NPC (single object) in {file_name}.")
            else:
                print(f"Warning: Data in {file_name} is not a list or object. Skipping.")
                continue
            
            file_inserted, file_updated, file_skipped, file_matched_no_change = 0,0,0,0
            for i, npc_raw in enumerate(npcs_to_process):
                total_records_in_files +=1
                
                is_soul = False
                main_id_link = None
                if file_name.lower() == 'vuthausk.json':
                    if i == 0: 
                        is_soul = False
                    else: 
                        is_soul = True
                        main_id_link = vuthausk_main_id_for_souls 

                inserted, updated, skipped, matched = process_npc_data(
                    npc_raw, npc_collection, file_name, 
                    is_soul_npc=is_soul,
                    main_npc_id_for_soul=main_id_link
                )
                file_inserted += inserted
                file_updated += updated
                file_skipped += skipped
                file_matched_no_change += matched
            
            print(f"Finished {file_name}: {file_inserted} ins, {file_updated} upd, {file_skipped} skip, {file_matched_no_change} no-change.")
            total_inserted += file_inserted
            total_updated += file_updated
            total_skipped += file_skipped
            total_matched_no_change += file_matched_no_change

    # Here you could add separate logic to load world_data_files if needed,
    # e.g., by iterating through them and inserting/updating them into their respective collections
    # For now, this script primarily focuses on the 'npcs' collection.

    print(f"\n--- Overall NPC Load Summary ---")
    print(f"NPC Files processed: {len(npc_json_files)}")
    print(f"NPC records in files (from NPC files only): {total_records_in_files}") # This count is now more accurate for NPCs
    print(f"Inserted to DB: {total_inserted}")
    print(f"Updated in DB: {total_updated}")
    print(f"Matched (no change): {total_matched_no_change}")
    print(f"Skipped: {total_skipped}")
    print(f"NPC Load complete.")

    client.close()

if __name__ == '__main__':
    print("Starting NPC data loader...")
    load_npcs_to_db()
>>>>>>> main
