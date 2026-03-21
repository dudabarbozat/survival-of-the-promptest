import json
import os
import random

from fastapi import FastAPI, HTTPException

from backend.db.connection import get_conn

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

app = FastAPI(title="Survival of the Promptest API")

NAMES = [
    "Astra", "Bento", "Cleo", "Dante",
    "Eloá", "Félix", "Gaia", "Hugo",
    "Íris", "Juno", "Kael", "Luna",
]

EPISODE_THEME = "Tell the house what you truly want from this experience."


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_client():
    if ANTHROPIC_AVAILABLE and os.getenv("ANTHROPIC_API_KEY"):
        return anthropic.Anthropic()
    return None


def _call_claude(client, prompt: str, fallback: str) -> str:
    if client is None:
        return fallback
    try:
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text.strip()
    except Exception:
        return fallback


def _log_event(cur, event_type: str, payload: dict):
    cur.execute(
        "INSERT INTO event_log (event_type, payload) VALUES (%s, %s)",
        (event_type, json.dumps(payload)),
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.post("/episodes")
def create_episode():
    """Step 1 — Create a new episode and return its ID."""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO episodes (title, status) VALUES (%s, %s) RETURNING id",
                ("Episode 1", "running"),
            )
            episode_id = cur.fetchone()["id"]
            _log_event(cur, "EPISODE_CREATED", {"episode_id": episode_id})
        conn.commit()
        return {"episode_id": episode_id, "title": "Episode 1", "status": "running"}
    finally:
        conn.close()


@app.post("/episodes/{episode_id}/characters")
def create_characters(episode_id: int):
    """Step 2 — Generate 8 participant characters with AI-crafted backstories."""
    client = _get_client()
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM episodes WHERE id = %s", (episode_id,))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Episode not found")

            names = NAMES[:]
            random.shuffle(names)
            characters = []

            for i in range(8):
                name = names[i]
                style = random.choice(["direct", "poetic", "sarcastic", "analytical"])
                trait = random.choice(["bold", "empathetic", "competitive", "chaotic-good"])

                backstory = _call_claude(
                    client,
                    f"Write a 1-sentence backstory for a reality show contestant named {name} "
                    f"with a {style} communication style and a {trait} personality. Be creative and concise.",
                    f"{name} joined the show seeking connection and a chance to prove themselves.",
                )

                personality = {"style": style, "trait": trait, "backstory": backstory}

                cur.execute(
                    "INSERT INTO characters (name, role, personality, episode_id) "
                    "VALUES (%s, %s, %s, %s) RETURNING id",
                    (name, "participant", json.dumps(personality), episode_id),
                )
                cid = cur.fetchone()["id"]
                _log_event(cur, "CHARACTER_CREATED", {"character_id": cid, "name": name})
                characters.append({"id": cid, "name": name, "personality": personality})

        conn.commit()
        return {"episode_id": episode_id, "characters": characters}
    finally:
        conn.close()


@app.post("/episodes/{episode_id}/posts")
def create_posts(episode_id: int):
    """Step 3 — Each character writes a post answering the episode theme via Claude."""
    client = _get_client()
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, personality FROM characters "
                "WHERE episode_id = %s AND role = 'participant'",
                (episode_id,),
            )
            characters = cur.fetchall()
            if not characters:
                raise HTTPException(status_code=404, detail="No characters found for this episode")

            posts = []
            for char in characters:
                personality = char["personality"] or {}
                style = personality.get("style", "direct")
                trait = personality.get("trait", "bold")

                content = _call_claude(
                    client,
                    f"You are {char['name']}, a reality show contestant with a {style} communication "
                    f"style and a {trait} personality. Write a short post (2-4 sentences) for the house "
                    f"answering this prompt: \"{EPISODE_THEME}\" Stay in character. No hashtags.",
                    f"[{char['name']}] {EPISODE_THEME} — I'm here to give it my all.",
                )

                cur.execute(
                    "INSERT INTO posts (character_id, content) VALUES (%s, %s) RETURNING id",
                    (char["id"], content),
                )
                pid = cur.fetchone()["id"]
                _log_event(cur, "POST_PUBLISHED", {"post_id": pid, "character_id": char["id"]})
                posts.append({
                    "id": pid,
                    "character_id": char["id"],
                    "character_name": char["name"],
                    "content": content,
                })

        conn.commit()
        return {"episode_id": episode_id, "posts": posts}
    finally:
        conn.close()


