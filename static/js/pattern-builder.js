// Pattern Builder - Visual Query Builder for Neo4j Knowledge Graph

let currentPattern = {
    nodes: [],
    relationships: [],
    filters: []
};

let nodeTypes = [];
let relationshipTypes = [];
let canvasNodeCounter = 0;

// Initialize the pattern builder
async function initializeBuilder() {
    try {
        // Fetch available node types
        const nodeResponse = await fetch('/api/entity-types');
        const nodeData = await nodeResponse.json();
        nodeTypes = nodeData.entity_types || [];

        // Fetch available relationship types
        const relResponse = await fetch('/api/graph/relationships');
        const relData = await relResponse.json();
        relationshipTypes = relData.relationships || [];

        populatePalette();
    } catch (error) {
        console.error('Error initializing builder:', error);
    }
}

// Populate the node and relationship palette
function populatePalette() {
    const nodePalette = document.getElementById('node-palette');
    const relPalette = document.getElementById('relationship-palette');

    if (!nodePalette || !relPalette) return;

    // Clear existing items
    nodePalette.innerHTML = '';
    relPalette.innerHTML = '';

    // Add node types
    nodeTypes.forEach(nodeType => {
        const item = document.createElement('div');
        item.className = 'palette-item';
        item.draggable = true;
        item.dataset.type = 'node';
        item.dataset.label = nodeType.label;
        item.textContent = nodeType.label;

        item.addEventListener('dragstart', handleDragStart);
        item.addEventListener('dragend', handleDragEnd);

        nodePalette.appendChild(item);
    });

    // Add relationship types
    relationshipTypes.forEach(relType => {
        const item = document.createElement('div');
        item.className = 'palette-item';
        item.draggable = true;
        item.dataset.type = 'relationship';
        item.dataset.relType = relType;
        item.textContent = relType;

        item.addEventListener('dragstart', handleDragStart);
        item.addEventListener('dragend', handleDragEnd);

        relPalette.appendChild(item);
    });
}

// Drag and drop handlers
function handleDragStart(e) {
    e.target.classList.add('dragging');
    e.dataTransfer.effectAllowed = 'copy';
    e.dataTransfer.setData('text/plain', JSON.stringify({
        type: e.target.dataset.type,
        label: e.target.dataset.label,
        relType: e.target.dataset.relType
    }));
}

function handleDragEnd(e) {
    e.target.classList.remove('dragging');
}

// Setup canvas drop zone
function setupCanvas() {
    const canvas = document.getElementById('query-canvas');
    if (!canvas) return;

    canvas.addEventListener('dragover', (e) => {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'copy';
    });

    canvas.addEventListener('drop', (e) => {
        e.preventDefault();

        const data = JSON.parse(e.dataTransfer.getData('text/plain'));
        const rect = canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        if (data.type === 'node') {
            addNodeToCanvas(data.label, x, y);
        } else if (data.type === 'relationship') {
            // Relationships need to connect two nodes
            // For now, just show a message
            console.log('Drag relationship to connect two nodes');
        }

        generateCypher();
    });
}

// Add a node to the canvas
function addNodeToCanvas(label, x, y) {
    const canvas = document.getElementById('query-canvas');
    const placeholder = canvas.querySelector('.canvas-placeholder');
    if (placeholder) {
        placeholder.style.display = 'none';
    }

    const nodeId = `node_${canvasNodeCounter++}`;
    const variableName = label.charAt(0).toLowerCase() + (currentPattern.nodes.length || '');

    const nodeElement = document.createElement('div');
    nodeElement.className = 'canvas-node';
    nodeElement.dataset.nodeId = nodeId;
    nodeElement.dataset.label = label;
    nodeElement.dataset.variable = variableName;
    nodeElement.style.position = 'absolute';
    nodeElement.style.left = `${x}px`;
    nodeElement.style.top = `${y}px`;

    nodeElement.innerHTML = `
        <div class="node-header">
            <span class="node-label">${label}</span>
            <button class="node-delete" onclick="deleteCanvasNode('${nodeId}')">&times;</button>
        </div>
        <div class="node-body">
            <input type="text" class="node-variable" value="${variableName}"
                   onchange="updateNodeVariable('${nodeId}', this.value)"
                   placeholder="variable">
        </div>
        <div class="node-connectors">
            <div class="connector connector-in" data-node-id="${nodeId}"></div>
            <div class="connector connector-out" data-node-id="${nodeId}"></div>
        </div>
    `;

    canvas.appendChild(nodeElement);

    // Add to pattern
    currentPattern.nodes.push({
        id: nodeId,
        label: label,
        variable: variableName,
        properties: {}
    });

    // Make draggable
    makeNodeDraggable(nodeElement);
}

