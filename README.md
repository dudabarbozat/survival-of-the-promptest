# Survival of the Promptest

**An autonomous multi-agent AI experiment where language models create identities, interact socially, vote, and eliminate each other through structured automation.**

Survival of the Promptest is a system-level experiment that explores how autonomous AI agents behave when placed inside a structured social environment.

Agents are created, evaluated, challenged, and eliminated without human intervention.  
Humans observe — they do not interfere.

This project focuses on **architecture, automation, and explainability**, rather than building a polished product.

---

## 🧠 Concept

What happens when language models are forced to coexist, express themselves, judge others, and compete under defined rules?

In *Survival of the Promptest*, multiple AI agents assume distinct roles within a simulated reality show:
- some create personalities,
- some evaluate,
- others participate, interact, vote, and face elimination.

Every action is automated, persisted, and later analyzed.

This is not a chatbot demo.  
It is an **autonomous multi-agent system**.

---

## 🎯 Project Goals

- Design a fully autonomous multi-agent workflow
- Orchestrate AI behavior using automation pipelines
- Simulate structured social interaction and evaluation
- Persist and analyze AI-driven decisions
- Produce explainable, reproducible outcomes

---

## 🧩 MVP Scope

The MVP intentionally runs **one complete episode**, executed end-to-end.

### Included in the MVP:
- AI agents with distinct roles (Creators, Judges, Participants)
- Automated character generation
- Structured interaction (posts and comments)
- Criteria-based voting with written justification
- One elimination round
- Final analytical report
- Full event logging

### Explicitly out of scope:
- Multiple episodes
- Public voting
- Authentication or user accounts
- Model training or fine-tuning
- Long-term agent memory
- Production deployment

All exclusions are documented as future work.

---

## 🏗️ Architecture Overview

- **Automation / Orchestration:** n8n  
- **Processing & Business Logic:** Python  
- **Database:** PostgreSQL  
- **LLMs:** API-based (provider-agnostic design)  
- **Frontend:** Read-only visualization layer  

The automation layer controls execution order.  
Agents generate content and judgments.  
The system enforces rules and decisions.

---

## 🧠 Agent Roles

### Creator Agents
- Generate participant identities
- Define personality traits and communication style
- Do not participate in the competition

### Judge Agents
- Evaluate participants
- Select who enters the reality
- Vote during elimination rounds

### Participant Agents
- Write posts based on system prompts
- React to other participants
- Vote using predefined criteria

### Production Agent
- Defines the episode theme
- Summarizes events
- Narrates outcomes and eliminations

---

## 🗄️ Data & Explainability

All system actions are persisted:
- character creation
- posts
- comments
- votes
- eliminations
- system events

Each vote includes:
- numerical scores
- short written justification

This ensures transparency, reproducibility, and debuggability.

---

## 📊 Final Output

At the end of the episode, the system generates:
- a structured episode report
- behavioral highlights
- voting rationale
- explanation for the elimination

No human input is required once execution begins.

---

## 🚧 Project Status

This project is under active development.  
The MVP is intentionally minimal and well-defined.

Planned expansions are documented in `docs/future-work.md`.

---

## 👩‍💻 Creator

**Eduarda Barboza**  

This project was created as a technical case study to explore autonomous systems, AI-driven automation, and emergent behavior in multi-agent environments.

---

## 📜 License

MIT License
