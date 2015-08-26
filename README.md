# IDP: Transforming Minecraft into a behavioral and creativity research platform

This work is part of a Interdisciplinary Project made at the TU München by Bastien Achard and Stefan Reu.

This Python 3 set of scripts contains the necessary tools to manage players connection, visualize and export statistics, and manage players.


## Server
A main server is setup with app.py. It is based on [Flask](http://flask.pocoo.org/) and uses [SQLAlchemy](http://www.sqlalchemy.org/) as Object Relational Mapper. The functionning is inspired by RESTFul APIs.
For the web interface, [Bootstrap](http://getbootstrap.com/) is used as CSS framework, [jQuery](https://jquery.com/) for JavaScript.

## Clients
Clients are created using client.py.

## Database
Any RDBMS can be used, it must be specified in the settings.yml file.
You will need to use a Python3 compatible plugin to connect to the RDBMS (ex. [PyMySQL](https://github.com/PyMySQL/PyMySQL) for MySQL).

## Settings
All the settings are specified in ```settings.yml```:

1. flask: Flask general settings
  * secret_key: secret key to be used
  * debug: launch in debug mode or not
  * ext: server available externally (set to True in production mode)
2. server: Server general settings
  * address: address of the server
  * port: port of the app
3. database: database connection URI
4. minecraft: Minecraft general settings
  * path: path to the Minecraft launcher.jar
  * connection_file: path to the connection file
  * server_file: path to the server file
5. java: Java general settings
  * path: path to the Java interpreter
