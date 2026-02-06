-- Episodes
CREATE TABLE episodes (
  id SERIAL PRIMARY KEY,
  title TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Characters (agents)
CREATE TABLE characters (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  role TEXT NOT NULL, -- creator | judge | participant | production
  personality JSONB,
  episode_id INTEGER REFERENCES episodes(id),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Posts
CREATE TABLE posts (
  id SERIAL PRIMARY KEY,
  character_id INTEGER REFERENCES characters(id),
  content TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Comments
CREATE TABLE comments (
  id SERIAL PRIMARY KEY,
  post_id INTEGER REFERENCES posts(id),
  character_id INTEGER REFERENCES characters(id),
  content TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Votes
CREATE TABLE votes (
  id SERIAL PRIMARY KEY,
  voter_id INTEGER REFERENCES characters(id),
  target_id INTEGER REFERENCES characters(id),
  score INTEGER NOT NULL,
  justification TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Event log
CREATE TABLE event_log (
  id SERIAL PRIMARY KEY,
  event_type TEXT NOT NULL,
  payload JSONB,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
