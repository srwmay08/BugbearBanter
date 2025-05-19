# server/app/services/dialogue_service.py
import google.generativeai as genai # type: ignore
from flask import current_app 

class DialogueService:
    def __init__(self):
        current_app.logger.error("--- DEBUG: DialogueService __init__ CALLED ---") # New Log
        self.gemini_api_key = current_app.config.get('GEMINI_API_KEY') or current_app.config.get('GOOGLE_API_KEY')
        
        if not self.gemini_api_key:
            current_app.logger.error("--- DEBUG: DialogueService __init__ - Gemini API key NOT FOUND. ---") # Changed to error
            self.model = None
            return

        try:
            # Attempt to configure genai if not already done.
            # Note: genai. अभी._is_configured is an internal check and might change.
            # A more robust way is to ensure configure() is called once at app startup.
            if not hasattr(genai, '_is_configured_custom_flag'): # Using a custom flag to avoid re-configuring if not needed
                genai.configure(api_key=self.gemini_api_key)
                genai._is_configured_custom_flag = True # Set our custom flag
                current_app.logger.info("--- DEBUG: DialogueService __init__ - genai.configure called. ---")
            else:
                current_app.logger.info("--- DEBUG: DialogueService __init__ - genai already configured. ---")

            model_name = current_app.config.get('GEMINI_MODEL_NAME', 'gemini-1.5-flash-latest')
            self.model = genai.GenerativeModel(model_name)
            current_app.logger.error(f"--- DEBUG: DialogueService __init__ - GenerativeModel '{model_name}' INITIALIZED. ---") # Changed to error
        except Exception as e:
            current_app.logger.error(f"--- DEBUG: DialogueService __init__ - FAILED to initialize GenerativeModel: {e} ---") # Changed to error
            self.model = None

    def generate_dialogue_for_npc_in_scene(self, npc_profile, scene_description, conversation_history):
        current_app.logger.error("--- DEBUG: DialogueService generate_dialogue_for_npc_in_scene CALLED ---") # New Log

        if not self.model:
            current_app.logger.error("--- DEBUG: generate_dialogue_for_npc_in_scene - Gemini model not initialized. ---")
            return "[Error: AI Model Not Initialized. Check API Key and Configuration.]"

        npc_name = npc_profile.get('name', 'The NPC')
        current_app.logger.info(f"--- DEBUG: Generating dialogue for: {npc_name} ---")


        # --- Construct a detailed prompt for the AI ---
        prompt_lines = []
        prompt_lines.append(f"You are an AI that excels at roleplaying. You will embody the character of {npc_name}, an NPC in a tabletop roleplaying game. Your personality, background, and current situation are detailed below. The Game Master (GM) will describe a scenario or ask a question. Your task is to respond with a single, immersive, in-character line of dialogue. This line should be exactly what {npc_name} says aloud. Do not include actions, thoughts, or any out-of-character narration. Stay true to the character's voice and motivations.")
        
        prompt_lines.append(f"\n--- Your Character Profile: {npc_name} ---")
        if npc_profile.get('race'):
            prompt_lines.append(f"Race: {npc_profile['race']}")
        if npc_profile.get('class'): 
            prompt_lines.append(f"Class/Role: {npc_profile['class']}")
        if npc_profile.get('appearance'):
            prompt_lines.append(f"Appearance: {npc_profile['appearance']}")
        if npc_profile.get('personality_traits'):
            prompt_lines.append(f"Key Personality Traits: {', '.join(npc_profile['personality_traits'])}. You MUST embody these traits in your response.")
        if npc_profile.get('backstory'):
            prompt_lines.append(f"Relevant Backstory Snippet: {npc_profile['backstory'][:300]}...") 
        if npc_profile.get('motivations'):
            prompt_lines.append(f"Primary Motivations: {npc_profile['motivations']}. Let these motivations strongly guide what you say.")
        if npc_profile.get('flaws'):
            prompt_lines.append(f"Flaws/Weaknesses: {npc_profile['flaws']}. These might make your reactions imperfect or biased.")
        
        prompt_lines.append("\n--- Current Scene (Described by GM) ---")
        prompt_lines.append(scene_description)

        if conversation_history:
            prompt_lines.append("\n--- Recent Conversation (Your lines are from your perspective as {npc_name}) ---")
            for entry in conversation_history[-4:]: 
                prompt_lines.append(f"{entry.get('speaker', 'Unknown')}: \"{entry.get('text', '')}\"")
        
        prompt_lines.append(f"\n--- Your Task ({npc_name}'s Response) ---")
        prompt_lines.append(f"Considering all the above information about yourself ({npc_name}) and the current scene, what is the one thing you say next? Your response must be a direct quote from {npc_name}'s perspective. Be creative, stay in character, and make your response directly relevant to the scene and your motivations. Do not just acknowledge the scene; react to it, question it, or initiate based on your personality. For example, if the GM says, \"{scene_description}\", how would YOU, {npc_name}, specifically respond with a line of dialogue?")
        prompt_lines.append("Output ONLY the spoken dialogue line itself, without any prefixes like your name or quotation marks unless they are part of the dialogue.")

        full_prompt = "\n".join(prompt_lines)
        
        # This is the crucial debug line you uncommented. Make sure it's hit.
        current_app.logger.error(f"--- DEBUG: Full prompt for {npc_name} (first 300 chars): {full_prompt[:300]} ---") # Changed to error
        current_app.logger.debug(f"Full prompt for {npc_name}:\n{full_prompt}") # This is the one you originally uncommented

        try:
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            ]
            generation_config = genai.types.GenerationConfig(
                temperature=0.75, 
                max_output_tokens=150 
            )

            response = self.model.generate_content(
                full_prompt,
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            
            if response.parts:
                generated_text = "".join(part.text for part in response.parts if hasattr(part, 'text')).strip()
                
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
                return generated_text if generated_text else f"[{npc_name} remains silent, observing.]"
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
