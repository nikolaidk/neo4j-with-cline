# Large Document Graph Analysis Architecture

## Overview
This document outlines the architecture for processing and analyzing large documentation files, specifically targeting `/home/nmr/demosql/cline_docs/azure-devops-boards-azure-devops.md`. The system uses Deepseek's AI capabilities to create a knowledge graph representing relationships and dependencies within extensive documentation, with emphasis on structured XML output for reliable parsing.

## Document Characteristics
- Large markdown file containing Azure DevOps Boards documentation
- Complex hierarchical structure
- Multiple interconnected concepts and relationships
- Extensive technical content

## AI Integration with Structured Output

### Deepseek Configuration for XML Output
```python
from openai import OpenAI
from dotenv import load_dotenv
import os
import xml.etree.ElementTree as ET

load_dotenv()

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

def analyze_chunk(chunk, context):
    # Request structured XML output
    system_prompt = """
    Analyze technical documentation and return results in the following XML format:
    <analysis>
        <concepts>
            <concept>
                <name>concept_name</name>
                <type>concept_type</type>
                <description>description</description>
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
                <properties>
                    <property name="strength">value</property>
                </properties>
            </relationship>
        </relationships>
    </analysis>
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
    """Parse the XML response into structured data for Neo4j"""
    root = ET.fromstring(xml_content)
    
    # Extract concepts
    concepts = []
    for concept in root.findall('./concepts/concept'):
        concepts.append({
            'name': concept.find('name').text,
            'type': concept.find('type').text,
            'description': concept.find('description').text,
            'references': [ref.text for ref in concept.findall('./references/reference')]
        })
    
    # Extract relationships
    relationships = []
    for rel in root.findall('./relationships/relationship'):
        relationships.append({
            'source': rel.find('source').text,
            'type': rel.find('type').text,
            'target': rel.find('target').text,
            'properties': {
                prop.get('name'): prop.text
                for prop in rel.findall('./properties/property')
            }
        })
    
    return {'concepts': concepts, 'relationships': relationships}
```

### XML Schema Definition
```xml
<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
    <xs:element name="analysis">
        <xs:complexType>
            <xs:sequence>
                <xs:element name="concepts">
                    <xs:complexType>
                        <xs:sequence>
                            <xs:element name="concept" maxOccurs="unbounded">
                                <xs:complexType>
                                    <xs:sequence>
                                        <xs:element name="name" type="xs:string"/>
                                        <xs:element name="type" type="xs:string"/>
                                        <xs:element name="description" type="xs:string"/>
                                        <xs:element name="references">
                                            <xs:complexType>
                                                <xs:sequence>
                                                    <xs:element name="reference" type="xs:string" maxOccurs="unbounded"/>
                                                </xs:sequence>
                                            </xs:complexType>
                                        </xs:element>
                                    </xs:sequence>
                                </xs:complexType>
                            </xs:element>
                        </xs:sequence>
                    </xs:complexType>
                </xs:element>
                <xs:element name="relationships">
                    <xs:complexType>
                        <xs:sequence>
                            <xs:element name="relationship" maxOccurs="unbounded">
                                <xs:complexType>
                                    <xs:sequence>
                                        <xs:element name="source" type="xs:string"/>
                                        <xs:element name="type" type="xs:string"/>
                                        <xs:element name="target" type="xs:string"/>
                                        <xs:element name="properties">
                                            <xs:complexType>
                                                <xs:sequence>
                                                    <xs:element name="property" maxOccurs="unbounded">
                                                        <xs:complexType>
                                                            <xs:simpleContent>
                                                                <xs:extension base="xs:string">
                                                                    <xs:attribute name="name" type="xs:string"/>
                                                                </xs:extension>
                                                            </xs:simpleContent>
                                                        </xs:complexType>
                                                    </xs:element>
                                                </xs:sequence>
                                            </xs:complexType>
                                        </xs:element>
                                    </xs:sequence>
                                </xs:complexType>
                            </xs:element>
                        </xs:sequence>
                    </xs:complexType>
                </xs:element>
            </xs:sequence>
        </xs:complexType>
    </xs:element>
</xs:schema>
```

## Processing Pipeline

### 1. Document Streaming
```python
def process_document_stream(file_path):
    current_context = []
    
    with open(file_path, 'r') as file:
        for chunk in chunk_iterator(file):
            # Get XML analysis for chunk
            xml_result = analyze_chunk(chunk, get_context(current_context))
            
            # Parse XML and update Neo4j
            update_graph_from_xml(xml_result)
            
            # Update rolling context
            update_context(current_context, xml_result)
```

### 2. XML to Neo4j Conversion
```python
def update_graph_from_xml(xml_result):
    # Create nodes from concepts
    for concept in xml_result['concepts']:
        create_concept_node(concept)
    
    # Create relationships
    for relationship in xml_result['relationships']:
        create_relationship(relationship)
```

## Infrastructure Setup

### Neo4j Directory Structure and Organization

The system uses a dedicated directory structure for Neo4j data organization:

