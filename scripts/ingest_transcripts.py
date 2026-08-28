#!/usr/bin/env python3
"""
Script to ingest Lenny's Podcast transcripts into the vector database.
Run this after adding JSON files to data/transcripts/
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.services.ingestion import ingestion_service


def main():
    print("Starting transcript ingestion...")
    print(f"Looking for transcripts in: data/transcripts/")
    
    result = ingestion_service.ingest_all()
    
    print("\nIngestion Result:")
    print(f"  Status: {result.get('status')}")
    print(f"  Transcripts processed: {result.get('transcripts_processed', 0)}")
    print(f"  Chunks created: {result.get('chunks_created', 0)}")
    
    if result.get('status') == 'no_transcripts_found':
        print("\nNo transcript files found in data/transcripts/")
        print("Please add JSON files with format:")
        print('  {"title": "...", "url": "...", "date": "...", "speaker": "...", "content": "..."}')
        sys.exit(1)
    
    if result.get('status') == 'success':
        print("\nIngestion complete! Vector database is ready.")
    else:
        print(f"\nIngestion failed: {result}")
        sys.exit(1)


if __name__ == "__main__":
    main()