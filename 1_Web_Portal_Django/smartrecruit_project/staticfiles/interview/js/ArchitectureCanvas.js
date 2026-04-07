/**
 * Phase 16: Visual System Design Canvas
 * Powered by React Flow (@xyflow/react) and Dagre for Layout
 */

const { useState, useCallback, useRef, useEffect, useMemo } = React;
const { 
    ReactFlow: Flow, 
    addEdge, 
    Background, 
    Controls, 
    applyEdgeChanges, 
    applyNodeChanges,
    ReactFlowProvider,
    useReactFlow
} = ReactFlow;

// --- Custom Node Icons ---
const NodeIcon = ({ type }) => {
    const icons = {
        server: 'fa-server',
        db: 'fa-database',
        lb: 'fa-network-wired',
        s3: 'fa-archive',
        apig: 'fa-door-open',
        lambda: 'fa-bolt'
    };
    return React.createElement('i', { className: `fas ${icons[type] || 'fa-box'}` });
};

const ArchitectureCanvas = ({ applicationId, csrfToken }) => {
    const reactFlowWrapper = useRef(null);
    const [nodes, setNodes] = useState([]);
    const [edges, setEdges] = useState([]);
    const { screenToFlowPosition, toObject, setViewport } = useReactFlow();

    // --- Core Methods ---
    const onNodesChange = useCallback((changes) => setNodes((nds) => applyNodeChanges(changes, nds)), []);
    const onEdgesChange = useCallback((changes) => setEdges((eds) => applyEdgeChanges(changes, eds)), []);
    
    const onConnect = useCallback((params) => {
        const edge = {
            ...params,
            id: `e-${params.source}-${params.target}`,
            animated: true,
            label: 'API Request',
            style: { stroke: '#00d2ff', strokeWidth: 2 },
            labelStyle: { fill: '#00d2ff', fontWeight: 700, fontSize: 10 },
            labelBgStyle: { fill: 'rgba(10, 20, 35, 0.8)' }
        };
        setEdges((eds) => addEdge(edge, eds));
    }, []);

    const onDragOver = useCallback((event) => {
        event.preventDefault();
        event.dataTransfer.dropEffect = 'move';
    }, []);

    const onDrop = useCallback((event) => {
        event.preventDefault();
        const type = event.dataTransfer.getData('application/reactflow');
        if (!type) return;

        const position = screenToFlowPosition({ x: event.clientX, y: event.clientY });
        
        const newNode = {
            id: `node_${Date.now()}`,
            type: 'default',
            position,
            data: { label: React.createElement('div', { className: 'd-flex align-items-center gap-2 px-2' }, 
                    React.createElement(NodeIcon, { type }),
                    React.createElement('span', { className: 'fw-bold x-small' }, type.toUpperCase())) },
            className: `arch-node node-${type}`,
        };

        setNodes((nds) => nds.concat(newNode));
    }, [screenToFlowPosition]);

    // --- Actions ---
    const clearCanvas = () => {
        if (confirm('Clear entire neural architecture?')) {
            setNodes([]);
            setEdges([]);
        }
    };

    const autoLayout = () => {
        const g = new dagre.graphlib.Graph();
        g.setGraph({ rankdir: 'LR', marginx: 50, marginy: 50 });
        g.setDefaultEdgeLabel(() => ({}));

        nodes.forEach(node => g.setNode(node.id, { width: 150, height: 60 }));
        edges.forEach(edge => g.setEdge(edge.source, edge.target));

        dagre.layout(g);

        const layoutedNodes = nodes.map(node => {
            const nodeWithPosition = g.node(node.id);
            return { ...node, position: { x: nodeWithPosition.x - 75, y: nodeWithPosition.y - 30 } };
        });

        setNodes(layoutedNodes);
    };

    const saveArchitecture = async () => {
        const flow = toObject();
        const exportSchema = {
            nodes: flow.nodes.map(n => ({ id: n.id, type: n.className, label: n.data.label?.props?.children[1]?.props?.children })),
            edges: flow.edges.map(e => ({ from: e.source, to: e.target, label: e.label })),
            timestamp: new Date().toISOString()
        };

        const btn = document.getElementById('save-arch-btn');
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i> Syncing...';

        try {
            const response = await fetch(`/api/save-system-design/${applicationId}/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
                body: JSON.stringify({ diagram: flow, analysis_schema: exportSchema })
            });
            const result = await response.json();
            if (result.status === 'success') {
                alert(`Architecture Sync Complete!\nAI Score: ${result.score}%\nMetrics: ${result.analysis}`);
            }
        } catch (err) {
            alert('Neuro-Sync Interrupted. Please check connectivity.');
        } finally {
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-cloud-upload-alt me-2"></i> Save Architecture';
        }
    };

    // Expose buttons to external DOM if needed or handle inside
    useEffect(() => {
        window.saveArchitecture = saveArchitecture;
        window.clearCanvas = clearCanvas;
        window.autoLayout = autoLayout;
    }, [nodes, edges, toObject]);

    return React.createElement('div', { className: 'h-100 w-100 position-relative' },
        React.createElement(Flow, {
            nodes,
            edges,
            onNodesChange,
            onEdgesChange,
            onConnect,
            onDrop,
            onDragOver,
            snapToGrid: true,
            snapGrid: [20, 20],
            fitView: true,
            style: { background: '#0a1423' }
        },
            React.createElement(Background, { color: '#00d2ff', opacity: 0.1, gap: 20 }),
            React.createElement(Controls),
            React.createElement('div', { className: 'position-absolute top-0 end-0 m-3 d-flex gap-2', style: { zIndex: 5 } },
                React.createElement('button', { className: 'btn btn-sm btn-glass text-cyan', onClick: autoLayout }, 
                    React.createElement('i', { className: 'fas fa-magic me-1' }), 'Auto-Layout'),
                React.createElement('button', { className: 'btn btn-sm btn-glass text-rose', onClick: clearCanvas },
                    React.createElement('i', { className: 'fas fa-trash me-1' }), 'Clear')
            )
        )
    );
};

// --- Initialization ---
const mountArchitectureCanvas = (applicationId, csrfToken) => {
    const container = document.getElementById('reactflow-container');
    if (!container) return;
    
    const root = ReactDOM.createRoot(container);
    root.render(
        React.createElement(ReactFlowProvider, null, 
            React.createElement(ArchitectureCanvas, { applicationId, csrfToken })
        )
    );
};

window.mountArchitectureCanvas = mountArchitectureCanvas;
