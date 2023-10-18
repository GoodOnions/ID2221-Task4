if [ ! -f .env ]; then
    echo ".env file not found!"
    exit 1 
fi

cd ./spotify-connector

cp .env.docker.example .env
cat ../.env >> .env

docker-compose build --no-cache