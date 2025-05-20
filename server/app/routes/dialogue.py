# server/app/routes/dialogue.py
from flask import Blueprint, request, jsonify, current_app, Response
from ..services.dialogue_service import DialogueService 
from ..utils.db import mongo 
# asyncio import and async_to_sync wrapper are no longer needed if all service calls are sync
# import asyncio 

dialogue_bp = Blueprint('dialogue', __name__)

# def async_to_sync(f): # No longer needed if all calls become synchronous
#     import functools
#     @functools.wraps(f)
#     def wrapper(*args, **kwargs):
#         return asyncio.run(f(*args, **kwargs))
#     return wrapper

@dialogue_bp.route('/generate_npc_line', methods=['POST'])
def generate_npc_line_route():
    # (This route is already synchronous and correct from the previous step)
    print("--- PRINT DEBUG: /api/dialogue/generate_npc_line ROUTE HIT ---") 
    current_app.logger.critical("--- CRITICAL DEBUG: /api/dialogue/generate_npc_line ROUTE HIT ---") 
    retrieved_gemini_key = current_app.config.get('GEMINI_API_KEY')
    retrieved_google_key = current_app.config.get('GOOGLE_API_KEY')
    if not (retrieved_gemini_key or retrieved_google_key):
        current_app.logger.critical("--- CRITICAL DEBUG [ROUTE]: API Key NOT FOUND. ABORTING early.")
        return jsonify({"error": "Server configuration error: API Key not found."}), 500
    data = request.get_json()
    if not data:
        current_app.logger.critical("--- CRITICAL DEBUG: /generate_npc_line - No JSON data.")
        return jsonify({"error": "Invalid request: No JSON data."}), 400
    npc_id = data.get('npc_id')
    scene_context = data.get('scene_context')
    conversation_history = data.get('history', []) 
    if not npc_id or not scene_context:
        current_app.logger.critical(f"--- CRITICAL DEBUG: /generate_npc_line - Missing fields.")
        return jsonify({"error": "npc_id and scene_context are required."}), 400
    current_app.logger.info(f"--- INFO DEBUG: /generate_npc_line - Req for NPC_ID: '{npc_id}'")
    try:
        npc_data_from_db = mongo.db.npcs.find_one({"_id": npc_id})
        if not npc_data_from_db:
            current_app.logger.critical(f"--- CRITICAL DEBUG: NPC ID '{npc_id}' NOT FOUND.")
            return jsonify({"error": f"NPC with ID '{npc_id}' not found."}), 404
        current_app.logger.info(f"--- INFO DEBUG: NPC Profile fetched for '{npc_data_from_db.get('name')}'")
    except Exception as e:
        current_app.logger.critical(f"--- CRITICAL DEBUG: DB error fetching NPC '{npc_id}': {e}", exc_info=True)
        return jsonify({"error": "DB error fetching NPC profile.", "details": str(e)}), 500
    try:
        dialogue_service = DialogueService() 
        if dialogue_service.model is None: 
            current_app.logger.critical("--- CRITICAL DEBUG: DialogueService model is None.")
            return jsonify({"error": "AI service initialization failed."}), 500
        ai_response_text = dialogue_service.generate_dialogue_for_npc_in_scene(
            npc_profile=npc_data_from_db, 
            scene_description=scene_context,
            conversation_history=conversation_history
        ) 
        if ai_response_text: 
            current_app.logger.info(f"--- INFO DEBUG: Generated dialogue for '{npc_id}'.")
            return jsonify({"dialogue_text": ai_response_text}), 200
        else:
            current_app.logger.critical(f"--- CRITICAL DEBUG: Dialogue service returned None/empty for '{npc_id}'.")
            return jsonify({"error": "AI failed to generate dialogue."}), 500
    except Exception as e:
        current_app.logger.critical(f"--- CRITICAL DEBUG: Error calling DialogueService for '{npc_id}': {e}", exc_info=True)
        return jsonify({"error": "Unexpected server error during dialogue generation."}), 500

@dialogue_bp.route('/npc_action', methods=['POST'])
# Removed @async_to_sync and async def
def npc_action_route():
    current_app.logger.info("--- INFO DEBUG: /api/dialogue/npc_action ROUTE HIT (SYNC) ---")
    data = request.get_json()

    if not data:
        current_app.logger.error("--- ERROR DEBUG: /npc_action - No JSON data.")
        return jsonify({"error": "Invalid request: No JSON data."}), 400

    npc_id = data.get('npc_id')
    action_type = data.get('action_type')
    payload = data.get('payload', {}) 
    scene_description = data.get('scene_description', payload.get('scene_description', '')) 
    conversation_history = data.get('history', payload.get('history', [])) 

    if not npc_id or not action_type:
        current_app.logger.error(f"--- ERROR DEBUG: /npc_action - Missing fields. NPC_ID: {npc_id}, Action: {action_type}")
        return jsonify({"error": "npc_id and action_type are required."}), 400

    current_app.logger.info(f"--- INFO DEBUG: NPC Action - NPC_ID: '{npc_id}', Action: '{action_type}', Payload: {str(payload)[:100]}...")

    try:
        # For most actions, a minimal profile might be enough for the service to decide if it needs more.
        # The service's handle_npc_action will fetch the full profile if needed (e.g., for submit_memory).
        npc_profile_minimal = mongo.db.npcs.find_one({"_id": npc_id}, {"name": 1, "personality_traits": 1, "motivations": 1, "memories": 1}) # Include memories for context
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

        # Calling the now synchronous service method
        response_data = dialogue_service.handle_npc_action(
            npc_id=npc_id, 
            action_type=action_type,
            payload=payload,
            npc_profile=npc_profile_minimal, 
            scene_description=scene_description, 
            conversation_history=conversation_history
        )
        
        status_code = 200
        if response_data.get("status") == "error":
            current_app.logger.error(f"--- ERROR DEBUG: /npc_action - Action '{action_type}' for NPC '{npc_id}' failed: {response_data.get('message')}")
            status_code = response_data.get("code", 500) 
        
        current_app.logger.info(f"--- INFO DEBUG: /npc_action - Action '{action_type}' for NPC '{npc_id}' processed. Status: {response_data.get('status')}, Message: {response_data.get('message')}")
        return jsonify(response_data), status_code

    except Exception as e:
        current_app.logger.error(f"--- ERROR DEBUG: /npc_action - Unexpected error during NPC action '{action_type}' for NPC '{npc_id}': {e}", exc_info=True)
        return jsonify({"error": f"Unexpected server error during NPC action '{action_type}'."}), 500