# server/app/routes/dialogue.py
from flask import Blueprint, request, jsonify, current_app, Response
# Ensure DialogueService is imported from the correct path
from ..services.dialogue_service import DialogueService # This should be the version from dialogue_service_final_debug
# Ensure mongo is imported for database access
from ..utils.db import mongo 

dialogue_bp = Blueprint('dialogue', __name__)

@dialogue_bp.route('/generate_npc_line', methods=['POST'])
def generate_npc_line_route():
    # Using print for maximum visibility during debugging
    print("--- PRINT DEBUG: /api/dialogue/generate_npc_line ROUTE HIT ---") 
    current_app.logger.critical("--- CRITICAL DEBUG: /api/dialogue/generate_npc_line ROUTE HIT ---") 
    
    retrieved_gemini_key = current_app.config.get('GEMINI_API_KEY')
    retrieved_google_key = current_app.config.get('GOOGLE_API_KEY')
    print(f"--- PRINT DEBUG [ROUTE]: current_app.config.get('GEMINI_API_KEY') = {retrieved_gemini_key}")
    print(f"--- PRINT DEBUG [ROUTE]: current_app.config.get('GOOGLE_API_KEY') = {retrieved_google_key}")
    current_app.logger.critical(f"--- CRITICAL DEBUG [ROUTE]: GEMINI_API_KEY from app.config: {'SET' if retrieved_gemini_key else 'NOT SET'}")
    current_app.logger.critical(f"--- CRITICAL DEBUG [ROUTE]: GOOGLE_API_KEY from app.config: {'SET' if retrieved_google_key else 'NOT SET'}")

    if not (retrieved_gemini_key or retrieved_google_key):
        print("--- PRINT DEBUG [ROUTE]: API Key NOT FOUND in current_app.config. ABORTING. ---")
        current_app.logger.critical("--- CRITICAL DEBUG [ROUTE]: API Key NOT FOUND in current_app.config. DialogueService will fail. ABORTING early.")
        return jsonify({"error": "Server configuration error: API Key not found by the application. Please check server .env and config files."}), 500
    
    data = request.get_json()
    if not data:
        print("--- PRINT DEBUG [ROUTE]: No JSON data received.")
        current_app.logger.critical("--- CRITICAL DEBUG: /generate_npc_line - No JSON data received.")
        return jsonify({"error": "Invalid request: No JSON data received or malformed."}), 400

    npc_id = data.get('npc_id')
    scene_context = data.get('scene_context')
    conversation_history = data.get('history', []) 

    if not npc_id or not scene_context:
        print(f"--- PRINT DEBUG [ROUTE]: Missing npc_id or scene_context. NPC_ID: '{npc_id}', Scene: {'Provided' if scene_context else 'Missing'}")
        current_app.logger.critical(f"--- CRITICAL DEBUG: /generate_npc_line - Missing npc_id or scene_context. NPC_ID: '{npc_id}', Scene: {'Provided' if scene_context else 'Missing'}")
        return jsonify({"error": "npc_id and scene_context are required fields."}), 400
    
    current_app.logger.info(f"--- INFO DEBUG: /generate_npc_line - Request for NPC_ID: '{npc_id}'")

    try:
        npc_data_from_db = mongo.db.npcs.find_one({"_id": npc_id})
        if not npc_data_from_db:
            print(f"--- PRINT DEBUG [ROUTE]: NPC ID '{npc_id}' NOT FOUND in DB.")
            current_app.logger.critical(f"--- CRITICAL DEBUG: /generate_npc_line - NPC ID '{npc_id}' NOT FOUND in DB.")
            return jsonify({"error": f"NPC with ID '{npc_id}' not found."}), 404
        
        npc_profile_for_service = {
            "name": npc_data_from_db.get("name", "Unknown NPC"),
            "appearance": npc_data_from_db.get("appearance", ""),
            "personality_traits": npc_data_from_db.get("personality_traits", []),
            "backstory": npc_data_from_db.get("backstory", ""), 
            "motivations": npc_data_from_db.get("motivations", ""), 
            "flaws": npc_data_from_db.get("flaws", ""),
            "race": npc_data_from_db.get("race", ""),
            "class": npc_data_from_db.get("class", "") 
        }
        current_app.logger.info(f"--- INFO DEBUG: /generate_npc_line - NPC Profile fetched for '{npc_profile_for_service.get('name')}'")

    except Exception as e:
        print(f"--- PRINT DEBUG [ROUTE]: DB error fetching NPC '{npc_id}': {e}")
        current_app.logger.critical(f"--- CRITICAL DEBUG: /generate_npc_line - DB error fetching NPC '{npc_id}': {e}")
        current_app.logger.exception("Full exception during DB fetch:")
        return jsonify({"error": "DB error fetching NPC profile.", "details": str(e)}), 500

    try:
        dialogue_service = DialogueService() 
        
        if dialogue_service.model is None: 
            print("--- PRINT DEBUG [ROUTE]: DialogueService model is None AFTER instantiation. ---")
            current_app.logger.critical("--- CRITICAL DEBUG: /generate_npc_line - DialogueService model is None AFTER instantiation. AI service init failed.")
            return jsonify({"error": "AI service initialization failed. Please check server logs for API key or model configuration issues."}), 500
            
        ai_response_text = dialogue_service.generate_dialogue_for_npc_in_scene(
            npc_profile=npc_profile_for_service,
            scene_description=scene_context,
            conversation_history=conversation_history
        ) 

        if ai_response_text: 
            current_app.logger.info(f"--- INFO DEBUG: /generate_npc_line - Generated dialogue for '{npc_id}': \"{ai_response_text[:100]}...\"")
            return jsonify({"dialogue_text": ai_response_text}), 200
        else:
            print(f"--- PRINT DEBUG [ROUTE]: Dialogue service returned None or empty for '{npc_id}'.")
            current_app.logger.critical(f"--- CRITICAL DEBUG: /generate_npc_line - Dialogue service returned None or empty for '{npc_id}'.")
            return jsonify({"error": "AI failed to generate dialogue (empty response from service)."}), 500
            
    except Exception as e:
        print(f"--- PRINT DEBUG [ROUTE]: Unexpected error calling DialogueService for '{npc_id}': {e}")
        current_app.logger.critical(f"--- CRITICAL DEBUG: /generate_npc_line - Unexpected error calling DialogueService or processing its response for '{npc_id}': {e}")
        current_app.logger.exception("Full exception during dialogue generation call:")
        return jsonify({"error": "Unexpected server error during dialogue generation."}), 500

