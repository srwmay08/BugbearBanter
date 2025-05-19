# server/app/routes/world_info.py
from flask import Blueprint, jsonify, current_app, request
from ..utils.db import mongo
from flask_login import login_required # Assuming only logged-in users can manage world info
from bson import ObjectId # For handling MongoDB ObjectIds
import uuid # If you prefer string UUIDs for new items

world_info_bp = Blueprint('world_info', __name__)

# --- Events CRUD ---
@world_info_bp.route('/events', methods=['GET'])
@login_required
def get_world_events():
    try:
        events_cursor = mongo.db.world_events.find({})
        events = []
        for event in events_cursor:
            event['_id'] = str(event['_id']) # Ensure _id is string
            events.append(event)
        return jsonify(events), 200
    except Exception as e:
        current_app.logger.error(f"Error fetching world events: {e}", exc_info=True)
        return jsonify({"error": "Failed to fetch world events."}), 500

@world_info_bp.route('/events', methods=['POST'])
@login_required
def create_world_event():
    try:
        data = request.get_json()
        if not data or not data.get('name') or not data.get('description'):
            return jsonify({"error": "Name and description are required for an event."}), 400
        
        # You can choose to generate _id as ObjectId or string UUID
        # event_id = ObjectId() # MongoDB ObjectId
        event_id = str(uuid.uuid4()) # String UUID

        new_event = {
            "_id": event_id,
            "name": data['name'],
            "description": data['description'],
            "impact": data.get('impact', ''),
            "status": data.get('status', 'Ongoing'),
            # Add any other relevant fields
        }
        mongo.db.world_events.insert_one(new_event)
        # Convert _id to string for the response if it was an ObjectId
        new_event['_id'] = str(new_event['_id']) 
        return jsonify({"message": "World event created successfully.", "event": new_event}), 201
    except Exception as e:
        current_app.logger.error(f"Error creating world event: {e}", exc_info=True)
        return jsonify({"error": "Failed to create world event."}), 500

@world_info_bp.route('/events/<event_id_str>', methods=['PUT'])
@login_required
def update_world_event(event_id_str):
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No update data provided."}), 400

        query_id = event_id_str
        if ObjectId.is_valid(event_id_str): # Check if it's a valid ObjectId string
            # If your _ids for world_events are ObjectIds:
            # query_id = ObjectId(event_id_str)
            pass # Assuming string UUIDs for now based on create_world_event

        update_data = {k: v for k, v in data.items() if k != '_id'} # Don't allow changing _id

        result = mongo.db.world_events.update_one({"_id": query_id}, {"$set": update_data})

        if result.matched_count == 0:
            return jsonify({"error": "World event not found."}), 404
        if result.modified_count == 0:
            return jsonify({"message": "World event data was the same, no changes made."}), 200
        
        updated_event = mongo.db.world_events.find_one({"_id": query_id})
        if updated_event:
            updated_event['_id'] = str(updated_event['_id'])
        return jsonify({"message": "World event updated successfully.", "event": updated_event}), 200
    except Exception as e:
        current_app.logger.error(f"Error updating world event {event_id_str}: {e}", exc_info=True)
        return jsonify({"error": "Failed to update world event."}), 500

@world_info_bp.route('/events/<event_id_str>', methods=['DELETE'])
@login_required
def delete_world_event(event_id_str):
    try:
        query_id = event_id_str
        if ObjectId.is_valid(event_id_str):
            # query_id = ObjectId(event_id_str) # If using ObjectIds
            pass

        result = mongo.db.world_events.delete_one({"_id": query_id})
        if result.deleted_count == 0:
            return jsonify({"error": "World event not found."}), 404
        return jsonify({"message": "World event deleted successfully."}), 200
    except Exception as e:
        current_app.logger.error(f"Error deleting world event {event_id_str}: {e}", exc_info=True)
        return jsonify({"error": "Failed to delete world event."}), 500

# --- Locations CRUD (Similar structure) ---
@world_info_bp.route('/locations', methods=['GET'])
@login_required
def get_world_locations():
    try:
        locations_cursor = mongo.db.world_locations.find({})
        locations = []
        for loc in locations_cursor:
            loc['_id'] = str(loc['_id'])
            locations.append(loc)
        return jsonify(locations), 200
    except Exception as e:
        current_app.logger.error(f"Error fetching world locations: {e}", exc_info=True)
        return jsonify({"error": "Failed to fetch world locations."}), 500
# TODO: Add POST, PUT, DELETE for /locations

# --- Religions CRUD (Similar structure) ---
@world_info_bp.route('/religions', methods=['GET'])
@login_required
def get_world_religions():
    try:
        religions_cursor = mongo.db.world_religions.find({})
        religions = []
        for rel in religions_cursor:
            rel['_id'] = str(rel['_id'])
            religions.append(rel)
        return jsonify(religions), 200
    except Exception as e:
        current_app.logger.error(f"Error fetching world religions: {e}", exc_info=True)
        return jsonify({"error": "Failed to fetch world religions."}), 500
# TODO: Add POST, PUT, DELETE for /religions

# Helper route to get all world info at once (as used by dashboard)
@world_info_bp.route('/all', methods=['GET']) # Changed from '' to '/all'
@login_required
def get_all_world_info():
    try:
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
        current_app.logger.error(f"Error fetching all world info: {e}", exc_info=True)
        return jsonify({"error": "Failed to fetch all world information."}), 500