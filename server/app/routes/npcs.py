# app/routes/npcs.py
from flask import Blueprint, jsonify, current_app, request, abort
from ..utils.db import mongo # Assuming this is how you access your MongoDB instance
from flask_login import login_required, current_user # Ensure current_user is imported
import json # Ensure json is imported
import uuid # Keep for your upload route
from bson import ObjectId # For converting string ID to MongoDB ObjectId if necessary

npcs_bp = Blueprint('npcs', __name__)
NPC_COLLECTION_NAME = 'npcs' # This collection stores both PCs and NPCs
USERS_COLLECTION_NAME = 'users'

@npcs_bp.route('', methods=['GET'])
@login_required
def get_combined_npcs(): # Kept your original function name
    """
    API endpoint to fetch all relevant characters (PCs and NPCs).
    It fetches characters that are default (user_id is None or does not exist)
    OR belong to the currently logged-in user.
    The 'type' field (pc/npc) from MongoDB is crucial for frontend filtering.
    """
    # CRITICAL FIX: Use current_user
    user_id_for_log = current_user.email if hasattr(current_user, 'email') else current_user.id
    
    query_conditions = [
        {"user_id": None}, 
        {"user_id": {"$exists": False}} 
    ]

    current_user_actual_id_str = current_user.get_id() # This is usually a string

    # Add condition for user-specific characters
    # User_id in the database could be ObjectId or string. Be flexible or ensure consistency.
    # For this example, let's assume user_id in npcs collection could be string or ObjectId.
    try:
        query_conditions.append({"user_id": ObjectId(current_user_actual_id_str)})
    except Exception: # If current_user_actual_id_str is not a valid ObjectId string
        query_conditions.append({"user_id": current_user_actual_id_str})
            
    final_query = {"$or": query_conditions}

    try:
        character_collection = mongo.db[NPC_COLLECTION_NAME]
        characters_cursor = character_collection.find(final_query)
        
        characters_list = []
        for char_doc in characters_cursor:
            char_doc["_id"] = str(char_doc["_id"]) 
            
            if 'user_id' in char_doc and char_doc['user_id'] is not None:
                char_doc['user_id'] = str(char_doc['user_id'])
            
            # The 'type' field (e.g., "pc" or "npc") is direct from the DB document.
            # load_npc_data.py is responsible for saving this 'type' field correctly.
            characters_list.append(char_doc)
        
        current_app.logger.info(f"API: Returning {len(characters_list)} characters (PCs & NPCs) for user {user_id_for_log}. Query: {final_query}")
        return jsonify(characters_list), 200

    except Exception as e:
        current_app.logger.error(f"API Error fetching characters for user {user_id_for_log}: {e}", exc_info=True)
        return jsonify({"error": "Failed to fetch characters", "details": str(e)}), 500

@npcs_bp.route('/<npc_id_str>', methods=['GET'])
@login_required
def get_single_npc(npc_id_str):
    try:
        npc_collection = mongo.db[NPC_COLLECTION_NAME]
        npc_data = None
        
        if ObjectId.is_valid(npc_id_str):
            npc_data = npc_collection.find_one({"_id": ObjectId(npc_id_str)})
        if not npc_data: # Fallback or if ID is not an ObjectId format
            npc_data = npc_collection.find_one({"_id": npc_id_str})

        if not npc_data:
            return jsonify({"error": "Character not found"}), 404

        is_global = not npc_data.get("user_id")
        
        user_id_in_doc = npc_data.get("user_id")
        current_user_id_str = current_user.get_id()
        is_owner = False
        if user_id_in_doc is not None:
            is_owner = str(user_id_in_doc) == current_user_id_str
        
        if not (is_global or is_owner):
            return jsonify({"error": "Forbidden: You do not have access to this character"}), 403
        
        npc_data['_id'] = str(npc_data['_id']) 
        if 'user_id' in npc_data and npc_data['user_id']:
            npc_data['user_id'] = str(npc_data['user_id'])
            
        return jsonify(npc_data), 200
    except Exception as e:
        current_app.logger.error(f"Error fetching single character {npc_id_str}: {e}", exc_info=True)
        return jsonify({"error": "Failed to fetch character details."}), 500


