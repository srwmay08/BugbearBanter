# ---- server/app/models.py ----
# This file will define the structure of your data.
# Even with NoSQL like MongoDB, having classes can help organize data expectations.
# You won't use an ORM like SQLAlchemy, but these classes serve as conceptual models.

import datetime

class User:
    """
    Represents a user in the system.
    """
    def __init__(self, email, password_hash, google_id=None, patreon_status=None, created_at=None):
        self.email = email
        self.password_hash = password_hash # Store hashed passwords only!
        self.google_id = google_id
        self.patreon_status = patreon_status # e.g., 'active_patron', 'former_patron', None
        self.created_at = created_at or datetime.datetime.utcnow()

    def to_dict(self):
        return {
            "email": self.email,
            "google_id": self.google_id,
            "patreon_status": self.patreon_status,
            "created_at": self.created_at.isoformat()
            # DO NOT return password_hash
        }

class NPC:
    """
    Represents a Non-Player Character.
    """
    def __init__(self, name, game_world_id, appearance=None, personality_traits=None, memories=None, life_events=None, organizations=None, religions=None, towns=None, portrait_url=None, created_at=None, updated_at=None):
        self.name = name
        self.game_world_id = game_world_id # ObjectId of the GameWorld it belongs to
        self.appearance = appearance or ""
        self.personality_traits = personality_traits or []
        self.memories = memories or [] # Could be a list of strings or more structured objects
        self.life_events = life_events or []
        self.organizations = organizations or []
        self.religions = religions or []
        self.towns = towns or [] # Towns the NPC is associated with
        self.portrait_url = portrait_url
        self.created_at = created_at or datetime.datetime.utcnow()
        self.updated_at = updated_at or datetime.datetime.utcnow()

    def to_dict(self):
        return {
            "name": self.name,
            "game_world_id": str(self.game_world_id), # Convert ObjectId to string for JSON
            "appearance": self.appearance,
            "personality_traits": self.personality_traits,
            "memories": self.memories,
            "life_events": self.life_events,
            "organizations": self.organizations,
            "religions": self.religions,
            "towns": self.towns,
            "portrait_url": self.portrait_url,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

class GameWorld:
    """
    Represents a game world/campaign.
    """
    def __init__(self, user_id, title, game_system=None, created_at=None):
        self.user_id = user_id # ObjectId of the user who owns this world
        self.title = title
        self.game_system = game_system
        self.created_at = created_at or datetime.datetime.utcnow()

    def to_dict(self):
        return {
            "user_id": str(self.user_id),
            "title": self.title,
            "game_system": self.game_system,
            "created_at": self.created_at.isoformat()
        }

class Scene:
    """
    Represents a scene within a game world.
    """
    def __init__(self, game_world_id, name, description=None, npc_ids=None, created_at=None):
        self.game_world_id = game_world_id # ObjectId
        self.name = name
        self.description = description
        self.npc_ids = npc_ids or [] # List of ObjectIds of NPCs in this scene
        self.created_at = created_at or datetime.datetime.utcnow()

    def to_dict(self):
        return {
            "game_world_id": str(self.game_world_id),
            "name": self.name,
            "description": self.description,
            "npc_ids": [str(npc_id) for npc_id in self.npc_ids],
            "created_at": self.created_at.isoformat()
        }

# Add other models like Resource, Event, Organization etc. as needed.