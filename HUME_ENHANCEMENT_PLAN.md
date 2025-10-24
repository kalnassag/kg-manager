# Product Enhancement Plan: Hume-Inspired Features
## Building on Product Knowledge Graph Manager

Based on research of GraphAware Hume, this plan outlines enhancements to transform our current knowledge graph manager into a more powerful analytics platform.

---

## Current State (What We Have)

✅ **Core Functionality**
- Entity-type agnostic design with auto-discovery
- Full CRUD operations (Create, Read, Update, Delete)
- Flexible entity ID support (works with any property)
- Dynamic property grouping by prefix patterns
- Relationship navigation and exploration
- Professional UI with light blue/white theme

✅ **Visualization**
- Interactive graph visualization using Cytoscape.js
- Multiple layout algorithms (force-directed, circle, grid, hierarchy)
- Click to select, double-click to expand
- Filter by entity type
- Basic search functionality
- Color-coded nodes by type
- Info panel with node details

---

## Phase 1: Visual Query Builder (High Priority)

### Overview
Allow users to build complex graph queries visually without writing Cypher.

### Key Features

#### 1.1 Pattern Builder Interface
**Goal**: Drag-and-drop query construction

**Components**:
- **Node palette**: Drag node types (Laptop, Brand, CPU, etc.) onto canvas
- **Relationship connector**: Draw lines between nodes to define relationships
- **Property filters**: Add conditions to nodes/edges (e.g., "price > 1000")
- **Path builder**: Define multi-hop patterns visually
- **Optional paths**: Mark certain paths as optional (OPTIONAL MATCH)

**UI Design**:
```
+----------------------------------+
|  Pattern Builder                 |
|  [Node Types] [Relationships]    |
|                                  |
|  Canvas:                         |
|  [Laptop] --MADE_BY--> [Brand]  |
|     ↓                             |
|  [CPUModel]                      |
|                                  |
|  Filters:                        |
|  • Laptop.price > 1000           |
|  • Brand.name = "HP"             |
|                                  |
|  [Run Query] [Save Pattern]      |
+----------------------------------+
```

**Technical Implementation**:
- New route: `/query-builder`
- React-like component or vanilla JS with drag-drop API
- Generate Cypher from visual pattern
- Execute and visualize results
- Save patterns to database

**Database Schema**:
```cypher
(:SavedPattern {
  id: string,
  name: string,
  description: string,
  pattern_json: string,  // Serialized visual pattern
  cypher_query: string,  // Generated Cypher
  created_by: string,
  created_at: datetime
})
```

#### 1.2 Query Export & Reuse
**Goal**: Save and share queries

**Features**:
- View generated Cypher query
- Copy to clipboard
- Save pattern with name and description
- Load saved patterns
- Share patterns with team (future: user management)

**API Endpoints**:
```python
POST   /api/patterns/save
GET    /api/patterns/list
GET    /api/patterns/{id}
DELETE /api/patterns/{id}
POST   /api/patterns/{id}/execute
```

#### 1.3 Smart Filters with Value Lists
**Goal**: Easier filtering with suggestions

**Features**:
- Auto-suggest property values as user types
- Dropdown menus for common properties
- Date range pickers for temporal properties
- Numeric sliders for ranges

**Implementation**:
```python
# Get unique values for a property
GET /api/properties/{label}/{property}/values
# Returns: ["HP", "Dell", "ASUS", "Lenovo", ...]
```

---

## Phase 2: Advanced Expand (High Priority)

### Overview
Enhanced node expansion with filters and multi-hop exploration.

### Key Features

#### 2.1 Configurable Expansion
**Goal**: Control what gets expanded

**Features**:
- **Relationship type filter**: Choose which relationships to expand
- **Depth control**: Expand 1, 2, 3+ hops
- **Direction**: Incoming, outgoing, or both
- **Node type filter**: Only expand to certain node types
- **Property filters**: Only expand to nodes matching criteria

