# ---- server/app/routes/npcs.py ----
from flask import Blueprint, jsonify
from ..utils.db import mongo # Or however you access your NPC collection

npcs_bp = Blueprint('npcs', __name__)

@npcs_bp.route('', methods=['GET'])
def get_npcs():
    try:
        # Assuming your NPCs are stored in a collection named 'npcs'
        # And you want to return all of them. Add filters/pagination as needed.
        npcs_cursor = mongo.db.npcs.find({})
        npcs_list = []
        for npc in npcs_cursor:
            npc['_id'] = str(npc['_id']) # Convert ObjectId to string for JSON
            # Add any other necessary transformations
            npcs_list.append(npc)
        return jsonify(npcs_list), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500