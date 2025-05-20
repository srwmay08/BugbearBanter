# server/load_npc_data.py
import os
import json
from pymongo import MongoClient, errors # type: ignore
from dotenv import load_dotenv
import glob 
import uuid

SERVER_DIR = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(SERVER_DIR, '.env')
load_dotenv(dotenv_path)

MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/ttrpg_app_db')
DATABASE_NAME = MONGO_URI.split('/')[-1].split('?')[0] 
NPC_COLLECTION_NAME = 'npcs'
NPC_DATA_DIR_PATH = os.path.join(SERVER_DIR, 'app', 'data')
VUTHAUSK_SOULS_KEY = 'wyrmshard_collected_souls'

def process_npc_data(npc_raw_data, npc_collection, file_name="Unknown File", is_soul_npc=False, main_npc_id_for_soul=None):
    inserted, updated, skipped, matched_no_change = 0, 0, 0, 0

    if not isinstance(npc_raw_data, dict):
        print(f"Warning [{file_name}]: Item is not a valid NPC object. Skipping: {str(npc_raw_data)[:100]}")
        return 0, 0, 1, 0

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