**UI Design**:
```
+--------------------------------+
| Expand Node: HP EliteBook      |
|                                |
| Depth: [1] [2] [3] [Custom]   |
|                                |
| Relationships:                 |
| ☑ MADE_BY                     |
| ☑ HAS_CPU                     |
| ☐ HAS_COLOR                   |
|                                |
| Node Types:                    |
| ☑ Brand                       |
| ☑ CPUModel                    |
| ☐ Color                       |
|                                |
| Filters:                       |
| + Add filter                   |
|                                |
| [Expand] [Cancel]              |
+--------------------------------+
```

**Technical Implementation**:
- Modal dialog for expansion options
- Build dynamic Cypher based on selections
- Animate new nodes appearing
- Highlight newly added nodes

**API Enhancement**:
```python
POST /api/graph/expand-advanced
{
  "label": "Laptop",
  "entity_id": "elitebook-630",
  "depth": 2,
  "relationships": ["MADE_BY", "HAS_CPU"],
  "node_types": ["Brand", "CPUModel"],
  "direction": "both",
  "filters": [
    {"property": "price", "operator": ">", "value": 1000}
  ]
}
```

#### 2.2 Path Highlighting
**Goal**: Show paths between nodes

**Features**:
- Find shortest path between two nodes
- Find all paths up to depth N
- Highlight path on graph
- Show path details (nodes and relationships)

**Implementation**:
```python
GET /api/graph/path/{label1}/{id1}/{label2}/{id2}
# Returns all paths between two nodes
```

---

## Phase 3: Perspectives & Access Control (Medium Priority)

### Overview
Multiple views of the same data for different users/purposes.

### Key Features

#### 3.1 Perspective Definition
**Goal**: Create filtered views of the graph

**Features**:
- **Name and description**: "Executive View", "Technical View"
- **Node type filters**: Only show certain entity types
- **Property filters**: Hide sensitive properties
- **Relationship filters**: Only show certain relationships
- **Virtual relationships**: Create shortcuts (e.g., Laptop-[BRAND]->Brand becomes Laptop.brand property)

**Database Schema**:
```cypher
(:Perspective {
  id: string,
  name: string,
  description: string,
  node_types: [string],      // Allowed node types
  properties_hidden: [string],  // Hidden properties
  relationships: [string],   // Allowed relationships
  created_by: string,
  is_default: boolean
})
```

**UI**:
- Perspective selector dropdown in header
- "Manage Perspectives" page
- Create/Edit/Delete perspectives
- Set default perspective

#### 3.2 User Roles & Permissions (Future)
**Goal**: Control who sees what

**Features**:
- User authentication (OAuth, JWT)
- Role-based access control (Admin, Analyst, Viewer)
- Assign perspectives to roles
- Audit logging

---

## Phase 4: Alerting & Monitoring (Medium Priority)

### Overview
Automated detection of patterns and changes in the graph.

### Key Features

#### 4.1 Alert Definitions
**Goal**: Define conditions that trigger notifications

**Alert Types**:
1. **Threshold Alerts**: "Notify when products > $5000 exceed 100 items"
2. **Pattern Alerts**: "Notify when new Laptop-[MADE_BY]->Brand connection created"
3. **Change Alerts**: "Notify when any property changes on entity X"
4. **Schedule Alerts**: "Daily report of new entities added"

**Database Schema**:
```cypher
(:Alert {
  id: string,
  name: string,
  description: string,
  type: string,  // threshold, pattern, change, schedule
  pattern: string,  // Cypher query or pattern
  enabled: boolean,
  email_to: [string],
  created_at: datetime,
  last_triggered: datetime,
  trigger_count: integer
})

(:AlertHistory {
  id: string,
  alert_id: string,
  triggered_at: datetime,
  matched_entities: [string],
  details: string
})
```

