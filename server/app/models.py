# app/models.py
import datetime
import uuid # Required for memory_id

class User:
    def __init__(self, email, password_hash=None, google_id=None, patreon_status=None, created_at=None, _id=None, name=None, picture=None, npc_ids=None): # Added new fields
        self._id = _id
        self.email = email
        self.password_hash = password_hash
        self.google_id = google_id
        self.patreon_status = patreon_status
        self.name = name # For Google Sign-In
        self.picture = picture # For Google Sign-In
        self.created_at = created_at or datetime.datetime.utcnow()
        self.npc_ids = npc_ids or [] # List of NPC _ids owned by the user

    def to_dict(self, include_sensitive=False):
        data = {
            "_id": str(self._id) if self._id else None,
            "email": self.email,
            "google_id": self.google_id,
            "patreon_status": self.patreon_status,
            "name": self.name,
            "picture": self.picture,
            "created_at": self.created_at.isoformat(),
            "npc_ids": [str(npc_id) for npc_id in self.npc_ids]
        }
        if include_sensitive: # Be careful with this
            data['password_hash'] = self.password_hash
        return data

    # Flask-Login required properties
    @property
    def is_active(self):
        return True

    @property
    def is_authenticated(self):
        return True # Assume true if User object exists; refine with actual session status

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self._id) # Required by Flask-Login

# ... (NPC, GameWorld, Scene models - consider adding user_id to NPC)
class NPC:
    def __init__(self, name, appearance=None, personality_traits=None, backstory=None, motivations=None, flaws=None, race=None, npc_class=None, source_file=None, is_soul_npc=False, main_npc_id_if_soul=None, user_id=None, _id=None, speech_patterns=None, mannerisms=None, past_situation=None, current_situation=None, relationships_with_pcs=None, memories=None): # Added user_id and other fields from JSON, Added memories
        self._id = _id
        self.user_id = user_id # Link NPC to a user
        self.name = name
        self.appearance = appearance
        self.personality_traits = personality_traits
        self.backstory = backstory
        self.motivations = motivations
        self.flaws = flaws
        self.race = race
        self.npc_class = npc_class # 'class' is reserved
        self.source_file = source_file
        self.is_soul_npc = is_soul_npc
        self.main_npc_id_if_soul = main_npc_id_if_soul
        self.speech_patterns = speech_patterns
        self.mannerisms = mannerisms
        self.past_situation = past_situation
        self.current_situation = current_situation
        self.relationships_with_pcs = relationships_with_pcs
        self.memories = memories if memories is not None else [] # Initialize memories as an empty list


    def to_dict(self):
        data = {
            "name": self.name,
            "appearance": self.appearance,
            "personality_traits": self.personality_traits, 
            "backstory": self.backstory,
            "motivations": self.motivations,
            "flaws": self.flaws,
            "race": self.race,
            "class": self.npc_class,
            "speech_patterns": self.speech_patterns,
            "mannerisms": self.mannerisms,
            "past_situation": self.past_situation,
            "current_situation": self.current_situation,
            "relationships_with_pcs": self.relationships_with_pcs,
            "memories": self.memories # Include memories
            # Add other fields as needed
        }
        if self._id:
            data["_id"] = str(self._id)
        if self.user_id:
            data["user_id"] = str(self.user_id)
        if self.source_file:
            data["source_file"] = self.source_file
        # ... include other fields from your JSON ...
        return data