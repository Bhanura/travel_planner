---
title: TripWeaver Travel Planner
emoji: ✈️
colorFrom: blue
colorTo: indigo
sdk: gradio
sdk_version: 6.19.0
python_version: 3.11.9
app_file: app.py
pinned: false
license: mit
short_description: MCP-based multi-agent travel planner
---

# TripWeaver Travel Planner

TripWeaver is a Gradio frontend for an MCP-based multi-agent travel planning system.

The application communicates with a separately deployed FastAPI backend. The backend URL is supplied through the `TRAVEL_PLANNER_API_URL` Hugging Face Space variable.

This Space is automatically deployed from the stable `main` branch of the GitHub repository after CI passes.