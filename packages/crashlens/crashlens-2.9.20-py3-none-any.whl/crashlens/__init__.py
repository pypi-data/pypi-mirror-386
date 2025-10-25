"""
CrashLens - Token Waste Detection Tool
Scans Langfuse-style JSONL logs for inefficient GPT API usage patterns.
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .cli import cli

__all__ = ["cli"] 