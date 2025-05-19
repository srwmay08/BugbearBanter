# app/routes/npcs.py
from flask import Blueprint, jsonify, current_app, request, abort
from ..utils.db import mongo
from flask_login import login_required, current_user
import json
import uuid
from bson import ObjectId # For converting string ID to MongoDB ObjectId if necessary

npcs_bp = Blueprint('npcs', __name__)
NPC_COLLECTION_NAME = 'npcs'
USERS_COLLECTION_NAME = 'users'

@npcs_bp.route('', methods=['GET'])
@login_required
def get_combined_npcs():
    try:
        npc_collection = mongo.db[NPC_COLLECTION_NAME]
        npcs_list = []
        processed_ids = set()

        # Fetch global/default NPCs (user_id does not exist or is explicitly null)
        # NPCs are considered global if 'user_id' field is missing or explicitly set to None
        global_npcs_cursor = npc_collection.find({"$or": [{"user_id": {"$exists": False}}, {"user_id": None}]})
        for npc in global_npcs_cursor:
            npc_id_str = str(npc['_id'])
            npc['_id'] = npc_id_str # Ensure _id is string for frontend
            if npc.get('user_id'): # Should be None or not exist for globals, but stringify if present for consistency
                 npc['user_id'] = str(npc['user_id'])
            npcs_list.append(npc)
            processed_ids.add(npc_id_str)

        # Fetch NPCs uploaded by the current user
        if current_user and hasattr(current_user, 'get_id') and current_user.get_id():
            # current_user.get_id() should return the user's _id as stored in the users collection
            user_specific_npcs_cursor = npc_collection.find({"user_id": current_user.get_id()})
            for npc in user_specific_npcs_cursor:
                npc_id_str = str(npc['_id'])
                if npc_id_str not in processed_ids: 
                    npc['_id'] = npc_id_str
                    if 'user_id' in npc: # Should always exist for user NPCs and match current_user.get_id()
                        npc['user_id'] = str(npc['user_id'])
                    npcs_list.append(npc)
                    processed_ids.add(npc_id_str)
        
        current_app.logger.info(f"Returning {len(npcs_list)} NPCs for user {current_user.email}.")
        return jsonify(npcs_list), 200
    except Exception as e:
        current_app.logger.error(f"Error fetching combined NPCs: {e}", exc_info=True)
        return jsonify({"error": "Failed to fetch NPCs.", "details": str(e)}), 500

