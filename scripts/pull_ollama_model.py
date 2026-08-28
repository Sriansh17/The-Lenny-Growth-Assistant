#!/usr/bin/env python3
"""
Script to pull Ollama model for the Lenny Growth Assistant.
Run this after starting Ollama service.
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import ollama
from app.core.config import settings


def pull_model(model_name: str = None):
    model = model_name or settings.OLLAMA_MODEL
    print(f"Pulling Ollama model: {model}")
    print(f"Connecting to: {settings.OLLAMA_BASE_URL}")
    
    try:
        client = ollama.Client(host=settings.OLLAMA_BASE_URL)
        client.pull(model)
        print(f"Successfully pulled {model}")
    except Exception as e:
        print(f"Error pulling model: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Pull Ollama model")
    parser.add_argument("--model", default=settings.OLLAMA_MODEL, help="Model name to pull")
    args = parser.parse_args()
    pull_model(args.model)