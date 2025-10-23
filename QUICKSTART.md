# Quick Start Guide

Get up and running with the Product Knowledge Graph Manager in 5 minutes.

## Prerequisites

- Python 3.8+
- Neo4j database running with data
- Neo4j credentials

## Steps

### 1. Install Dependencies

```bash
cd kg-manager
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure

```bash
cp config.yaml.template config.yaml
```

Edit `config.yaml` with your Neo4j credentials:

```yaml
neo4j:
  uri: "bolt://localhost:7687"
  user: "neo4j"
  password: "your_password_here"
```

### 3. Run

```bash
python run.py
```

### 4. Access

Open your browser:
```
http://localhost:8000
```

## That's It!

The application will automatically:
- Connect to your Neo4j database
- Discover all node types
- Create a browsable interface
- Enable full CRUD operations

## Next Steps

- Browse the dashboard to see your entity types
- Click on any product type to view entities
- Create, edit, or delete entities as needed
- Explore relationships between entities

## Troubleshooting

**Can't connect to Neo4j?**
- Check if Neo4j is running
- Verify your credentials in `config.yaml`
- Check the URI (default: `bolt://localhost:7687`)

**Empty dashboard?**
- Make sure your Neo4j database has data
- Check that nodes have an `_id` property

**Port already in use?**
- Change the port in `config.yaml` under `app.port`

For more details, see [README.md](README.md).
