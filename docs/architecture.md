# Architecture Overview

Survival of the Promptest is designed as an event-driven, automation-first system.

The system is composed of:
- An orchestration layer (n8n)
- A processing layer (Python)
- A persistence layer (PostgreSQL)
- A read-only visualization layer

Automation controls execution order.
Agents generate content and evaluations.
The system enforces rules and persistence.
