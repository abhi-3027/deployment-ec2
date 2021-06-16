# Professional-project
flask backend with mysql database

1. Clone this repository.
# Install required Python packages
   $ pip install -r requirements.txt
# Config and start webservice
#### Configure MySQL settings
In app.py file, fill in your real MySQL connection settings

_DB_CONF = {
 'host':'<YOUR-MYSQL-HOST>',
 'port':3306,
 'user':'<YOUR-MYSQL-USERNAME>',
 'passwd':'<YOUR-MYSQL-PASSWORD>',
 'db':'<YOUR-MYSQL-DATABASE>'
}

### To start mysql server
*mysqld --console* 

### To run flask server
*python app.py*
