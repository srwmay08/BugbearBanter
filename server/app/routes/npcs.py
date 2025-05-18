# ---- server/app/routes/npcs.py ----
from flask import Blueprint, jsonify
from ..utils.db import mongo # Assuming mongo is initialized and configured

npcs_bp = Blueprint('npcs', __name__)

@npcs_bp.route('', methods=['GET']) # Responds to GET /api/npcs
def get_npcs():
    try:
        # Replace 'npcs_collection_name' with your actual MongoDB collection name for NPCs
        npcs_cursor = mongo.db.npcs_collection_name.find({})
        npcs_list = []
        for npc in npcs_cursor:
            npc['_id'] = str(npc['_id']) # Convert ObjectId to string
            # Ensure your NPC documents have 'name', 'appearance', 'personality_traits'
            # or adjust the data you send and how app.js uses it.
            npcs_list.append(npc)
        return jsonify(npcs_list), 200
    except Exception as e:
        current_app.logger.error(f"Error fetching NPCs: {e}") # Requires from flask import current_app
        return jsonify({"error": "Failed to fetch NPCs", "details": str(e)}), 500