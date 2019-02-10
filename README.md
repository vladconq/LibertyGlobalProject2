# LibertyGlobalProject2
The project was created as a service that allows you to store the ip and port, as well as their current status. Storage is performed in a Postgresql database deployed in a docker.

## Prerequisites
All the necessary libraries are in the requirements.txt file.

## Getting Started
To use this service (instructions for Ubuntu 18.04), in the project folder, enter the following:
```
$ sudo docker-compose up -d
$ python3 app.py
```
## Usage
```
http://127.0.0.1:5000/get_by/127.0.0.1  # get information about this ip from the database
http://127.0.0.1:5000/get_by/172.217.21.142/80  # get information about this ip and port from the database
http://127.0.0.1:5000/add_entity/127.0.0.4/123/true  # add new entity to database
```
Every 30 seconds, the available addresses are checked for existence, and the service updates the information.
