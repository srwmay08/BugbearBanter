# server/app/routes/dialogue.py
from flask import Blueprint, request, jsonify, current_app, Response
# Ensure DialogueService is imported from the correct path
from ..services.dialogue_service import DialogueService
# Ensure mongo is imported for database access
from ..utils.db import mongo 

dialogue_bp = Blueprint('dialogue', __name__)

# You might have other pre-existing routes here, like for ElevenLabs.
# Make sure to keep them if they are still needed.

@dialogue_bp.route('/generate_npc_line', methods=['POST'])
def generate_npc_line_route():
    """
    Endpoint to generate a single dialogue line for a specific NPC in a scene.
    Expects JSON: {
        "npc_id": "string",
        "scene_context": "string",
        "history": [ { "speaker": "string", "text": "string" }, ... ] // Optional
    }
    """
    # Log that the route was hit
    current_app.logger.error("--- DEBUG: /api/dialogue/generate_npc_line ROUTE HIT ---") 
    
    data = request.get_json()
    if not data:
        current_app.logger.error("--- DEBUG: /generate_npc_line - No JSON data received or data is None.")
        return jsonify({"error": "Invalid request: No JSON data received or malformed JSON."}), 400

    npc_id = data.get('npc_id')
    scene_context = data.get('scene_context')
    # Default to an empty list if 'history' is not provided or is None
    conversation_history = data.get('history', []) 

    if not npc_id or not scene_context:
        current_app.logger.error(f"--- DEBUG: /generate_npc_line - Missing npc_id or scene_context. NPC_ID: '{npc_id}', Scene Context Provided: {'Yes' if scene_context else 'No'}")
        return jsonify({"error": "npc_id and scene_context are required fields."}), 400
    
    current_app.logger.info(f"--- DEBUG: /generate_npc_line - Request received for NPC_ID: '{npc_id}'")

    # --- Fetch NPC Profile from Database ---
    try:
        # Ensure your NPC collection name in MongoDB is 'npcs'
        npc_data_from_db = mongo.db.npcs.find_one({"_id": npc_id})
        
        if not npc_data_from_db:
            current_app.logger.error(f"--- DEBUG: /generate_npc_line - NPC with ID '{npc_id}' NOT FOUND in database.")
            return jsonify({"error": f"NPC with ID '{npc_id}' not found in the database."}), 404
        
        # Prepare the npc_profile dictionary for the DialogueService.
        # Ensure these keys match what your data loader script (load_npc_data.py) stores
        # and what your DialogueService expects.
        npc_profile_for_service = {
            "name": npc_data_from_db.get("name", "Unknown NPC"),
            "appearance": npc_data_from_db.get("appearance", ""),
            "personality_traits": npc_data_from_db.get("personality_traits", []),
            "backstory": npc_data_from_db.get("backstory", ""), 
            "motivations": npc_data_from_db.get("motivations", ""), 
            "flaws": npc_data_from_db.get("flaws", ""),
            "race": npc_data_from_db.get("race", ""), # Added race
            "class": npc_data_from_db.get("class", "")  # Added class (ensure your loader saves this as 'class')
        }
        current_app.logger.info(f"--- DEBUG: /generate_npc_line - NPC Profile successfully fetched from DB for '{npc_profile_for_service.get('name')}' (ID: {npc_id})")

    except Exception as e:
        current_app.logger.error(f"--- DEBUG: /generate_npc_line - Database error fetching NPC profile for ID '{npc_id}': {e}")
        return jsonify({"error": "Failed to retrieve NPC profile due to a database error.", "details": str(e)}), 500

    # --- Instantiate DialogueService and Generate Dialogue ---
    try:
        # The DialogueService __init__ now has its own logging
        dialogue_service = DialogueService()
        
        # Check if the AI model was successfully initialized in the service
        if dialogue_service.model is None:
            current_app.logger.error("--- DEBUG: /generate_npc_line - DialogueService's AI model is None. This likely means API key or model configuration failed during service initialization.")
            return jsonify({"error": "AI service initialization failed. Please check server logs for API key or model configuration issues."}), 500
            
    except Exception as e:
        current_app.logger.error(f"--- DEBUG: /generate_npc_line - CRITICAL: Failed to instantiate DialogueService: {e}")
        return jsonify({"error": "AI dialogue service could not be started. Check server logs."}), 500
    
    try:
        # The generate_dialogue_for_npc_in_scene method also has its own logging
        ai_response_text = dialogue_service.generate_dialogue_for_npc_in_scene(
            npc_profile=npc_profile_for_service,
            scene_description=scene_context,
            conversation_history=conversation_history
        )

        if ai_response_text:
            # Log success before returning
            current_app.logger.info(f"--- DEBUG: /generate_npc_line - Successfully generated dialogue for NPC ID '{npc_id}': \"{ai_response_text[:100]}...\"")
            return jsonify({"dialogue_text": ai_response_text}), 200
        else:
            # This case should ideally be handled by more specific error messages from the service itself
            current_app.logger.error(f"--- DEBUG: /generate_npc_line - Dialogue service returned no text (None or empty) for NPC ID '{npc_id}'.")
            return jsonify({"error": "AI failed to generate a dialogue response for this NPC. The service returned no text."}), 500
            
    except Exception as e:
        # Catch any other unexpected errors during the dialogue generation call
        current_app.logger.error(f"--- DEBUG: /generate_npc_line - Unexpected error during dialogue generation call for NPC ID '{npc_id}': {e}")
        return jsonify({"error": "An unexpected server error occurred while generating dialogue."}), 500

# If you have other routes like for ElevenLabs TTS, they would go here.
# For example:
# @dialogue_bp.route('/speak', methods=['POST'])
# def speak_dialogue_route():
#     # ... your implementation for text-to-speech ...
#     pass