@npcs_bp.route('/upload', methods=['POST'])
@login_required
def upload_npc_route(): # Your original function name was upload_npc_file
    if 'npc_file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400
    
    file = request.files['npc_file']
    if file.filename == '':
        return jsonify({"error": "No file selected for uploading"}), 400

    if file and file.filename.endswith('.json'):
        try:
            # CRITICAL FIX: Use file.stream for a file opened in binary mode by Flask
            uploaded_data = json.load(file.stream) 
            
            if not isinstance(uploaded_data, dict) or 'name' not in uploaded_data:
                return jsonify({"error": "Invalid JSON format or missing character name."}), 400

            npc_collection = mongo.db[NPC_COLLECTION_NAME]
            users_collection = mongo.db[USERS_COLLECTION_NAME]
            
            char_doc = uploaded_data.copy() # Make a copy to modify

            # Handle _id: if present in JSON use it, otherwise generate.
            if "_id" in char_doc and isinstance(char_doc["_id"], str) and char_doc["_id"]:
                char_id_str = char_doc["_id"]
            else:
                char_id_str = str(uuid.uuid4())
            char_doc['_id'] = char_id_str
            
            # Assign user_id
            char_doc['user_id'] = current_user.get_id() 

            # Handle 'type': must be in JSON, default if not or invalid.
            if 'type' not in char_doc or char_doc['type'] not in ['pc', 'npc']:
                current_app.logger.warn(
                    f"Uploaded character '{char_doc.get('name')}' by {current_user.id} (file: {file.filename}) "
                    f"missing valid 'type' (had: '{char_doc.get('type')}'). Defaulting to 'npc'."
                )
                char_doc['type'] = 'npc'
            
            char_doc['source_file'] = file.filename

            # Upsert logic based on _id
            existing_char = npc_collection.find_one({"_id": char_doc['_id']})
            message = ""
            status_code = 200

            if existing_char:
                if str(existing_char.get("user_id")) == str(current_user.get_id()): # It's theirs, update
                    npc_collection.replace_one({"_id": char_doc['_id']}, char_doc)
                    message = f"Character '{char_doc.get('name')}' updated successfully."
                    current_app.logger.info(f"Character {char_doc['_id']} updated by user {current_user.id}.")
                elif existing_char.get("user_id") is None: # Default/global
                    return jsonify({"error": f"A default character with ID '{char_doc['_id']}' already exists. Cannot overwrite."}), 409
                else: # Belongs to another user
                    return jsonify({"error": f"A character with ID '{char_doc['_id']}' exists and belongs to another user."}), 409
            else: # New character, insert
                npc_collection.insert_one(char_doc)
                message = f"Character '{char_doc.get('name')}' uploaded successfully."
                status_code = 201
                current_app.logger.info(f"Character {char_doc['_id']} uploaded by user {current_user.id} with type '{char_doc['type']}'.")
                
                # Add character ID to user's list (assuming user._id is ObjectId compatible string)
                try:
                    users_collection.update_one(
                        {"_id": ObjectId(current_user.get_id())}, 
                        {"$addToSet": {"character_ids": char_id_str}} # Or "npc_ids"
                    )
                except Exception as e_user_update:
                     current_app.logger.error(f"Failed to add char_id to user list for {current_user.id}: {e_user_update}")


            final_char_doc = npc_collection.find_one({"_id": char_id_str})
            if final_char_doc:
                 final_char_doc['_id'] = str(final_char_doc['_id'])
                 if 'user_id' in final_char_doc and final_char_doc['user_id'] is not None:
                     final_char_doc['user_id'] = str(final_char_doc['user_id'])

            return jsonify({"message": message, "character": final_char_doc}), status_code

        except json.JSONDecodeError:
            current_app.logger.warn(f"Invalid JSON during upload by user {current_user.id}, file: {file.filename}")
            return jsonify({"error": "Invalid JSON file provided."}), 400
        except Exception as e:
            current_app.logger.error(f"Error uploading character for user {current_user.id}: {e}", exc_info=True)
            return jsonify({"error": "Failed to upload character.", "details": str(e)}), 500
    else:
        return jsonify({"error": "Invalid file type. Only .json files are allowed."}), 400

