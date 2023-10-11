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
  PRIMARY KEY (user_id, played_at, track_id)
);

CREATE MATERIALIZED VIEW general_stats AS
   SELECT 
    user_id,
    AVG(duration_ms),
    AVG(popularity),
    AVG(energy),
    AVG(danceability),
    AVG(instrumentalress),
    AVG(loudness),
    AVG(tempo),
    AVG(valence)
    FROM music_play_history
    GROUP BY user_id
   PRIMARY KEY (user_id);