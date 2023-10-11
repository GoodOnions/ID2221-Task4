CREATE  KEYSPACE IF NOT EXISTS goodonions                
WITH REPLICATION = {'class' : 'SimpleStrategy'}
AND DURABLE_WRITES = true; 