// Make node draggable within canvas
function makeNodeDraggable(element) {
    let isDragging = false;
    let currentX;
    let currentY;
    let initialX;
    let initialY;

    const header = element.querySelector('.node-header');

    header.addEventListener('mousedown', (e) => {
        isDragging = true;
        initialX = e.clientX - element.offsetLeft;
        initialY = e.clientY - element.offsetTop;
    });

    document.addEventListener('mousemove', (e) => {
        if (isDragging) {
            e.preventDefault();
            currentX = e.clientX - initialX;
            currentY = e.clientY - initialY;
            element.style.left = `${currentX}px`;
            element.style.top = `${currentY}px`;
        }
    });

    document.addEventListener('mouseup', () => {
        isDragging = false;
    });
}

// Delete node from canvas
function deleteCanvasNode(nodeId) {
    const element = document.querySelector(`[data-node-id="${nodeId}"]`);
    if (element) {
        element.remove();
    }

    // Remove from pattern
    currentPattern.nodes = currentPattern.nodes.filter(n => n.id !== nodeId);
    currentPattern.relationships = currentPattern.relationships.filter(
        r => r.from !== nodeId && r.to !== nodeId
    );

    // Show placeholder if no nodes
    const canvas = document.getElementById('query-canvas');
    const nodes = canvas.querySelectorAll('.canvas-node');
    if (nodes.length === 0) {
        const placeholder = canvas.querySelector('.canvas-placeholder');
        if (placeholder) {
            placeholder.style.display = 'block';
        }
    }

    generateCypher();
}

// Update node variable name
function updateNodeVariable(nodeId, newVariable) {
    const node = currentPattern.nodes.find(n => n.id === nodeId);
    if (node) {
        node.variable = newVariable;
        generateCypher();
    }
}

// Generate Cypher query from current pattern
function generateCypher() {
    let cypher = '';

    if (currentPattern.nodes.length === 0) {
        cypher = 'MATCH (n) RETURN n LIMIT 25';
    } else if (currentPattern.nodes.length === 1) {
        const node = currentPattern.nodes[0];
        cypher = `MATCH (${node.variable}:${node.label}) RETURN ${node.variable} LIMIT 25`;
    } else {
        // Multiple nodes - try to connect them
        const matches = [];
        currentPattern.nodes.forEach(node => {
            matches.push(`(${node.variable}:${node.label})`);
        });

        if (currentPattern.relationships.length > 0) {
            // Build path with relationships
            cypher = 'MATCH ' + buildPathPattern() + '\n';
            cypher += 'RETURN ' + currentPattern.nodes.map(n => n.variable).join(', ') + ' LIMIT 25';
        } else {
            // No explicit relationships - just match independently
            cypher = 'MATCH ' + matches.join(', ') + '\n';
            cypher += 'RETURN ' + currentPattern.nodes.map(n => n.variable).join(', ') + ' LIMIT 25';
        }
    }

    document.getElementById('cypher-output').textContent = cypher;
    return cypher;
}

// Build Cypher path pattern from relationships
function buildPathPattern() {
    if (currentPattern.relationships.length === 0) {
        return currentPattern.nodes.map(n => `(${n.variable}:${n.label})`).join(', ');
    }

    // For now, simple chain
    let pattern = '';
    const used = new Set();

    currentPattern.relationships.forEach((rel, idx) => {
        const fromNode = currentPattern.nodes.find(n => n.id === rel.from);
        const toNode = currentPattern.nodes.find(n => n.id === rel.to);

        if (idx === 0) {
            pattern += `(${fromNode.variable}:${fromNode.label})`;
        }

        pattern += `-[${rel.variable || 'r' + idx}:${rel.type}]->`;
        pattern += `(${toNode.variable}:${toNode.label})`;
    });

    return pattern;
}

// Copy Cypher to clipboard
async function copyCypher() {
    const cypher = document.getElementById('cypher-output').textContent;
    try {
        await navigator.clipboard.writeText(cypher);
        showMessage('Cypher query copied to clipboard!');
    } catch (error) {
        console.error('Failed to copy:', error);
    }
}

