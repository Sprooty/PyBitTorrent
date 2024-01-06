import logging
import mysql.connector
from datetime import datetime
import uuid
from mysql.connector import pooling
# # Setup basic logging
# logging.basicConfig(level=logging.DEBUG)
# logger = logging.getLogger(__name__)

# Database Configuration
DB_CONFIG = {
    'host': '192.168.0.10',
    'user': 'root',
    'password': 'JJntJGHtgRsZGUwDmoknfGV4',
    'database': 'torworldTracker',
    'port': '32768',
    'pool_name': 'torrentmapper_pool',
    'pool_size': 32
}

# Create a connection pool
connection_pool = mysql.connector.pooling.MySQLConnectionPool(**DB_CONFIG)

def get_connection():
    """
    Get a connection from the connection pool.
    """
    return connection_pool.get_connection()


def insert_into_torrents_table(torrent_name, info_hash=None, magnet_link=None, site=None, category=None, date_inserted=None):
    connection = get_connection()
    cursor = connection.cursor()
    query = """
    INSERT INTO Torrents (TorrentName, InfoHash, MagnetLink, Site, Category, DateInserted)
    VALUES (%s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE TorrentName = VALUES(TorrentName)"""
    data = (torrent_name, info_hash, magnet_link, site, category, date_inserted or datetime.now())
    cursor.execute(query, data)
    connection.commit()
    
    # Get the last inserted id
    torrent_id = cursor.lastrowid
    cursor.close()
    connection.close()
    return torrent_id


# Function to check if a record exists in a table
def check_record_exists(table_name, condition):
    connection = get_connection()
    cursor = connection.cursor()
    query = f"SELECT EXISTS(SELECT 1 FROM {table_name} WHERE {condition})"
    cursor.execute(query)
    result = cursor.fetchone()[0]
    cursor.close()
    connection.close()
    return result


def insert_into_ips_table(ip, country=None):
    connection = get_connection()
    cursor = connection.cursor()
    query = """
    INSERT INTO IPs (IP, Country) VALUES (%s, %s)
    ON DUPLICATE KEY UPDATE Country = VALUES(Country)
    """
    data = (ip, country)
    cursor.execute(query, data)
    connection.commit()
    cursor.close()
    connection.close()

def insert_torrent_info(torrent_name, info_hash=None):
    connection = get_connection()
    cursor = connection.cursor()

    # Prepare the query. Note that TorrentID is not included in the columns list as it auto-increments.
    query = """INSERT INTO Torrents (TorrentName, InfoHash, MagnetLink, Site, Category, DateInserted)
               VALUES (%s, %s, NULL, NULL, NULL, NULL)
               ON DUPLICATE KEY UPDATE TorrentName = VALUES(TorrentName)"""
    
    # Execute the query. Set info_hash to None if not provided.
    cursor.execute(query, (torrent_name, info_hash))
    
    # Commit and close connection
    connection.commit()
    cursor.close()
    connection.close()

# Usage:
# torrent_name = self.torrent.file_name  # Or however you fetch the torrent name
# insert_torrent_name(torrent_name)

def insert_into_torrent_ips_table(torrent_id, ip):
    connection = get_connection()
    cursor = connection.cursor()
    query = """
    INSERT INTO Torrent_IPs (TorrentID, IP, Occurrences)
    VALUES (%s, %s, 1)
    ON DUPLICATE KEY UPDATE Occurrences = Occurrences + 1
    """
    data = (torrent_id, ip)
    cursor.execute(query, data)
    connection.commit()
    cursor.close()
    connection.close()

def get_null_country_ips():
    connection = get_connection()
    cursor = connection.cursor()
    query = "SELECT IP FROM IPs WHERE Country IS NULL"
    cursor.execute(query)
    ips = [item[0] for item in cursor.fetchall()]
    cursor.close()
    connection.close()
    return ips


def insert_enriched_ip_data(ip, country, country_code, region, city, latitude, longitude, timezone, isp, as_description, org):
    connection = get_connection()  # Make sure this gets your DB connection
    cursor = connection.cursor()

    query = """
    INSERT INTO IPs (IP, Country, CountryCode, Region, City, Latitude, Longitude, Timezone, ISP, ASDescription, Org)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE 
        Country = VALUES(Country), 
        CountryCode = VALUES(CountryCode),
        Region = VALUES(Region),
        City = VALUES(City),
        Latitude = VALUES(Latitude),
        Longitude = VALUES(Longitude),
        Timezone = VALUES(Timezone),
        ISP = VALUES(ISP),
        ASDescription = VALUES(ASDescription),
        Org = VALUES(Org)
    """

    data = (ip, country, country_code, region, city, latitude, longitude, timezone, isp, as_description, org)

    cursor.execute(query, data)
    connection.commit()
    cursor.close()
    connection.close()

