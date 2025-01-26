#!/usr/bin/env python3
from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

def verify_processing():
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")
    
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        with driver.session() as session:
            # Query all concepts
            print("\n=== Concepts ===")
            concepts_query = """
            MATCH (c:Concept)
            RETURN c
            """
            result = session.run(concepts_query)
            for record in result:
                concept = record['c']
                print("\nConcept:")
                for key, value in concept.items():
                    print(f"{key}: {value}")

            # Query all relationships
            print("\n=== Relationships ===")
            relationships_query = """
            MATCH (c1:Concept)-[r:RELATES_TO]->(c2:Concept)
            RETURN c1.name as source, type(r) as type, r as relationship, c2.name as target
            """
            result = session.run(relationships_query)
            for record in result:
                print(f"\nRelationship from {record['source']} to {record['target']}:")
                for key, value in record['relationship'].items():
                    print(f"{key}: {value}")

            # Query hierarchical structure
            print("\n=== Hierarchy ===")
            hierarchy_query = """
            MATCH (c:Concept)
            WHERE c.hierarchy_parent IS NOT NULL
            RETURN c.name as concept, c.hierarchy_parent as parent, c.hierarchy_level as level
            ORDER BY c.hierarchy_level
            """
            result = session.run(hierarchy_query)
            for record in result:
                print(f"Concept: {record['concept']}, Parent: {record['parent']}, Level: {record['level']}")

        driver.close()
        return True
    except Exception as e:
        print(f"Verification failed: {e}")
        return False

if __name__ == "__main__":
    verify_processing()