@dialogue_bp.route('/npc_action', methods=['POST'])
def npc_action_route():
    """
    Handles various actions related to an NPC in a scene,
    like submitting to memory, getting next topic, etc.
    Expects JSON: {
        "npc_id": "string",
        "action_type": "string" (e.g., "submit_memory", "next_topic"),
        "payload": {object}, // Optional, action-specific data
        "scene_description": "string", // Optional, current scene context
        "history": [ { "speaker": "string", "text": "string" }, ... ] // Optional, recent conversation history
    }
    """
    current_app.logger.info("--- INFO DEBUG: /api/dialogue/npc_action ROUTE HIT ---")
    print("--- PRINT DEBUG: /api/dialogue/npc_action ROUTE HIT ---")
    data = request.get_json()

    if not data:
        current_app.logger.error("--- ERROR DEBUG: /npc_action - No JSON data received.")
        return jsonify({"error": "Invalid request: No JSON data."}), 400

    npc_id = data.get('npc_id')
    action_type = data.get('action_type')
    payload = data.get('payload', {}) 
    scene_description = data.get('scene_description', payload.get('scene_description', ''))
    conversation_history = data.get('history', payload.get('history', []))

    if not npc_id or not action_type:
        current_app.logger.error(f"--- ERROR DEBUG: /npc_action - Missing npc_id or action_type. NPC_ID: {npc_id}, Action: {action_type}")
        return jsonify({"error": "npc_id and action_type are required."}), 400

    current_app.logger.info(f"--- INFO DEBUG: NPC Action - NPC_ID: '{npc_id}', Action: '{action_type}', Payload: {str(payload)[:100]}...")

    # Fetch NPC profile (simplified version for now, as not all actions might need full deep profile)
    try:
        npc_data_from_db = mongo.db.npcs.find_one({"_id": npc_id})
        if not npc_data_from_db:
            current_app.logger.error(f"--- ERROR DEBUG: /npc_action - NPC ID '{npc_id}' NOT FOUND for action '{action_type}'.")
            return jsonify({"error": f"NPC with ID '{npc_id}' not found."}), 404
        
        # Pass a relevant subset of the profile, or the full profile if needed by the service method
        npc_profile = {
            "name": npc_data_from_db.get("name", "Unknown NPC"),
            "personality_traits": npc_data_from_db.get("personality_traits", []),
            "motivations": npc_data_from_db.get("motivations", []),
            # Add other fields if your handle_npc_action service method uses them
        }
        current_app.logger.info(f"--- INFO DEBUG: /npc_action - Profile fetched for '{npc_profile.get('name')}' for action '{action_type}'.")
    except Exception as e:
        current_app.logger.error(f"--- ERROR DEBUG: /npc_action - DB error fetching NPC '{npc_id}' for action '{action_type}': {e}")
        current_app.logger.exception("Full exception during DB fetch for NPC action:")
        return jsonify({"error": "DB error fetching NPC profile for action."}), 500

    try:
        dialogue_service = DialogueService()
        # Check if model is needed for this specific action type
        actions_requiring_model = ["next_topic", "regenerate_topics", "show_top5_options"]
        if action_type in actions_requiring_model and dialogue_service.model is None:
            current_app.logger.error(f"--- ERROR DEBUG: /npc_action - DialogueService model is None for AI-dependent action '{action_type}'.")
            return jsonify({"error": f"AI service initialization failed for action '{action_type}'. Check server logs."}), 500

        response_data = dialogue_service.handle_npc_action(
            npc_id=npc_id, # Though service might re-fetch or use profile directly
            action_type=action_type,
            payload=payload,
            npc_profile=npc_profile, 
            scene_description=scene_description, 
            conversation_history=conversation_history
        )
        
        if response_data.get("status") == "error":
            current_app.logger.error(f"--- ERROR DEBUG: /npc_action - Action '{action_type}' for NPC '{npc_id}' failed with message: {response_data.get('message')}")
            return jsonify(response_data), response_data.get("code", 500) # Use a code from response if available
        
        current_app.logger.info(f"--- INFO DEBUG: /npc_action - Action '{action_type}' for NPC '{npc_id}' processed successfully.")
        return jsonify(response_data), 200

    except Exception as e:
        current_app.logger.error(f"--- ERROR DEBUG: /npc_action - Unexpected error during NPC action '{action_type}' for NPC '{npc_id}': {e}")
        current_app.logger.exception("Full exception during NPC action:")
        return jsonify({"error": f"Unexpected server error during NPC action '{action_type}'."}), 500

