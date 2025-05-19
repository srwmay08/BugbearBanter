# app/routes/npcs.py
from flask import Blueprint, jsonify, current_app, request, abort
from ..utils.db import mongo
from flask_login import login_required, current_user
import json
import uuid
# from ..models import NPC # Using direct dicts for DB interaction here

npcs_bp = Blueprint('npcs', __name__)
NPC_COLLECTION_NAME = 'npcs'
USERS_COLLECTION_NAME = 'users'

@npcs_bp.route('', methods=['GET'])
@login_required
def get_combined_npcs(): # Renamed for clarity
    try:
        npc_collection = mongo.db[NPC_COLLECTION_NAME]
        npcs_list = []

        # 1. Fetch global/default NPCs (those without a user_id or user_id is null)
        # Using $or to find documents where user_id is null OR user_id does not exist.
        global_npcs_cursor = npc_collection.find({"user_id": {"$exists": False}}) # Or {"user_id": None} if you consistently set it to None for global ones
        
        processed_ids = set()

        for npc in global_npcs_cursor:
            npc_id_str = str(npc['_id'])
            if '_id' in npc and not isinstance(npc['_id'], str):
                npc['_id'] = npc_id_str
            
            # Ensure user_id is not present or explicitly null if that's how you mark globals
            # For this logic, we assume absence of user_id means global
            if npc.get('user_id'): # Defensive: if a global somehow got a user_id, ensure it's string
                 npc['user_id'] = str(npc['user_id'])

            npcs_list.append(npc)
            processed_ids.add(npc_id_str)

        # 2. Fetch NPCs uploaded by the current user
        if current_user and hasattr(current_user, 'get_id'): # Check if current_user is valid
            user_specific_npcs_cursor = npc_collection.find({"user_id": current_user.get_id()})
            for npc in user_specific_npcs_cursor:
                npc_id_str = str(npc['_id'])
                if npc_id_str not in processed_ids: # Avoid duplicates if an NPC could be global and user-owned (unlikely with this logic)
                    if '_id' in npc and not isinstance(npc['_id'], str):
                        npc['_id'] = npc_id_str
                    if 'user_id' in npc and not isinstance(npc['user_id'], str):
                        npc['user_id'] = str(npc['user_id'])
                    npcs_list.append(npc)
                    processed_ids.add(npc_id_str)
        
        current_app.logger.info(f"Returning {len(npcs_list)} NPCs for user {current_user.email} (globals + user-specific).")
        return jsonify(npcs_list), 200
    except Exception as e:
        current_app.logger.error(f"Error fetching combined NPCs: {e}", exc_info=True) # Log full traceback
        return jsonify({"error": "Failed to fetch NPCs.", "details": str(e)}), 500

# The /upload route should remain largely the same as it correctly assigns user_id.
@npcs_bp.route('/upload', methods=['POST'])
@login_required
def upload_npc_route():
    if 'npc_file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400
    
    file = request.files['npc_file']
    if file.filename == '':
        return jsonify({"error": "No file selected for uploading"}), 400

    if file and file.filename.endswith('.json'):
        try:
            npc_data_raw = json.load(file.stream) 
            
            if not isinstance(npc_data_raw, dict) or 'name' not in npc_data_raw:
                return jsonify({"error": "Invalid JSON format or missing NPC name."}), 400

            npc_collection = mongo.db[NPC_COLLECTION_NAME]
            users_collection = mongo.db[USERS_COLLECTION_NAME]

            npc_id = str(uuid.uuid4()) 
            
            npc_doc = {
                '_id': npc_id,
                'user_id': current_user.get_id(), 
                'name': npc_data_raw.get('name'),
                'race': npc_data_raw.get('race'),
                'class': npc_data_raw.get('class'), 
                'alignment': npc_data_raw.get('alignment'),
                'age': npc_data_raw.get('age'),
                'personality_traits': npc_data_raw.get('personality_traits'), 
                'ideals': npc_data_raw.get('ideals'),
                'bonds': npc_data_raw.get('bonds'),
                'flaws': npc_data_raw.get('flaws'),
                'backstory': npc_data_raw.get('backstory'),
                'motivations': npc_data_raw.get('motivations'),
                'speech_patterns': npc_data_raw.get('speech_patterns'),
                'mannerisms': npc_data_raw.get('mannerisms'),
                'past_situation': npc_data_raw.get('past_situation'),
                'current_situation': npc_data_raw.get('current_situation'),
                'relationships_with_pcs': npc_data_raw.get('relationships_with_pcs'),
                'appearance': npc_data_raw.get('appearance', 'No description available.'), 
                'source_file': file.filename 
            }
            npc_doc_cleaned = {k: v for k, v in npc_doc.items() if v is not None}

            npc_collection.insert_one(npc_doc_cleaned)
            
            users_collection.update_one(
                {"_id": current_user.get_id()},
                {"$addToSet": {"npc_ids": npc_id}} 
            )
            if hasattr(current_user, 'npc_ids') and isinstance(current_user.npc_ids, list) and npc_id not in current_user.npc_ids: # Ensure current_user object is updated if used by Flask-Login session
                current_user.npc_ids.append(npc_id)

            return jsonify({"message": f"NPC '{npc_doc.get('name')}' uploaded successfully with ID {npc_id}", "npc_id": npc_id, "npc_data": npc_doc_cleaned}), 201 # Return uploaded NPC data

        except json.JSONDecodeError:
            return jsonify({"error": "Invalid JSON file."}), 400
        except Exception as e:
            current_app.logger.error(f"Error uploading NPC: {e}", exc_info=True)
            return jsonify({"error": "Failed to upload NPC due to server error.", "details": str(e)}), 500
    else:
        return jsonify({"error": "Invalid file type. Only .json files are allowed."}), 400