@npcs_bp.route('/<npc_id_str>', methods=['GET'])
@login_required
def get_single_npc(npc_id_str):
    try:
        npc_collection = mongo.db[NPC_COLLECTION_NAME]
        
        # Attempt to find by string ID first (e.g., UUIDs)
        npc_data = npc_collection.find_one({"_id": npc_id_str})
        
        # If not found and the string is a valid ObjectId, try finding by ObjectId
        # This handles cases where some _ids might be ObjectIds and others strings
        if not npc_data and ObjectId.is_valid(npc_id_str):
            npc_data = npc_collection.find_one({"_id": ObjectId(npc_id_str)})

        if not npc_data:
            return jsonify({"error": "NPC not found"}), 404

        # Security check: User can only get their own NPC or a global NPC
        is_global = not npc_data.get("user_id") # Global if no user_id or user_id is None
        is_owner = npc_data.get("user_id") == current_user.get_id()

        if not (is_global or is_owner):
            return jsonify({"error": "Forbidden: You do not have access to this NPC"}), 403
        
        npc_data['_id'] = str(npc_data['_id']) 
        if 'user_id' in npc_data and npc_data['user_id']:
            npc_data['user_id'] = str(npc_data['user_id'])
            
        return jsonify(npc_data), 200
    except Exception as e:
        current_app.logger.error(f"Error fetching single NPC {npc_id_str}: {e}", exc_info=True)
        return jsonify({"error": "Failed to fetch NPC details."}), 500


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
            npc_id = str(uuid.uuid4()) # Generate a new unique string ID for this NPC
            
            # Map all fields from your standard NPC JSON structure
            npc_doc = {
                '_id': npc_id, 
                'user_id': current_user.get_id(), # Associate with current user
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
            # Remove any keys that have None values before insertion, if desired
            npc_doc_cleaned = {k: v for k, v in npc_doc.items() if v is not None}

            npc_collection.insert_one(npc_doc_cleaned)
            
            # Add this NPC's string ID to the user's list of NPC IDs
            users_collection.update_one(
                {"_id": current_user.get_id()}, # Assumes user _id is also a string
                {"$addToSet": {"npc_ids": npc_id}} 
            )
            # Update current_user object in session if Flask-Login stores the full object
            if hasattr(current_user, 'npc_ids') and isinstance(current_user.npc_ids, list) and npc_id not in current_user.npc_ids:
                current_user.npc_ids.append(npc_id)

            created_npc = npc_collection.find_one({"_id": npc_id})
            if created_npc: # Ensure _id is string in the returned document
                 created_npc['_id'] = str(created_npc['_id'])
                 if 'user_id' in created_npc: # Ensure user_id is string
                     created_npc['user_id'] = str(created_npc['user_id'])

            return jsonify({"message": f"NPC '{created_npc.get('name')}' uploaded successfully.", "npc": created_npc}), 201

        except json.JSONDecodeError:
            return jsonify({"error": "Invalid JSON file."}), 400
        except Exception as e:
            current_app.logger.error(f"Error uploading NPC: {e}", exc_info=True)
            return jsonify({"error": "Failed to upload NPC.", "details": str(e)}), 500
    else:
        return jsonify({"error": "Invalid file type. Only .json files are allowed."}), 400

@npcs_bp.route('/<npc_id_str>', methods=['PUT'])
@login_required
def update_npc(npc_id_str):
    try:
        npc_collection = mongo.db[NPC_COLLECTION_NAME]
        npc_data_to_update = request.get_json()
        if not npc_data_to_update:
            return jsonify({"error": "No update data provided"}), 400

        query_id_str = npc_id_str # Use the string ID for querying, assuming your _ids are stored as strings
        
        existing_npc = npc_collection.find_one({"_id": query_id_str})

        if not existing_npc:
            return jsonify({"error": "NPC not found"}), 404

        if not existing_npc.get("user_id") or existing_npc.get("user_id") != current_user.get_id():
            return jsonify({"error": "Forbidden: You can only update your own NPCs"}), 403

        npc_data_to_update.pop('_id', None)
        npc_data_to_update.pop('user_id', None) 
        # Consider adding an 'updated_at': datetime.utcnow() field here

        result = npc_collection.update_one(
            {"_id": query_id_str, "user_id": current_user.get_id()}, 
            {"$set": npc_data_to_update}
        )

        if result.matched_count == 0:
            return jsonify({"error": "NPC not found or update forbidden (match failed)"}), 404 
        if result.modified_count == 0:
            # Fetch to confirm it's truly unchanged vs. an issue
            unchanged_npc = npc_collection.find_one({"_id": query_id_str})
            if unchanged_npc:
                unchanged_npc['_id'] = str(unchanged_npc['_id'])
                if 'user_id' in unchanged_npc: unchanged_npc['user_id'] = str(unchanged_npc['user_id'])
                return jsonify({"message": "NPC data was the same, no changes made.", "npc": unchanged_npc}), 200
            else: # Should not happen if matched_count was > 0
                return jsonify({"error": "NPC found but could not retrieve after no-modification update."}), 500

        updated_npc = npc_collection.find_one({"_id": query_id_str})
        updated_npc['_id'] = str(updated_npc['_id'])
        if 'user_id' in updated_npc: updated_npc['user_id'] = str(updated_npc['user_id'])

        return jsonify({"message": "NPC updated successfully", "npc": updated_npc}), 200
    except Exception as e:
        current_app.logger.error(f"Error updating NPC {npc_id_str}: {e}", exc_info=True)
        return jsonify({"error": "Failed to update NPC."}), 500

@npcs_bp.route('/<npc_id_str>', methods=['DELETE'])
@login_required
def delete_npc(npc_id_str):
    try:
        npc_collection = mongo.db[NPC_COLLECTION_NAME]
        users_collection = mongo.db[USERS_COLLECTION_NAME]

        query_id_str = npc_id_str # Assuming _ids are stored and queried as strings

        npc_to_delete = npc_collection.find_one({"_id": query_id_str, "user_id": current_user.get_id()})
        
        if not npc_to_delete:
            is_global_check = npc_collection.find_one({"_id": query_id_str, "$or": [{"user_id": {"$exists": False}}, {"user_id": None}]})
            if is_global_check:
                return jsonify({"error": "Forbidden: Default NPCs cannot be deleted by users."}), 403
            return jsonify({"error": "NPC not found or you do not have permission to delete it"}), 404

        result = npc_collection.delete_one({"_id": query_id_str, "user_id": current_user.get_id()})

        if result.deleted_count == 0:
            return jsonify({"error": "NPC not found or delete failed (no document deleted)"}), 404
        
        users_collection.update_one(
            {"_id": current_user.get_id()},
            {"$pull": {"npc_ids": npc_id_str}} 
        )
        if hasattr(current_user, 'npc_ids') and isinstance(current_user.npc_ids, list) and npc_id_str in current_user.npc_ids:
            current_user.npc_ids.remove(npc_id_str)

        return jsonify({"message": f"NPC with ID {npc_id_str} deleted successfully"}), 200
    except Exception as e:
        current_app.logger.error(f"Error deleting NPC {npc_id_str}: {e}", exc_info=True)
        return jsonify({"error": "Failed to delete NPC."}), 500
