# app/routes/npcs.py
from flask import Blueprint, jsonify, current_app, request, abort
from ..utils.db import mongo # Assuming this is how you access your MongoDB instance
from flask_login import login_required, current_user
# import json # Not strictly needed for this version unless doing complex JSON manipulation
# import uuid # Not strictly needed for GET requests here
from bson import ObjectId # For converting string ID to MongoDB ObjectId if necessary

# Your existing Blueprint name
npcs_bp = Blueprint('npcs', __name__) # Use your actual blueprint name if different
NPC_COLLECTION_NAME = 'npcs' # This collection should store both PCs and NPCs
USERS_COLLECTION_NAME = 'users' # Unchanged, used for other routes

@npcs_bp.route('', methods=['GET']) # This will be /api/npcs if prefix is /api in app registration
@login_required
def get_all_characters_api(): # Renamed for clarity, was get_combined_npcs
    """
    API endpoint to fetch all relevant characters (PCs and NPCs).
    It fetches characters that are default (user_id is None or does not exist)
    OR belong to the currently logged-in user.
    The 'type' field (pc/npc) is determined by the data in MongoDB.
    """
    user_id_for_log = वर्तमान_उपयोगकर्ता.email if hasattr(वर्तमान_उपयोगकर्ता, 'email') else वर्तमान_उपयोगकर्ता.id
    
    # Query for characters:
    # 1. Default/shared characters (user_id is null or does not exist)
    # 2. Characters owned by the current user
    query_conditions = [
        {"user_id": None},
        {"user_id": {"$exists": False}} 
    ]
    if hasattr(current_user, 'id') and current_user.id:
        # Ensure current_user.id is properly formatted if it needs to be an ObjectId for the query
        # If user_id in your DB is stored as a string, no ObjectId conversion needed here.
        # If user_id in your DB is ObjectId, then current_user.id should be convertible.
        try:
            user_obj_id = ObjectId(current_user.id)
            query_conditions.append({"user_id": user_obj_id})
        except Exception:
            # If current_user.id is not a valid format for ObjectId (e.g. it's an email or non-hex string)
            # and your user_id field in 'npcs' stores string IDs that match current_user.id directly:
            query_conditions.append({"user_id": current_user.id})


    final_query = {"$or": query_conditions}

    try:
        # Access the 'npcs' collection (which stores both PCs and NPCs)
        character_collection = mongo.db[NPC_COLLECTION_NAME]
        
        characters_cursor = character_collection.find(final_query)
        
        characters_list = []
        for char_doc in characters_cursor:
            # Ensure _id is a string for JSON serialization
            char_doc["_id"] = str(char_doc["_id"]) 
            
            # Ensure user_id (if present) is a string
            if 'user_id' in char_doc and char_doc['user_id'] is not None:
                char_doc['user_id'] = str(char_doc['user_id'])
            
            # The 'type' field (e.g., "pc" or "npc") should be directly from the DB document
            # No special handling needed here if load_npc_data.py saves it correctly.
            characters_list.append(char_doc)
        
        # Accurate logging message
        current_app.logger.info(f"API: Returning {len(characters_list)} characters (PCs and NPCs) for user {user_id_for_log}.")
        return jsonify(characters_list)

    except Exception as e:
        current_app.logger.error(f"API Error fetching characters for user {user_id_for_log}: {e}", exc_info=True)
        return jsonify({"error": "Failed to fetch characters", "details": str(e)}), 500

