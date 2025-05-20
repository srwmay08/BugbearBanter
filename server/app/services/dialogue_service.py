# server/app/services/dialogue_service.py
import google.generativeai as genai # type: ignore
from flask import current_app, jsonify 
from ..utils.db import mongo 
import random 
import uuid # For memory_id
from datetime import datetime # For memory timestamp
import json # For parsing potential JSON output from AI

class DialogueService:
    def __init__(self):
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

            if not hasattr(genai, '_is_configured_globally_by_bugbear_v4'): 
                print("--- PRINT DEBUG: DialogueService __init__ - Calling genai.configure()... ---")
                current_app.logger.info("--- INFO DEBUG: Attempting to call genai.configure()... ---")
                genai.configure(api_key=self.gemini_api_key)
                genai._is_configured_globally_by_bugbear_v4 = True 
                print("--- PRINT DEBUG: DialogueService __init__ - genai.configure() CALLED SUCCESSFULLY. ---")
                current_app.logger.critical("--- CRITICAL DEBUG: DialogueService __init__ - genai.configure() CALLED SUCCESSFULLY. ---")
            else:
                print("--- PRINT DEBUG: DialogueService __init__ - genai already configured globally by Bugbear. ---")
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

    def _get_world_knowledge_summary(self):
        knowledge_parts = []
        try:
            recent_events = list(mongo.db.world_events.find().sort("status", -1).limit(3)) 
            if recent_events:
                knowledge_parts.append("Some Recent World Events of Note:")
                for event in recent_events:
                    knowledge_parts.append(f"- {event.get('name')}: {event.get('description', '')[:100]}... (Impact: {event.get('impact', '')[:70]}...) Status: {event.get('status', 'Unknown')}.")
            
            prominent_locations = list(mongo.db.world_locations.find().limit(2)) 
            if prominent_locations:
                knowledge_parts.append("\nKey Locations in the World:")
                for loc in prominent_locations:
                    knowledge_parts.append(f"- {loc.get('name')} ({loc.get('type')}): {loc.get('description', '')[:100]}... Current Mood: {loc.get('current_mood', 'Normal')}.")

            prominent_religions = list(mongo.db.world_religions.find().limit(2))
            if prominent_religions:
                knowledge_parts.append("\nProminent Deities or Beliefs:")
                for religion in prominent_religions:
                    domains = religion.get('domains', [])
                    domains_str = ', '.join(domains) if isinstance(domains, list) else str(domains)
                    knowledge_parts.append(f"- {religion.get('name')}: Known for {domains_str}. Common saying: \"{religion.get('common_saying','')}\"")


        except Exception as e:
            current_app.logger.error(f"Error fetching world knowledge from DB: {e}")
            knowledge_parts.append("Error retrieving some world knowledge details.")
        
        return "\n".join(knowledge_parts) if knowledge_parts else "General world knowledge is currently undefined or sparse."

    def _get_npc_memories_summary(self, npc_profile, current_scene_context):
        if not npc_profile or 'memories' not in npc_profile or not npc_profile['memories']:
            return "This NPC has no specific memories recorded yet or they could not be accessed."

        memories = npc_profile.get('memories', [])
        if not memories:
            return "This NPC has no specific memories recorded yet."

        recent_memories = sorted(memories, key=lambda m: m.get('timestamp', datetime.min), reverse=True)[:3]
        
        if not recent_memories:
            return "No recent memories found for this NPC."

        summary_lines = [f"\n=== {npc_profile.get('name', 'The NPC')}'s Relevant Recent Memories ==="]
        for mem in recent_memories:
            summary = mem.get('ai_generated_summary', 'A past event.')
            sentiment = mem.get('npc_sentiment_tag', 'Neutral')
            timestamp_obj = mem.get('timestamp')
            timestamp_str = timestamp_obj.strftime('%Y-%m-%d %H:%M') if isinstance(timestamp_obj, datetime) else "some time ago"
            summary_lines.append(f"- ({timestamp_str}) You recall: \"{summary}\" (Felt: {sentiment}).")
        
        return "\n".join(summary_lines)

    # Changed back to synchronous
    def generate_dialogue_for_npc_in_scene(self, npc_profile, scene_description, conversation_history):
        print("--- PRINT DEBUG: DialogueService generate_dialogue_for_npc_in_scene (SYNC) CALLED ---")
        current_app.logger.critical("--- CRITICAL DEBUG: DialogueService generate_dialogue_for_npc_in_scene (SYNC) CALLED ---")

        if not self.model:
            current_app.logger.critical("--- CRITICAL DEBUG: generate_dialogue_for_npc_in_scene - Gemini model is None. ---")
            return "[Error: AI Model Not Initialized. Check server logs for API key/configuration issues.]"

        npc_name = npc_profile.get('name', 'The NPC')
        current_app.logger.info(f"--- INFO DEBUG: Generating dialogue for: {npc_name} ---")

        world_knowledge_summary = self._get_world_knowledge_summary()
        npc_memory_summary = self._get_npc_memories_summary(npc_profile, scene_description)

        prompt_lines = []
        prompt_lines.append(f"You are an AI masterfully roleplaying as {npc_name}, a character in a rich fantasy world. Your goal is to deliver compelling, cinematic dialogue that reveals your character's depth, advances the narrative, and engages the Game Master (GM).")
        prompt_lines.append(f"The GM will describe a scene or pose a question. Your response MUST be a single, impactful, in-character line or two of spoken dialogue from {npc_name}'s perspective. Do NOT narrate actions, describe thoughts out of character, or break character. Focus purely on what {npc_name} says aloud.")
        
        prompt_lines.append(f"\n=== {npc_name}'s In-Depth Character Profile ===")
        prompt_lines.append(f"Name: {npc_name}")
        prompt_lines.append(f"Race: {npc_profile.get('race', 'Unknown')}")
        prompt_lines.append(f"Class/Role: {npc_profile.get('class', 'Unknown')}") 
        prompt_lines.append(f"Appearance: {npc_profile.get('appearance', 'Not clearly described.')}")
        
        # Ensure personality_traits is treated as a list of strings
        personality_traits_input = npc_profile.get('personality_traits', [])
        if isinstance(personality_traits_input, str):
            personality_traits_list = [trait.strip() for trait in personality_traits_input.split(',') if trait.strip()]
            current_app.logger.info(f"--- DEBUG TRAITS (generate_dialogue): Raw 'personality_traits' for {npc_name}: '{personality_traits_input}' (Type: {type(personality_traits_input)}) ---")
            current_app.logger.info(f"--- DEBUG TRAITS (generate_dialogue): Converted to LIST for {npc_name}: {personality_traits_list} ---")
        elif isinstance(personality_traits_input, list):
            personality_traits_list = personality_traits_input
        else:
            personality_traits_list = []
            current_app.logger.warning(f"--- WARNING TRAITS (generate_dialogue): 'personality_traits' for {npc_name} is neither string nor list: {personality_traits_input} (Type: {type(personality_traits_input)}) ---")


        if personality_traits_list:
            prompt_lines.append(f"Core Personality Traits: {', '.join(personality_traits_list)}. These traits MUST be evident in your speech and attitude. Consider the subtext they imply.")
        else:
             # Fallback if it's still a string after attempts (should not happen with above logic but as safety)
            if isinstance(personality_traits_input, str) and personality_traits_input:
                 prompt_lines.append(f"Core Personality Traits: {personality_traits_input}. These traits MUST be evident in your speech and attitude. Consider the subtext they imply.")
                 current_app.logger.info(f"--- DEBUG TRAITS (generate_dialogue): Using traits as STRING for {npc_name}: '{personality_traits_input}' ---")
            else:
                prompt_lines.append("Core Personality Traits: Not specified. (Adopt a generally observant and cautious demeanor, reacting based on the immediate context).")


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
        
        prompt_lines.append(npc_memory_summary)

        prompt_lines.append("\n=== Current Scene Context (Provided by GM) ===")
        prompt_lines.append(scene_description)

        if conversation_history:
            prompt_lines.append("\n=== Recent Turns in Conversation (Your lines are as {npc_name}) ===")
            for entry in conversation_history[-5:]: 
                prompt_lines.append(f"{entry.get('speaker', 'Unknown')}: \"{entry.get('text', '')}\"")
        
        prompt_lines.append(f"\n=== Your Task: {npc_name}'s Cinematic Dialogue Line ===")
        prompt_lines.append(f"Based on your detailed profile ({npc_name}), your awareness of the world knowledge, YOUR RECENT MEMORIES, and the current scene, deliver your next spoken line(s). Aim for dialogue that is memorable, reveals character, and feels like it belongs in a compelling story or movie. Your response should integrate your knowledge subtly if relevant. Avoid generic acknowledgments. Instead, react specifically, ask a pertinent question, make a charged statement, or subtly hint at your thoughts/intentions through your words. How would YOU, {npc_name}, truly respond in this moment to \"{scene_description}\"?")
        prompt_lines.append("Provide ONLY the dialogue spoken by {npc_name}. If the dialogue is short, that's fine, but make it count. If a slightly longer, more impactful statement (1-3 sentences) is appropriate for your character and the situation, deliver that.")
        prompt_lines.append("DIALOGUE RESPONSE:")

        full_prompt = "\n".join(prompt_lines)
        current_app.logger.debug(f"--- FULL PROMPT FOR {npc_name} ---\n{full_prompt}\n--- END OF FULL PROMPT ---")

        try:
            safety_settings = self.get_default_safety_settings()
            generation_config = genai.types.GenerationConfig(temperature=0.8, top_p=0.95, max_output_tokens=200)
            # Using synchronous call
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
                current_app.logger.error(f"Prompt for {npc_name} was BLOCKED by API or empty. Reason: {block_reason_msg}. Full feedback: {response.prompt_feedback if hasattr(response, 'prompt_feedback') else 'N/A'}")
                return f"[{npc_name} seems unable to respond clearly. AI Reason: {block_reason_msg}]"

        except Exception as e:
            current_app.logger.critical(f"Exception during Gemini API call for {npc_name}: {e}", exc_info=True)
            return f"[Error: AI service encountered an issue for {npc_name}. Check server logs for full exception.]"

    async def _extract_memory_details_with_ai(self, npc_profile, dialogue_exchange, scene_context_for_memory):
        if not self.model:
            current_app.logger.error("Memory extraction: AI model not initialized.")
            return None

        npc_name = npc_profile.get('name', 'The NPC')
        
        personality_traits_input = npc_profile.get('personality_traits', [])
        if isinstance(personality_traits_input, str):
            personality_summary = personality_traits_input # Use as is if already a descriptive string
        elif isinstance(personality_traits_input, list):
            personality_summary = ", ".join(personality_traits_input)
        else:
            personality_summary = "observant" # Default
        
        extraction_prompt_lines = [
            f"You are an AI specializing in analyzing dialogue for memory creation in a role-playing game.",
            f"The NPC in question is '{npc_name}', who is generally {personality_summary}.",
            f"Current Scene Context: \"{scene_context_for_memory}\"",
            f"Recent Dialogue Exchange to analyze:\n---\n{dialogue_exchange}\n---",
            f"Your task is to analyze this exchange from {npc_name}'s perspective and extract the following information. Respond ONLY with a valid JSON object containing these fields:",
            f"1. 'key_entities': A list of important named entities (people, places, significant items, organizations) mentioned or critically relevant to {npc_name} in this exchange.",
            f"2. 'key_facts_events': A concise string summarizing the most crucial information {npc_name} learned, decisions made, or significant actions that occurred relevant to {npc_name}.",
            f"3. 'npc_sentiment_tag': From {npc_name}'s perspective and personality, what is the general sentiment {npc_name} would feel about this exchange? Choose ONE: POSITIVE, NEGATIVE, NEUTRAL.",
            f"4. 'ai_generated_summary': A very brief (10-20 words) summary of what {npc_name} would primarily remember from this specific exchange. This should be phrased as if {npc_name} is recalling it (e.g., 'I learned that X...', 'I felt Y about Z...', 'Someone told me A...').",
            f"Focus on what is new, important, or emotionally impactful for {npc_name} based on the context and dialogue.",
            f"Example JSON Output:",
            f"{{",
            f"  \"key_entities\": [\"Sir Reginald\", \"The Sunken Temple\", \"The Azure Gem\"],",
            f"  \"key_facts_events\": \"Sir Reginald revealed the Azure Gem is hidden in the Sunken Temple and asked for my help to retrieve it.\",",
            f"  \"npc_sentiment_tag\": \"POSITIVE\",",
            f"  \"ai_generated_summary\": \"Sir Reginald needs my help to find the Azure Gem in the Sunken Temple.\"",
            f"}}"
        ]
        extraction_prompt = "\n".join(extraction_prompt_lines)
        current_app.logger.debug(f"Memory Extraction Prompt for {npc_name}:\n{extraction_prompt}")

        try:
            extraction_config = genai.types.GenerationConfig(temperature=0.4, max_output_tokens=350) # Increased tokens slightly
            safety_settings = self.get_default_safety_settings()
            
            response = await self.model.generate_content_async(
                extraction_prompt,
                generation_config=extraction_config,
                safety_settings=safety_settings
            )

            if response.parts:
                raw_json_text = "".join(part.text for part in response.parts if hasattr(part, 'text')).strip()
                if raw_json_text.startswith("```json"):
                    raw_json_text = raw_json_text[7:]
                if raw_json_text.endswith("```"):
                    raw_json_text = raw_json_text[:-3]
                raw_json_text = raw_json_text.strip() # Ensure no leading/trailing whitespace
                
                current_app.logger.debug(f"Raw JSON from AI for memory extraction: {raw_json_text}")
                extracted_data = json.loads(raw_json_text)
                return extracted_data
            else:
                current_app.logger.error(f"Memory extraction for {npc_name} failed: No parts in AI response. Feedback: {response.prompt_feedback if hasattr(response, 'prompt_feedback') else 'N/A'}")
                return None
        except json.JSONDecodeError as je:
            current_app.logger.error(f"Memory extraction JSON parsing error for {npc_name}: {je}. Raw text was: '{raw_json_text}'")
            return None 
        except Exception as e:
            current_app.logger.error(f"Error during AI memory extraction for {npc_name}: {e}", exc_info=True)
            return None


    async def handle_npc_action(self, npc_id, action_type, payload, npc_profile, scene_description, conversation_history):
        current_app.logger.info(f"--- INFO DEBUG: Handling action '{action_type}' for NPC ID '{npc_id}' ---")
        npc_name = npc_profile.get('name', 'The NPC')

        if action_type == "submit_memory":
            dialogue_to_remember = payload.get("dialogue_exchange", "")
            scene_context_for_memory = payload.get("scene_context_for_memory", scene_description) 

            if not dialogue_to_remember:
                return {"status": "error", "message": "No dialogue provided to remember."}

            current_app.logger.info(f"NPC Action: '{npc_name}' attempting to remember: \"{dialogue_to_remember[:100]}...\" with scene context: \"{scene_context_for_memory[:100]}...\"")
            
            full_npc_data_for_memory = mongo.db.npcs.find_one({"_id": npc_id})
            if not full_npc_data_for_memory:
                 return {"status": "error", "message": f"NPC {npc_id} not found for memory submission."}

            extracted_details = await self._extract_memory_details_with_ai(full_npc_data_for_memory, dialogue_to_remember, scene_context_for_memory)

            if extracted_details:
                memory_entry = {
                    "memory_id": str(uuid.uuid4()),
                    "timestamp": datetime.utcnow(),
                    "scene_context_summary": scene_context_for_memory[:250],
                    "dialogue_snippet": dialogue_to_remember,
                    "extracted_entities": extracted_details.get("key_entities", []),
                    "extracted_facts_events": extracted_details.get("key_facts_events", "Details not extracted."),
                    "npc_sentiment_tag": extracted_details.get("npc_sentiment_tag", "NEUTRAL").upper(),
                    "ai_generated_summary": extracted_details.get("ai_generated_summary", "A notable event occurred.")
                }
                try:
                    mongo.db.npcs.update_one(
                        {"_id": npc_id}, 
                        {"$push": {"memories": {"$each": [memory_entry], "$slice": -20}}} 
                    )
                    current_app.logger.info(f"Memory entry successfully added for {npc_name}.")
                    return {"status": "success", "message": f"Memory of '{memory_entry['ai_generated_summary'][:50]}...' recorded for {npc_name}."}
                except Exception as e:
                    current_app.logger.error(f"DB error saving memory for {npc_name}: {e}", exc_info=True)
                    return {"status": "error", "message": "Failed to save memory to database."}
            else:
                current_app.logger.warning(f"Could not extract details to form a memory for {npc_name}.")
                return {"status": "error", "message": f"AI could not extract details to form a memory for {npc_name}."}

        elif action_type == "undo_memory":
            current_app.logger.info(f"NPC Action: '{npc_name}' is attempting to 'undo last memory'.")
            try:
                result = mongo.db.npcs.update_one({"_id": npc_id}, {"$pop": {"memories": 1}})
                if result.modified_count > 0:
                    return {"status": "success", "message": f"Last memory item for {npc_name} removed."}
                else:
                    npc_check = mongo.db.npcs.find_one({"_id": npc_id}, {"memories": 1})
                    if npc_check and (not npc_check.get("memories") or len(npc_check.get("memories")) == 0) :
                         return {"status": "info", "message": f"{npc_name} has no memories to remove."}
                    return {"status": "info", "message": f"No memory removed for {npc_name} (perhaps none existed or ID mismatch)."}
            except Exception as e:
                current_app.logger.error(f"DB error undoing memory for {npc_name}: {e}", exc_info=True)
                return {"status": "error", "message": "Failed to undo memory from database."}

        elif action_type == "next_topic" or action_type == "regenerate_topics":
            current_app.logger.info(f"NPC Action: '{npc_name}' - Generating for action '{action_type}'...")
            full_npc_data_for_action = mongo.db.npcs.find_one({"_id": npc_id})
            if not full_npc_data_for_action:
                 return {"status": "error", "message": f"NPC {npc_id} not found for {action_type}."}

            world_knowledge_summary = self._get_world_knowledge_summary()
            npc_memory_summary = self._get_npc_memories_summary(full_npc_data_for_action, scene_description)
            
            personality_traits_input = full_npc_data_for_action.get('personality_traits', [])
            if isinstance(personality_traits_input, str):
                personality_traits_list = [trait.strip() for trait in personality_traits_input.split(',') if trait.strip()]
                current_app.logger.info(f"--- DEBUG TRAITS ({action_type}): Raw 'personality_traits' for {npc_name}: '{personality_traits_input}' (Type: {type(personality_traits_input)}) ---")
                current_app.logger.info(f"--- DEBUG TRAITS ({action_type}): Converted to LIST for {npc_name}: {personality_traits_list} ---")
            elif isinstance(personality_traits_input, list):
                personality_traits_list = personality_traits_input
            else:
                personality_traits_list = []
                current_app.logger.warning(f"--- WARNING TRAITS ({action_type}): 'personality_traits' for {npc_name} is neither string nor list: {personality_traits_input} (Type: {type(personality_traits_input)}) ---")
            
            personality_summary = ', '.join(personality_traits_list) if personality_traits_list else 'Unknown'


            topic_prompt_lines = [
                f"You are an AI assistant for a tabletop RPG. The NPC {npc_name} (profile and memories below) is in the following scene, with some general world context.",
                f"NPC Profile Summary: Personality: {personality_summary}. Motivations: {full_npc_data_for_action.get('motivations', 'Unknown')}.",
                npc_memory_summary, 
                f"World Context: {world_knowledge_summary[:300]}...",
                f"Current Scene: {scene_description}",
                f"Recent Conversation with {npc_name} (last ~3 exchanges):"
            ]
            for entry in conversation_history[-3:]: 
                topic_prompt_lines.append(f"  {entry.get('speaker', 'Unknown')}: \"{entry.get('text', '')}\"")
            
            topic_prompt_lines.append(f"\nBased on all this (especially {npc_name}'s recent memories and personality), suggest 3-5 distinct and engaging conversation topics, questions, or observations that {npc_name} might bring up or be interested in discussing next. Each topic should be a short phrase or question suitable for a player to click on to steer the conversation.")
            topic_prompt_lines.append("Output each topic on a new line, starting with '- '.")
            topic_prompt = "\n".join(topic_prompt_lines)
            
            current_app.logger.debug(f"--- ACTION PROMPT ({action_type}) for {npc_name} ---\n{topic_prompt}\n--- END ACTION PROMPT ---")

            try:
                if not self.model: return {"status": "error", "message": "AI model not initialized."}
                action_gen_config = genai.types.GenerationConfig(temperature=0.75, max_output_tokens=150)
                safety_settings_action = self.get_default_safety_settings()

                response = await self.model.generate_content_async(topic_prompt, generation_config=action_gen_config, safety_settings=safety_settings_action)
                
                if response.parts:
                    text_from_ai = "".join(part.text for part in response.parts if hasattr(part, 'text')).strip()
                    suggestions = [sug.strip().lstrip('- ') for sug in text_from_ai.split('\n') if sug.strip() and len(sug.strip()) > 2]
                    current_app.logger.info(f"Generated suggestions for {action_type} for {npc_name}: {suggestions}")
                    return {"status": "success", "action": action_type, "data": {"new_topics": suggestions, "message": f"Suggestions for {action_type} generated for {npc_name}."}}
                else:
                    block_reason_msg = f"{action_type} gen response had no parts."
                    if hasattr(response, 'prompt_feedback') and response.prompt_feedback and response.prompt_feedback.block_reason:
                         block_reason_msg = response.prompt_feedback.block_reason_message
                    current_app.logger.warning(f"{action_type} generation for {npc_name} failed: {block_reason_msg}")
                    return {"status": "error", "message": f"Could not generate suggestions for {action_type}: {block_reason_msg}"}
            except Exception as e:
                current_app.logger.error(f"Error generating suggestions for {action_type} for {npc_name}: {e}", exc_info=True)
                return {"status": "error", "message": f"Error during {action_type} generation."}

        elif action_type == "show_top5_options":
            current_app.logger.info(f"NPC Action: '{npc_name}' - Generating for action '{action_type}'...")
            full_npc_data_for_action = mongo.db.npcs.find_one({"_id": npc_id})
            if not full_npc_data_for_action:
                 return {"status": "error", "message": f"NPC {npc_id} not found for {action_type}."}
            
            npc_memory_summary = self._get_npc_memories_summary(full_npc_data_for_action, scene_description)
            
            personality_traits_input = full_npc_data_for_action.get('personality_traits', [])
            if isinstance(personality_traits_input, str):
                personality_traits_list = [trait.strip() for trait in personality_traits_input.split(',') if trait.strip()]
                current_app.logger.info(f"--- DEBUG TRAITS ({action_type}): Raw 'personality_traits' for {npc_name}: '{personality_traits_input}' (Type: {type(personality_traits_input)}) ---")
            elif isinstance(personality_traits_input, list):
                personality_traits_list = personality_traits_input
            else:
                personality_traits_list = [] # Default to empty list

            personality_summary = ', '.join(personality_traits_list) if personality_traits_list else 'Unknown'


            options_prompt_lines = [
                f"You are an AI assistant for a tabletop RPG. The NPC {npc_name} (profile, memories, and scene context are below) needs some dialogue options.",
                f"NPC Profile Summary: Personality: {personality_summary}. Motivations: {full_npc_data_for_action.get('motivations', 'Unknown')}.",
                npc_memory_summary,
                f"Current Scene: {scene_description}",
                f"Recent Conversation with {npc_name} (last ~3 exchanges):"
            ]
            for entry in conversation_history[-3:]:
                options_prompt_lines.append(f"  {entry.get('speaker', 'Unknown')}: \"{entry.get('text', '')}\"")
            options_prompt_lines.append(f"\nConsidering all this, especially {npc_name}'s memories and personality, generate 3 to 5 distinct, in-character dialogue lines that {npc_name} could say next. Each line should offer a different approach or reaction to the current situation. Number each option (e.g., 1. Dialogue line one. 2. Dialogue line two.).")
            options_prompt_lines.append("Output ONLY the numbered dialogue lines.")
            options_prompt = "\n".join(options_prompt_lines)

            current_app.logger.debug(f"--- ACTION PROMPT ({action_type}) for {npc_name} ---\n{options_prompt}\n--- END ACTION PROMPT ---")
            
            try:
                if not self.model: return {"status": "error", "message": "AI model not initialized."}
                action_gen_config = genai.types.GenerationConfig(temperature=0.85, max_output_tokens=300) 
                response = await self.model.generate_content_async(options_prompt, generation_config=action_gen_config, safety_settings=self.get_default_safety_settings()) 

                if response.parts:
                    text_from_ai = "".join(part.text for part in response.parts if hasattr(part, 'text')).strip()
                    suggestions = [opt.strip().lstrip('0123456789. ') for opt in text_from_ai.split('\n') if opt.strip() and len(opt.strip()) > 2]
                    current_app.logger.info(f"Generated dialogue options for {npc_name}: {suggestions}")
                    return {"status": "success", "action": action_type, "data": {"dialogue_options": suggestions[:5], "message": f"Top dialogue options for {npc_name}."}}
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