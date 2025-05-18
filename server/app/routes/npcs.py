# server/app/routes/npcs.py
from flask import Blueprint, jsonify, current_app
from ..utils.db import mongo # Assuming mongo is initialized via Flask-PyMongo

npcs_bp = Blueprint('npcs', __name__)

NPC_COLLECTION_NAME = 'npcs' # Should match the collection name in load_npc_data.py

@npcs_bp.route('', methods=['GET']) # Responds to GET /api/npcs
def get_npcs():
    try:
        # Access the MongoDB collection through the initialized 'mongo' object
        # The 'db' attribute of 'mongo' refers to your database.
        npc_collection = mongo.db[NPC_COLLECTION_NAME]
        
        npcs_cursor = npc_collection.find({})
        npcs_list = []
        for npc in npcs_cursor:
            # Convert MongoDB's ObjectId to string for JSON serialization
            if '_id' in npc and not isinstance(npc['_id'], str):
                 npc['_id'] = str(npc['_id'])
            
            # Convert other ObjectId fields if you have them (e.g., game_world_id)
            # Example:
            # if 'game_world_id' in npc and not isinstance(npc['game_world_id'], str):
            #    npc['game_world_id'] = str(npc['game_world_id'])

            npcs_list.append(npc)
            
        return jsonify(npcs_list), 200
    except Exception as e:
        # Use current_app.logger for logging within Flask context
        current_app.logger.error(f"An unexpected error occurred while fetching NPCs from MongoDB: {e}")
        return jsonify({"error": "Failed to fetch NPCs due to an internal server error.", "details": str(e)}), 500

