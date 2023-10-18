cp ./spotify-connector/.env.example .env

docker-compose -f compose.yaml -f compose.connector.yaml create