@app.post("/episodes/{episode_id}/comments")
def create_comments(episode_id: int):
    """Step 4 — Each character reacts to another participant's post via Claude."""
    client = _get_client()
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT c.id, c.name, c.personality, p.id as post_id, p.content as post_content "
                "FROM characters c JOIN posts p ON p.character_id = c.id "
                "WHERE c.episode_id = %s",
                (episode_id,),
            )
            rows = cur.fetchall()
            if not rows:
                raise HTTPException(status_code=404, detail="No posts found for this episode")

            char_posts = {
                row["id"]: {
                    "post_id": row["post_id"],
                    "post_content": row["post_content"],
                    "name": row["name"],
                    "personality": row["personality"],
                }
                for row in rows
            }

            comments = []
            for char_id, char_data in char_posts.items():
                targets = [(cid, d) for cid, d in char_posts.items() if cid != char_id]
                if not targets:
                    continue
                target_cid, target_data = random.choice(targets)

                personality = char_data["personality"] or {}
                style = personality.get("style", "direct")
                trait = personality.get("trait", "bold")

                content = _call_claude(
                    client,
                    f"You are {char_data['name']}, a reality show contestant with a {style} communication "
                    f"style and a {trait} personality. React to this post from {target_data['name']}: "
                    f"\"{target_data['post_content']}\". Write a short comment (1-2 sentences) in character. "
                    f"It can be supportive, competitive, or curious.",
                    f"[{char_data['name']}] Interesting take, {target_data['name']}. I see things differently.",
                )

                cur.execute(
                    "INSERT INTO comments (post_id, character_id, content) VALUES (%s, %s, %s) RETURNING id",
                    (target_data["post_id"], char_id, content),
                )
                com_id = cur.fetchone()["id"]
                _log_event(cur, "COMMENT_ADDED", {
                    "comment_id": com_id,
                    "post_id": target_data["post_id"],
                    "character_id": char_id,
                })
                comments.append({
                    "id": com_id,
                    "character_id": char_id,
                    "post_id": target_data["post_id"],
                    "content": content,
                })

        conn.commit()
        return {"episode_id": episode_id, "comments": comments}
    finally:
        conn.close()


@app.post("/episodes/{episode_id}/votes")
def run_votes(episode_id: int):
    """Step 5 — Each character votes for another with a Claude-justified score (1-10)."""
    client = _get_client()
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT c.id, c.name, c.personality, p.content as post_content "
                "FROM characters c LEFT JOIN posts p ON p.character_id = c.id "
                "WHERE c.episode_id = %s AND c.role = 'participant'",
                (episode_id,),
            )
            characters = cur.fetchall()
            if not characters:
                raise HTTPException(status_code=404, detail="No characters found")

            totals = {char["id"]: 0 for char in characters}
            votes = []

            for voter in characters:
                targets = [c for c in characters if c["id"] != voter["id"]]
                target = random.choice(targets)

                personality = voter["personality"] or {}
                style = personality.get("style", "direct")

                result_text = _call_claude(
                    client,
                    f"You are {voter['name']}, a reality show contestant with a {style} style. "
                    f"Vote for {target['name']} who posted: \"{target.get('post_content', 'no post')}\". "
                    f"Give a score from 1 to 10 and a brief justification (1 sentence). "
                    f"Reply ONLY in this exact format:\nSCORE: <number>\nJUSTIFICATION: <text>",
                    f"SCORE: {random.randint(1, 10)}\nJUSTIFICATION: Strong presence in the house.",
                )

                score = random.randint(1, 10)
                justification = "No justification provided."
                for line in result_text.splitlines():
                    if line.startswith("SCORE:"):
                        try:
                            score = max(1, min(10, int(line.replace("SCORE:", "").strip())))
                        except ValueError:
                            pass
                    elif line.startswith("JUSTIFICATION:"):
                        justification = line.replace("JUSTIFICATION:", "").strip()

                cur.execute(
                    "INSERT INTO votes (voter_id, target_id, score, justification) "
                    "VALUES (%s, %s, %s, %s)",
                    (voter["id"], target["id"], score, justification),
                )
                totals[target["id"]] += score
                _log_event(cur, "VOTE_CAST", {
                    "voter_id": voter["id"],
                    "target_id": target["id"],
                    "score": score,
                })
                votes.append({
                    "voter_id": voter["id"],
                    "voter_name": voter["name"],
                    "target_id": target["id"],
                    "target_name": target["name"],
                    "score": score,
                    "justification": justification,
                })

        conn.commit()
        return {"episode_id": episode_id, "votes": votes, "totals": totals}
    finally:
        conn.close()


