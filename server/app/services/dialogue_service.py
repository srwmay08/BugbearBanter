# server/app/services/dialogue_service.py
# Ensure you have 'import google.generativeai as genai' and it's configured in config.py
import google.generativeai as genai # type: ignore
from flask import current_app # To access app.config for API keys and logger

class DialogueService:
    """
    Service class for handling dialogue generation with AI APIs.
    """
    def __init__(self):
        # API keys should be loaded from app.config, set via environment variables
        self.gemini_api_key = current_app.config.get('GEMINI_API_KEY') # Or GOOGLE_API_KEY
        if not self.gemini_api_key:
            # This check should ideally happen at app startup or when service is first used
            current_app.logger.warning("Gemini API key (GEMINI_API_KEY or GOOGLE_API_KEY) is not configured in app.config.")
            # Potentially raise an error or have a fallback if critical
        
        # Initialize the Gemini model - ensure genai is configured
        # This might be better done once, e.g., when the app starts or service is initialized,
        # if genai.configure() is not called globally already in config.py.
        # Assuming genai.configure(api_key=YOUR_KEY) has been called in config.py
        try:
            self.model = genai.GenerativeModel(current_app.config.get('GEMINI_MODEL_NAME', 'gemini-1.5-flash-latest')) # Or your preferred model
        except Exception as e:
            current_app.logger.error(f"Failed to initialize GenerativeModel: {e}")
            self.model = None


    def generate_dialogue_for_npc_in_scene(self, npc_profile, scene_description, conversation_history):
        """
        Generates a single line of dialogue for an NPC based on their profile,
        the scene description, and recent conversation history.

        Args:
            npc_profile (dict): Contains details like name, personality, backstory.
            scene_description (str): The GM's description of the current scene.
            conversation_history (list): A list of recent dialogue turns, e.g.,
                                         [{"speaker": "NPC_NAME", "text": "..."}, {"speaker": "GM", "text": "..."}]

        Returns:
            str: The generated dialogue text, or None if an error occurs.
        """
        if not self.model:
            current_app.logger.error("Gemini model not initialized. Cannot generate dialogue.")
            return None
        if not self.gemini_api_key: # Redundant if model init fails, but good check
             current_app.logger.error("Gemini API key is missing. Cannot generate dialogue.")
             return None


        # --- Construct a detailed prompt for the AI ---
        prompt_lines = []
        prompt_lines.append("You are an AI roleplaying assistant. Generate a single, immersive, in-character line of dialogue for an NPC in a tabletop roleplaying game based on the following information.")
        prompt_lines.append("\n--- NPC Profile ---")
        prompt_lines.append(f"Name: {npc_profile.get('name', 'NPC')}")
        if npc_profile.get('appearance'):
            prompt_lines.append(f"Appearance: {npc_profile['appearance']}")
        if npc_profile.get('personality_traits'):
            prompt_lines.append(f"Personality Traits: {', '.join(npc_profile['personality_traits'])}")
        if npc_profile.get('backstory'):
            prompt_lines.append(f"Relevant Backstory Snippet: {npc_profile['backstory'][:200]}...") # Keep it concise
        if npc_profile.get('motivations'):
            prompt_lines.append(f"Motivations: {npc_profile['motivations']}")
        if npc_profile.get('flaws'):
            prompt_lines.append(f"Flaws/Weaknesses: {npc_profile['flaws']}")
        
        prompt_lines.append("\n--- Current Scene Context ---")
        prompt_lines.append(scene_description)

        if conversation_history:
            prompt_lines.append("\n--- Recent Conversation History (most recent last) ---")
            for entry in conversation_history[-5:]: # Limit to last 5 entries for brevity
                prompt_lines.append(f"{entry.get('speaker', 'Unknown')}: {entry.get('text', '')}")
        
        prompt_lines.append(f"\n--- Task ---")
        prompt_lines.append(f"Considering all the above, generate one plausible and engaging line of dialogue that {npc_profile.get('name', 'the NPC')} would say now. The line should be a direct quote. Do not add narration or actions, only the spoken dialogue.")
        prompt_lines.append("Output only the dialogue line itself.")

        full_prompt = "\n".join(prompt_lines)
        
        current_app.logger.info(f"Generating dialogue for {npc_profile.get('name')} with prompt (first 200 chars): {full_prompt[:200]}...")

        try:
            # Configure safety settings to be less restrictive if needed, but be mindful of content policies
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
            generation_config = genai.types.GenerationConfig(
                # temperature=0.7, # Adjust for creativity vs. coherence
                # top_p=1.0,
                # top_k=40,
                # max_output_tokens=100 # Limit length of the dialogue line
            )

            response = self.model.generate_content(
                full_prompt,
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            
            # Debug: Log the full response parts if available
            # current_app.logger.debug(f"Gemini Raw Response Parts: {response.parts}")

            if response.parts:
                generated_text = "".join(part.text for part in response.parts if hasattr(part, 'text')).strip()
                # Clean up common AI artifacts like "NPC Name:" at the start if the prompt wasn't perfect
                if generated_text.lower().startswith(f"{npc_profile.get('name', 'NPC').lower()}:"):
                    generated_text = generated_text[len(npc_profile.get('name', 'NPC'))+1:].strip()
                # Remove surrounding quotes if AI adds them
                if (generated_text.startswith('"') and generated_text.endswith('"')) or \
                   (generated_text.startswith("'") and generated_text.endswith("'")):
                    generated_text = generated_text[1:-1]
                
                current_app.logger.info(f"Generated dialogue for {npc_profile.get('name')}: {generated_text}")
                return generated_text
            else:
                current_app.logger.warning(f"Gemini response for {npc_profile.get('name')} had no usable parts. Prompt block? Response: {response}")
                # Check for prompt_feedback if generation was blocked
                if response.prompt_feedback and response.prompt_feedback.block_reason:
                    current_app.logger.error(f"Prompt for {npc_profile.get('name')} was blocked. Reason: {response.prompt_feedback.block_reason_message}")
                    return f"[AI content generation blocked: {response.prompt_feedback.block_reason_message}]"
                return None

        except Exception as e:
            current_app.logger.error(f"Error calling Gemini API for {npc_profile.get('name')}: {e}")
            # Consider more specific error handling or re-raising
            return None

    # Keep your existing generate_voice_elevenlabs if needed
    def generate_voice_elevenlabs(self, text_to_speak, voice_id="21m00Tcm4TlvDq8ikWAM"):
        # ... (implementation as before) ...
        pass
