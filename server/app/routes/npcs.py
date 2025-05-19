# app/routes/npcs.py
from flask import Blueprint, jsonify, current_app, request, abort
from ..utils.db import mongo
from flask_login import login_required, current_user # For user-specific NPCs
import json
import uuid
from ..models import NPC # For consistency

npcs_bp = Blueprint('npcs', __name__)
NPC_COLLECTION_NAME = 'npcs'
USERS_COLLECTION_NAME = 'users'

@npcs_bp.route('', methods=['GET'])
@login_required # Protect this route - only logged-in users can see their NPCs
def get_user_npcs(): # Renamed to reflect it's user-specific
    try:
        npc_collection = mongo.db[NPC_COLLECTION_NAME]

        # Fetch NPCs associated with the current logged-in user
        # Assumes NPC documents have a 'user_id' field matching current_user.get_id()
        # And current_user.npc_ids stores the _ids of NPCs owned by the user.

        user_npc_ids = current_user.npc_ids or []
        if not user_npc_ids:
             return jsonify([]), 200 # No NPCs for this user

        # Convert string IDs to ObjectId if your DB uses ObjectId for NPC _id
        # If your NPC _ids are strings (like from uuid), this conversion is not needed.
        # from bson import ObjectId
        # object_id_list = [ObjectId(id_str) for id_str in user_npc_ids if ObjectId.is_valid(id_str)]
        # query = {"_id": {"$in": object_id_list}}

        # If NPC _ids are stored as strings in the DB (matching npc_ids in user doc):
        query = {"_id": {"$in": user_npc_ids}, "user_id": current_user.get_id()}

        npcs_cursor = npc_collection.find(query)
        npcs_list = []
        for npc in npcs_cursor:
            if '_id' in npc and not isinstance(npc['_id'], str):
                npc['_id'] = str(npc['_id'])
            if 'user_id' in npc and not isinstance(npc['user_id'], str): # Ensure user_id is string for consistency
                npc['user_id'] = str(npc['user_id'])
            npcs_list.append(npc)

        return jsonify(npcs_list), 200
    except Exception as e:
        current_app.logger.error(f"Error fetching user NPCs: {e}")
        return jsonify({"error": "Failed to fetch NPCs.", "details": str(e)}), 500

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
            npc_data_raw = json.load(file.stream) # file.stream is a file-like object

            # Validate basic structure (assuming single NPC object per file for now)
            if not isinstance(npc_data_raw, dict) or 'name' not in npc_data_raw:
                return jsonify({"error": "Invalid JSON format or missing NPC name."}), 400

            npc_collection = mongo.db[NPC_COLLECTION_NAME]
            users_collection = mongo.db[USERS_COLLECTION_NAME]

            # Prepare NPC document
            npc_id = str(uuid.uuid4()) # Generate a new unique ID for this NPC

            # Map fields from uploaded JSON to your NPC model structure
            # Using your Bugbear.json structure as a guide
            npc_doc = {
                '_id': npc_id,
                'user_id': current_user.get_id(), # Associate with current user
                'name': npc_data_raw.get('name'),
                'race': npc_data_raw.get('race'),
                'class': npc_data_raw.get('class'), # In DB, store as 'class'
                'alignment': npc_data_raw.get('alignment'),
                'age': npc_data_raw.get('age'),
                'personality_traits': npc_data_raw.get('personality_traits'), # Store as string
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
                'appearance': npc_data_raw.get('appearance', 'No description available.'), # Add if present
                'source_file': file.filename # Store original filename
            }
            # Remove None fields if you prefer cleaner DB entries
            npc_doc_cleaned = {k: v for k, v in npc_doc.items() if v is not None}


            npc_collection.insert_one(npc_doc_cleaned)

            # Add this NPC's ID to the user's list of NPC IDs
            users_collection.update_one(
                {"_id": current_user.get_id()},
                {"$addToSet": {"npc_ids": npc_id}} # $addToSet prevents duplicates
            )
            # Update current_user session object (important for Flask-Login)
            if npc_id not in current_user.npc_ids:
                current_user.npc_ids.append(npc_id)


            return jsonify({"message": f"NPC '{npc_doc.get('name')}' uploaded successfully with ID {npc_id}", "npc_id": npc_id}), 201

        except json.JSONDecodeError:
            return jsonify({"error": "Invalid JSON file."}), 400
        except Exception as e:
            current_app.logger.error(f"Error uploading NPC: {e}")
            return jsonify({"error": "Failed to upload NPC due to server error.", "details": str(e)}), 500
    else:
        return jsonify({"error": "Invalid file type. Only .json files are allowed."}), 400