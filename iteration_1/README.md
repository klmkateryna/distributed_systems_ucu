# Replication Log

The Replicated Log should have the following deployment architecture: one Master and any number of Secondaries.

Master should expose a simple HTTP server (or alternative service with a similar API) with: 
- POST method - appends a message into the in-memory list
- GET method - returns all messages from the in-memory list

Secondary should expose a simple  HTTP server(or alternative service with a similar API)  with:
- GET method - returns all replicated messages from the in-memory list

## First iteration

Properties and assumptions:
 - after each POST request, the message should be replicated on every Secondary server 
 - Master should ensure that Secondaries have received a message via ACK 
 - Master’s POST request should be finished only after receiving ACKs from all Secondaries (blocking replication approach)
 - to test that the replication is blocking, introduce the delay/sleep on the Secondary
 - at this stage assume that the communication channel is a perfect link (no failures and messages lost)
 - implementation support logging 
 - Master and Secondaries run in Docker

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
`request.post('{HOST_MASTER}:{PORT_MASTER}/add-message?secondary={HOST_SLAVE_1}:{PORT_SLAVE_1}&secondary={HOST_SLAVE_2}:{PORT_SLAVE_2}', json = {'entry':'message_1'})`

### Example of GET request from Master using Python
`request.get('{HOST_MASTER}:{PORT_MASTER}/get-message')`

### Example of GET request from Secondary server using Python
`request.get('{HOST_SLAVE_1}:{PORT_SLAVE_1}/replicate-log')`


### Run command
 - `docker-compose up`