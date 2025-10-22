"""Agent profile management for capability tracking and preferences.

This module manages per-agent profiles that track capabilities, preferences,
and learned patterns for AI coding agents.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import json


@dataclass
class AgentProfile:
    """Profile for an AI coding agent."""

    agent_name: str
    agent_version: str
    last_active: datetime
    session_count: int = 0
    capabilities: Dict[str, dict] = field(default_factory=dict)
    preferences: Dict[str, any] = field(default_factory=dict)
    context_switches: Dict[str, any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert profile to dictionary."""
        return {
            "agent_name": self.agent_name,
            "agent_version": self.agent_version,
            "last_active": self.last_active.isoformat(),
            "session_count": self.session_count,
            "capabilities": self.capabilities,
            "preferences": self.preferences,
            "context_switches": self.context_switches,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AgentProfile":
        """Create profile from dictionary."""
        data["last_active"] = datetime.fromisoformat(data["last_active"])
        return cls(**data)


class AgentProfileManager:
    """Manages agent profiles (load, save, update)."""

    def __init__(self, profiles_dir: Optional[Path] = None):
        """Initialize profile manager.

        Args:
            profiles_dir: Directory to store profiles (default: .chora/memory/profiles/)
        """
        if profiles_dir is None:
            profiles_dir = Path.cwd() / ".chora" / "memory" / "profiles"

        self.profiles_dir = profiles_dir
        self.profiles_dir.mkdir(parents=True, exist_ok=True)

    def load_profile(self, agent_name: str) -> Optional[AgentProfile]:
        """Load agent profile.

        Args:
            agent_name: Name of the agent

        Returns:
            AgentProfile if exists, None otherwise
        """
        profile_file = self.profiles_dir / f"{agent_name}.json"

        if not profile_file.exists():
            return None

        data = json.loads(profile_file.read_text())
        return AgentProfile.from_dict(data)

    def save_profile(self, profile: AgentProfile):
        """Save agent profile.

        Args:
            profile: AgentProfile to save
        """
        profile_file = self.profiles_dir / f"{profile.agent_name}.json"
        profile_file.write_text(json.dumps(profile.to_dict(), indent=2))

    def update_profile(
        self,
        agent_name: str,
        agent_version: str,
        **updates
    ) -> AgentProfile:
        """Update agent profile (creates if doesn't exist).

        Args:
            agent_name: Name of the agent
            agent_version: Version of the agent
            **updates: Additional fields to update

        Returns:
            Updated AgentProfile
        """
        profile = self.load_profile(agent_name)

        if profile is None:
            profile = AgentProfile(
                agent_name=agent_name,
                agent_version=agent_version,
                last_active=datetime.now(),
                session_count=1,
            )
        else:
            profile.last_active = datetime.now()
            profile.session_count += 1
            profile.agent_version = agent_version

        # Apply updates
        for key, value in updates.items():
            if hasattr(profile, key):
                setattr(profile, key, value)

        self.save_profile(profile)
        return profile

    def list_profiles(self) -> List[str]:
        """List all agent profiles.

        Returns:
            List of agent names
        """
        return [f.stem for f in self.profiles_dir.glob("*.json")]
