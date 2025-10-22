"""Agent memory system for cross-session learning and knowledge persistence.

This module provides stateful memory infrastructure for AI coding agents,
implementing the A-MEM (Agentic Memory) principles from agentic coding best practices.
"""

from coda_mcp.memory.event_log import EventLog, query_events
from coda_mcp.memory.knowledge_graph import KnowledgeGraph
from coda_mcp.memory.profiles import AgentProfile, AgentProfileManager
from coda_mcp.memory.trace import TraceContext, emit_event, get_trace_id

__all__ = [
    "EventLog",
    "query_events",
    "KnowledgeGraph",
    "TraceContext",
    "get_trace_id",
    "emit_event",
    "AgentProfile",
    "AgentProfileManager",
]