@app.post("/episodes/{episode_id}/eliminate")
def eliminate(episode_id: int):
    """Step 6 — Eliminate the character with the lowest accumulated vote score."""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT c.id, c.name, COALESCE(SUM(v.score), 0) AS total_score
                FROM characters c
                LEFT JOIN votes v ON v.target_id = c.id
                WHERE c.episode_id = %s AND c.role = 'participant'
                GROUP BY c.id, c.name
                ORDER BY total_score ASC
                LIMIT 1
                """,
                (episode_id,),
            )
            eliminated = cur.fetchone()
            if not eliminated:
                raise HTTPException(status_code=404, detail="No characters to eliminate")

            _log_event(cur, "PARTICIPANT_ELIMINATED", {
                "character_id": eliminated["id"],
                "name": eliminated["name"],
                "total_score": eliminated["total_score"],
            })

        conn.commit()
        return {
            "episode_id": episode_id,
            "eliminated_id": eliminated["id"],
            "eliminated_name": eliminated["name"],
            "total_score": eliminated["total_score"],
        }
    finally:
        conn.close()


@app.post("/episodes/{episode_id}/finish")
def finish_episode(episode_id: int):
    """Step 7 — Mark episode as finished and generate a Claude-narrated report."""
    client = _get_client()
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT p.content, c.name FROM posts p "
                "JOIN characters c ON p.character_id = c.id "
                "WHERE c.episode_id = %s",
                (episode_id,),
            )
            posts = cur.fetchall()

            cur.execute(
                """
                SELECT c.id, c.name, COALESCE(SUM(v.score), 0) AS total_score
                FROM characters c
                LEFT JOIN votes v ON v.target_id = c.id
                WHERE c.episode_id = %s
                GROUP BY c.id, c.name
                ORDER BY total_score ASC
                """,
                (episode_id,),
            )
            scores = cur.fetchall()

            eliminated = scores[0] if scores else None

            summary = f"Episode theme: {EPISODE_THEME}\n\nParticipant posts:\n"
            for post in posts:
                summary += f"- {post['name']}: \"{post['content'][:120]}\"\n"
            if eliminated:
                summary += (
                    f"\nEliminated: {eliminated['name']} "
                    f"with lowest score of {eliminated['total_score']}.\n"
                )

            report = _call_claude(
                client,
                f"You are the narrator of a reality show. Write a brief analytical episode report "
                f"(3-5 sentences) based on the following:\n\n{summary}",
                (
                    f"Episode 1 concluded with {eliminated['name'] if eliminated else 'unknown'} "
                    f"being eliminated with the lowest vote total. The contestants displayed diverse "
                    f"personalities throughout the episode. The Survival of the Promptest pipeline "
                    f"ran successfully end-to-end."
                ),
            )

            cur.execute(
                "UPDATE episodes SET status = %s WHERE id = %s",
                ("finished", episode_id),
            )
            _log_event(cur, "EPISODE_FINISHED", {"episode_id": episode_id, "report": report})

        conn.commit()
        return {
            "episode_id": episode_id,
            "status": "finished",
            "report": report,
            "eliminated": (
                {
                    "id": eliminated["id"],
                    "name": eliminated["name"],
                    "total_score": eliminated["total_score"],
                }
                if eliminated
                else None
            ),
        }
    finally:
        conn.close()


@app.get("/episodes/{episode_id}/report")
def get_report(episode_id: int):
    """Final — Return the full structured episode report."""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM episodes WHERE id = %s", (episode_id,))
            episode = cur.fetchone()
            if not episode:
                raise HTTPException(status_code=404, detail="Episode not found")

            cur.execute(
                "SELECT id, name, personality FROM characters WHERE episode_id = %s",
                (episode_id,),
            )
            characters = cur.fetchall()

            cur.execute(
                "SELECT p.id, p.content, c.name AS character_name "
                "FROM posts p JOIN characters c ON p.character_id = c.id "
                "WHERE c.episode_id = %s",
                (episode_id,),
            )
            posts = cur.fetchall()

            cur.execute(
                """
                SELECT c.id, c.name, COALESCE(SUM(v.score), 0) AS total_score
                FROM characters c
                LEFT JOIN votes v ON v.target_id = c.id
                WHERE c.episode_id = %s
                GROUP BY c.id, c.name
                ORDER BY total_score DESC
                """,
                (episode_id,),
            )
            rankings = cur.fetchall()

            cur.execute(
                "SELECT event_type, payload, created_at FROM event_log "
                "WHERE payload->>'episode_id' = %s ORDER BY created_at",
                (str(episode_id),),
            )
            events = cur.fetchall()

        return {
            "episode": dict(episode),
            "characters": [dict(c) for c in characters],
            "posts": [dict(p) for p in posts],
            "rankings": [dict(r) for r in rankings],
            "events": [dict(e) for e in events],
        }
    finally:
        conn.close()
