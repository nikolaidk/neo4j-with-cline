# Azure DevOps Boards Knowledge Graph

A graph-based analysis system for Azure DevOps Boards documentation using Neo4j and Deepseek AI. The system processes documentation into a rich knowledge graph with enhanced metadata for concepts and relationships.

## Features

### Enhanced Concept Extraction
- Confidence scoring for extracted concepts
- Source location tracking with context preservation
- Hierarchical concept classification
- Version tracking for concept evolution
- Reference tracking and linking

### Rich Relationship Metadata
- Bidirectional strength scoring
- Temporal tracking (first/last seen)
- Relationship classification (category, directness, strength)
- Provenance tracking with source context
- Confidence scoring for relationships

### Intelligent Context Handling
- Enhanced rolling context window
- Confidence-based filtering
- Hierarchical context preservation
- Parent-child relationship tracking

## Setup

### Prerequisites
- Python 3.10+
- Docker and Docker Compose
- Neo4j (automatically configured via Docker)

### Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd knowledge-graph-project
```

2. Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install neo4j python-dotenv
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your settings:
# - DEEPSEEK_API_KEY
# - NEO4J_PASSWORD (default: graphpassword)
```

5. Start Neo4j:
```bash
docker-compose up -d
```

## Usage

### Process Documentation
```bash
python3 process_document.py path/to/document.md
```

### Test Connection and Schema
```bash
python3 test_connection.py
```

### Verify Processing Results
```bash
python3 verify_processing.py
```

## Data Structure

### Concept Metadata
```json
{
    "name": "concept_name",
    "type": "concept_type",
    "description": "description",
    "confidence": 0.95,
    "source": {
        "position": 1234,
        "context": "surrounding text"
    },
    "hierarchy": {
        "parent": "parent_concept",
        "level": 1
    },
    "version": 1,
    "references": ["related_concept"]
}
```

### Relationship Metadata
```json
{
    "type": "relationship_type",
    "metadata": {
        "confidence": 0.90,
        "bidirectional_strength": {
            "forward": 0.85,
            "backward": 0.75
        },
        "temporal": {
            "first_seen": "timestamp",
            "last_seen": "timestamp"
        },
        "classification": {
            "category": "dependency",
            "directness": "direct",
            "strength": "strong"
        },
        "provenance": {
            "source_context": "contextual information",
            "extraction_method": "deepseek_analysis"
        }
    }
}
```

## Project Structure

The project uses a dedicated `neo4j` directory for all Neo4j-related data:
```
neo4j/
├── data/                 # Database files and system data
│   ├── databases/       # Neo4j and system databases
│   ├── dbms/           # Database management files (auth.ini)
│   └── transactions/   # Transaction logs
├── logs/                # Log files
│   ├── debug.log       # Debug information
│   ├── http.log        # HTTP API access logs
│   ├── neo4j.log       # Main database logs
│   ├── query.log       # Query execution logs
│   └── security.log    # Security-related logs
├── import/              # Import directory for data files
└── plugins/             # Neo4j plugins directory
```

This organization keeps all Neo4j data within the project structure for better portability and easier backups. Each directory serves a specific purpose:

### Data Directory (`neo4j/data/`)
- `databases/`: Contains the main Neo4j database files and system database
- `dbms/`: Stores database management files including authentication configuration
- `transactions/`: Maintains transaction logs for data consistency

### Logs Directory (`neo4j/logs/`)
- `debug.log`: Detailed debugging information
- `http.log`: HTTP API access and operations
- `neo4j.log`: Main database operations and status
- `query.log`: Cypher query execution logs
- `security.log`: Security-related events and authentication

### Import Directory (`neo4j/import/`)
Used for importing external data files into Neo4j. This directory is accessible to the Neo4j container for bulk data imports.

### Plugins Directory (`neo4j/plugins/`)
Reserved for Neo4j plugins and extensions. Add any custom plugins or extensions here before starting the container.

Note: The `import` and `plugins` directories are owned by the Neo4j user inside the container, which is why you might see "Permission denied" when trying to list their contents from the host system. This is normal and ensures proper security isolation.

## Testing

1. Basic connection test:
```bash
python3 test_connection.py
```

2. Process test document:
```bash
python3 process_document.py test_doc.md
```

3. Verify results:
```bash
python3 verify_processing.py
```

## Maintenance

### Clear Neo4j Data
```bash
docker-compose down -v
docker-compose up -d
```

### View Logs
```bash
docker logs devops-boards-neo4j
```

### Access Neo4j Browser
Open http://localhost:7474 in your browser
- Default username: neo4j
- Default password: graphpassword

## Schema Validation

The system uses XML schema validation to ensure data integrity:
- Validates concept structure
- Validates relationship metadata
- Ensures consistent data format

See `schema.xsd` for the complete schema definition.
