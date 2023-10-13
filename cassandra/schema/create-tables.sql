USE goodonions;

CREATE TABLE IF NOT EXISTS music_play_history (
  user_id text,
  played_at text,
  track_id text,
  track_name text,
  context_type text,
  context_href text,
  duration_ms double,
  track_popularity double,
  energy double,
  danceability double,
  instrumentalness double,
  loudness double,
  tempo double,
  valence double,
  day_of_week int,
  hour_of_day int,
  PRIMARY KEY (user_id, played_at, track_id)
);