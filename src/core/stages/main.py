"""
Definition of the overall flow and the entry point for the background worker.
"""

from shared.schemas.brief import Brief
from shared.schemas.run import Run

from stages.ingestion.ingest_data import SourceKey, ingest_data

def main(brief: Brief, selected_sources: list[SourceKey]) -> Run:

    raw_data = ingest_data(selected_sources, brief)
    
