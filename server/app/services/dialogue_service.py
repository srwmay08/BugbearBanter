# server/app/services/dialogue_service.py
import google.generativeai as genai # type: ignore # Assuming you've installed the google-generativeai package
from flask import current_app # To access app.config for API keys and logger

class DialogueService:
    """
    Service class for handling dialogue generation with AI APIs.
    """
    def __init__(self):
        # API keys should be loaded from app.config, set via environment variables
        # Ensure your config.py loads GOOGLE_API_KEY or GEMINI_API_KEY
        self.gemini_api_key = current_app.config.get('GEMINI_API_KEY') or current_app.config.get('GOOGLE_API_KEY')
        
        if not self.gemini_api_key:
            current_app.logger.warning("Gemini API key (GEMINI_API_KEY or GOOGLE_API_KEY) is not configured in app.config. Dialogue generation will fail.")
            self.model = None
            return # Stop initialization if no key

        try:
            # Ensure genai is configured. This should ideally be done once at app startup.
            # If genai.configure() was called in config.py or app init, this might not be needed here.
            # However, checking and configuring if not already done can be a safeguard.
            if not genai. अभी._is_configured: # A way to check if already configured (Note: internal API, might change)
                 genai.configure(api_key=self.gemini_api_key)
            
            self.model = genai.GenerativeModel(
                current_app.config.get('GEMINI_MODEL_NAME', 'gemini-1.5-flash-latest') # Or your preferred model like 'gemini-pro'
            )
            current_app.logger.info(f"GenerativeModel '{current_app.config.get('GEMINI_MODEL_NAME', 'gemini-1.5-flash-latest')}' initialized successfully.")
        except Exception as e:
            current_app.logger.error(f"Failed to initialize GenerativeModel or configure genai: {e}")
            self.model = None


    def generate_dialogue_for_npc_in_scene(self, npc_profile, scene_description, conversation_history):
        """
        Generates a single line of dialogue for an NPC based on their profile,
        the scene description, and recent conversation history.

        Args:
            npc_profile (dict): Contains details like name, personality, backstory, race, class, etc.
            scene_description (str): The GM's description of the current scene.
            conversation_history (list): A list of recent dialogue turns, e.g.,
                                         [{"speaker": "NPC_NAME", "text": "..."}, {"speaker": "GM", "text": "..."}]

        Returns:
            str: The generated dialogue text, or a placeholder/error message if an error occurs.
        """
        if not self.model:
            current_app.logger.error("Gemini model not initialized. Cannot generate dialogue.")
            return "[Error: AI Model Not Initialized. Check API Key and Configuration.]"
        # No need to check self.gemini_api_key again if model initialization relied on it.

        npc_name = npc_profile.get('name', 'The NPC')

        # --- Construct a detailed prompt for the AI ---
        prompt_lines = []
        prompt_lines.append(f"You are an AI that excels at roleplaying. You will embody the character of {npc_name}, an NPC in a tabletop roleplaying game. Your personality, background, and current situation are detailed below. The Game Master (GM) will describe a scenario or ask a question. Your task is to respond with a single, immersive, in-character line of dialogue. This line should be exactly what {npc_name} says aloud. Do not include actions, thoughts, or any out-of-character narration. Stay true to the character's voice and motivations.")
        
        prompt_lines.append(f"\n--- Your Character Profile: {npc_name} ---")
        if npc_profile.get('race'):
            prompt_lines.append(f"Race: {npc_profile['race']}")
        if npc_profile.get('class'): # 'class' is a common field name
            prompt_lines.append(f"Class/Role: {npc_profile['class']}")
        if npc_profile.get('appearance'):
            prompt_lines.append(f"Appearance: {npc_profile['appearance']}")
        if npc_profile.get('personality_traits'):
            prompt_lines.append(f"Key Personality Traits: {', '.join(npc_profile['personality_traits'])}. You MUST embody these traits in your response.")
        if npc_profile.get('backstory'):
            # Limit backstory length to keep prompt focused
            prompt_lines.append(f"Relevant Backstory Snippet: {npc_profile['backstory'][:300]}...") 
        if npc_profile.get('motivations'):
            prompt_lines.append(f"Primary Motivations: {npc_profile['motivations']}. Let these motivations strongly guide what you say.")
        if npc_profile.get('flaws'):
            prompt_lines.append(f"Flaws/Weaknesses: {npc_profile['flaws']}. These might make your reactions imperfect or biased.")
        
        prompt_lines.append("\n--- Current Scene (Described by GM) ---")
        prompt_lines.append(scene_description)

        if conversation_history:
            prompt_lines.append("\n--- Recent Conversation (Your lines are from your perspective as {npc_name}) ---")
            # Show last 3-4 exchanges to provide immediate context
            for entry in conversation_history[-4:]: 
                prompt_lines.append(f"{entry.get('speaker', 'Unknown')}: \"{entry.get('text', '')}\"")
        
        prompt_lines.append(f"\n--- Your Task ({npc_name}'s Response) ---")
        prompt_lines.append(f"Considering all the above information about yourself ({npc_name}) and the current scene, what is the one thing you say next? Your response must be a direct quote from {npc_name}'s perspective. Be creative, stay in character, and make your response directly relevant to the scene and your motivations. Do not just acknowledge the scene; react to it, question it, or initiate based on your personality. For example, if the GM says, \"{scene_description}\", how would YOU, {npc_name}, specifically respond with a line of dialogue?")
        prompt_lines.append("Output ONLY the spoken dialogue line itself, without any prefixes like your name or quotation marks unless they are part of the dialogue.")

        full_prompt = "\n".join(prompt_lines)
        
        current_app.logger.info(f"Attempting to generate dialogue for {npc_name}. Prompt (first 300 chars): {full_prompt[:300]}...")
        # For detailed debugging, uncomment the next line to see the full prompt in your Flask logs:
        current_app.logger.debug(f"Full prompt for {npc_name}:\n{full_prompt}")

        try:
            # Safety settings: Adjust as needed. BLOCK_NONE can lead to undesirable content.
            # Start with more restrictive settings and loosen if necessary and appropriate.
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            ]
            
            generation_config = genai.types.GenerationConfig(
                temperature=0.75, # 0.0 (deterministic) to 1.0 (more creative). 0.7-0.8 is often good.
                # top_p=0.95, # Nucleus sampling
                # top_k=40,   # Top-k sampling
                max_output_tokens=150 # Max length of the generated dialogue line
            )

            response = self.model.generate_content(
                full_prompt,
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            
            # current_app.logger.debug(f"Gemini Raw Response for {npc_name}: {response}")

            if response.parts:
                generated_text = "".join(part.text for part in response.parts if hasattr(part, 'text')).strip()
                
                # Clean up common AI artifacts
                if generated_text.lower().startswith(f"{npc_name.lower()}:"):
                    generated_text = generated_text[len(npc_name)+1:].strip()
                
                common_ai_prefixes = ["dialogue:", "response:", f"{npc_name} says:"]
                for prefix in common_ai_prefixes:
                    if generated_text.lower().startswith(prefix.lower()): # Case-insensitive prefix check
                        generated_text = generated_text[len(prefix):].strip()

                # Remove surrounding quotes if the AI consistently adds them and they are not part of the dialogue
                if len(generated_text) > 1 and ((generated_text.startswith('"') and generated_text.endswith('"')) or \
                   (generated_text.startswith("'") and generated_text.endswith("'"))):
                    generated_text = generated_text[1:-1]
                
                current_app.logger.info(f"Successfully generated dialogue for {npc_name}: \"{generated_text}\"")
                return generated_text if generated_text else f"[{npc_name} remains silent, observing.]" # Fallback for empty string
            else:
                block_reason_msg = "Response contained no usable parts."
                if response.prompt_feedback and response.prompt_feedback.block_reason:
                    block_reason_msg = response.prompt_feedback.block_reason_message
                    current_app.logger.error(f"Prompt for {npc_name} was blocked by API. Reason: {block_reason_msg}")
                else:
                    current_app.logger.warning(f"Gemini response for {npc_name} had no usable parts. Full Response: {response}")
                return f"[{npc_name} seems unable to respond. AI Reason: {block_reason_msg}]"

        except Exception as e:
            current_app.logger.error(f"Exception during Gemini API call for {npc_name}: {e}")
            return f"[Error: AI service encountered an issue while generating a line for {npc_name}.]"

    # If you have an ElevenLabs voice generation service, it would remain here.
    # def generate_voice_elevenlabs(self, text_to_speak, voice_id="21m00Tcm4TlvDq8ikWAM"):
    #     # ... (implementation as before) ...
    #     pass
