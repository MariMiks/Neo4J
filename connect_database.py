from neo4j import GraphDatabase

uri = "neo4j+s://1f2572df.databases.neo4j.io"
username = "neo4j"
password = "ayTeBqrSUSX7b-CO2HjYaqYkdpAARcfkYXhHpgPDabw"

driver = GraphDatabase.driver(uri, auth=(username, password))