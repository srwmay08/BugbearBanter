# server/app/services/dialogue_service.py
import google.generativeai as genai # type: ignore
from flask import current_app 

class DialogueService:
    def __init__(self):
        current_app.logger.critical("--- CRITICAL DEBUG: DialogueService __init__ ENTERED ---") 
        
        self.gemini_api_key = current_app.config.get('GEMINI_API_KEY') or current_app.config.get('GOOGLE_API_KEY')
        current_app.logger.critical(f"--- CRITICAL DEBUG: DialogueService __init__ - API Key Retrieved: {'SET' if self.gemini_api_key else 'NOT SET'} ---")

        if not self.gemini_api_key:
            current_app.logger.critical("--- CRITICAL DEBUG: DialogueService __init__ - Gemini API key IS MISSING. Model will not be initialized. ---")
            self.model = None
            return

        try:
            # Ensure genai is configured. This should ideally happen once at app startup.
            # Using a simple flag to try and avoid re-configuration issues.
            if not hasattr(genai, '_is_configured_globally_by_bugbear'):
                current_app.logger.info("--- INFO DEBUG: Attempting to call genai.configure()... ---")
                genai.configure(api_key=self.gemini_api_key)
                genai._is_configured_globally_by_bugbear = True # Mark that we've configured it
                current_app.logger.critical("--- CRITICAL DEBUG: DialogueService __init__ - genai.configure() CALLED SUCCESSFULLY. ---")
            else:
                current_app.logger.info("--- INFO DEBUG: genai already configured globally by Bugbear. ---")

            model_name = current_app.config.get('GEMINI_MODEL_NAME', 'gemini-1.5-flash-latest')
            current_app.logger.info(f"--- INFO DEBUG: Attempting to initialize GenerativeModel with name: {model_name} ---")
            self.model = genai.GenerativeModel(model_name)
            current_app.logger.critical(f"--- CRITICAL DEBUG: DialogueService __init__ - GenerativeModel '{model_name}' INITIALIZED SUCCESSFULLY. ---")
        except Exception as e:
            current_app.logger.critical(f"--- CRITICAL DEBUG: DialogueService __init__ - FAILED to initialize GenerativeModel or configure genai: {e} ---")
            current_app.logger.exception("Full exception during DialogueService init:") # Logs full traceback
            self.model = None

    def generate_dialogue_for_npc_in_scene(self, npc_profile, scene_description, conversation_history):
        current_app.logger.critical("--- CRITICAL DEBUG: DialogueService generate_dialogue_for_npc_in_scene CALLED ---")

        if not self.model:
            current_app.logger.critical("--- CRITICAL DEBUG: generate_dialogue_for_npc_in_scene - Gemini model is None. Cannot generate. ---")
            return "[Error: AI Model Not Initialized. Check server logs for API key/configuration issues.]"

        npc_name = npc_profile.get('name', 'The NPC')
        current_app.logger.info(f"--- INFO DEBUG: Generating dialogue for: {npc_name} ---")

        prompt_lines = [
            f"You are an AI that excels at roleplaying. You will embody the character of {npc_name}, an NPC in a tabletop roleplaying game. Your personality, background, and current situation are detailed below. The Game Master (GM) will describe a scenario or ask a question. Your task is to respond with a single, immersive, in-character line of dialogue. This line should be exactly what {npc_name} says aloud. Do not include actions, thoughts, or any out-of-character narration. Stay true to the character's voice and motivations.",
            f"\n--- Your Character Profile: {npc_name} ---",
            f"Race: {npc_profile.get('race', 'Unknown')}",
            f"Class/Role: {npc_profile.get('class', 'Unknown')}",
            f"Appearance: {npc_profile.get('appearance', 'Not specified')}",
            f"Key Personality Traits: {', '.join(npc_profile.get('personality_traits', ['Not specified']))}. You MUST embody these traits.",
            f"Relevant Backstory Snippet: {npc_profile.get('backstory', 'Not specified')[:300]}...",
            f"Primary Motivations: {npc_profile.get('motivations', 'Not specified')}. Let these motivations strongly guide what you say.",
            f"Flaws/Weaknesses: {npc_profile.get('flaws', 'Not specified')}. These might influence your reactions.",
            "\n--- Current Scene (Described by GM) ---",
            scene_description,
        ]
        if conversation_history:
            prompt_lines.append("\n--- Recent Conversation (Your lines are from your perspective as {npc_name}) ---")
            for entry in conversation_history[-4:]: 
                prompt_lines.append(f"{entry.get('speaker', 'Unknown')}: \"{entry.get('text', '')}\"")
        
        prompt_lines.append(f"\n--- Your Task ({npc_name}'s Response) ---")
        prompt_lines.append(f"Considering all the above, what is the one thing you say next? Your response must be a direct quote from {npc_name}'s perspective. Be creative, stay in character, and make your response directly relevant. Do not just acknowledge the scene; react to it, question it, or initiate. For example, if the GM says, \"{scene_description}\", how would YOU, {npc_name}, specifically respond with a line of dialogue?")
        prompt_lines.append("Output ONLY the spoken dialogue line itself, without any prefixes like your name or quotation marks unless they are part of the dialogue.")

        full_prompt = "\n".join(prompt_lines)
        
        current_app.logger.critical(f"--- CRITICAL DEBUG: Full prompt for {npc_name} (first 300 chars): {full_prompt[:300]} ---")
        current_app.logger.debug(f"Full prompt for {npc_name}:\n{full_prompt}") # Full prompt for detailed inspection

        try:
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            ]
            generation_config = genai.types.GenerationConfig(temperature=0.75, max_output_tokens=150)

            response = self.model.generate_content(
                full_prompt,
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            
            if response.parts:
                generated_text = "".join(part.text for part in response.parts if hasattr(part, 'text')).strip()
                # Cleanup logic (as before)
                if generated_text.lower().startswith(f"{npc_name.lower()}:"):
                    generated_text = generated_text[len(npc_name)+1:].strip()
                common_ai_prefixes = ["dialogue:", "response:", f"{npc_name} says:"]
                for prefix in common_ai_prefixes:
                    if generated_text.lower().startswith(prefix.lower()):
                        generated_text = generated_text[len(prefix):].strip()
                if len(generated_text) > 1 and ((generated_text.startswith('"') and generated_text.endswith('"')) or \
                   (generated_text.startswith("'") and generated_text.endswith("'"))):
                    generated_text = generated_text[1:-1]
                
                current_app.logger.info(f"Successfully generated dialogue for {npc_name}: \"{generated_text}\"")
                return generated_text if generated_text else f"[{npc_name} ponders silently...]"
            else: # Handle blocked prompts or empty responses
                block_reason_msg = "Response contained no usable parts."
                if hasattr(response, 'prompt_feedback') and response.prompt_feedback and response.prompt_feedback.block_reason:
                    block_reason_msg = response.prompt_feedback.block_reason_message
                    current_app.logger.error(f"Prompt for {npc_name} was BLOCKED by API. Reason: {block_reason_msg}")
                else:
                    current_app.logger.warning(f"Gemini response for {npc_name} had no usable parts. Full Response: {response}")
                return f"[{npc_name} seems unable to respond. AI Reason: {block_reason_msg}]"

        except Exception as e:
            current_app.logger.critical(f"--- CRITICAL DEBUG: Exception during Gemini API call for {npc_name}: {e} ---")
            current_app.logger.exception("Full exception during AI call:")
            return f"[Error: AI service encountered an issue for {npc_name}. Check server logs.]"