@npcs_bp.route('/<npc_id_str>', methods=['PUT'])
@login_required
def update_npc(npc_id_str):
    try:
        npc_collection = mongo.db[NPC_COLLECTION_NAME]
        data_to_update = request.get_json()
        if not data_to_update:
            return jsonify({"error": "No update data provided"}), 400

        query_filter_id = ObjectId(npc_id_str) if ObjectId.is_valid(npc_id_str) else npc_id_str
        
        # Ensure user is trying to update their own character
        # Note: current_user.get_id() returns a string. If user_id in DB is ObjectId, convert for query.
        user_id_for_query = ObjectId(current_user.get_id()) if ObjectId.is_valid(current_user.get_id()) else current_user.get_id()

        query_filter = {"_id": query_filter_id, "user_id": user_id_for_query}
        
        existing_npc = npc_collection.find_one(query_filter)
        if not existing_npc:
             # Check if it's a global NPC or belongs to someone else
            check_npc = npc_collection.find_one({"_id": query_filter_id})
            if check_npc and not check_npc.get("user_id"):
                return jsonify({"error": "Forbidden: Default characters cannot be modified."}), 403
            return jsonify({"error": "Character not found or you don't have permission to edit it"}), 404

        data_to_update.pop('_id', None) # Cannot change _id
        data_to_update.pop('user_id', None) # Cannot change owner

        if not data_to_update:
            return jsonify({"error": "No valid fields provided for update after stripping protected fields."}), 400

        result = npc_collection.update_one(query_filter, {"$set": data_to_update})
        
        if result.modified_count == 0 and result.matched_count > 0:
             return jsonify({"message": "Character data was the same, no changes made.", "_id": npc_id_str}), 200

        updated_char = npc_collection.find_one({"_id": query_filter_id})
        if updated_char:
            updated_char['_id'] = str(updated_char['_id'])
            if 'user_id' in updated_char and updated_char['user_id']: 
                updated_char['user_id'] = str(updated_char['user_id'])
        
        return jsonify({"message": "Character updated successfully", "character": updated_char}), 200
    except Exception as e:
        current_app.logger.error(f"Error updating character {npc_id_str}: {e}", exc_info=True)
        return jsonify({"error": "Failed to update character."}), 500

@npcs_bp.route('/<npc_id_str>', methods=['DELETE'])
@login_required
def delete_npc(npc_id_str):
    try:
        npc_collection = mongo.db[NPC_COLLECTION_NAME]
        users_collection = mongo.db[USERS_COLLECTION_NAME]

        query_filter_id = ObjectId(npc_id_str) if ObjectId.is_valid(npc_id_str) else npc_id_str
        user_id_for_query = ObjectId(current_user.get_id()) if ObjectId.is_valid(current_user.get_id()) else current_user.get_id()

        npc_to_delete = npc_collection.find_one({"_id": query_filter_id, "user_id": user_id_for_query})
        
        if not npc_to_delete:
            check_npc = npc_collection.find_one({"_id": query_filter_id})
            if check_npc and not check_npc.get("user_id"): # It's a global/default NPC
                return jsonify({"error": "Forbidden: Default characters cannot be deleted."}), 403
            return jsonify({"error": "Character not found or you do not have permission to delete it"}), 404

        result = npc_collection.delete_one({"_id": query_filter_id, "user_id": user_id_for_query})

        if result.deleted_count == 0:
            return jsonify({"error": "Character not found during delete operation or delete failed"}), 404
        
        # Remove character ID from user's list (e.g., 'character_ids' or 'npc_ids')
        users_collection.update_one(
            {"_id": user_id_for_query}, # Assuming user _id for query is same format as in users collection
            {"$pull": {"character_ids": npc_id_str}} # Adjust field name if needed
        )
        # Also update current_user object in session if it caches this list
        if hasattr(current_user, 'character_ids') and isinstance(current_user.character_ids, list) and npc_id_str in current_user.character_ids:
            current_user.character_ids.remove(npc_id_str)
        elif hasattr(current_user, 'npc_ids') and isinstance(current_user.npc_ids, list) and npc_id_str in current_user.npc_ids:
            current_user.npc_ids.remove(npc_id_str)


        current_app.logger.info(f"Character {npc_id_str} deleted by user {current_user.id}")
        return jsonify({"message": f"Character with ID {npc_id_str} deleted successfully"}), 200
    except Exception as e:
        current_app.logger.error(f"Error deleting character {npc_id_str}: {e}", exc_info=True)
        return jsonify({"error": "Failed to delete character."}), 500