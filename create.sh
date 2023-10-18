docker-compose up -d

cd ./spotify-connector

cp .env.example .env

docker-compose up -d

docker exec spotify-connector-laravel.test-1 composer install 
docker exec spotify-connector-laravel.test-1 php artisan key:generate
docker exec spotify-connector-laravel.test-1 php artisan migrate
docker exec spotify-connector-laravel.test-1 npm install
docker exec spotify-connector-laravel.test-1 npm run build
