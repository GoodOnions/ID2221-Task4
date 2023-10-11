docker-compose exec kafka kafka-topics.sh --create --if-not-exists --topic onions --partitions 1 --replication-factor 1 --bootstrap-server kafka:9093
echo "Kafka setup completed!" 

#echo "Enter cassandra DB password: " 
docker-compose exec cassandra cqlsh -u cassandra -p cassandra --file /schema/create-database.sql


#echo "Enter cassandra DB password: "
docker-compose exec cassandra cqlsh -u cassandra -p cassandra --file /schema/create-tables.sql
echo "Cassandra setup completed!"

echo "Installation of dependencies spark worker: "
docker exec spark_master pip install pandas requests PyArrow &
docker exec spark_worker pip install pandas requests PyArrow 
echo "Installation complited!"

