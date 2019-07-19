# Kung Fu Chess
A Kung Fu chess server implementation (work in progress)

Uses Redis and MySQL which should be configured in config file.

MySQL on ubunutu requires additionally libmysqlclient-dev.

`sudo apt-get install libmysqlclient-dev`

The config file need to be configured with database name and relevant user name and password.
The script create.sql will create a database (named "kfchess") with the required tables for
the web interface.

