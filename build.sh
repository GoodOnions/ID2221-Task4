cd ./spotify-connector

cp .env.docker.example .env
cat ../.env >> .env

docker-compose build --no-cache