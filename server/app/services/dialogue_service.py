# ---- server/app/services/dialogue_service.py ----
import requests
from flask import current_app # To access app.config for API keys

class DialogueService:
    """
    Service class for handling dialogue generation with AI APIs.
    """
    def __init__(self):
        self.gemini_api_key = current_app.config.get('GEMINI_API_KEY')
        self.elevenlabs_api_key = current_app.config.get('ELEVENLABS_API_KEY')
        # Initialize API clients if necessary, e.g., Google Generative AI client

    def generate_dialogue_gemini(self, npc_profile, scene_context, prompt_customization):
        """
        Generates dialogue using Google Gemini.
        Args:
            npc_profile (dict): Information about the NPC.
            scene_context (str): Context of the current scene.
            prompt_customization (str): GM's specific instructions or prompt.
        Returns:
            str: The generated dialogue text, or None if an error occurs.
        """
        if not self.gemini_api_key:
            current_app.logger.error("Gemini API key is not configured.")
            return None

        # This is a very simplified example.
        # You'll need to use the actual Google Gemini API client library.
        # Construct the prompt carefully based on inputs.
        prompt = f"NPC Profile: {npc_profile['name']}, {npc_profile.get('personality_traits', '')}. " \
                 f"Scene: {scene_context}. " \
                 f"Task: Generate dialogue for this NPC. {prompt_customization}"
        
        current_app.logger.info(f"Generating dialogue with Gemini. Prompt: {prompt[:100]}...") # Log snippet

        # Example API call structure (replace with actual Gemini SDK usage)
        # try:
        #     # model = genai.GenerativeModel('gemini-pro') # Or your chosen model
        #     # response = model.generate_content(prompt)
        #     # return response.text
        #     pass # Placeholder for actual API call
        # except Exception as e:
        #     current_app.logger.error(f"Error calling Gemini API: {e}")
        #     return None
        
        return f"Placeholder Gemini dialogue for {npc_profile['name']}: '{prompt_customization}' in {scene_context}" # Placeholder

    def generate_voice_elevenlabs(self, text_to_speak, voice_id="21m00Tcm4TlvDq8ikWAM"): # Example voice ID
        """
        Generates voiceover using ElevenLabs.
        Args:
            text_to_speak (str): The text to convert to speech.
            voice_id (str): The ID of the ElevenLabs voice to use.
        Returns:
            bytes: The audio data, or None if an error occurs.
        """
        if not self.elevenlabs_api_key:
            current_app.logger.error("ElevenLabs API key is not configured.")
            return None

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.elevenlabs_api_key
        }
        data = {
            "text": text_to_speak,
            "model_id": "eleven_multilingual_v2", # Or your preferred model
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }
        
        current_app.logger.info(f"Generating voice with ElevenLabs for text: {text_to_speak[:50]}...")

        try:
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status() # Raises an HTTPError for bad responses (4XX or 5XX)
            return response.content # Returns audio data as bytes
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Error calling ElevenLabs API: {e}")
            if response is not None:
                current_app.logger.error(f"ElevenLabs API Response: {response.text}")
            return None
