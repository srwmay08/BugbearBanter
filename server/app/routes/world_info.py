# server/app/routes/world_info.py
from flask import Blueprint, jsonify, current_app
from ..utils.db import mongo
from flask_login import login_required

world_info_bp = Blueprint('world_info', __name__)

@world_info_bp.route('', methods=['GET'])
@login_required # Make sure only logged-in users can access this
def get_world_info():
    try:
        # Fetching data from collections you've mentioned (e.g., in dialogue_service.py)
        # The dialogue_service.py already has a _get_world_knowledge_summary method
        # that accesses mongo.db.world_events, mongo.db.world_locations, mongo.db.world_religions
        # We'll fetch them directly here.

        events_cursor = mongo.db.world_events.find({})
        events = [{k: str(v) if k == '_id' else v for k, v in event.items()} for event in events_cursor]
        
        locations_cursor = mongo.db.world_locations.find({})
        locations = [{k: str(v) if k == '_id' else v for k, v in location.items()} for location in locations_cursor]

        religions_cursor = mongo.db.world_religions.find({})
        religions = [{k: str(v) if k == '_id' else v for k, v in religion.items()} for religion in religions_cursor]

        return jsonify({
            "events": events,
            "locations": locations,
            "religions": religions
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error fetching world info: {e}", exc_info=True)
        return jsonify({"error": "Failed to fetch world information."}), 500