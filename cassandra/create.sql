CREATE TABLE IF NOT EXISTS music_play_history (
  user_id text,
  played_at text,
  track_id text,
  track_name text,
  context_type text,
  context_href text,
  PRIMARY KEY (user_id, played_at, track_id)
);