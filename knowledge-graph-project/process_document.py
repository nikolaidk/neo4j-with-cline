#!/usr/bin/env python3
from openai import OpenAI
from dotenv import load_dotenv
import os
from lxml import etree as ET
from neo4j import GraphDatabase
import time

# Load environment variables
load_dotenv()

# Initialize OpenAI client for Deepseek
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

class Neo4jConnection:
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.auth = (
            os.getenv("NEO4J_USER", "neo4j"),
            os.getenv("NEO4J_PASSWORD")
        )
        self.driver = None
        self.connect()

    def connect(self):
        """Establish connection to Neo4j"""
        try:
            if self.driver:
                self.driver.close()
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=self.auth,
                max_connection_lifetime=300  # 5 minutes
            )
            print("Connected to Neo4j")
        except Exception as e:
            print(f"Failed to connect to Neo4j: {e}")
            raise

    def execute_with_retry(self, operation, max_retries=3):
        """Execute Neo4j operation with retry logic"""
        for attempt in range(max_retries):
            try:
                with self.driver.session() as session:
                    return operation(session)
            except Exception as e:
                print(f"Neo4j operation failed (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    print("Attempting to reconnect...")
                    time.sleep(2 ** attempt)  # Exponential backoff
                    self.connect()
                else:
                    raise

    def create_concept_node(self, concept):
        """Create or update a concept node with enhanced metadata"""
        query = """
        MERGE (c:Concept {name: $name})
        SET c.type = $type,
            c.description = $description,
            c.confidence = $confidence,
            c.source_position = $source.position,
            c.source_context = $source.context,
            c.hierarchy_parent = $hierarchy.parent,
            c.hierarchy_level = $hierarchy.level,
            c.version = $version,
            c.references = $references
        """
        def operation(session):
            return session.run(query, concept)
        return self.execute_with_retry(operation)

    def create_relationship(self, rel):
        """Create a relationship between concepts with enhanced metadata"""
        query = """
        MATCH (source:Concept {name: $source})
        MATCH (target:Concept {name: $target})
        CREATE (source)-[r:RELATES_TO {
            type: $type,
            confidence: $metadata.confidence,
            forward_strength: $metadata.bidirectional_strength.forward,
            backward_strength: $metadata.bidirectional_strength.backward,
            first_seen: $metadata.temporal.first_seen,
            last_seen: $metadata.temporal.last_seen,
            category: $metadata.classification.category,
            directness: $metadata.classification.directness,
            strength: $metadata.classification.strength,
            source_context: $metadata.provenance.source_context,
            extraction_method: $metadata.provenance.extraction_method
        }]->(target)
        SET r += $properties
        """
        def operation(session):
            return session.run(query, rel)
        return self.execute_with_retry(operation)

    def __del__(self):
        """Cleanup connection on object destruction"""
        if self.driver:
            self.driver.close()

def validate_xml_response(xml_content, schema_path='schema.xsd'):
    """Validate XML against schema"""
    try:
        schema_doc = ET.parse(schema_path)
        schema = ET.XMLSchema(schema_doc)
        parser = ET.XMLParser(schema=schema)
        ET.fromstring(xml_content.encode('utf-8'), parser)
        return True
    except Exception as e:
        print(f"XML validation failed: {e}")
        return False

def analyze_chunk(chunk, context):
    """Process document chunk with Deepseek AI"""
    system_prompt = """
    Analyze technical documentation and return results in the following XML format:
    <analysis>
        <concepts>
            <concept>
                <name>concept_name</name>
                <type>concept_type</type>
                <description>description</description>
                <confidence>0.95</confidence>
                <source>
                    <position>1234</position>
                    <context>surrounding text for context</context>
                </source>
                <hierarchy>
                    <parent>parent_concept</parent>
                    <level>1</level>
                </hierarchy>
                <version>1</version>
                <references>
                    <reference>related_concept</reference>
                </references>
            </concept>
        </concepts>
        <relationships>
            <relationship>
                <source>source_concept</source>
                <type>relationship_type</type>
                <target>target_concept</target>
                <metadata>
                    <confidence>0.90</confidence>
                    <bidirectional_strength>
                        <forward>0.85</forward>
                        <backward>0.75</backward>
                    </bidirectional_strength>
                    <temporal>
                        <first_seen>2024-01-26T13:45:00Z</first_seen>
                        <last_seen>2024-01-26T13:45:00Z</last_seen>
                    </temporal>
                    <classification>
                        <category>dependency</category>
                        <directness>direct</directness>
                        <strength>strong</strength>
                    </classification>
                    <provenance>
                        <source_context>contextual information</source_context>
                        <extraction_method>deepseek_analysis</extraction_method>
                    </provenance>
                </metadata>
                <properties>
                    <property name="additional_info">value</property>
                </properties>
            </relationship>
        </relationships>
    </analysis>

    Guidelines for analysis:
    1. Assign confidence scores based on clarity and context
    2. Use hierarchical classification for concepts
    3. Track relationship directionality and strength
    4. Provide detailed context for provenance
    5. Classify relationships by type and directness
    """
    
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Context: {context}\n\nChunk: {chunk}"}
        ],
        stream=False
    )
    return parse_xml_response(response.choices[0].message.content)

