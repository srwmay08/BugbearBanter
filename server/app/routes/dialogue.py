# ---- server/app/routes/dialogue.py ----
from flask import Blueprint, request, jsonify, current_app, Response
from ..services.dialogue_service import DialogueService
# from ..utils.db import mongo # For fetching NPC data, etc.
# from bson import ObjectId # If you need to convert string IDs to MongoDB ObjectIds

dialogue_bp = Blueprint('dialogue', __name__)

@dialogue_bp.route('/generate', methods=['POST'])
def generate_dialogue_route():
    """
    Endpoint to generate NPC dialogue text.
    Expects JSON: {
        "npc_id": "...",
        "scene_context": "...",
        "custom_prompt": "..."
    }
    """
    data = request.get_json()
    if not data or not data.get('npc_id') or not data.get('scene_context'):
        return jsonify({"error": "npc_id and scene_context are required"}), 400

    npc_id = data['npc_id']
    scene_context = data['scene_context']
    custom_prompt = data.get('custom_prompt', "") # Optional

    # --- Placeholder for fetching NPC data ---
    # In a real app, fetch NPC details from the database:
    # try:
    #     npc_object_id = ObjectId(npc_id)
    # except Exception:
    #     return jsonify({"error": "Invalid NPC ID format"}), 400
    # npc_data = mongo.db.npcs.find_one({"_id": npc_object_id})
    # if not npc_data:
    #     return jsonify({"error": "NPC not found"}), 404
    # npc_profile = {"name": npc_data.get("name", "Unknown NPC"), "personality_traits": npc_data.get("personality_traits", [])}
    # --- End Placeholder ---
    
    # Using placeholder NPC data for now
    npc_profile = {"name": f"NPC_{npc_id}", "personality_traits": ["Brave", "Mysterious"]}


    dialogue_service = DialogueService() # Instantiated here, or could be managed by app context
    
    generated_text = dialogue_service.generate_dialogue_gemini(
        npc_profile=npc_profile,
        scene_context=scene_context,
        prompt_customization=custom_prompt
    )

    if generated_text:
        return jsonify({"dialogue_text": generated_text, "npc_name": npc_profile["name"]}), 200
    else:
        return jsonify({"error": "Failed to generate dialogue"}), 500

@dialogue_bp.route('/speak', methods=['POST'])
def speak_dialogue_route():
    """
    Endpoint to generate voice for a given text.
    Expects JSON: { "text": "...", "voice_id": "..." (optional) }
    """
    data = request.get_json()
    if not data or not data.get('text'):
        return jsonify({"error": "Text to speak is required"}), 400

    text_to_speak = data['text']
    # voice_id = data.get('voice_id', 'default_voice_id_from_config_or_service') # Get from request or use a default
    # For now, using the example voice ID from the service
    voice_id = "21m00Tcm4TlvDq8ikWAM" 

    dialogue_service = DialogueService()
    audio_data = dialogue_service.generate_voice_elevenlabs(text_to_speak, voice_id)

    if audio_data:
        return Response(audio_data, mimetype='audio/mpeg')
    else:
        return jsonify({"error": "Failed to generate voice"}), 500
