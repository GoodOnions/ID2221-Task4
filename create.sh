if [ ! -f .env ]; then
    echo ".env file not found!"
    exit 1 
fi

docker-compose up -d

cd ./spotify-connector

cp .env.docker.example .env

cat ../.env >> .env

docker-compose up -d

docker exec spotify-connector-backend-1 composer install 
docker exec spotify-connector-backend-1 php artisan key:generate
docker exec spotify-connector-backend-1 php artisan migrate
docker exec spotify-connector-backend-1 npm install
docker exec spotify-connector-backend-1 npm run build
