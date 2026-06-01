from enum import Enum

class DBConnectivity(str, Enum):
    MSSQL    = "MSSQL"
    MYSQL    = "MYSQL"
    POSTGRES = "POSTGRES"
    SQLITE   = "SQLITE"