@npcs_bp.route('/upload', methods=['POST'])
@login_required
def upload_npc_file():
    if 'npc_file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['npc_file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and file.filename.endswith('.json'):
        try:
            npc_data = json.load(file) # This loads the JSON content from the file stream
            
            npc_collection = mongo.db[NPC_COLLECTION_NAME]
            users_collection = mongo.db[USERS_COLLECTION_NAME]

            # Assign a new _id (as string) and user_id
            # The 'type' field should ideally be IN THE UPLOADED JSON FILE.
            # If not, you might default it here, but it's better if the user specifies it.
            if 'type' not in npc_data or npc_data['type'] not in ['pc', 'npc']:
                current_app.logger.warn(f"Uploaded character JSON for user {current_user.id} missing valid 'type'. Defaulting to 'npc'.")
                npc_data['type'] = 'npc' # Default if not specified in upload

            # Determine ID - reuse determine_id_for_character if it handles user uploads well,
            # or simplify for user uploads if they always get a new UUID or specific format.
            # For user uploads, typically a new unique ID is generated.
            
            # Let's assume uploaded NPCs always get a new unique ID string managed by this upload process.
            # We won't use the complex determine_id_for_character from load_npc_data.py here,
            # as that's more for initial data loading and reconciling existing IDs.
            
            # If the uploaded JSON contains an "_id", respect it if it's a string.
            # Otherwise, generate a new one.
            if "_id" in npc_data and isinstance(npc_data["_id"], str):
                npc_id_str = npc_data["_id"]
            else:
                npc_id_str = str(uuid.uuid4()) # Generate a new unique ID
            
            npc_data['_id'] = npc_id_str
            npc_data['user_id'] = current_user.get_id() # Assign to current user (ensure get_id() returns string or ObjectId as stored)
                                                       # If user_id is stored as ObjectId in DB, convert here.

            # Check if an NPC with this _id already exists for this user or globally
            existing_npc = npc_collection.find_one({"_id": npc_data['_id']})
            if existing_npc:
                # If it's a global NPC, user cannot overwrite.
                if existing_npc.get('user_id') is None:
                     return jsonify({"error": f"NPC with ID {npc_data['_id']} is a default NPC and cannot be overwritten."}), 409
                # If it belongs to another user, they shouldn't be able to see it to overwrite.
                # If it belongs to the current user, this is an update.
                if str(existing_npc.get('user_id')) == str(current_user.get_id()):
                    npc_collection.replace_one({"_id": npc_data['_id'], "user_id": current_user.get_id()}, npc_data)
                    current_app.logger.info(f"NPC {npc_data.get('name', npc_data['_id'])} updated by user {current_user.id}")
                    return jsonify({"message": "NPC updated successfully", "npc_id": npc_data['_id']}), 200
                else: # Should not happen if queries are correct, but as a safeguard
                    return jsonify({"error": "Conflict with existing NPC ID."}), 409


            # Insert new NPC
            result = npc_collection.insert_one(npc_data)
            
            # Add NPC ID to user's list of NPCs
            users_collection.update_one(
                {"_id": ObjectId(current_user.get_id())}, # Assuming current_user.get_id() is string of ObjectId
                {"$addToSet": {"npc_ids": str(result.inserted_id)}}
            )
            # Update current_user session object if necessary (Flask-Login usually handles user object state)
            if hasattr(current_user, 'npc_ids') and isinstance(current_user.npc_ids, list):
                 if str(result.inserted_id) not in current_user.npc_ids:
                    current_user.npc_ids.append(str(result.inserted_id))


            current_app.logger.info(f"NPC {npc_data.get('name', str(result.inserted_id))} uploaded by user {current_user.id} with type '{npc_data['type']}'")
            return jsonify({"message": "NPC uploaded successfully", "npc_id": str(result.inserted_id)}), 201

        except json.JSONDecodeError:
            return jsonify({"error": "Invalid JSON format"}), 400
        except Exception as e:
            current_app.logger.error(f"NPC Upload Error: {e}", exc_info=True)
            return jsonify({"error": "An internal error occurred", "details": str(e)}), 500
    else:
        return jsonify({"error": "Invalid file type, only .json allowed"}), 400


@npcs_bp.route('/<npc_id_str>', methods=['GET'])
@login_required
def get_single_npc(npc_id_str):
    try:
        npc_collection = mongo.db[NPC_COLLECTION_NAME]
        
        # Try to find as user's NPC first
        # Ensure npc_id_str is queried correctly (string vs ObjectId)
        npc = npc_collection.find_one({"_id": npc_id_str, "user_id": ObjectId(current_user.get_id())}) 
        if not npc:
            # If not found, try to find as a global NPC
            npc = npc_collection.find_one({"_id": npc_id_str, "$or": [{"user_id": {"$exists": False}}, {"user_id": None}]})

        if not npc:
            return jsonify({"error": "NPC not found or not accessible"}), 404

        npc["_id"] = str(npc["_id"]) # Ensure _id is string
        if 'user_id' in npc and npc['user_id'] is not None:
            npc['user_id'] = str(npc['user_id'])
            
        return jsonify(npc)
    except Exception as e:
        current_app.logger.error(f"Error fetching single NPC {npc_id_str}: {e}", exc_info=True)
        return jsonify({"error": "An error occurred", "details": str(e)}), 500