// Clear canvas
function clearCanvas() {
    if (!confirm('Clear the canvas? This will delete all nodes and relationships.')) {
        return;
    }

    const canvas = document.getElementById('query-canvas');
    const nodes = canvas.querySelectorAll('.canvas-node');
    nodes.forEach(node => node.remove());

    currentPattern = {
        nodes: [],
        relationships: [],
        filters: []
    };

    const placeholder = canvas.querySelector('.canvas-placeholder');
    if (placeholder) {
        placeholder.style.display = 'block';
    }

    generateCypher();
}

// Open query builder
function openQueryBuilder(patternId = null) {
    const modal = document.getElementById('query-builder-modal');
    modal.classList.add('active');

    if (!nodeTypes.length) {
        initializeBuilder();
    }

    setupCanvas();

    if (patternId) {
        loadPattern(patternId);
    } else {
        clearCanvas();
        document.getElementById('pattern-form').reset();
        document.getElementById('pattern-id').value = '';
    }
}

// Close query builder
function closeQueryBuilder() {
    const modal = document.getElementById('query-builder-modal');
    modal.classList.remove('active');
}

// Save pattern
async function savePattern(event) {
    event.preventDefault();

    const patternId = document.getElementById('pattern-id').value;
    const name = document.getElementById('pattern-name').value;
    const description = document.getElementById('pattern-description').value;
    const author = document.getElementById('pattern-author').value;
    const cypher = document.getElementById('cypher-output').textContent;

    const patternData = {
        name: name,
        description: description,
        pattern_json: JSON.stringify(currentPattern),
        cypher_query: cypher,
        created_by: author || 'Anonymous'
    };

    try {
        let response;
        if (patternId) {
            // Update existing pattern
            response = await fetch(`/api/patterns/${patternId}`, {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(patternData)
            });
        } else {
            // Create new pattern
            response = await fetch('/api/patterns/save', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(patternData)
            });
        }

        const result = await response.json();

        if (result.success) {
            showMessage('Pattern saved successfully!');
            closeQueryBuilder();
            setTimeout(() => location.reload(), 1000);
        } else {
            showMessage('Error saving pattern: ' + (result.error || 'Unknown error'), 'error');
        }
    } catch (error) {
        console.error('Error saving pattern:', error);
        showMessage('Error saving pattern: ' + error.message, 'error');
    }
}

// Load pattern for editing
async function loadPattern(patternId) {
    try {
        const response = await fetch(`/api/patterns/${patternId}`);
        const data = await response.json();

        if (data.pattern) {
            const pattern = data.pattern;

            document.getElementById('pattern-id').value = pattern.id;
            document.getElementById('pattern-name').value = pattern.name;
            document.getElementById('pattern-description').value = pattern.description || '';
            document.getElementById('pattern-author').value = pattern.created_by || '';

            if (pattern.pattern_json) {
                try {
                    currentPattern = JSON.parse(pattern.pattern_json);
                    renderPatternOnCanvas();
                } catch (e) {
                    console.error('Error parsing pattern JSON:', e);
                }
            }

            if (pattern.cypher_query) {
                document.getElementById('cypher-output').textContent = pattern.cypher_query;
            }
        }
    } catch (error) {
        console.error('Error loading pattern:', error);
        showMessage('Error loading pattern', 'error');
    }
}

// Render loaded pattern on canvas
function renderPatternOnCanvas() {
    clearCanvas();

    currentPattern.nodes.forEach((node, idx) => {
        addNodeToCanvas(node.label, 100 + (idx * 200), 100);
        // Update variable name
        const lastNode = currentPattern.nodes[currentPattern.nodes.length - 1];
        lastNode.variable = node.variable;
    });

    generateCypher();
}

// Edit pattern
function editPattern(patternId) {
    openQueryBuilder(patternId);
}

// Delete pattern
async function deletePattern(patternId) {
    if (!confirm('Are you sure you want to delete this pattern?')) {
        return;
    }

    try {
        const response = await fetch(`/api/patterns/${patternId}`, {
            method: 'DELETE'
        });

        const result = await response.json();

        if (result.success) {
            showMessage('Pattern deleted successfully!');
            location.reload();
        } else {
            showMessage('Error deleting pattern', 'error');
        }
    } catch (error) {
        console.error('Error deleting pattern:', error);
        showMessage('Error deleting pattern', 'error');
    }
}