**UI Components**:
- "Alerts" page in navigation
- Create alert wizard
- Alert history/log
- Test alert functionality
- Enable/disable alerts

**Technical Implementation**:
```python
# Background task (Celery, APScheduler, or simple cron)
class AlertMonitor:
    def check_alerts(self):
        # Get all enabled alerts
        # Execute each alert query
        # Check if results changed
        # Send notifications if triggered
        pass
```

#### 4.2 Notification System
**Goal**: Deliver alerts to users

**Channels**:
- Email notifications
- In-app notifications (bell icon with badge)
- Webhook to external systems (Slack, Teams)

---

## Phase 5: Collaboration Features (Low Priority)

### Overview
Enable teams to work together on graph analysis.

### Key Features

#### 5.1 Snapshots & Sharing
**Goal**: Save and share graph views

**Features**:
- **Save snapshot**: Capture current graph view (nodes, layout, filters)
- **Share link**: Generate shareable URL
- **Live vs Static**: Live snapshots update as data changes
- **Annotations**: Add notes/comments to nodes on snapshot
- **Collections**: Organize snapshots into folders

**Database Schema**:
```cypher
(:Snapshot {
  id: string,
  name: string,
  description: string,
  graph_data: string,  // JSON of nodes/edges
  layout: string,      // Layout algorithm used
  filters: string,     // Applied filters
  is_live: boolean,
  created_by: string,
  created_at: datetime,
  share_token: string  // For sharing
})

(:Annotation {
  id: string,
  snapshot_id: string,
  node_id: string,
  text: string,
  created_by: string,
  created_at: datetime
})
```

**UI**:
- "Save Snapshot" button in graph toolbar
- "My Snapshots" page
- Share dialog with copy link button
- View snapshot page (read-only or live)

#### 5.2 Shared Actions
**Goal**: Reusable one-click queries

**Features**:
- **Action definition**: Name, icon, Cypher query
- **Parameters**: Allow user input when running action
- **Categories**: Organize actions by category
- **Share with team**: Make actions available to others

**Example Actions**:
- "Find all laptops by brand" (parameter: brand name)
- "Show competitor comparison" (parameter: product ID)
- "Load complete product specs" (parameter: product ID)

---

## Phase 6: Advanced Analytics (Low Priority)

### Overview
Built-in graph algorithms and insights.

### Key Features

#### 6.1 Graph Algorithms
**Goal**: Discover patterns automatically

**Algorithms**:
- **Centrality**: Find most important nodes (PageRank, Betweenness)
- **Community Detection**: Find clusters (Louvain, Label Propagation)
- **Similarity**: Find similar products (Jaccard, Cosine)
- **Path Finding**: Shortest path, all paths

**UI**:
- "Analytics" menu item
- Select algorithm and parameters
- Run on current graph or full database
- Visualize results (color nodes by community, size by centrality)

**Technical**:
- Use Neo4j Graph Data Science library
- Or implement algorithms in Python (NetworkX)

#### 6.2 Temporal Analysis
**Goal**: Analyze changes over time

**Features**:
- Timeline view of graph evolution
- "Rewind" to see graph at point in time
- Diff view showing what changed
- Trend analysis

**Requirements**:
- Temporal properties (created_at, updated_at)
- Version history in database

---

## Implementation Priority

### MVP (Minimum Viable Product) - 2-3 weeks
1. ✅ **Visual Query Builder Basic** (1 week)
   - Node and relationship selection
   - Simple filters
   - Execute and visualize

2. ✅ **Advanced Expand Enhanced** (1 week)
   - Depth and relationship filters
   - Direction control
   - Node type filtering

3. ✅ **Saved Patterns** (3 days)
   - Save/load patterns
   - View generated Cypher
   - Pattern library

### Phase 2 - 2-3 weeks
4. **Perspectives Basic** (1 week)
   - Create perspectives
   - Filter by node types
   - Perspective selector

