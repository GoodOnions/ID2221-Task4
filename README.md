# ID2221-Task4
 Distributed Music Genre Preferences Tracker with Spotify API


## Start CassandraCluster
```
 docker compose -f CassandraCluster/compose.yml up -d
```

## To run script
```
docker-compose exec spark_master spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.1.2 /bitnami/data_clean.py
```