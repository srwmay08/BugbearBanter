# server/app/routes/dialogue.py
from flask import Blueprint, request, jsonify, current_app, Response
from ..services.dialogue_service import DialogueService 
from ..utils.db import mongo 
import asyncio # For running async service methods

dialogue_bp = Blueprint('dialogue', __name__)

# Helper to run async function from sync Flask route
def async_to_sync(f):
    import functools
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapper

@dialogue_bp.route('/generate_npc_line', methods=['POST'])
# Removed @async_to_sync and async from def
def generate_npc_line_route():
    print("--- PRINT DEBUG: /api/dialogue/generate_npc_line ROUTE HIT ---") 
    current_app.logger.critical("--- CRITICAL DEBUG: /api/dialogue/generate_npc_line ROUTE HIT ---") 
    
    retrieved_gemini_key = current_app.config.get('GEMINI_API_KEY')
    retrieved_google_key = current_app.config.get('GOOGLE_API_KEY')
    if not (retrieved_gemini_key or retrieved_google_key):
        current_app.logger.critical("--- CRITICAL DEBUG [ROUTE]: API Key NOT FOUND in current_app.config. DialogueService will fail. ABORTING early.")
        return jsonify({"error": "Server configuration error: API Key not found by the application. Please check server .env and config files."}), 500

    data = request.get_json()
    if not data:
        current_app.logger.critical("--- CRITICAL DEBUG: /generate_npc_line - No JSON data received.")
        return jsonify({"error": "Invalid request: No JSON data received or malformed."}), 400

    npc_id = data.get('npc_id')
    scene_context = data.get('scene_context')
    conversation_history = data.get('history', []) 

    if not npc_id or not scene_context:
        current_app.logger.critical(f"--- CRITICAL DEBUG: /generate_npc_line - Missing npc_id or scene_context. NPC_ID: '{npc_id}', Scene: {'Provided' if scene_context else 'Missing'}")
        return jsonify({"error": "npc_id and scene_context are required fields."}), 400
    
    current_app.logger.info(f"--- INFO DEBUG: /generate_npc_line - Request for NPC_ID: '{npc_id}'")

    try:
        npc_data_from_db = mongo.db.npcs.find_one({"_id": npc_id})
        if not npc_data_from_db:
            current_app.logger.critical(f"--- CRITICAL DEBUG: /generate_npc_line - NPC ID '{npc_id}' NOT FOUND in DB.")
            return jsonify({"error": f"NPC with ID '{npc_id}' not found."}), 404
        
        current_app.logger.info(f"--- INFO DEBUG: /generate_npc_line - NPC Profile (including memories) fetched for '{npc_data_from_db.get('name')}'")

    except Exception as e:
        current_app.logger.critical(f"--- CRITICAL DEBUG: /generate_npc_line - DB error fetching NPC '{npc_id}': {e}", exc_info=True)
        return jsonify({"error": "DB error fetching NPC profile.", "details": str(e)}), 500

    try:
        dialogue_service = DialogueService() 
        
        if dialogue_service.model is None: 
            current_app.logger.critical("--- CRITICAL DEBUG: /generate_npc_line - DialogueService model is None AFTER instantiation. AI service init failed.")
            return jsonify({"error": "AI service initialization failed. Please check server logs for API key or model configuration issues."}), 500
            
        # Removed await, calling the now synchronous service method
        ai_response_text = dialogue_service.generate_dialogue_for_npc_in_scene(
            npc_profile=npc_data_from_db, 
            scene_description=scene_context,
            conversation_history=conversation_history
        ) 

        if ai_response_text: 
            current_app.logger.info(f"--- INFO DEBUG: /generate_npc_line - Generated dialogue for '{npc_id}': \"{ai_response_text[:100]}...\"")
            return jsonify({"dialogue_text": ai_response_text}), 200
        else:
            current_app.logger.critical(f"--- CRITICAL DEBUG: /generate_npc_line - Dialogue service returned None or empty for '{npc_id}'.")
            return jsonify({"error": "AI failed to generate dialogue (empty response from service)."}), 500
            
    except Exception as e:
        current_app.logger.critical(f"--- CRITICAL DEBUG: /generate_npc_line - Unexpected error calling DialogueService or processing its response for '{npc_id}': {e}", exc_info=True)
        return jsonify({"error": "Unexpected server error during dialogue generation."}), 500

@dialogue_bp.route('/npc_action', methods=['POST'])
@async_to_sync # This route handler remains async because handle_npc_action service method is async
async def npc_action_route():
    current_app.logger.info("--- INFO DEBUG: /api/dialogue/npc_action ROUTE HIT ---")
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

    try:
        npc_profile_minimal = mongo.db.npcs.find_one({"_id": npc_id}, {"name": 1, "personality_traits": 1, "motivations": 1}) 
        if not npc_profile_minimal:
            current_app.logger.error(f"--- ERROR DEBUG: /npc_action - NPC ID '{npc_id}' NOT FOUND for action '{action_type}'.")
            return jsonify({"error": f"NPC with ID '{npc_id}' not found."}), 404
        
        current_app.logger.info(f"--- INFO DEBUG: /npc_action - Minimal profile fetched for '{npc_profile_minimal.get('name')}' for action '{action_type}'.")
    except Exception as e:
        current_app.logger.error(f"--- ERROR DEBUG: /npc_action - DB error fetching NPC '{npc_id}' for action '{action_type}': {e}", exc_info=True)
        return jsonify({"error": "DB error fetching NPC profile for action."}), 500

    try:
        dialogue_service = DialogueService()
        actions_requiring_model = ["submit_memory", "next_topic", "regenerate_topics", "show_top5_options"]
        if action_type in actions_requiring_model and dialogue_service.model is None:
            current_app.logger.error(f"--- ERROR DEBUG: /npc_action - DialogueService model is None for AI-dependent action '{action_type}'.")
            return jsonify({"error": f"AI service initialization failed for action '{action_type}'. Check server logs."}), 500

        response_data = await dialogue_service.handle_npc_action(
            npc_id=npc_id, 
            action_type=action_type,
            payload=payload,
            npc_profile=npc_profile_minimal, 
            scene_description=scene_description, 
            conversation_history=conversation_history
        )
        
        status_code = 200
        if response_data.get("status") == "error":
            current_app.logger.error(f"--- ERROR DEBUG: /npc_action - Action '{action_type}' for NPC '{npc_id}' failed with message: {response_data.get('message')}")
            status_code = response_data.get("code", 500) 
        elif response_data.get("status") == "info" and action_type == "undo_memory" and "has no memories to remove" in response_data.get("message", ""):
             pass 
        elif response_data.get("status") == "info": 
            pass

        current_app.logger.info(f"--- INFO DEBUG: /npc_action - Action '{action_type}' for NPC '{npc_id}' processed. Status: {response_data.get('status')}, Message: {response_data.get('message')}")
        return jsonify(response_data), status_code

    except Exception as e:
        current_app.logger.error(f"--- ERROR DEBUG: /npc_action - Unexpected error during NPC action '{action_type}' for NPC '{npc_id}': {e}", exc_info=True)
        return jsonify({"error": f"Unexpected server error during NPC action '{action_type}'."}), 500