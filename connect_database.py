from neo4j import GraphDatabase

uri = "neo4j+s://aa34ac88.databases.neo4j.io"
username = "neo4j"
password = "fce97o3OIGmdnbSzAjFnYOtXbjyKN_ip_8tb2D8byx0"

driver = GraphDatabase.driver(uri, auth=(username, password))