// Execute pattern
async function executePattern(patternId) {
    try {
        const response = await fetch(`/api/patterns/${patternId}/execute`, {
            method: 'POST'
        });

        const result = await response.json();

        if (result.success) {
            displayResults(result.results, result.pattern_name);
        } else {
            showMessage('Error executing pattern: ' + (result.error || 'Unknown error'), 'error');
        }
    } catch (error) {
        console.error('Error executing pattern:', error);
        showMessage('Error executing pattern', 'error');
    }
}

// Display query results
function displayResults(results, patternName) {
    const modal = document.getElementById('pattern-results-modal');
    const content = document.getElementById('pattern-results-content');

    if (!results || results.length === 0) {
        content.innerHTML = '<p class="empty-message">No results found</p>';
    } else {
        let html = `<h3>Results for: ${patternName}</h3>`;
        html += `<p>Found ${results.length} result(s)</p>`;
        html += '<div class="results-grid">';

        results.forEach((row, idx) => {
            html += '<div class="result-card">';
            html += `<h4>Result ${idx + 1}</h4>`;
            html += '<pre>' + JSON.stringify(row, null, 2) + '</pre>';
            html += '</div>';
        });

        html += '</div>';
        content.innerHTML = html;
    }

    modal.classList.add('active');
}

// Close results modal
function closeResults() {
    const modal = document.getElementById('pattern-results-modal');
    modal.classList.remove('active');
}

// Search patterns
function searchPatterns() {
    const searchTerm = document.getElementById('pattern-search').value.toLowerCase();
    const cards = document.querySelectorAll('.pattern-card');

    cards.forEach(card => {
        const name = card.dataset.name;
        if (name.includes(searchTerm)) {
            card.style.display = 'block';
        } else {
            card.style.display = 'none';
        }
    });
}

// Show message to user
function showMessage(message, type = 'success') {
    // Create toast notification
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        background: ${type === 'success' ? '#28a745' : '#dc3545'};
        color: white;
        border-radius: 4px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 10000;
        animation: slideIn 0.3s ease;
    `;

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    // Close modals when clicking outside
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.remove('active');
            }
        });
    });
});

// Add keyframes for animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }

    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }

    .canvas-node {
        background: white;
        border: 2px solid var(--primary);
        border-radius: 8px;
        padding: 0;
        min-width: 150px;
        cursor: move;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }

    .node-header {
        background: var(--primary);
        color: white;
        padding: 0.5rem 0.75rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        cursor: grab;
        border-radius: 6px 6px 0 0;
    }

    .node-header:active {
        cursor: grabbing;
    }

    .node-label {
        font-weight: 600;
        font-size: 0.875rem;
    }

    .node-delete {
        background: none;
        border: none;
        color: white;
        font-size: 1.25rem;
        cursor: pointer;
        padding: 0;
        line-height: 1;
        opacity: 0.8;
    }

    .node-delete:hover {
        opacity: 1;
    }

    .node-body {
        padding: 0.75rem;
    }

    .node-variable {
        width: 100%;
        padding: 0.5rem;
        border: 1px solid var(--border);
        border-radius: 4px;
        font-family: 'Monaco', 'Courier New', monospace;
        font-size: 0.875rem;
    }

    .node-connectors {
        display: flex;
        justify-content: space-between;
        padding: 0 0.5rem 0.5rem 0.5rem;
    }

    .connector {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background: var(--primary);
        cursor: pointer;
        border: 2px solid white;
    }

    .connector:hover {
        transform: scale(1.2);
    }

    .results-grid {
        display: grid;
        gap: 1rem;
        margin-top: 1rem;
    }

    .result-card {
        background: var(--bg-light);
        border: 1px solid var(--border);
        border-radius: 4px;
        padding: 1rem;
    }

    .result-card h4 {
        margin: 0 0 0.5rem 0;
        color: var(--primary);
    }

    .result-card pre {
        background: white;
        padding: 0.75rem;
        border-radius: 4px;
        overflow-x: auto;
        font-size: 0.875rem;
    }

    .empty-message {
        text-align: center;
        color: var(--text-light);
        padding: 2rem;
    }
`;
document.head.appendChild(style);
