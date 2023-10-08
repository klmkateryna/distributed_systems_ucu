# Replication Log

The Replicated Log should have the following deployment architecture: one Master and any number of Secondaries.

Master should expose a simple HTTP server (or alternative service with a similar API) with: 
- POST method - appends a message into the in-memory list
- GET method - returns all messages from the in-memory list

Secondary should expose a simple  HTTP server(or alternative service with a similar API)  with:
- GET method - returns all replicated messages from the in-memory list


### Project structure
 - `iteration_1/` - folder for first task;
 - `iteration_2/` - folder for second task;
 - `iteration_3/` - folder for third task;

### Run command
 - `docker-compose up`