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
 - `.env` - file with environment variables. Example:
```
HOST_MASTER =
PORT_MASTER =
HOST_SLAVE_1 = 
PORT_SLAVE_1 = 
TIME_SLEEP_IN_SEC_SLAVE_1 = 
HOST_SLAVE_2 =
PORT_SLAVE_2 =
TIME_SLEEP_IN_SEC_SLAVE_2 =
```

### Required structure for JSON file
`{'entry':'message_1'}`

### Example of POST request to Master using Python
`request.post('{HOST_MASTER}:{PORT_MASTER}/add-message?secondary={HOST_SLAVE_1}:{PORT_SLAVE_1}&secondary={HOST_SLAVE_2}:{PORT_SLAVE_2}&concern={concern_value}', json = {'entry':'message_1'})`

### Example of GET request from Master using Python
`request.get('{HOST_MASTER}:{PORT_MASTER}/get-message')`

### Example of GET request from Secondary server using Python
`request.get('{HOST_SLAVE_1}:{PORT_SLAVE_1}/replicate-log')`


### Run command
 - `docker-compose up`