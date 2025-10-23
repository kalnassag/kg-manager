/**
 * Graph Visualization - Similar to Neo4j Bloom
 */

// Global variables
let cy = null;
let currentLayout = 'cose';
let selectedNode = null;

// Color palette for node types
const nodeColors = {
    'Laptop': '#4A90E2',
    'Phone': '#E27D4A',
    'Tablet': '#8E4AE2',
    'GPU': '#4AE28E',
    'Brand': '#FFA726',
    'CPUModel': '#26A69A',
    'CPUFamily': '#5C6BC0',
    'CPUBrand': '#7E57C2',
    'Color': '#EC407A',
    'DisplayTechnology': '#66BB6A',
    'OperatingSystem': '#42A5F5',
    'default': '#90A4AE'
};

// Initialize Cytoscape
function initCytoscape() {
    const container = document.getElementById('cy-container');

    cy = cytoscape({
        container: container,

        style: [
            {
                selector: 'node',
                style: {
                    'label': 'data(label)',
                    'text-valign': 'center',
                    'text-halign': 'center',
                    'background-color': function(ele) {
                        return nodeColors[ele.data('type')] || nodeColors['default'];
                    },
                    'color': '#fff',
                    'text-outline-color': function(ele) {
                        return nodeColors[ele.data('type')] || nodeColors['default'];
                    },
                    'text-outline-width': 2,
                    'font-size': '12px',
                    'width': '60px',
                    'height': '60px',
                    'border-width': 2,
                    'border-color': '#fff',
                    'overlay-opacity': 0
                }
            },
            {
                selector: 'node:selected',
                style: {
                    'border-width': 4,
                    'border-color': '#FFD700',
                    'z-index': 999
                }
            },
            {
                selector: 'edge',
                style: {
                    'width': 2,
                    'line-color': '#CBD5E0',
                    'target-arrow-color': '#CBD5E0',
                    'target-arrow-shape': 'triangle',
                    'curve-style': 'bezier',
                    'label': 'data(label)',
                    'font-size': '10px',
                    'text-rotation': 'autorotate',
                    'text-margin-y': -10,
                    'color': '#718096',
                    'text-background-color': '#fff',
                    'text-background-opacity': 0.8,
                    'text-background-padding': '2px'
                }
            },
            {
                selector: 'edge:selected',
                style: {
                    'line-color': '#4A90E2',
                    'target-arrow-color': '#4A90E2',
                    'width': 3
                }
            }
        ],

        layout: {
            name: 'cose',
            animate: true,
            animationDuration: 500
        },

        minZoom: 0.2,
        maxZoom: 3,
        wheelSensitivity: 0.2
    });

    // Event listeners
    cy.on('tap', 'node', function(evt) {
        const node = evt.target;
        selectNode(node);
    });

    cy.on('tap', function(evt) {
        if (evt.target === cy) {
            deselectNode();
        }
    });

    cy.on('dbltap', 'node', function(evt) {
        const node = evt.target;
        expandNode(node.data('type'), node.data('id'));
    });
}

// Select a node and show details
function selectNode(node) {
    selectedNode = node;

    // Update selection
    cy.elements().removeClass('selected');
    node.addClass('selected');

    // Show info panel
    const data = node.data();
    const infoPanel = document.getElementById('info-panel');
    const infoTitle = document.getElementById('info-title');
    const infoContent = document.getElementById('info-content');

    infoTitle.textContent = data.label;

    // Build properties display
    let html = `<div class="info-type"><strong>Type:</strong> ${data.type}</div>`;

    if (data.properties) {
        html += '<div class="info-properties"><h4>Properties</h4>';
        for (const [key, value] of Object.entries(data.properties)) {
            if (!key.startsWith('_') && value) {
                const displayKey = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                html += `<div class="info-prop"><strong>${displayKey}:</strong> ${value}</div>`;
            }
        }
        html += '</div>';
    }

    infoContent.innerHTML = html;
    infoPanel.style.display = 'block';

    // Center on node
    cy.animate({
        center: {
            eles: node
        },
        zoom: 1.5
    }, {
        duration: 500
    });
}

// Deselect node
function deselectNode() {
    selectedNode = null;
    cy.elements().removeClass('selected');
    document.getElementById('info-panel').style.display = 'none';
}

// Load sample graph
async function loadSampleGraph() {
    try {
        const response = await fetch('/api/graph/explore?limit=30');
        const data = await response.json();
        renderGraph(data);
    } catch (error) {
        console.error('Error loading sample graph:', error);
        alert('Failed to load sample graph');
    }
}

