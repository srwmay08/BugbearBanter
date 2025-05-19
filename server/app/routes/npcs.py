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
        global_npcs_cursor = npc_collection.find({"$or": [{"user_id": {"$exists": False}}, {"user_id": None}]})
        for npc in global_npcs_cursor:
            npc_id_str = str(npc['_id'])
            npc['_id'] = npc_id_str # Ensure _id is string for frontend
            if npc.get('user_id'): # Should be None or not exist, but stringify if present
                 npc['user_id'] = str(npc['user_id'])
            npcs_list.append(npc)
            processed_ids.add(npc_id_str)

        # Fetch NPCs uploaded by the current user
        if current_user and hasattr(current_user, 'get_id') and current_user.get_id():
            user_specific_npcs_cursor = npc_collection.find({"user_id": current_user.get_id()})
            for npc in user_specific_npcs_cursor:
                npc_id_str = str(npc['_id'])
                if npc_id_str not in processed_ids: 
                    npc['_id'] = npc_id_str
                    if 'user_id' in npc: # Should always exist for user NPCs
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
        # Assuming _id in DB could be ObjectId or string from UUID
        # Try finding by string first (if you use UUIDs as _id)
        npc_data = npc_collection.find_one({"_id": npc_id_str})
        if not npc_data and ObjectId.is_valid(npc_id_str): # If not found and it's a valid ObjectId string
            npc_data = npc_collection.find_one({"_id": ObjectId(npc_id_str)})

        if not npc_data:
            return jsonify({"error": "NPC not found"}), 404

        # Security check: User can only get their own NPC or a global NPC
        is_global = not npc_data.get("user_id")
        is_owner = npc_data.get("user_id") == current_user.get_id()

        if not (is_global or is_owner):
            return jsonify({"error": "Forbidden: You do not have access to this NPC"}), 403
        
        npc_data['_id'] = str(npc_data['_id']) # Ensure _id is string
        if 'user_id' in npc_data and npc_data['user_id']:
            npc_data['user_id'] = str(npc_data['user_id'])
            
        return jsonify(npc_data), 200
    except Exception as e:
        current_app.logger.error(f"Error fetching single NPC {npc_id_str}: {e}", exc_info=True)
        return jsonify({"error": "Failed to fetch NPC details."}), 500


@npcs_bp.route('/upload', methods=['POST']) # This is your CREATE route
@login_required
def upload_npc_route():
    # ... (your existing upload logic - ensure it adds user_id to the NPC and npc_id to user.npc_ids)
    # ... (Make sure it returns the created NPC data with its new _id)
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
                '_id': npc_id, 'user_id': current_user.get_id(), 'name': npc_data_raw.get('name'),
                'race': npc_data_raw.get('race'), 'class': npc_data_raw.get('class'), 
                'alignment': npc_data_raw.get('alignment'), 'age': npc_data_raw.get('age'),
                'personality_traits': npc_data_raw.get('personality_traits'), 
                'ideals': npc_data_raw.get('ideals'), 'bonds': npc_data_raw.get('bonds'),
                'flaws': npc_data_raw.get('flaws'), 'backstory': npc_data_raw.get('backstory'),
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
            result = npc_collection.insert_one(npc_doc_cleaned)
            
            users_collection.update_one(
                {"_id": current_user.get_id()},
                {"$addToSet": {"npc_ids": npc_id}} 
            )
            if hasattr(current_user, 'npc_ids') and isinstance(current_user.npc_ids, list) and npc_id not in current_user.npc_ids:
                current_user.npc_ids.append(npc_id)

            # Fetch the inserted document to return it fully, including MongoDB's _id if it was auto-generated differently
            # (though we are setting it with uuid here)
            created_npc = npc_collection.find_one({"_id": npc_id})
            if created_npc:
                 created_npc['_id'] = str(created_npc['_id'])
                 if 'user_id' in created_npc:
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

        # Find existing NPC
        # Again, handle string UUIDs or ObjectIds for _id
        query_id = npc_id_str
        if ObjectId.is_valid(npc_id_str): # If it could be an ObjectId
             # Check if it exists as ObjectId first if your old data used it
             check_as_oid = npc_collection.find_one({"_id": ObjectId(npc_id_str)})
             if check_as_oid: query_id = ObjectId(npc_id_str)
        
        existing_npc = npc_collection.find_one({"_id": query_id})

        if not existing_npc:
            return jsonify({"error": "NPC not found"}), 404

        # Security: Only owner can update their NPC. Global NPCs might be non-editable or admin-only.
        if not existing_npc.get("user_id") or existing_npc.get("user_id") != current_user.get_id():
            return jsonify({"error": "Forbidden: You can only update your own NPCs"}), 403

        # Prepare update data: remove _id and user_id from payload if present, as they shouldn't be changed
        npc_data_to_update.pop('_id', None)
        npc_data_to_update.pop('user_id', None) 
        # Add an 'updated_at' timestamp if you have such a field
        # npc_data_to_update['updated_at'] = datetime.utcnow()


        result = npc_collection.update_one(
            {"_id": query_id, "user_id": current_user.get_id()}, 
            {"$set": npc_data_to_update}
        )

        if result.matched_count == 0:
            # This case should ideally be caught by the initial find_one and permission check
            return jsonify({"error": "NPC not found or update forbidden"}), 404 
        if result.modified_count == 0:
            return jsonify({"message": "NPC data was the same, no changes made.", "npc_id": npc_id_str}), 200
        
        updated_npc = npc_collection.find_one({"_id": query_id})
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

        # Determine if _id is string or ObjectId for query
        query_id = npc_id_str
        if ObjectId.is_valid(npc_id_str):
             check_as_oid = npc_collection.find_one({"_id": ObjectId(npc_id_str)})
             if check_as_oid: query_id = ObjectId(npc_id_str)
        
        # Ensure the NPC belongs to the current user before deleting
        npc_to_delete = npc_collection.find_one({"_id": query_id, "user_id": current_user.get_id()})
        
        if not npc_to_delete:
            # Check if it's a global NPC the user might be trying to delete (disallow for now)
            is_global_check = npc_collection.find_one({"_id": query_id, "user_id": {"$exists": False}})
            if is_global_check:
                return jsonify({"error": "Forbidden: Default NPCs cannot be deleted by users."}), 403
            return jsonify({"error": "NPC not found or you do not have permission to delete it"}), 404

        result = npc_collection.delete_one({"_id": query_id, "user_id": current_user.get_id()})

        if result.deleted_count == 0:
            # Should have been caught by find_one above
            return jsonify({"error": "NPC not found or delete failed"}), 404
        
        # Remove NPC ID from user's npc_ids list
        users_collection.update_one(
            {"_id": current_user.get_id()},
            {"$pull": {"npc_ids": npc_id_str}} # npc_id_str should match how it's stored in user's array
        )
        if hasattr(current_user, 'npc_ids') and isinstance(current_user.npc_ids, list) and npc_id_str in current_user.npc_ids:
            current_user.npc_ids.remove(npc_id_str)

        return jsonify({"message": f"NPC with ID {npc_id_str} deleted successfully"}), 200
    except Exception as e:
        current_app.logger.error(f"Error deleting NPC {npc_id_str}: {e}", exc_info=True)
        return jsonify({"error": "Failed to delete NPC."}), 500
```