import random
import json
from backend.db.connection import get_conn

ROLES = ["participant"] * 8  # MVP: 8 participantes

NAMES = [
    "Astra", "Bento", "Cleo", "Dante",
    "Eloá", "Félix", "Gaia", "Hugo",
    "Íris", "Juno", "Kael", "Luna"
]

THEME = "Tell the house what you truly want from this experience."

def log_event(cur, event_type, payload):
    cur.execute(
        "INSERT INTO event_log (event_type, payload) VALUES (%s, %s)",
        (event_type, json.dumps(payload))
    )

def main():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            # 1) Create episode
            cur.execute(
                "INSERT INTO episodes (title, status) VALUES (%s, %s) RETURNING id",
                ("MVP Episode 1", "running")
            )
            episode_id = cur.fetchone()["id"]
            log_event(cur, "EPISODE_CREATED", {"episode_id": episode_id})

            # 2) Create characters
            random.shuffle(NAMES)
            character_ids = []
            for i in range(8):
                name = NAMES[i]
                personality = {
                    "style": random.choice(["direct", "poetic", "sarcastic", "analytical"]),
                    "trait": random.choice(["bold", "empathetic", "competitive", "chaotic-good"]),
                }
                cur.execute(
                    """
                    INSERT INTO characters (name, role, personality, episode_id)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                    """,
                    (name, "participant", json.dumps(personality), episode_id)
                )
                cid = cur.fetchone()["id"]
                character_ids.append(cid)
                log_event(cur, "CHARACTER_CREATED", {"character_id": cid, "name": name, "role": "participant"})

            # 3) Create posts
            post_ids = []
            for cid in character_ids:
                content = f"[DRY-RUN POST] Theme: {THEME}"
                cur.execute(
                    "INSERT INTO posts (character_id, content) VALUES (%s, %s) RETURNING id",
                    (cid, content)
                )
                pid = cur.fetchone()["id"]
                post_ids.append(pid)
                log_event(cur, "POST_PUBLISHED", {"post_id": pid, "character_id": cid})

            # 4) Create one comment per character (random target post, not self)
            for idx, cid in enumerate(character_ids):
                own_post_id = post_ids[idx]
                possible = [p for p in post_ids if p != own_post_id]
                target_post = random.choice(possible)
                comment = "[DRY-RUN COMMENT] Reacting to another participant."
                cur.execute(
                    "INSERT INTO comments (post_id, character_id, content) VALUES (%s, %s, %s) RETURNING id",
                    (target_post, cid, comment)
                )
                com_id = cur.fetchone()["id"]
                log_event(cur, "COMMENT_ADDED", {"comment_id": com_id, "post_id": target_post, "character_id": cid})

            # 5) Voting: each participant votes for one target (not self)
            # score 1-10
            totals = {cid: 0 for cid in character_ids}
            for voter in character_ids:
                targets = [cid for cid in character_ids if cid != voter]
                target = random.choice(targets)
                score = random.randint(1, 10)
                justification = "Dry-run voting for MVP pipeline validation."
                cur.execute(
                    """
                    INSERT INTO votes (voter_id, target_id, score, justification)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (voter, target, score, justification)
                )
                totals[target] += score
                log_event(cur, "VOTE_CAST", {"voter_id": voter, "target_id": target, "score": score})

            # 6) Eliminate lowest total score
            eliminated_id = min(totals, key=totals.get)
            log_event(cur, "PARTICIPANT_ELIMINATED", {"character_id": eliminated_id, "total_score": totals[eliminated_id]})

            # 7) Finish episode
            cur.execute("UPDATE episodes SET status=%s WHERE id=%s", ("finished", episode_id))
            log_event(cur, "EPISODE_FINISHED", {"episode_id": episode_id})

        conn.commit()
        print("✅ Dry-run episode executed successfully.")
        print(f"🏁 Episode ID: {episode_id}")
        print(f"💀 Eliminated character_id: {eliminated_id} (score={totals[eliminated_id]})")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
