# server/app/routes/dialogue.py
from flask import Blueprint, request, jsonify, current_app, Response
from ..services.dialogue_service import DialogueService
from ..utils.db import mongo 

dialogue_bp = Blueprint('dialogue', __name__)

@dialogue_bp.route('/generate_npc_line', methods=['POST'])
def generate_npc_line_route():
    current_app.logger.critical("--- CRITICAL DEBUG: /api/dialogue/generate_npc_line ROUTE HIT ---") 
    
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
        current_app.logger.critical(f"--- CRITICAL DEBUG: /generate_npc_line - DB error fetching NPC '{npc_id}': {e}")
        current_app.logger.exception("Full exception during DB fetch:")
        return jsonify({"error": "DB error fetching NPC profile.", "details": str(e)}), 500

    try:
        dialogue_service = DialogueService() # __init__ has its own critical logs
        if dialogue_service.model is None: 
            current_app.logger.critical("--- CRITICAL DEBUG: /generate_npc_line - DialogueService model is None AFTER instantiation. AI service init failed.")
            # This error message is now sent back to the frontend.
            return jsonify({"error": "AI service initialization failed. Please check server logs for API key or model configuration issues."}), 500
            
        ai_response_text = dialogue_service.generate_dialogue_for_npc_in_scene(
            npc_profile=npc_profile_for_service,
            scene_description=scene_context,
            conversation_history=conversation_history
        ) # This method also has critical logs

        if ai_response_text: # Check if text is not None and not empty
            current_app.logger.info(f"--- INFO DEBUG: /generate_npc_line - Generated dialogue for '{npc_id}': \"{ai_response_text[:100]}...\"")
            return jsonify({"dialogue_text": ai_response_text}), 200
        else:
            current_app.logger.critical(f"--- CRITICAL DEBUG: /generate_npc_line - Dialogue service returned None or empty for '{npc_id}'.")
            return jsonify({"error": "AI failed to generate dialogue (empty response from service)."}), 500
            
    except Exception as e:
        current_app.logger.critical(f"--- CRITICAL DEBUG: /generate_npc_line - Unexpected error calling DialogueService or processing its response for '{npc_id}': {e}")
        current_app.logger.exception("Full exception during dialogue generation call:")
        return jsonify({"error": "Unexpected server error during dialogue generation."}), 500