```
neo4j/
├── data/                 # Database files and system data
│   ├── databases/       # Neo4j and system databases
│   │   ├── neo4j/      # Main database files
│   │   └── system/     # System database files
│   ├── dbms/           # Database management files
│   │   └── auth.ini    # Authentication configuration
│   └── transactions/   # Transaction logs
│       ├── neo4j/      # Main database transactions
│       └── system/     # System database transactions
├── logs/                # Log files
│   ├── debug.log       # Debug information
│   ├── http.log        # HTTP API access logs
│   ├── neo4j.log       # Main database logs
│   ├── query.log       # Query execution logs
│   └── security.log    # Security-related logs
├── import/              # Import directory for data files
└── plugins/             # Neo4j plugins directory
```

### Neo4j Docker Configuration
```yaml
services:
  neo4j:
    image: neo4j:latest
    container_name: ${NEO4J_CONTAINER_NAME}
    ports:
      - "7474:7474"  # HTTP
      - "7687:7687"  # Bolt
    environment:
      - NEO4J_AUTH=neo4j/graphpassword
      - NEO4J_dbms_memory_heap_max__size=4G
      - NEO4J_dbms_memory_pagecache_size=1G
    volumes:
      - ./neo4j/data:/data
      - ./neo4j/logs:/logs
      - ./neo4j/import:/var/lib/neo4j/import
      - ./neo4j/plugins:/plugins
    healthcheck:
      test: ["CMD-SHELL", "wget --no-verbose --tries=1 --spider localhost:7474 || exit 1"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
```

### Data Organization

1. Database Files (`neo4j/data/databases/`)
   - Main database files in `neo4j/` subdirectory
   - System database files in `system/` subdirectory
   - Property stores, relationship stores, and schema information
   - Transaction logs for data consistency

2. Log Management (`neo4j/logs/`)
   - Structured logging with different log files for different purposes
   - Debug logs for detailed troubleshooting
   - HTTP logs for API monitoring
   - Query logs for performance analysis
   - Security logs for access monitoring

3. Import Directory (`neo4j/import/`)
   - Dedicated directory for data import operations
   - Accessible to Neo4j container for bulk imports
   - Managed by Neo4j user for security

4. Plugin Management (`neo4j/plugins/`)
   - Directory for Neo4j extensions
   - Custom plugins can be added before container start
   - Managed by Neo4j user for security

### Graph Database Integration
```python
from neo4j import GraphDatabase

class Neo4jConnection:
    def __init__(self):
        self.uri = "bolt://localhost:7687"
        self.auth = ("neo4j", os.getenv("NEO4J_PASSWORD"))
        self.driver = GraphDatabase.driver(self.uri, auth=self.auth)

    def create_concept_node(self, concept):
        query = """
        MERGE (c:Concept {name: $name})
        SET c.type = $type,
            c.description = $description
        """
        with self.driver.session() as session:
            session.run(query, concept)

    def create_relationship(self, rel):
        query = """
        MATCH (source:Concept {name: $source})
        MATCH (target:Concept {name: $target})
        CREATE (source)-[r:$type]->(target)
        SET r += $properties
        """
        with self.driver.session() as session:
            session.run(query, rel)
```

## Validation and Error Handling

### XML Validation
```python
def validate_xml_response(xml_content, schema_path):
    schema = ET.XMLSchema(file=schema_path)
    parser = ET.XMLParser(schema=schema)
    try:
        ET.fromstring(xml_content, parser)
        return True
    except ET.XMLSyntaxError as e:
        log_error(f"XML validation failed: {e}")
        return False
```

### Error Recovery
```python
def process_with_recovery(chunk, retries=3):
    for attempt in range(retries):
        try:
            xml_result = analyze_chunk(chunk, context)
            if validate_xml_response(xml_result):
                return xml_result
        except Exception as e:
            log_error(f"Attempt {attempt + 1} failed: {e}")
            time.sleep(2 ** attempt)  # Exponential backoff
    
    raise ProcessingError("Failed to process chunk after multiple attempts")
```

## Deployment Steps

1. **Setup Environment**
```bash
# Create project directory and environment
mkdir -p knowledge-graph-project
cd knowledge-graph-project
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install neo4j openai python-dotenv lxml
```

2. **Start Infrastructure**
```bash
# Start Neo4j container
docker-compose up -d

# Verify deployment
curl http://localhost:7474
```

3. **Run Processing Pipeline**
```bash
# Execute the processing script
python process_document.py /home/nmr/demosql/cline_docs/azure-devops-boards-azure-devops.md
```

## Monitoring and Maintenance

1. **Health Checks**
   - XML validation status
   - Neo4j connection status
   - Processing pipeline progress

2. **Performance Metrics**
   - Processing speed
   - Memory usage
   - Graph size and complexity

## Security and Backup

1. **Data Protection**
   - Regular XML schema validation
   - Graph consistency checks
   - Automated backups

2. **Access Control**
   - Neo4j authentication
   - API key rotation
   - Network security

## Future Enhancements

1. **Processing Improvements**
   - Enhanced XML schema
   - Parallel processing
   - Incremental updates

2. **Feature Additions**
   - Advanced querying
   - Visualization tools
   - Export capabilities
