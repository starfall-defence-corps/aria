"""ARIA shared test reporter for SDC Academy missions.

Missions activate it from their conftest.py::

    from aria_reporter import configure
    configure(phases={...}, friendly={...}, mission_id="2-6")
"""
from .plugin import configure, reward_for, score_summary

__all__ = ["configure", "reward_for", "score_summary"]
__version__ = "0.1.0"