def parse_xml_response(xml_content):
    """Parse XML response into structured data with enhanced metadata"""
    if not validate_xml_response(xml_content):
        raise ValueError("Invalid XML response")
    
    root = ET.fromstring(xml_content.encode('utf-8'))
    
    # Extract concepts with enhanced metadata
    concepts = []
    for concept in root.findall('./concepts/concept'):
        source_elem = concept.find('source')
        hierarchy_elem = concept.find('hierarchy')
        
        concepts.append({
            'name': concept.find('name').text,
            'type': concept.find('type').text,
            'description': concept.find('description').text,
            'confidence': float(concept.find('confidence').text),
            'source': {
                'position': int(source_elem.find('position').text),
                'context': source_elem.find('context').text
            },
            'hierarchy': {
                'parent': hierarchy_elem.find('parent').text if hierarchy_elem.find('parent') is not None else None,
                'level': int(hierarchy_elem.find('level').text)
            },
            'version': int(concept.find('version').text),
            'references': [ref.text for ref in concept.findall('./references/reference')]
        })
    
    # Extract relationships with enhanced metadata
    relationships = []
    for rel in root.findall('./relationships/relationship'):
        metadata_elem = rel.find('metadata')
        temporal_elem = metadata_elem.find('temporal')
        classification_elem = metadata_elem.find('classification')
        strength_elem = metadata_elem.find('bidirectional_strength')
        provenance_elem = metadata_elem.find('provenance')
        
        relationships.append({
            'source': rel.find('source').text,
            'type': rel.find('type').text,
            'target': rel.find('target').text,
            'metadata': {
                'confidence': float(metadata_elem.find('confidence').text),
                'bidirectional_strength': {
                    'forward': float(strength_elem.find('forward').text),
                    'backward': float(strength_elem.find('backward').text)
                },
                'temporal': {
                    'first_seen': temporal_elem.find('first_seen').text,
                    'last_seen': temporal_elem.find('last_seen').text
                },
                'classification': {
                    'category': classification_elem.find('category').text,
                    'directness': classification_elem.find('directness').text,
                    'strength': classification_elem.find('strength').text
                },
                'provenance': {
                    'source_context': provenance_elem.find('source_context').text,
                    'extraction_method': provenance_elem.find('extraction_method').text
                }
            },
            'properties': {
                prop.get('name'): prop.text
                for prop in rel.findall('./properties/property')
            }
        })
    
    return {'concepts': concepts, 'relationships': relationships}

def chunk_iterator(file_obj, chunk_size=1000):
    """Iterate over file in chunks"""
    buffer = []
    current_size = 0
    
    for line in file_obj:
        buffer.append(line)
        current_size += len(line)
        
        if current_size >= chunk_size:
            yield ''.join(buffer)
            buffer = []
            current_size = 0
    
    if buffer:
        yield ''.join(buffer)

def get_context(current_context, window_size=5):
    """Get enhanced rolling context window with metadata"""
    context_entries = []
    for entry in current_context[-window_size:]:
        context_entries.append(f"{entry['name']} ({entry['type']}): {entry['description']}")
        if entry.get('hierarchy', {}).get('parent'):
            context_entries.append(f"Parent: {entry['hierarchy']['parent']}")
    return '\n'.join(context_entries)

def update_context(current_context, xml_result, max_size=15):
    """Update rolling context with enhanced concept information"""
    for concept in xml_result['concepts']:
        # Only keep high-confidence concepts in context
        if concept['confidence'] >= 0.7:
            current_context.append({
                'name': concept['name'],
                'type': concept['type'],
                'description': concept['description'],
                'hierarchy': concept['hierarchy'],
                'confidence': concept['confidence']
            })
    
    # Maintain fixed context size, prioritizing high-confidence entries
    if len(current_context) > max_size:
        # Sort by confidence and keep top entries
        current_context.sort(key=lambda x: x['confidence'], reverse=True)
        current_context[:] = current_context[:max_size]

def process_with_recovery(chunk, context, retries=3):
    """Process chunk with retry mechanism"""
    for attempt in range(retries):
        try:
            xml_result = analyze_chunk(chunk, context)
            return xml_result
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                raise

def process_document(file_path):
    """Main document processing pipeline"""
    neo4j = Neo4jConnection()
    current_context = []
    
    print(f"Processing document: {file_path}")
    
    with open(file_path, 'r') as file:
        for chunk in chunk_iterator(file):
            try:
                # Process chunk with context
                xml_result = process_with_recovery(
                    chunk,
                    get_context(current_context)
                )
                
                # Update Neo4j
                for concept in xml_result['concepts']:
                    neo4j.create_concept_node(concept)
                
                for relationship in xml_result['relationships']:
                    neo4j.create_relationship(relationship)
                
                # Update rolling context
                update_context(current_context, xml_result)
                
                print("Chunk processed successfully")
                
            except Exception as e:
                print(f"Error processing chunk: {e}")
                continue

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python process_document.py <file_path>")
        sys.exit(1)
    
    process_document(sys.argv[1])
