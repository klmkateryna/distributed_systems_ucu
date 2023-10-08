# Replication Log

The Replicated Log should have the following deployment architecture: one Master and any number of Secondaries.

Master should expose a simple HTTP server (or alternative service with a similar API) with: 
- POST method - appends a message into the in-memory list
- GET method - returns all messages from the in-memory list

Secondary should expose a simple  HTTP server(or alternative service with a similar API)  with:
- GET method - returns all replicated messages from the in-memory list

## Second iteration

Current iteration should provide tunable semi-synchronicity for replication, by defining write concern parameters. 
client POST request in addition to the message should also contain write concern parameter w=1,2,3,..,n
w value specifies how many ACKs the master should receive from secondaries before responding to the client
- w = 1 - only from master
- w = 2 - from master and one secondary
- w = 3 - from master and two secondaries 

### Project structure
 - `master/` - folder for Master node;
 - `slave_1/` - folder for Secondary 1 node;
 - `slave_2/` - folder for Secondary 2 node;

### Run command
 - `docker-compose up`