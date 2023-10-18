# ID2221-Task4 Data Intensive Computing Project
 In this project, we aimed to create a web application capable of providing analytics and statistics on music streaming via Spotify. The project is composed of a back-end and a front-end element that allows users to link their Spotify account and view their listening statistics. The back-end consists of a distributed system designed to process and store all the relevant information. 

## System structure
![System structure](/images/system_structure.png)

# Docker
Our project requires `docker` and `docker-compose`

# Spotify API access
This project is using the Spotify API so you will need a Spotify API Client ID and Token. 
You can request your token [here](https://developer.spotify.com/)


# Setup ENV
Add the environment variables to the `.env` file, you can find a template in `.env.example`
```
###### Spotify variables ######
SPOTIFY_CLIENT_ID=''
SPOTIFY_CLIENT_SECRET=''
SPOTIFY_REDIRECT_URI='http://localhost/auth/spotify/callback'

###### Cassandra variables ######
CASSANDRA_USER='cassandra'
CASSANDRA_PASSWORD='cassandra'
```

# Prebuild docker image
Keep in mind that it will take more than three minutes
```
bash build.sh
```

# Running the application

## Create docker container
To create your docker containers for both backend and distributed spark processing run the following code
```
bash create.sh
```

## Additional setup required
Please note that Cassandra may take a while to start up, so wait a few seconds between commands
```
bash setup.sh
```

## Start
```
bash start.sh
```

## View web application
To view the web application open the browser to [http://localhost](http://localhost) and register your account

## Generate fake data
```
bash generate-data.sh
```
