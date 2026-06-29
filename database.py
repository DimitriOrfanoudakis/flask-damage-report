from flask_mysqldb import MySQL

mysql = MySQL()

def init_db(app):
    #Initiate database connection with Flask app
    mysql.init_app(app)

