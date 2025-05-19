# server/app/services/dialogue_service.py
import google.generativeai as genai # type: ignore # Ensure NO leading spaces/tabs on this line or the comment above
from flask import current_app 
import random # For placeholder topic generation

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
        prompt_lines.append(f"You are an AI masterfully roleplaying as {npc_name}, a character in a rich fantasy world. Your goal is to deliver compelling, cinematic dialogue that reveals your character's depth, advances the narrative, and engages the Game Master (GM).")
        prompt_lines.append("The GM will describe a scene or pose a question. Your response MUST be a single, impactful, in-character line or two of spoken dialogue from {npc_name}'s perspective. Do NOT narrate actions, describe thoughts out of character, or break character. Focus purely on what {npc_name} says aloud.")
        
        prompt_lines.append(f"\n=== {npc_name}'s In-Depth Character Profile ===")
        prompt_lines.append(f"Name: {npc_name}")
        prompt_lines.append(f"Race: {npc_profile.get('race', 'Unknown')}")
        prompt_lines.append(f"Class/Role: {npc_profile.get('class', 'Unknown')}") 
        prompt_lines.append(f"Appearance: {npc_profile.get('appearance', 'Not clearly described.')}")
        
        if npc_profile.get('personality_traits'):
            prompt_lines.append(f"Core Personality Traits: {', '.join(npc_profile['personality_traits'])}. These traits MUST be evident in your speech and attitude. Consider the subtext they imply.")
        else:
            prompt_lines.append("Core Personality Traits: Not specified. (Adopt a generally observant and cautious demeanor, reacting based on the immediate context).")

        if npc_profile.get('backstory'):
            prompt_lines.append(f"Key Backstory Elements: {npc_profile['backstory'][:400]}...") # Provide a bit more backstory
        else:
            prompt_lines.append("Key Backstory Elements: Not specified.")

        if npc_profile.get('motivations'):
            prompt_lines.append(f"Driving Motivations: {npc_profile['motivations']}. Your dialogue should reflect these underlying goals and desires, even if subtly.")
        else:
            prompt_lines.append("Driving Motivations: Not specified.")

        if npc_profile.get('flaws'):
            prompt_lines.append(f"Significant Flaws/Weaknesses: {npc_profile['flaws']}. These can create internal conflict or lead to characteristic reactions or mistakes in your speech.")
        else:
            prompt_lines.append("Significant Flaws/Weaknesses: Not specified.")

        if npc_profile.get('speech_patterns'):
            prompt_lines.append(f"Speech Patterns: {npc_profile['speech_patterns']}. These should be considered when creating your response as this is how you speak in the world around you.")
        else:
            prompt_lines.append("Speech Patterns: Not specified.")
        
        if npc_profile.get('mannerisms'):
            prompt_lines.append(f"Mannerisms: {npc_profile['mannerisms']}. A distinctive behavioral trait, especially one that calls attention to itself; an idiosyncrasy.")
        else:
            prompt_lines.append("Mannerisms: Not specified.")

        if npc_profile.get('past_situation'):
            prompt_lines.append(f"Past history: {npc_profile['past_situation']}. These are events that happened to you in the past.")
        else:
            prompt_lines.append("Past: Not specified.")
            
        if npc_profile.get('current_situation'):
            prompt_lines.append(f"Current time: {npc_profile['current_situation']}. This is the current situation your find yourself in.")
        else:
            prompt_lines.append("Current: Not specified.")

        if npc_profile.get('relationship_with_pcs'):
            prompt_lines.append(f"Relationships: {npc_profile['relationships']}. These are details about the relationships you've built with the party.")
        else:
            prompt_lines.append("Relationships: Not specified.")
        

        
        prompt_lines.append("\n=== Current Scene Context (Provided by GM) ===")
        prompt_lines.append(scene_description)

        if conversation_history:
            prompt_lines.append("\n=== Recent Turns in Conversation (Your lines are as {npc_name}) ===")
            for entry in conversation_history[-3:]: 
                prompt_lines.append(f"{entry.get('speaker', 'Unknown')}: \"{entry.get('text', '')}\"")
        
        prompt_lines.append(f"\n=== Your Task: {npc_name}'s Cinematic Dialogue Line ===")
        prompt_lines.append(f"Based on your detailed profile ({npc_name}) and the current scene, deliver your next spoken line(s). Aim for dialogue that is memorable, reveals character, and feels like it belongs in a compelling story or movie. Avoid generic acknowledgments. Instead, react specifically, ask a pertinent question, make a charged statement, or subtly hint at your thoughts/intentions through your words. How would YOU, {npc_name}, truly respond in this moment to \"{scene_description}\"?")
        prompt_lines.append("Provide ONLY the dialogue spoken by {npc_name}. A slightly longer, more impactful statement (1-3 sentences) is appropriate for your character and the situation, deliver that.")
        prompt_lines.append("DIALOGUE RESPONSE:") # Clear marker for AI output

        full_prompt = "\n".join(prompt_lines)
        
        # Ensure the full prompt is logged for debugging if issues persist
        current_app.logger.debug(f"--- FULL PROMPT FOR {npc_name} ---\n{full_prompt}\n--- END OF FULL PROMPT ---")


        try:
            safety_settings = [ # Using slightly more permissive settings for creative dialogue
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
            ]
            
            generation_config = genai.types.GenerationConfig(
                temperature=0.8, # Increased for more creative/varied and less predictable dialogue
                top_p=0.95,      # Works with temperature to shape the output
                # top_k=50,      # Can be used, but top_p is often preferred with temperature
                max_output_tokens=200 # Allow for potentially longer, more "movie style" lines
            )

            response = self.model.generate_content(
                full_prompt,
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            
            if response.parts:
                generated_text = "".join(part.text for part in response.parts if hasattr(part, 'text')).strip()
                
                # Cleanup logic (as before, but ensure it's robust)
                if generated_text.lower().startswith(f"{npc_name.lower()}:"):
                    generated_text = generated_text[len(npc_name)+1:].strip()
                
                common_ai_prefixes = ["dialogue:", "response:", f"{npc_name} says:", "spokendialogue:"]
                for prefix in common_ai_prefixes:
                    if generated_text.lower().startswith(prefix.lower()): 
                        generated_text = generated_text[len(prefix):].strip()

                # Remove surrounding quotes only if they are the very first and very last characters
                if len(generated_text) > 1 and \
                   ((generated_text.startswith('"') and generated_text.endswith('"')) or \
                    (generated_text.startswith("'") and generated_text.endswith("'"))):
                    generated_text = generated_text[1:-1]
                
                current_app.logger.info(f"Successfully generated dialogue for {npc_name}: \"{generated_text}\"")
                return generated_text if generated_text else f"[{npc_name} pauses, considering the weight of the moment.]" 
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

    def handle_npc_action(self, npc_id, action_type, payload, npc_profile, scene_description, conversation_history):
        """
        Handles various NPC-specific actions triggered by dialogue controls.
        """
        current_app.logger.info(f"--- INFO DEBUG: Handling action '{action_type}' for NPC ID '{npc_id}' ---")
        npc_name = npc_profile.get('name', 'The NPC')

        if action_type == "submit_memory":
            # Placeholder: In a real app, you'd save this to the NPC's memory in the database.
            # The payload might contain the last few dialogue exchanges.
            dialogue_to_remember = payload.get("dialogue_exchange", "an important event")
            current_app.logger.info(f"NPC Action: '{npc_name}' is 'remembering': {dialogue_to_remember[:100]}...")
            # For now, just return a confirmation.
            return {"status": "success", "message": f"'{dialogue_to_remember[:30]}...' noted for {npc_name}."}

        elif action_type == "undo_memory":
            # Placeholder: Logic to find and remove the last memory item.
            current_app.logger.info(f"NPC Action: '{npc_name}' is attempting to 'undo last memory'.")
            return {"status": "success", "message": f"Last memory item for {npc_name} (simulated) undone."}

        elif action_type == "next_topic" or action_type == "regenerate_topics":
            # Placeholder: Call AI to generate new conversation topics.
            # This would involve a different kind of prompt.
            current_app.logger.info(f"NPC Action: '{npc_name}' - Generating new topics...")
            
            # Simplified prompt for topic generation
            topic_prompt_lines = [
                f"You are an AI assistant for a tabletop RPG. The NPC {npc_name} (profile below) is in the following scene.",
                f"NPC Profile Summary: Personality: {', '.join(npc_profile.get('personality_traits', ['Unknown']))}. Motivations: {npc_profile.get('motivations', 'Unknown')}.",
                f"Current Scene: {scene_description}",
                "Based on this, suggest 3-5 distinct and engaging conversation topics or questions that this NPC might bring up or be interested in discussing next. Each topic should be a short phrase or question.",
                "Output each topic on a new line."
            ]
            topic_prompt = "\n".join(topic_prompt_lines)
            
            try:
                if not self.model:
                    return {"status": "error", "message": "AI model not initialized for topic generation."}
                
                response = self.model.generate_content(topic_prompt) # Use default generation config
                
                if response.parts:
                    topics_text = "".join(part.text for part in response.parts if hasattr(part, 'text')).strip()
                    suggested_topics = [topic.strip() for topic in topics_text.split('\n') if topic.strip()]
                    current_app.logger.info(f"Generated topics for {npc_name}: {suggested_topics}")
                    return {"status": "success", "action": action_type, "data": {"new_topics": suggested_topics, "message": f"New topics generated for {npc_name}."}}
                else:
                    current_app.logger.warning(f"Topic generation for {npc_name} produced no usable parts.")
                    return {"status": "error", "message": "Could not generate topics."}
            except Exception as e:
                current_app.logger.error(f"Error generating topics for {npc_name}: {e}")
                return {"status": "error", "message": "Error during topic generation."}

        elif action_type == "show_top5_options":
            # Placeholder: Call AI to generate 5 potential next dialogue lines for THIS NPC.
            current_app.logger.info(f"NPC Action: '{npc_name}' - Generating top 5 dialogue options...")
            # This would be similar to generate_dialogue_for_npc_in_scene but ask for multiple options.
            # For now, returning placeholder options.
            options = [
                f"{npc_name} considers saying: 'Perhaps we should discuss the old ruins?'",
                f"{npc_name} might ask: 'What do you make of the recent omens?'",
                f"{npc_name} could state: 'I have a proposal for you.'",
                f"A more direct line from {npc_name}: 'Tell me your true intentions.'",
                f"{npc_name} offers: 'Maybe a drink would loosen our tongues?'"
            ]
            random.shuffle(options) # Make them seem a bit random
            return {"status": "success", "action": action_type, "data": {"dialogue_options": options[:3], "message": f"Top dialogue options for {npc_name}."}} # Return 3 for now

        # "show_tree" is more complex and would likely be handled mostly on the frontend with stored history,
        # or require a backend to structure and return the conversation graph.
        elif action_type == "show_tree":
            current_app.logger.info(f"NPC Action: '{npc_name}' - Show Conversation Tree (not implemented).")
            return {"status": "info", "message": "Conversation Tree feature is not yet implemented."}
            
        else:
            current_app.logger.warning(f"NPC Action: Unknown action type '{action_type}' for NPC ID '{npc_id}'.")
            return {"status": "error", "message": f"Unknown action: {action_type}"}

