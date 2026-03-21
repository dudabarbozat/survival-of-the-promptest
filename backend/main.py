"""
Entrypoint for the Survival of the Promptest API.

Run with:
    uvicorn backend.main:app --reload

The n8n workflow in n8n/workflow.json orchestrates all endpoints.
"""
from backend.api import app  # noqa: F401 — re-exported for uvicorn
