# server/app/services/dialogue_service.py
import google.generativeai as genai # type: ignore # Ensure NO leading spaces/tabs on this line or the comment above
from flask import current_app 

class DialogueService:
    def __init__(self):
        # Using both print and logger for maximum visibility during debugging
        print("--- PRINT DEBUG: DialogueService __init__ ENTERED ---")
        current_app.logger.critical("--- CRITICAL DEBUG: DialogueService __init__ ENTERED ---") 
        
        self.gemini_api_key = current_app.config.get('GEMINI_API_KEY') or current_app.config.get('GOOGLE_API_KEY')
        
        print(f"--- PRINT DEBUG: DialogueService __init__ - API Key Retrieved: {'SET' if self.gemini_api_key else 'NOT SET'} ---")
        current_app.logger.critical(f"--- CRITICAL DEBUG: DialogueService __init__ - API Key Retrieved: {'SET' if self.gemini_api_key else 'NOT SET'} ---")

        if not self.gemini_api_key:
            print("--- PRINT DEBUG: DialogueService __init__ - Gemini API key IS MISSING. Model will not be initialized. ---")
            current_app.logger.critical("--- CRITICAL DEBUG: DialogueService __init__ - Gemini API key IS MISSING. Model will not be initialized. ---")
            self.model = None
            return 

        try:
            print("--- PRINT DEBUG: DialogueService __init__ - Attempting to configure genai and initialize model... ---")
            current_app.logger.info("--- INFO DEBUG: DialogueService __init__ - Attempting to configure genai and initialize model... ---")

            if not hasattr(genai, '_is_configured_globally_by_bugbear_v3'): # Use a new flag version
                print("--- PRINT DEBUG: DialogueService __init__ - Calling genai.configure()... ---")
                current_app.logger.info("--- INFO DEBUG: Attempting to call genai.configure()... ---")
                genai.configure(api_key=self.gemini_api_key)
                genai._is_configured_globally_by_bugbear_v3 = True 
                print("--- PRINT DEBUG: DialogueService __init__ - genai.configure() CALLED SUCCESSFULLY. ---")
                current_app.logger.critical("--- CRITICAL DEBUG: DialogueService __init__ - genai.configure() CALLED SUCCESSFULLY. ---")
            else:
                print("--- PRINT DEBUG: DialogueService __init__ - genai already configured globally. ---")
                current_app.logger.info("--- INFO DEBUG: genai already configured globally by Bugbear. ---")

            model_name = current_app.config.get('GEMINI_MODEL_NAME', 'gemini-1.5-flash-latest')
            print(f"--- PRINT DEBUG: DialogueService __init__ - Attempting to initialize GenerativeModel with name: {model_name} ---")
            current_app.logger.info(f"--- INFO DEBUG: Attempting to initialize GenerativeModel with name: {model_name} ---")
            
            self.model = genai.GenerativeModel(model_name)
            
            print(f"--- PRINT DEBUG: DialogueService __init__ - GenerativeModel '{model_name}' INITIALIZED SUCCESSFULLY. ---")
            current_app.logger.critical(f"--- CRITICAL DEBUG: DialogueService __init__ - GenerativeModel '{model_name}' INITIALIZED SUCCESSFULLY. ---")

        except Exception as e:
            print(f"--- PRINT DEBUG: DialogueService __init__ - FAILED to initialize GenerativeModel or configure genai: {e} ---")
            current_app.logger.critical(f"--- CRITICAL DEBUG: DialogueService __init__ - FAILED to initialize GenerativeModel or configure genai: {e} ---")
            current_app.logger.exception("Full exception during DialogueService init:") 
            self.model = None

    def generate_dialogue_for_npc_in_scene(self, npc_profile, scene_description, conversation_history):
        print("--- PRINT DEBUG: DialogueService generate_dialogue_for_npc_in_scene CALLED ---")
        current_app.logger.critical("--- CRITICAL DEBUG: DialogueService generate_dialogue_for_npc_in_scene CALLED ---")

        if not self.model:
            print("--- PRINT DEBUG: generate_dialogue_for_npc_in_scene - Gemini model is None. ---")
            current_app.logger.critical("--- CRITICAL DEBUG: generate_dialogue_for_npc_in_scene - Gemini model is None. Cannot generate. ---")
            return "[Error: AI Model Not Initialized. Check server logs for API key/configuration issues.]"

        npc_name = npc_profile.get('name', 'The NPC')
        current_app.logger.info(f"--- INFO DEBUG: Generating dialogue for: {npc_name} ---")

        # --- Construct a detailed prompt for the AI ---
        prompt_lines = []
        prompt_lines.append(f"You are an AI roleplaying as {npc_name}, an NPC in a fantasy tabletop game. Your persona is defined by the details below. The Game Master (GM) will describe a situation. Your response MUST be a single, in-character line of dialogue that {npc_name} would say aloud. It should directly reflect your character's personality, motivations, and current understanding of the scene. Do NOT describe actions, thoughts, or break character. Only provide the spoken words.")
        
        prompt_lines.append(f"\n=== {npc_name}'s Character Profile ===")
        prompt_lines.append(f"Name: {npc_name}")
        prompt_lines.append(f"Race: {npc_profile.get('race', 'Unknown')}")
        prompt_lines.append(f"Class/Role: {npc_profile.get('class', 'Unknown')}") 
        prompt_lines.append(f"Appearance: {npc_profile.get('appearance', 'Not clearly described.')}")
        
        if npc_profile.get('personality_traits'):
            prompt_lines.append(f"Key Personality Traits: {', '.join(npc_profile['personality_traits'])}. These are core to how you behave and speak. Embody them.")
        else:
            prompt_lines.append("Key Personality Traits: Not specified. (Respond based on general context or a neutral but observant stance).")

        if npc_profile.get('backstory'):
            prompt_lines.append(f"Relevant Backstory: {npc_profile['backstory'][:350]}...") 
        else:
            prompt_lines.append("Relevant Backstory: Not specified.")

        if npc_profile.get('motivations'):
            prompt_lines.append(f"Primary Motivations: {npc_profile['motivations']}. These should strongly influence your words and goals.")
        else:
            prompt_lines.append("Primary Motivations: Not specified.")

        if npc_profile.get('flaws'):
            prompt_lines.append(f"Flaws/Weaknesses: {npc_profile['flaws']}. These might cause you to react in particular, sometimes suboptimal, ways.")
        else:
            prompt_lines.append("Flaws/Weaknesses: Not specified.")
        
        prompt_lines.append("\n=== Current Scene (Described by GM) ===")
        prompt_lines.append(scene_description)

        if conversation_history:
            prompt_lines.append("\n=== Recent Conversation (Your lines are from your perspective as {npc_name}) ===")
            for entry in conversation_history[-3:]: 
                prompt_lines.append(f"{entry.get('speaker', 'Unknown')}: \"{entry.get('text', '')}\"")
        
        prompt_lines.append(f"\n=== Your Task: {npc_name}'s Next Spoken Line ===")
        prompt_lines.append(f"Given your profile and the current scene, what is the one thing you, {npc_name}, say next? Your response must be only the direct quote. Do not just acknowledge the scene; react to it, ask a question, or make a statement driven by your personality, motivations, or flaws. For instance, if the GM says, \"{scene_description}\", how would YOU, {npc_name}, specifically respond with a line of dialogue? Be concise and impactful. Your response should be unique and characteristic of {npc_name}.")
        prompt_lines.append("RESPONSE:")

        full_prompt = "\n".join(prompt_lines)
        
        print(f"--- PRINT DEBUG: Full prompt for {npc_name} (first 300 chars): {full_prompt[:300]} ---")
        current_app.logger.critical(f"--- CRITICAL DEBUG: Full prompt for {npc_name} (first 300 chars): {full_prompt[:300]} ---")
        # Uncomment for very detailed debugging of the entire prompt:
        # current_app.logger.debug(f"--- FULL PROMPT FOR {npc_name} ---\n{full_prompt}\n--- END OF FULL PROMPT ---")

        try:
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            ]
            
            generation_config = genai.types.GenerationConfig(
                temperature=0.75, 
                max_output_tokens=120 
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
                    if (generated_text[0] == '"' and generated_text[-1] == '"') or \
                       (generated_text[0] == "'" and generated_text[-1] == "'"):
                        generated_text = generated_text[1:-1]
                
                current_app.logger.info(f"Successfully generated dialogue for {npc_name}: \"{generated_text}\"")
                return generated_text if generated_text else f"[{npc_name} considers the situation.]" 
            else: 
                block_reason_msg = "Response contained no usable parts (e.g., empty or only safety attributes)."
                if hasattr(response, 'prompt_feedback') and response.prompt_feedback and response.prompt_feedback.block_reason:
                    block_reason_msg = response.prompt_feedback.block_reason_message
                    current_app.logger.error(f"Prompt for {npc_name} was BLOCKED by API. Reason: {block_reason_msg}. Full prompt feedback: {response.prompt_feedback}")
                else:
                    current_app.logger.warning(f"Gemini response for {npc_name} had no usable parts. Full Response object: {response}")
                return f"[{npc_name} seems unable to respond clearly. AI Reason: {block_reason_msg}]"

        except Exception as e:
            print(f"--- PRINT DEBUG: Exception during Gemini API call for {npc_name}: {e} ---")
            current_app.logger.critical(f"--- CRITICAL DEBUG: Exception during Gemini API call for {npc_name}: {e} ---")
            current_app.logger.exception("Full exception details during AI call:")
            return f"[Error: AI service encountered an issue for {npc_name}. Check server logs for full exception.]"
