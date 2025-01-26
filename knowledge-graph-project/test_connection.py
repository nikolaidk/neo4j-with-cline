#!/usr/bin/env python3
from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

def test_connection():
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")
    
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        with driver.session() as session:
            # Test creating concept with enhanced metadata
            create_concept = """
            CREATE (c:Concept {
                name: 'TestConcept',
                type: 'test_type',
                description: 'Test description',
                confidence: 0.95,
                source_position: 123,
                source_context: 'Test context',
                hierarchy_parent: 'ParentConcept',
                hierarchy_level: 1,
                version: 1,
                references: ['ref1', 'ref2']
            })
            """
            session.run(create_concept)
            print("Created test concept")

            # Test creating relationship with enhanced metadata
            create_relationship = """
            CREATE (c1:Concept {name: 'TestConcept2'})
            WITH c1
            MATCH (c2:Concept {name: 'TestConcept'})
            CREATE (c1)-[r:RELATES_TO {
                type: 'test_relationship',
                confidence: 0.90,
                forward_strength: 0.85,
                backward_strength: 0.75,
                first_seen: datetime(),
                last_seen: datetime(),
                category: 'test_category',
                directness: 'direct',
                strength: 'strong',
                source_context: 'Test relationship context',
                extraction_method: 'test_extraction'
            }]->(c2)
            """
            session.run(create_relationship)
            print("Created test relationship")

            # Verify concept data
            verify_concept = """
            MATCH (c:Concept {name: 'TestConcept'})
            RETURN c
            """
            result = session.run(verify_concept)
            concept = result.single()['c']
            print("\nVerified Concept Data:")
            for key, value in concept.items():
                print(f"{key}: {value}")

            # Verify relationship data
            verify_relationship = """
            MATCH (c1:Concept {name: 'TestConcept2'})-[r:RELATES_TO]->(c2:Concept {name: 'TestConcept'})
            RETURN r
            """
            result = session.run(verify_relationship)
            relationship = result.single()['r']
            print("\nVerified Relationship Data:")
            for key, value in relationship.items():
                print(f"{key}: {value}")

            print("\nConnection and schema verification successful!")
        driver.close()
        return True
    except Exception as e:
        print(f"Test failed: {e}")
        return False

if __name__ == "__main__":
    test_connection()
