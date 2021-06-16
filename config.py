class Config(object):
    DEBUG = False
    TESTING = False
    DATABASE_URI = 'sqlite://:memory:'
class ProductionConfig(Config):
    SECRET_KEY="b48d0632cb70ed951f88e4a99b1c35f168380a04ea01b861efc26709876067a7"
    SEND_FILE_MAX_AGE_DEFAULT = 0
    #mail server settings
    MAIL_SERVER='smtp.gmail.com'
    MAIL_PORT = 465
    MAIL_USERNAME = 'ctd.tiet.database@gmail.com'
    MAIL_PASSWORD = 'Password@123'
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    MAIL_DEFAULT_SENDER = 'ctd.tiet.database@gmail.com'
    #database connection settings
    MYSQL_HOST = 'ctd-db.cqk073dzxudb.us-east-2.rds.amazonaws.com'
    MYSQL_PORT = 3306
    MYSQL_USER = 'admin'
    MYSQL_PASSWORD = 'Admin_CTD_2021'
    MYSQL_DB = 'CTD_database'

class DevelopmentConfig(Config):
    ENV="development"
    SECRET_KEY="b48d0632cb70ed951f88e4a99b1c35f168380a04ea01b861efc26709876067a7"
    DEBUG = True
    MYSQL_HOST = 'localhost'
    MYSQL_PORT = 3306
    MYSQL_USER = 'admin_ctd'
    MYSQL_PASSWORD = 'ctd_admin_hy'
    MYSQL_DB = 'ctd_tiet'
class TestingConfig(Config):
    TESTING = True