// Search and load specific entity
async function searchAndLoad() {
    const searchInput = document.getElementById('graph-search');
    const query = searchInput.value.trim();

    if (!query) {
        loadSampleGraph();
        return;
    }

    try {
        const response = await fetch(`/search?q=${encodeURIComponent(query)}`);
        // This returns HTML, we need to call the search API
        // For now, let's just load sample - we'll enhance this later
        loadSampleGraph();
    } catch (error) {
        console.error('Error searching:', error);
    }
}

// Expand a node to show its connections
async function expandNode(label, entityId) {
    if (!label || !entityId) return;

    try {
        const response = await fetch(`/api/graph/expand/${label}/${entityId}?depth=1`);
        const data = await response.json();

        // Add new nodes and edges
        const newElements = [];

        data.nodes.forEach(node => {
            if (!cy.getElementById(node.id).length) {
                newElements.push({
                    group: 'nodes',
                    data: node
                });
            }
        });

        data.edges.forEach(edge => {
            if (!cy.getElementById(edge.id).length) {
                newElements.push({
                    group: 'edges',
                    data: edge
                });
            }
        });

        if (newElements.length > 0) {
            cy.add(newElements);
            applyLayout(currentLayout);
        }
    } catch (error) {
        console.error('Error expanding node:', error);
        alert('Failed to expand node');
    }
}

// Render graph data
function renderGraph(data) {
    // Clear existing graph
    cy.elements().remove();

    // Add nodes
    const elements = [];

    data.nodes.forEach(node => {
        elements.push({
            group: 'nodes',
            data: node
        });
    });

    // Add edges
    data.edges.forEach(edge => {
        elements.push({
            group: 'edges',
            data: edge
        });
    });

    cy.add(elements);
    applyLayout(currentLayout);
}

// Apply layout
function applyLayout(layoutName) {
    currentLayout = layoutName;

    const layoutOptions = {
        name: layoutName,
        animate: true,
        animationDuration: 500,
        fit: true,
        padding: 50
    };

    // Specific options for different layouts
    if (layoutName === 'cose') {
        layoutOptions.nodeRepulsion = 8000;
        layoutOptions.idealEdgeLength = 100;
        layoutOptions.edgeElasticity = 100;
        layoutOptions.nestingFactor = 5;
        layoutOptions.gravity = 80;
        layoutOptions.numIter = 1000;
    }

    cy.layout(layoutOptions).run();
}

// Filter by node type
function filterByType(type) {
    if (!type) {
        cy.elements().style('display', 'element');
    } else {
        cy.nodes().forEach(node => {
            if (node.data('type') === type) {
                node.style('display', 'element');
                node.connectedEdges().style('display', 'element');
                node.connectedEdges().connectedNodes().style('display', 'element');
            } else {
                const hasConnection = node.connectedEdges().some(edge => {
                    const otherNode = edge.source().id() === node.id() ? edge.target() : edge.source();
                    return otherNode.data('type') === type;
                });

                if (!hasConnection) {
                    node.style('display', 'none');
                    node.connectedEdges().forEach(edge => {
                        if (!edge.source().visible() && !edge.target().visible()) {
                            edge.style('display', 'none');
                        }
                    });
                }
            }
        });
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initCytoscape();

    // Event listeners
    document.getElementById('load-sample-btn').addEventListener('click', loadSampleGraph);

    document.getElementById('fit-btn').addEventListener('click', function() {
        cy.fit(null, 50);
    });

    document.getElementById('clear-btn').addEventListener('click', function() {
        cy.elements().remove();
        deselectNode();
    });

    document.getElementById('layout-select').addEventListener('change', function(e) {
        applyLayout(e.target.value);
    });

    document.getElementById('filter-type').addEventListener('change', function(e) {
        filterByType(e.target.value);
    });

    document.getElementById('search-btn').addEventListener('click', searchAndLoad);

    document.getElementById('graph-search').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            searchAndLoad();
        }
    });

    document.getElementById('close-info').addEventListener('click', deselectNode);

    document.getElementById('expand-node-btn').addEventListener('click', function() {
        if (selectedNode) {
            expandNode(selectedNode.data('type'), selectedNode.data('id'));
        }
    });

    document.getElementById('view-details-btn').addEventListener('click', function() {
        if (selectedNode) {
            const type = selectedNode.data('type');
            const id = selectedNode.data('id');
            window.location.href = `/entities/${type}/${id}`;
        }
    });

    // Load sample graph on start
    loadSampleGraph();
});