5. **Snapshots** (1 week)
   - Save graph view
   - Share link
   - View snapshot page

6. **Alerts Basic** (1 week)
   - Pattern alerts
   - Email notifications
   - Alert management UI

### Phase 3 - 2-3 weeks
7. **Advanced Filters** (4 days)
   - Value lists with autocomplete
   - Date pickers
   - Numeric ranges

8. **Shared Actions** (3 days)
   - Define actions
   - Execute actions
   - Action library

9. **Path Analysis** (1 week)
   - Find paths between nodes
   - Path highlighting
   - Path details

### Future Enhancements
10. User authentication & permissions
11. Graph algorithms
12. Temporal analysis
13. API for external integrations
14. Mobile app

---

## Technical Architecture

### New Components Needed

**Backend (Python/FastAPI)**:
```
backend/
├── patterns/
│   ├── builder.py         # Pattern to Cypher converter
│   ├── storage.py         # Save/load patterns
│   └── validator.py       # Validate patterns
├── alerts/
│   ├── monitor.py         # Background alert checker
│   ├── notifier.py        # Send notifications
│   └── scheduler.py       # Schedule checks
├── perspectives/
│   ├── manager.py         # Perspective CRUD
│   └── filter.py          # Apply perspective filters
├── snapshots/
│   ├── storage.py         # Save/load snapshots
│   └── share.py           # Generate share links
└── analytics/
    ├── algorithms.py      # Graph algorithms
    └── paths.py          # Path finding
```

**Frontend (HTML/JS)**:
```
static/js/
├── query-builder.js       # Visual query builder
├── advanced-expand.js     # Enhanced expansion
├── pattern-library.js     # Saved patterns UI
├── alerts.js             # Alert management
├── snapshots.js          # Snapshot functionality
└── perspectives.js       # Perspective selector

templates/
├── query-builder.html
├── alerts.html
├── patterns.html
├── snapshots.html
└── perspectives.html
```

**Database Extensions**:
```cypher
// New node types for features
CREATE (p:SavedPattern)
CREATE (a:Alert)
CREATE (s:Snapshot)
CREATE (p:Perspective)
CREATE (a:Action)
CREATE (an:Annotation)
```

---

## Success Metrics

### User Engagement
- % of users using visual query builder vs manual search
- Average queries per session
- Most used saved patterns
- Alert effectiveness (true positives vs false positives)

### Performance
- Query execution time < 2 seconds for 90% of queries
- Graph rendering < 1 second for graphs up to 500 nodes
- Alert check frequency (every 5 minutes without impact)

### Adoption
- Number of saved patterns created
- Number of active alerts
- Number of snapshots shared
- Perspectives created per team

---

## Risk Assessment

### Technical Risks
- **Complex queries may timeout**: Mitigation - Query timeout limits, optimization
- **Large graphs may not render**: Mitigation - Pagination, subgraph sampling
- **Alert spam**: Mitigation - Rate limiting, smart aggregation

### User Experience Risks
- **Too complex for casual users**: Mitigation - Progressive disclosure, wizards
- **Feature overload**: Mitigation - Phased rollout, feature flags
- **Learning curve**: Mitigation - Interactive tutorials, examples

---

## Next Steps

1. **Review this plan** with stakeholders
2. **Prioritize features** based on user needs
3. **Create detailed specs** for Phase 1
4. **Set up development environment** for new components
5. **Begin implementation** with Visual Query Builder
6. **Iterate based on feedback**

---

## Conclusion

By implementing these Hume-inspired features, our Product Knowledge Graph Manager will evolve from a basic CRUD and visualization tool into a comprehensive graph analytics platform suitable for:

- **Business analysts** exploring product relationships
- **Data scientists** building complex queries visually
- **Product managers** monitoring changes and trends
- **Teams** collaborating on graph insights

The phased approach allows for incremental value delivery while managing complexity and risk.
