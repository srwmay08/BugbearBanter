# server/app/routes/dialogue.py
from flask import Blueprint, request, jsonify, current_app, Response
from ..services.dialogue_service import DialogueService # Ensure this is correctly imported
# If you need to fetch NPC data from DB:
from ..utils.db import mongo # Assuming mongo is initialized via Flask-PyMongo

dialogue_bp = Blueprint('dialogue', __name__)

# Your existing /generate and /speak routes ... (keep them if still used)

@dialogue_bp.route('/generate_npc_line', methods=['POST'])
def generate_npc_line_route():
    """
    Endpoint to generate a single dialogue line for a specific NPC in a scene.
    Expects JSON: {
        "npc_id": "...",
        "scene_context": "...",
        "history": [ { "speaker": "...", "text": "..." }, ... ] // Optional conversation history
        // "npc_profile": { ... } // Optionally, frontend can send profile to reduce DB lookups
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request: No JSON data received."}), 400

    npc_id = data.get('npc_id')
    scene_context = data.get('scene_context')
    conversation_history = data.get('history', []) # Default to empty list if not provided
    # npc_profile_from_request = data.get('npc_profile') # If frontend sends it

    if not npc_id or not scene_context:
        return jsonify({"error": "npc_id and scene_context are required."}), 400

    # --- Fetch NPC Profile from Database ---
    # (If not provided directly by the frontend, which is generally more robust)
    try:
        # Assuming your NPC collection is named 'npcs'
        npc_data = mongo.db.npcs.find_one({"_id": npc_id})
        if not npc_data:
            return jsonify({"error": f"NPC with ID '{npc_id}' not found."}), 404
        
        # Prepare the profile for the dialogue service
        # You might want to select/format specific fields from npc_data
        npc_profile = {
            "name": npc_data.get("name", "Unknown NPC"),
            "appearance": npc_data.get("appearance", ""),
            "personality_traits": npc_data.get("personality_traits", []),
            "backstory": npc_data.get("backstory", ""), # Add if you have this field
            "motivations": npc_data.get("motivations", ""), # Add if you have this field
            "flaws": npc_data.get("flaws", ""), # Add if you have this field
            # Add any other fields from your NPC model relevant for dialogue generation
        }

    except Exception as e:
        current_app.logger.error(f"Error fetching NPC profile for ID {npc_id}: {e}")
        return jsonify({"error": "Failed to retrieve NPC profile from database.", "details": str(e)}), 500


    dialogue_service = DialogueService() # Instantiated here, or could be managed by app context
    
    try:
        # Call the service to generate dialogue
        # The service will construct the detailed prompt for the AI
        ai_response_text = dialogue_service.generate_dialogue_for_npc_in_scene(
            npc_profile=npc_profile,
            scene_description=scene_context,
            conversation_history=conversation_history
        )

        if ai_response_text:
            # For now, just returning the text. Later, you might return options too.
            return jsonify({"dialogue_text": ai_response_text}), 200
        else:
            current_app.logger.error(f"Dialogue service returned no text for NPC {npc_id} in scene.")
            return jsonify({"error": "AI failed to generate dialogue for this NPC."}), 500
            
    except Exception as e:
        current_app.logger.error(f"Error during dialogue generation for NPC {npc_id}: {e}")
        # Be careful about exposing raw error messages from AI services to the client
        return jsonify({"error": "An unexpected error occurred during dialogue generation."}), 500

