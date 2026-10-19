"""
Bridge between M1's ingestion contract and the central pipeline engine.
"""
from backend.app.services.pipeline import run_sync_pipeline as stream_outlet_sync

__all__ = ["stream_outlet_sync"]
