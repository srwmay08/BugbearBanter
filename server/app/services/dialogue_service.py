# server/app/services/dialogue_service.py
import google.generativeai as genai # type: ignore
from flask import current_app 
from ..utils.db import mongo 
import random 

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
            current_app.logger.info("--- INFO DEBUG: DialogueService __init__ - Attempting to configure genai and initialize model... ---")
            if not hasattr(genai, '_is_configured_globally_by_bugbear_v4'): 
                current_app.logger.info("--- INFO DEBUG: Attempting to call genai.configure()... ---")
                genai.configure(api_key=self.gemini_api_key)
                genai._is_configured_globally_by_bugbear_v4 = True 
                current_app.logger.critical("--- CRITICAL DEBUG: DialogueService __init__ - genai.configure() CALLED SUCCESSFULLY. ---")
            else:
                current_app.logger.info("--- INFO DEBUG: genai already configured globally by Bugbear. ---")

            model_name = current_app.config.get('GEMINI_MODEL_NAME', 'gemini-1.5-flash-latest')
            current_app.logger.info(f"--- INFO DEBUG: Attempting to initialize GenerativeModel with name: {model_name} ---")
            self.model = genai.GenerativeModel(model_name)
            current_app.logger.critical(f"--- CRITICAL DEBUG: DialogueService __init__ - GenerativeModel '{model_name}' INITIALIZED SUCCESSFULLY. ---")

        except Exception as e:
            current_app.logger.critical(f"--- CRITICAL DEBUG: DialogueService __init__ - FAILED to initialize GenerativeModel or configure genai: {e} ---")
            current_app.logger.exception("Full exception during DialogueService init:") 
            self.model = None

    def _get_world_knowledge_summary(self):
        knowledge_parts = []
        try:
            recent_events = list(mongo.db.world_events.find().limit(3)) 
            if recent_events:
                knowledge_parts.append("Some Recent World Events of Note:")
                for event in recent_events:
                    knowledge_parts.append(f"- {event.get('name')}: {event.get('description', '')[:120]}... (Impact: {event.get('impact', '')[:80]}...) Status: {event.get('status', 'Unknown')}.")
            
            prominent_locations = list(mongo.db.world_locations.find().limit(2))
            if prominent_locations:
                knowledge_parts.append("\nKey Locations in the World:")
                for loc in prominent_locations:
                    knowledge_parts.append(f"- {loc.get('name')} ({loc.get('type')}): {loc.get('description', '')[:120]}... Current Mood: {loc.get('current_mood', 'Normal')}.")

            prominent_religions = list(mongo.db.world_religions.find().limit(2))
            if prominent_religions:
                knowledge_parts.append("\nProminent Deities or Beliefs:")
                for religion in prominent_religions:
                    # Adjust based on your actual world_religions.json structure
                    domains = religion.get('domains', [])
                    domains_str = ', '.join(domains) if isinstance(domains, list) else str(domains)
                    knowledge_parts.append(f"- {religion.get('name')}: Known for {domains_str}. Common saying: \"{religion.get('common_saying','')}\" General Influence: {religion.get('general_influence', '')[:100]}...")

        except Exception as e:
            current_app.logger.error(f"Error fetching world knowledge from DB: {e}")
            knowledge_parts.append("Error retrieving some world knowledge details.")
        
        return "\n".join(knowledge_parts) if knowledge_parts else "General world knowledge is currently undefined or sparse."


    def generate_dialogue_for_npc_in_scene(self, npc_profile, scene_description, conversation_history):
        current_app.logger.critical("--- CRITICAL DEBUG: DialogueService generate_dialogue_for_npc_in_scene CALLED ---")

        if not self.model:
            current_app.logger.critical("--- CRITICAL DEBUG: generate_dialogue_for_npc_in_scene - Gemini model is None. Cannot generate. ---")
            return "[Error: AI Model Not Initialized. Check server logs for API key/configuration issues.]"

        npc_name = npc_profile.get('name', 'The NPC')
        current_app.logger.info(f"--- INFO DEBUG: Generating dialogue for: {npc_name} ---")

        world_knowledge_summary = self._get_world_knowledge_summary()

        prompt_lines = []
        prompt_lines.append(f"You are an AI masterfully roleplaying as {npc_name}, a character in a rich fantasy world. Your goal is to deliver compelling, cinematic dialogue that reveals your character's depth, advances the narrative, and engages the Game Master (GM).")
        prompt_lines.append("The GM will describe a scene or pose a question. Your response MUST be a single, impactful, in-character line or two of spoken dialogue from {npc_name}'s perspective. Do NOT narrate actions, describe thoughts out of character, or break character. Focus purely on what {npc_name} says aloud.")
        
        prompt_lines.append(f"\n=== {npc_name}'s In-Depth Character Profile ===")
        prompt_lines.append(f"Name: {npc_name}")
        prompt_lines.append(f"Race: {npc_profile.get('race', 'Unknown')}")
        prompt_lines.append(f"Class/Role: {npc_profile.get('class', 'Unknown')}") 
        prompt_lines.append(f"Appearance: {npc_profile.get('appearance', 'Not clearly described.')}")
        
        # --- CORRECTED PERSONALITY TRAITS HANDLING ---
        traits = npc_profile.get('personality_traits')
        if traits and isinstance(traits, str): # Ensure it's a string
            prompt_lines.append(f"Core Personality Traits: {traits}. These traits MUST be evident in your speech and attitude. Consider the subtext they imply.")
        elif traits and isinstance(traits, list): # Fallback if it was accidentally an array
             prompt_lines.append(f"Core Personality Traits: {', '.join(traits)}. These traits MUST be evident in your speech and attitude. Consider the subtext they imply.")
        else:
            prompt_lines.append("Core Personality Traits: Not specified. (Adopt a generally observant and cautious demeanor, reacting based on the immediate context).")
        # --- END CORRECTION ---

        if npc_profile.get('backstory'):
            prompt_lines.append(f"Key Backstory Elements: {npc_profile['backstory'][:400]}...") 
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
             prompt_lines.append(f"Speech Patterns/Voice: {npc_profile.get('speech_patterns')}")

        prompt_lines.append("\n=== General World Knowledge & Recent Events (You are aware of this as background context) ===")
        prompt_lines.append(world_knowledge_summary if world_knowledge_summary else "The world is a vast place, full of everyday occurrences. Specific details are not immediately relevant unless the scene implies otherwise.")
        
        prompt_lines.append("\n=== Current Scene Context (Provided by GM) ===")
        prompt_lines.append(scene_description)

        if conversation_history:
            prompt_lines.append("\n=== Recent Turns in Conversation (Your lines are as {npc_name}) ===")
            for entry in conversation_history[-3:]: 
                prompt_lines.append(f"{entry.get('speaker', 'Unknown')}: \"{entry.get('text', '')}\"")
        
        prompt_lines.append(f"\n=== Your Task: {npc_name}'s Cinematic Dialogue Line ===")
        prompt_lines.append(f"Based on your detailed profile ({npc_name}), your awareness of the world knowledge, and the current scene, deliver your next spoken line(s). Aim for dialogue that is memorable, reveals character, and feels like it belongs in a compelling story or movie. Your response should integrate your knowledge subtly if relevant. Avoid generic acknowledgments. Instead, react specifically, ask a pertinent question, make a charged statement, or subtly hint at your thoughts/intentions through your words. How would YOU, {npc_name}, truly respond in this moment to \"{scene_description}\"?")
        prompt_lines.append("Provide ONLY the dialogue spoken by {npc_name}. If the dialogue is short, that's fine, but make it count. If a slightly longer, more impactful statement (1-3 sentences) is appropriate for your character and the situation, deliver that.")
        prompt_lines.append("DIALOGUE RESPONSE:")

        full_prompt = "\n".join(prompt_lines)
        current_app.logger.debug(f"--- FULL PROMPT FOR {npc_name} ---\n{full_prompt}\n--- END OF FULL PROMPT ---")

        try:
            safety_settings = self.get_default_safety_settings()
            generation_config = genai.types.GenerationConfig(temperature=0.8, top_p=0.95, max_output_tokens=200)
            response = self.model.generate_content(full_prompt, generation_config=generation_config, safety_settings=safety_settings)
            
            if response.parts:
                generated_text = "".join(part.text for part in response.parts if hasattr(part, 'text')).strip()
                if generated_text.lower().startswith(f"{npc_name.lower()}:"):
                    generated_text = generated_text[len(npc_name)+1:].strip()
                common_ai_prefixes = ["dialogue:", "response:", f"{npc_name} says:", "spokendialogue:"]
                for prefix in common_ai_prefixes:
                    if generated_text.lower().startswith(prefix.lower()): 
                        generated_text = generated_text[len(prefix):].strip()
                if len(generated_text) > 1 and ((generated_text.startswith('"') and generated_text.endswith('"')) or (generated_text.startswith("'") and generated_text.endswith("'"))):
                    generated_text = generated_text[1:-1]
                current_app.logger.info(f"Successfully generated dialogue for {npc_name}: \"{generated_text}\"")
                return generated_text if generated_text else f"[{npc_name} pauses, considering the weight of the moment.]" 
            else: 
                block_reason_msg = "Response contained no usable parts."
                if hasattr(response, 'prompt_feedback') and response.prompt_feedback and response.prompt_feedback.block_reason:
                    block_reason_msg = response.prompt_feedback.block_reason_message
                    current_app.logger.error(f"Prompt for {npc_name} was BLOCKED by API. Reason: {block_reason_msg}. Full prompt feedback: {response.prompt_feedback}")
                else:
                    current_app.logger.warning(f"Gemini response for {npc_name} had no usable parts. Full Response object: {response}")
                return f"[{npc_name} seems unable to respond clearly. AI Reason: {block_reason_msg}]"
        except Exception as e:
            current_app.logger.critical(f"--- CRITICAL DEBUG: Exception during Gemini API call for {npc_name}: {e} ---")
            current_app.logger.exception("Full exception details during AI call:")
            return f"[Error: AI service encountered an issue for {npc_name}. Check server logs for full exception.]"

    def handle_npc_action(self, npc_id, action_type, payload, npc_profile, scene_description, conversation_history):
        current_app.logger.info(f"--- INFO DEBUG: Handling action '{action_type}' for NPC ID '{npc_id}' ---")
        npc_name = npc_profile.get('name', 'The NPC')

        if action_type == "submit_memory":
            dialogue_to_remember = payload.get("dialogue_exchange", "an important event")
            current_app.logger.info(f"NPC Action: '{npc_name}' is 'remembering': {dialogue_to_remember[:100]}...")
            # mongo.db.npcs.update_one({"_id": npc_id}, {"$push": {"memories": {"text": dialogue_to_remember, "timestamp": datetime.utcnow()}}})
            return {"status": "success", "message": f"'{dialogue_to_remember[:30]}...' noted for {npc_name} (simulated)."}

        elif action_type == "undo_memory":
            current_app.logger.info(f"NPC Action: '{npc_name}' is attempting to 'undo last memory'.")
            # mongo.db.npcs.update_one({"_id": npc_id}, {"$pop": {"memories": 1}})
            return {"status": "success", "message": f"Last memory item for {npc_name} (simulated) undone."}

        elif action_type == "next_topic" or action_type == "regenerate_topics":
            current_app.logger.info(f"NPC Action: '{npc_name}' - Generating new topics...")
            world_knowledge_summary = self._get_world_knowledge_summary()
            
            traits_for_prompt = npc_profile.get('personality_traits', 'Unknown')
            if isinstance(traits_for_prompt, list): # Should be string now
                traits_for_prompt = ', '.join(traits_for_prompt)

            topic_prompt_lines = [
                f"You are an AI assistant for a tabletop RPG. The NPC {npc_name} (profile below) is in the following scene, with some general world context.",
                f"NPC Profile Summary: Personality: {traits_for_prompt}. Motivations: {npc_profile.get('motivations', 'Unknown')}.", # Use corrected traits
                f"World Context: {world_knowledge_summary[:300]}...",
                f"Current Scene: {scene_description}",
                f"Recent Conversation with {npc_name}:"
            ]
            for entry in conversation_history[-2:]:
                topic_prompt_lines.append(f"  {entry.get('speaker', 'Unknown')}: \"{entry.get('text', '')}\"")
            
            topic_prompt_lines.append(f"\nBased on this, suggest 3-5 distinct and engaging conversation topics, questions, or observations that this specific NPC, {npc_name}, might bring up or be interested in discussing next. Each topic should be a short phrase or question suitable for a player to click on to steer the conversation. Consider {npc_name}'s personality and the current situation.")
            topic_prompt_lines.append("Output each topic on a new line, starting with '- '.")
            topic_prompt = "\n".join(topic_prompt_lines)
            
            current_app.logger.debug(f"--- TOPIC PROMPT for {npc_name} ---\n{topic_prompt}\n--- END TOPIC PROMPT ---")

            try:
                if not self.model: return {"status": "error", "message": "AI model not initialized."}
                topic_gen_config = genai.types.GenerationConfig(temperature=0.75, max_output_tokens=150) # Slightly increased temp
                safety_settings_topics = self.get_default_safety_settings()

                response = self.model.generate_content(topic_prompt, generation_config=topic_gen_config, safety_settings=safety_settings_topics)
                
                if response.parts:
                    topics_text = "".join(part.text for part in response.parts if hasattr(part, 'text')).strip()
                    suggested_topics = [topic.strip().lstrip('- ').strip('"') for topic in topics_text.split('\n') if topic.strip()] # Also strip quotes
                    current_app.logger.info(f"Generated topics for {npc_name}: {suggested_topics}")
                    return {"status": "success", "action": action_type, "data": {"new_topics": suggested_topics, "message": f"New topics generated for {npc_name}."}}
                else:
                    block_reason_msg = "Topic gen response had no parts."
                    if hasattr(response, 'prompt_feedback') and response.prompt_feedback and response.prompt_feedback.block_reason:
                         block_reason_msg = response.prompt_feedback.block_reason_message
                    current_app.logger.warning(f"Topic generation for {npc_name} failed: {block_reason_msg}")
                    return {"status": "error", "message": f"Could not generate topics: {block_reason_msg}"}
            except Exception as e:
                current_app.logger.error(f"Error generating topics for {npc_name}: {e}", exc_info=True)
                return {"status": "error", "message": "Error during topic generation."}

        elif action_type == "show_top5_options":
            current_app.logger.info(f"NPC Action: '{npc_name}' - Generating top 5 dialogue options...")
            
            traits_for_prompt = npc_profile.get('personality_traits', 'Unknown')
            if isinstance(traits_for_prompt, list): # Should be string now
                traits_for_prompt = ', '.join(traits_for_prompt)

            options_prompt_lines = [
                f"You are roleplaying as {npc_name}. Profile and scene context are below.",
                f"NPC Profile Summary: Personality: {traits_for_prompt}. Motivations: {npc_profile.get('motivations', 'Unknown')}.", # Use corrected traits
                f"Current Scene: {scene_description}",
                f"Recent Conversation with {npc_name}:"
            ]
            for entry in conversation_history[-2:]:
                options_prompt_lines.append(f"  {entry.get('speaker', 'Unknown')}: \"{entry.get('text', '')}\"")
            options_prompt_lines.append(f"\nConsidering this, generate 3 to 5 distinct, in-character dialogue lines that {npc_name} could say next. Each line should offer a different approach or reaction to the current situation. Number each option.")
            options_prompt_lines.append("Output ONLY the numbered dialogue lines.")
            options_prompt = "\n".join(options_prompt_lines)

            current_app.logger.debug(f"--- OPTIONS PROMPT for {npc_name} ---\n{options_prompt}\n--- END OPTIONS PROMPT ---")
            
            try:
                if not self.model: return {"status": "error", "message": "AI model not initialized."}
                options_gen_config = genai.types.GenerationConfig(temperature=0.85, max_output_tokens=300) 
                response = self.model.generate_content(options_prompt, generation_config=options_gen_config, safety_settings=self.get_default_safety_settings())

                if response.parts:
                    options_text = "".join(part.text for part in response.parts if hasattr(part, 'text')).strip()
                    dialogue_options = [opt.strip().lstrip('0123456789. ').strip('"') for opt in options_text.split('\n') if opt.strip()] # Also strip quotes
                    current_app.logger.info(f"Generated dialogue options for {npc_name}: {dialogue_options}")
                    return {"status": "success", "action": action_type, "data": {"dialogue_options": dialogue_options[:5], "message": f"Top dialogue options for {npc_name}."}}
                else: 
                    block_reason_msg = "Options gen response had no parts."
                    if hasattr(response, 'prompt_feedback') and response.prompt_feedback and response.prompt_feedback.block_reason:
                         block_reason_msg = response.prompt_feedback.block_reason_message
                    current_app.logger.warning(f"Options generation for {npc_name} failed: {block_reason_msg}")
                    return {"status": "error", "message": f"Could not generate options: {block_reason_msg}"}
            except Exception as e:
                current_app.logger.error(f"Error generating dialogue options for {npc_name}: {e}", exc_info=True)
                return {"status": "error", "message": "Error generating dialogue options."}

        elif action_type == "show_tree":
            current_app.logger.info(f"NPC Action: '{npc_name}' - Show Conversation Tree (not implemented).")
            return {"status": "info", "message": "Conversation Tree feature is not yet implemented."}
            
        else:
            current_app.logger.warning(f"NPC Action: Unknown action type '{action_type}' for NPC ID '{npc_id}'.")
            return {"status": "error", "message": f"Unknown action: {action_type}"}

    def get_default_safety_settings(self):
        return [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
        ]
