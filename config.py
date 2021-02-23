# .env
import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SQLALCHEMY_DATABASE_URI = 'postgres://jqfaanmd:xkQ9pPvrHz2cNeTxRcfrSxy6Ayq_uN_j@ziggy.db.elephantsql.com:5432/jqfaanmd'
    SQLALCHEMY_TRACK_MODIFICATIONS = False