@npcs_bp.route('/<npc_id_str>', methods=['PUT'])
@login_required
def update_npc(npc_id_str):
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided for update"}), 400

        npc_collection = mongo.db[NPC_COLLECTION_NAME]
        
        # User can only update their own NPCs. They cannot update default NPCs.
        query_filter = {"_id": npc_id_str, "user_id": ObjectId(current_user.get_id())}
        
        # Fields that should not be updatable by the user directly through this generic PUT
        # _id is immutable, user_id is set by system.
        # 'type' could be updatable if you allow users to re-classify, but handle with care.
        # For now, let's assume 'type' is not changed via this generic update.
        # If you want to allow 'type' update, remove it from forbidden_updates.
        forbidden_updates = ['_id', 'user_id', 'id'] 
        update_data = {k: v for k, v in data.items() if k not in forbidden_updates}

        if not update_data:
            return jsonify({"error": "No valid fields provided for update"}), 400

        result = npc_collection.update_one(query_filter, {"$set": update_data})

        if result.matched_count == 0:
            # Check if it's a global NPC the user is trying to edit
            is_global_check = npc_collection.find_one({"_id": npc_id_str, "$or": [{"user_id": {"$exists": False}}, {"user_id": None}]})
            if is_global_check:
                 return jsonify({"error": "Forbidden: Default NPCs cannot be modified by users."}), 403
            return jsonify({"error": "NPC not found or you don't have permission to edit it"}), 404
        
        if result.modified_count == 0 and result.matched_count > 0:
             return jsonify({"message": "NPC data was the same, no changes made.", "npc_id": npc_id_str}), 200


        return jsonify({"message": "NPC updated successfully", "npc_id": npc_id_str}), 200
    except Exception as e:
        current_app.logger.error(f"Error updating NPC {npc_id_str}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred", "details": str(e)}), 500


@npcs_bp.route('/<npc_id_str>', methods=['DELETE'])
@login_required
def delete_npc(npc_id_str):
    try:
        npc_collection = mongo.db[NPC_COLLECTION_NAME]
        users_collection = mongo.db[USERS_COLLECTION_NAME]

        # Ensure current_user.get_id() is in the correct format for querying user_id
        # If user_id in DB is ObjectId, convert current_user.get_id()
        user_mongo_id = ObjectId(current_user.get_id())

        npc_to_delete = npc_collection.find_one({"_id": npc_id_str, "user_id": user_mongo_id})
        
        if not npc_to_delete:
            is_global_check = npc_collection.find_one({"_id": npc_id_str, "$or": [{"user_id": {"$exists": False}}, {"user_id": None}]})
            if is_global_check:
                return jsonify({"error": "Forbidden: Default NPCs cannot be deleted by users."}), 403
            return jsonify({"error": "NPC not found or you do not have permission to delete it"}), 404

        result = npc_collection.delete_one({"_id": npc_id_str, "user_id": user_mongo_id})

        if result.deleted_count == 0: # Should not happen if find_one succeeded, but as a safeguard
            return jsonify({"error": "NPC not found or delete failed (no document deleted)"}), 404
        
        # Remove NPC ID from user's list of NPCs
        users_collection.update_one(
            {"_id": user_mongo_id},
            {"$pull": {"npc_ids": npc_id_str}} 
        )
        # Also update the session/current_user object if it holds this list and is mutable
        if hasattr(current_user, 'npc_ids') and isinstance(current_user.npc_ids, list) and npc_id_str in current_user.npc_ids:
            current_user.npc_ids.remove(npc_id_str)
            # If your User class has a save method or similar for session updates:
            # current_user.save() 

        current_app.logger.info(f"NPC {npc_id_str} deleted by user {current_user.id}")
        return jsonify({"message": "NPC deleted successfully", "npc_id": npc_id_str}), 200
    except Exception as e:
        current_app.logger.error(f"Error deleting NPC {npc_id_str}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred", "details": str(e)}), 500

# Ensure this blueprint is registered in your app's __init__.py
# from .routes.npcs import npcs_bp 
# app.register_blueprint(npcs_bp, url_prefix='/api/npcs') 
# Note: The url_prefix is already in the Blueprint definition above, 
# so if you register it like app.register_blueprint(npcs_bp), the routes will be /api/npcs/...