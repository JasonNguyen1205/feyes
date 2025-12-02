// ROI Editor - Visual AOI Client
// Complete ROI configuration editor with canvas interaction and server API integration

// ==================== ROI Format Helpers ====================
// Helper functions to handle both server format and client format
const ROI = {
    // Type mapping
    typeMap: { 1: 'barcode', 2: 'compare', 3: 'ocr', 4: 'color' },
    typeMapReverse: { 'barcode': 1, 'compare': 2, 'ocr': 3, 'color': 4 },

    // Getters that work with both formats
    getId: (roi) => roi.idx || roi.roi_id,
    getType: (roi) => typeof roi.type === 'number' ? ROI.typeMap[roi.type] : (roi.roi_type_name || roi.type),
    getTypeNum: (roi) => typeof roi.type === 'number' ? roi.type : ROI.typeMapReverse[roi.roi_type_name || roi.type],
    getCoords: (roi) => roi.coords || roi.coordinates,
    getDevice: (roi) => roi.device_location || roi.device_id,

    // Setters
    setId: (roi, val) => { if (roi.idx !== undefined) roi.idx = val; if (roi.roi_id !== undefined) roi.roi_id = val; },
    setType: (roi, val) => {
        if (typeof val === 'number') {
            roi.type = val;
            if (roi.roi_type_name !== undefined) roi.roi_type_name = ROI.typeMap[val];
        } else {
            roi.roi_type_name = val;
            if (roi.type !== undefined) roi.type = ROI.typeMapReverse[val];
        }
    },
    setCoords: (roi, val) => { if (roi.coords !== undefined) roi.coords = val; if (roi.coordinates !== undefined) roi.coordinates = val; },
    setDevice: (roi, val) => { if (roi.device_location !== undefined) roi.device_location = val; if (roi.device_id !== undefined) roi.device_id = val; }
};

// ==================== State Management ====================
const editorState = {
    serverUrl: 'http://10.100.27.156:5000',
    connected: false,
    currentProduct: null,
    currentTool: 'select',
    rois: [],
    roiGroups: {},  // Store ROI groups with camera settings
    selectedROI: null,
    image: null,
    canvas: null,
    ctx: null,
    zoom: 1.0,
    panOffset: { x: 0, y: 0 },
    isPanning: false,
    isDrawing: false,
    drawStart: null,
    theme: 'light',
    isCapturing: false  // Track if camera capture is in progress
};

// ==================== Initialization ====================
document.addEventListener('DOMContentLoaded', () => {
    initializeCanvas();
    loadTheme();
    setupEventListeners();

    // Auto-connect to server
    connectToServer();
});

function initializeCanvas() {
    editorState.canvas = document.getElementById('roiCanvas');
    editorState.ctx = editorState.canvas.getContext('2d');

    // Set canvas size
    const container = document.querySelector('.canvas-container');
    editorState.canvas.width = container.clientWidth - 40;
    editorState.canvas.height = container.clientHeight - 40;

    // Setup canvas event listeners
    editorState.canvas.addEventListener('mousedown', handleCanvasMouseDown);
    editorState.canvas.addEventListener('mousemove', handleCanvasMouseMove);
    editorState.canvas.addEventListener('mouseup', handleCanvasMouseUp);
    editorState.canvas.addEventListener('wheel', handleCanvasWheel);
    editorState.canvas.addEventListener('mouseleave', handleCanvasMouseUp);
}

function setupEventListeners() {
    // Window resize
    window.addEventListener('resize', () => {
        const container = document.querySelector('.canvas-container');
        editorState.canvas.width = container.clientWidth - 40;
        editorState.canvas.height = container.clientHeight - 40;
        redrawCanvas();
    });
}

// ==================== Server Connection ====================
async function connectToServer() {
    const urlInput = document.getElementById('serverUrl');
    editorState.serverUrl = urlInput.value;

    const statusEl = document.getElementById('connectionStatus');
    statusEl.className = 'status-indicator connecting';
    statusEl.textContent = 'Connecting...';

    try {
        // Step 1: Connect Flask backend to the AOI server
        console.log(`Connecting to server: ${editorState.serverUrl}`);
        const connectResponse = await fetch('/api/server/connect', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ server_url: editorState.serverUrl })
        });

        if (!connectResponse.ok) {
            const error = await connectResponse.json();
            throw new Error(error.error || 'Connection failed');
        }

        const connectData = await connectResponse.json();
        console.log('Server connected:', connectData);

        // Step 2: Fetch products from connected server
        const productsResponse = await fetch(`/api/products`);
        if (!productsResponse.ok) throw new Error('Failed to fetch products');

        const productsData = await productsResponse.json();
        console.log('Products data:', productsData);

        editorState.connected = true;

        statusEl.className = 'status-indicator connected';
        statusEl.textContent = '✓ Connected';

        // Populate products dropdown
        populateProducts(productsData.products || []);

        showNotification(`Connected to server successfully. Source: ${productsData.source}`, 'success');
    } catch (error) {
        editorState.connected = false;
        statusEl.className = 'status-indicator disconnected';
        statusEl.textContent = '✗ Connection failed';

        console.error('Connection error:', error);
        showNotification(`Failed to connect: ${error.message}`, 'error');
    }
}

function populateProducts(products) {
    const select = document.getElementById('productSelect');
    select.innerHTML = '<option value="">-- Select Product --</option>';

    products.forEach(product => {
        const option = document.createElement('option');

        // Handle both string and object formats
        if (typeof product === 'string') {
            option.value = product;
            option.textContent = product;
        } else if (typeof product === 'object' && product.product_name) {
            option.value = product.product_name;
            option.textContent = product.description
                ? `${product.product_name} - ${product.description}`
                : product.product_name;
        } else {
            console.warn('Invalid product format:', product);
            return;
        }

        select.appendChild(option);
    });

    console.log(`✅ Populated ${products.length} products in dropdown`);
}

function onProductChange() {
    const select = document.getElementById('productSelect');
    editorState.currentProduct = select.value;

    if (editorState.currentProduct) {
        showNotification(`Product "${editorState.currentProduct}" selected`, 'info');
    }
}

// ==================== Product Creation ====================
async function createNewProduct() {
    if (!editorState.connected) {
        showNotification('Not connected to server', 'error');
        return;
    }

    // Show dialog to get product details
    const productName = prompt('Enter Product Name (e.g., 20003548):');
    if (!productName || !productName.trim()) {
        showNotification('Product creation cancelled', 'info');
        return;
    }

    const description = prompt('Enter Product Description (optional):') || '';
    const deviceCountStr = prompt('Enter Device Count (1-4):', '1');
    const deviceCount = parseInt(deviceCountStr) || 1;

    if (deviceCount < 1 || deviceCount > 4) {
        showNotification('Device count must be between 1 and 4', 'error');
        return;
    }

    try {
        showNotification('Creating product...', 'info');

        // Call client proxy endpoint to create product on server
        const response = await fetch('/api/products/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                product_name: productName.trim(),
                description: description.trim(),
                device_count: deviceCount
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || `Server error: ${response.status}`);
        }

        const result = await response.json();
        showNotification(`Product "${productName}" created successfully!`, 'success');

        // Refresh product list
        await connectToServer();

        // Auto-select the new product
        editorState.currentProduct = productName.trim();
        document.getElementById('productSelect').value = productName.trim();

        // Initialize empty ROI list for new product
        editorState.rois = [];
        updateROIList();
        updateSummary();
        redrawCanvas();

    } catch (error) {
        console.error('Failed to create product:', error);
        showNotification(`Failed to create product: ${error.message}`, 'error');
    }
}

// ==================== Configuration Loading ====================
async function loadProductConfig() {
    if (!editorState.currentProduct) {
        showNotification('Please select a product first', 'error');
        return;
    }

    if (!editorState.connected) {
        showNotification('Not connected to server', 'error');
        return;
    }

    try {
        showNotification('Loading configuration...', 'info');

        // Use client proxy endpoint to avoid CORS
        const response = await fetch(`/api/products/${editorState.currentProduct}/config`);

        if (response.status === 404) {
            // 404 is normal for new products without configuration yet
            console.log(`No existing config for product "${editorState.currentProduct}" - starting fresh`);
            editorState.rois = [];
            showNotification(`No existing config found. Starting with empty configuration.`, 'info');

            updateROIList();
            updateSummary();
            redrawCanvas();
            return;
        }

        if (!response.ok) {
            throw new Error(`Server error: ${response.status} ${response.statusText}`);
        }

        const config = await response.json();

        // Load ROIs from config
        editorState.rois = config.rois || [];

        // Load ROI groups with camera settings
        editorState.roiGroups = config.roi_groups || {};

        // Debug: Log loaded data
        console.log('ROIs loaded:', editorState.rois.length);
        console.log('ROI Groups loaded:', editorState.roiGroups);
        if (Object.keys(editorState.roiGroups).length > 0) {
            const firstKey = Object.keys(editorState.roiGroups).sort()[0];
            console.log(`First ROI group: ${firstKey}`, editorState.roiGroups[firstKey]);
        }

        // Update ROI groups UI
        updateROIGroupsList();

        showNotification(`Loaded ${editorState.rois.length} ROIs`, 'success');
        updateROIList();
        updateSummary();
        redrawCanvas();
    } catch (error) {
        console.error('Failed to load configuration:', error);
        showNotification(`Failed to load configuration: ${error.message}`, 'error');

        // Initialize empty config on error
        editorState.rois = [];
        updateROIList();
        updateSummary();
        redrawCanvas();
    }
}

function createNewConfig() {
    if (!editorState.currentProduct) {
        showNotification('Please select a product first', 'error');
        return;
    }

    if (confirm('Create a new configuration? This will clear current ROIs.')) {
        editorState.rois = [];
        editorState.selectedROI = null;
        updateROIList();
        updatePropertiesPanel();
        updateSummary();
        redrawCanvas();
        showNotification('New configuration created', 'success');
    }
}

// ==================== ROI Groups Management ====================
function updateROIGroupsList() {
    const container = document.getElementById('roiGroupsList');

    if (!editorState.roiGroups || Object.keys(editorState.roiGroups).length === 0) {
        container.innerHTML = '<p class="info-text">No ROI groups available</p>';
        return;
    }

    container.innerHTML = '';

    // Sort groups by key
    const sortedKeys = Object.keys(editorState.roiGroups).sort();

    sortedKeys.forEach((groupKey, index) => {
        const group = editorState.roiGroups[groupKey];

        const groupItem = document.createElement('div');
        groupItem.className = 'roi-group-item';
        if (index === 0) groupItem.classList.add('active');

        groupItem.innerHTML = `
            <div class="roi-group-info">
                <div class="roi-group-key">Group ${index + 1}</div>
                <div class="roi-group-details">F:${group.focus} | E:${group.exposure}</div>
            </div>
            <div class="roi-group-count">${group.count || 0} ROIs</div>
        `;

        groupItem.onclick = () => selectROIGroup(groupKey, group);
        container.appendChild(groupItem);
    });
}

/**
 * Handles group selection, updates UI and input fields
 */
function selectROIGroup(groupKey, group) {
    // Update active state
    document.querySelectorAll('.roi-group-item').forEach(item => {
        item.classList.remove('active');
    });
    event.target.closest('.roi-group-item')?.classList.add('active');

    // Populate custom inputs with group settings
    document.getElementById('customFocus').value = group.focus || '';
    document.getElementById('customExposure').value = group.exposure || '';

    showNotification(`Selected group: F:${group.focus}, E:${group.exposure}`, 'info');
    console.log('Selected ROI group:', groupKey, group);
}

/**
 * Clears custom camera settings and removes group selection
 */
function clearCustomSettings() {
    document.getElementById('customFocus').value = '';
    document.getElementById('customExposure').value = '';

    // Remove active state from all groups
    document.querySelectorAll('.roi-group-item').forEach(item => {
        item.classList.remove('active');
    });

    showNotification('Custom settings cleared. Will use default or first group settings.', 'info');
    console.log('Cleared custom camera settings');
}

/**
 * Validates custom camera settings
 * @returns {object} - {valid: boolean, message: string, focus: number, exposure: number}
 */
function validateCameraSettings() {
    const focusInput = document.getElementById('customFocus');
    const exposureInput = document.getElementById('customExposure');

    const focus = focusInput.value ? parseInt(focusInput.value) : null;
    const exposure = exposureInput.value ? parseInt(exposureInput.value) : null;

    // If both empty, it's valid (will use defaults)
    if (!focus && !exposure) {
        return { valid: true, focus: null, exposure: null };
    }

    // Validate focus range (0-1000)
    if (focus !== null && (focus < 0 || focus > 1000)) {
        return {
            valid: false,
            message: 'Focus must be between 0 and 1000',
            focus: focus,
            exposure: exposure
        };
    }

    // Validate exposure range (50-30000)
    if (exposure !== null && (exposure < 50 || exposure > 30000)) {
        return {
            valid: false,
            message: 'Exposure must be between 50 and 30000',
            focus: focus,
            exposure: exposure
        };
    }

    return { valid: true, focus: focus, exposure: exposure };
}// ==================== Image Handling ====================
async function captureImage() {
    // Prevent concurrent captures
    if (editorState.isCapturing) {
        showNotification('Capture already in progress, please wait...', 'warning');
        return;
    }

    editorState.isCapturing = true;
    const captureBtn = document.querySelector('button[onclick="captureImage()"]');
    if (captureBtn) {
        captureBtn.disabled = true;
        captureBtn.textContent = '📸 Capturing...';
    }

    showNotification('Capturing image from camera...', 'info');

    try {
        // Validate custom camera settings first
        const validation = validateCameraSettings();
        if (!validation.valid) {
            showNotification(validation.message, 'error');
            return;
        }

        // Get camera settings from custom inputs or ROI groups
        let captureParams = {};

        // Priority 1: Use custom input values if provided and valid
        if (validation.focus !== null || validation.exposure !== null) {
            captureParams = {
                focus: validation.focus,
                exposure: validation.exposure
            };
            console.log(`✓ Using custom camera settings: focus=${captureParams.focus}, exposure=${captureParams.exposure}`);
            showNotification(`Capturing with custom settings (F:${captureParams.focus}, E:${captureParams.exposure})`, 'info');
        }
        // Priority 2: Use first ROI group if no custom values
        else if (editorState.roiGroups && Object.keys(editorState.roiGroups).length > 0) {
            // Get the first group (sorted by key)
            const firstGroupKey = Object.keys(editorState.roiGroups).sort()[0];
            const firstGroup = editorState.roiGroups[firstGroupKey];

            console.log('First group key:', firstGroupKey);
            console.log('First group data:', firstGroup);

            // Server format: focus and exposure are direct properties
            if (firstGroup && (firstGroup.focus || firstGroup.exposure)) {
                captureParams = {
                    focus: firstGroup.focus,
                    exposure: firstGroup.exposure
                };
                console.log(`✓ Using first ROI group settings: focus=${captureParams.focus}, exposure=${captureParams.exposure}`);
                showNotification(`Capturing with Group 1 settings (F:${captureParams.focus}, E:${captureParams.exposure})`, 'info');
            } else {
                console.warn('First group found but no camera settings (focus/exposure):', firstGroup);
            }
        } else {
            console.log('No ROI groups or custom settings, using default camera settings');
        }

        console.log('Sending capture request with params:', captureParams);

        const response = await fetch('/api/camera/capture', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(captureParams)
        });

        // Handle camera busy (429) response
        if (response.status === 429) {
            const data = await response.json();
            showNotification('Camera busy, retrying in 3 seconds...', 'warning');
            await new Promise(resolve => setTimeout(resolve, 3000));
            // Retry once
            return await captureImage();
        }

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || 'Capture failed');
        }

        const data = await response.json();

        // Load the captured image
        await loadImageFromURL(`/shared/${data.image_path}`);

        showNotification('Image captured successfully', 'success');
    } catch (error) {
        console.error('Capture error:', error);
        showNotification(`Failed to capture image: ${error.message}`, 'error');
    } finally {
        // Always reset capture state
        editorState.isCapturing = false;
        if (captureBtn) {
            captureBtn.disabled = false;
            captureBtn.textContent = '📸 Capture from Camera';
        }
    }
}

function loadImageFile(event) {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
        loadImageFromURL(e.target.result);
    };
    reader.readAsDataURL(file);
}

async function loadImageFromURL(url, retryCount = 0) {
    return new Promise((resolve, reject) => {
        const img = new Image();

        img.onload = () => {
            editorState.image = img;

            // Hide overlay
            document.getElementById('canvasOverlay').style.display = 'none';

            // Update canvas size to match image
            editorState.canvas.width = Math.min(img.width, 1920);
            editorState.canvas.height = Math.min(img.height, 1080);

            // Fit image to screen
            fitToScreen();

            // Update info
            document.getElementById('imageInfo').textContent =
                `${img.width} × ${img.height} pixels`;
            document.getElementById('imageInfo').className = 'info-text has-image';
            document.getElementById('canvasSize').textContent =
                `${img.width} × ${img.height}`;

            redrawCanvas();
            resolve();
        };

        img.onerror = async (error) => {
            console.error(`Failed to load image from ${url}:`, error);

            // Retry up to 3 times with exponential backoff
            if (retryCount < 3) {
                const delay = Math.pow(2, retryCount) * 1000; // 1s, 2s, 4s
                console.log(`Retrying image load in ${delay}ms (attempt ${retryCount + 1}/3)...`);
                showNotification(`Retrying image load... (${retryCount + 1}/3)`, 'warning');

                await new Promise(resolve => setTimeout(resolve, delay));
                try {
                    await loadImageFromURL(url, retryCount + 1);
                    resolve();
                } catch (retryError) {
                    reject(retryError);
                }
            } else {
                reject(new Error(`Failed to load image after ${retryCount} retries. The server may have crashed or the image file is missing.`));
            }
        };

        img.src = url;
    });
}

// ==================== Drawing Tools ====================
function setTool(tool) {
    editorState.currentTool = tool;

    // Update UI
    document.querySelectorAll('.tool-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`[data-tool="${tool}"]`).classList.add('active');

    // Update cursor
    const canvas = editorState.canvas;
    canvas.className = '';
    canvas.classList.add(`${tool}-mode`);
}

function zoomIn() {
    editorState.zoom = Math.min(editorState.zoom * 1.2, 5.0);
    updateZoomDisplay();
    redrawCanvas();
}

function zoomOut() {
    editorState.zoom = Math.max(editorState.zoom / 1.2, 0.1);
    updateZoomDisplay();
    redrawCanvas();
}

function fitToScreen() {
    if (!editorState.image) return;

    const container = document.querySelector('.canvas-container');
    const scaleX = (container.clientWidth - 40) / editorState.image.width;
    const scaleY = (container.clientHeight - 40) / editorState.image.height;
    editorState.zoom = Math.min(scaleX, scaleY, 1.0);

    editorState.panOffset = { x: 0, y: 0 };
    updateZoomDisplay();
    redrawCanvas();
}

function updateZoomDisplay() {
    document.getElementById('zoomLevel').textContent = `${Math.round(editorState.zoom * 100)}%`;
}

// ==================== Canvas Event Handlers ====================
function handleCanvasMouseDown(e) {
    const rect = editorState.canvas.getBoundingClientRect();
    const x = (e.clientX - rect.left - editorState.panOffset.x) / editorState.zoom;
    const y = (e.clientY - rect.top - editorState.panOffset.y) / editorState.zoom;

    if (editorState.currentTool === 'draw') {
        editorState.isDrawing = true;
        editorState.drawStart = { x, y };
    } else if (editorState.currentTool === 'select') {
        // Check if clicked on an ROI
        selectROIAt(x, y);
    } else if (editorState.currentTool === 'pan') {
        editorState.isPanning = true;
        editorState.panStart = { x: e.clientX, y: e.clientY };
    }
}

function handleCanvasMouseMove(e) {
    const rect = editorState.canvas.getBoundingClientRect();
    const x = (e.clientX - rect.left - editorState.panOffset.x) / editorState.zoom;
    const y = (e.clientY - rect.top - editorState.panOffset.y) / editorState.zoom;

    // Update mouse coordinates display
    document.getElementById('mouseCoords').textContent =
        `X: ${Math.round(x)}, Y: ${Math.round(y)}`;

    if (editorState.isDrawing && editorState.currentTool === 'draw') {
        redrawCanvas();

        // Draw temporary rectangle
        const ctx = editorState.ctx;
        ctx.save();
        ctx.translate(editorState.panOffset.x, editorState.panOffset.y);
        ctx.scale(editorState.zoom, editorState.zoom);

        ctx.strokeStyle = '#2196F3';
        ctx.lineWidth = 2 / editorState.zoom;
        ctx.setLineDash([5 / editorState.zoom, 5 / editorState.zoom]);
        ctx.strokeRect(
            editorState.drawStart.x,
            editorState.drawStart.y,
            x - editorState.drawStart.x,
            y - editorState.drawStart.y
        );

        ctx.restore();
    } else if (editorState.isPanning && editorState.currentTool === 'pan') {
        const dx = e.clientX - editorState.panStart.x;
        const dy = e.clientY - editorState.panStart.y;

        editorState.panOffset.x += dx;
        editorState.panOffset.y += dy;
        editorState.panStart = { x: e.clientX, y: e.clientY };

        redrawCanvas();
    }
}

function handleCanvasMouseUp(e) {
    if (editorState.isDrawing && editorState.currentTool === 'draw') {
        const rect = editorState.canvas.getBoundingClientRect();
        const x = (e.clientX - rect.left - editorState.panOffset.x) / editorState.zoom;
        const y = (e.clientY - rect.top - editorState.panOffset.y) / editorState.zoom;

        // Create new ROI
        const newROI = createROI(editorState.drawStart.x, editorState.drawStart.y, x, y);
        editorState.rois.push(newROI);
        editorState.selectedROI = newROI;

        updateROIList();
        updatePropertiesPanel();
        updateSummary();
        redrawCanvas();

        // Enhanced notification with source info
        const sourceMsg = editorState.rois.length > 1
            ? ` (copied attributes from previous ROI)`
            : ` (using default attributes)`;
        showNotification(`ROI ${ROI.getId(newROI)} created${sourceMsg}`, 'success');
    }

    editorState.isDrawing = false;
    editorState.isPanning = false;
}

function handleCanvasWheel(e) {
    e.preventDefault();

    if (e.deltaY < 0) {
        zoomIn();
    } else {
        zoomOut();
    }
}

// ==================== ROI Management ====================
function createROI(x1, y1, x2, y2) {
    // Normalize coordinates
    const minX = Math.min(x1, x2);
    const minY = Math.min(y1, y2);
    const maxX = Math.max(x1, x2);
    const maxY = Math.max(y1, y2);

    // Generate new ROI ID (handle both server format idx and client format roi_id)
    const maxId = editorState.rois.length > 0
        ? Math.max(...editorState.rois.map(r => ROI.getId(r)))
        : 0;

    // Get default attributes from last created ROI or first ROI
    let defaultAttributes = {
        type: 2,  // Server format: 2 = compare
        device_location: 1,  // Server format
        ai_threshold: 0.8,
        focus: 305,
        exposure: 1200,  // Server format
        enabled: true,
        feature_method: 'mobilenet',  // Server format uses feature_method
        notes: ''
    };

    if (editorState.rois.length > 0) {
        // Find the last created ROI (highest idx) to copy attributes from
        const lastROI = editorState.rois.reduce((max, roi) =>
            ROI.getId(roi) > ROI.getId(max) ? roi : max
        );

        // Copy all attributes from last ROI except coordinates and idx
        const lastType = ROI.getType(lastROI);
        const lastTypeNum = ROI.getTypeNum(lastROI);

        defaultAttributes = {
            type: lastTypeNum,  // Server format
            device_location: ROI.getDevice(lastROI),  // Server format
            ai_threshold: lastROI.ai_threshold !== undefined ? lastROI.ai_threshold : 0.8,
            focus: lastROI.focus || 305,
            exposure: lastROI.exposure || 1200,  // Server format
            enabled: lastROI.enabled !== undefined ? lastROI.enabled : true,
            notes: ''  // Always clear notes for new ROI
        };

        // Copy feature_method for compare type
        if (lastType === 'compare') {
            defaultAttributes.feature_method = lastROI.feature_method || lastROI.detection_method || 'mobilenet';
        }

        // Copy type-specific attributes
        if (lastType === 'barcode' && lastROI.expected_pattern) {
            defaultAttributes.expected_pattern = lastROI.expected_pattern;
        } else if (lastType === 'ocr') {
            if (lastROI.expected_text) defaultAttributes.expected_text = lastROI.expected_text;
            if (lastROI.rotation !== undefined) defaultAttributes.rotation = lastROI.rotation;
            if (lastROI.case_sensitive !== undefined) defaultAttributes.case_sensitive = lastROI.case_sensitive;
        } else if (lastType === 'color') {
            // Server v3.2: color properties are directly on ROI object
            if (lastROI.expected_color) defaultAttributes.expected_color = lastROI.expected_color;
            if (lastROI.color_tolerance !== undefined) defaultAttributes.color_tolerance = lastROI.color_tolerance;
            if (lastROI.min_pixel_percentage !== undefined) defaultAttributes.min_pixel_percentage = lastROI.min_pixel_percentage;
        }

        console.log(`Creating new ROI with attributes from last ROI (ID: ${ROI.getId(lastROI)})`);
    } else {
        console.log('Creating first ROI with default attributes');
    }

    return {
        idx: maxId + 1,  // Server format
        ...defaultAttributes,
        coords: [  // Server format
            Math.round(minX),
            Math.round(minY),
            Math.round(maxX),
            Math.round(maxY)
        ]
    };
}

function selectROIAt(x, y) {
    // Find ROI at coordinates
    for (let i = editorState.rois.length - 1; i >= 0; i--) {
        const roi = editorState.rois[i];
        const [x1, y1, x2, y2] = ROI.getCoords(roi);

        if (x >= x1 && x <= x2 && y >= y1 && y <= y2) {
            editorState.selectedROI = roi;
            updateROIList();
            updatePropertiesPanel();
            redrawCanvas();
            return;
        }
    }

    // No ROI found, deselect
    editorState.selectedROI = null;
    updateROIList();
    updatePropertiesPanel();
    redrawCanvas();
}

async function deleteSelectedROI() {
    if (!editorState.selectedROI) {
        showNotification('No ROI selected', 'error');
        return;
    }

    const roiId = ROI.getId(editorState.selectedROI);

    if (confirm(`Delete ROI ${roiId}?\n\nThis will also update the server configuration.`)) {
        const index = editorState.rois.indexOf(editorState.selectedROI);
        editorState.rois.splice(index, 1);
        editorState.selectedROI = null;

        updateROIList();
        updatePropertiesPanel();
        updateSummary();
        redrawCanvas();

        showNotification(`ROI ${roiId} deleted`, 'success');

        // Automatically save configuration to server
        if (editorState.connected && editorState.currentProduct) {
            try {
                showNotification('Syncing with server...', 'info');

                const config = {
                    product_name: editorState.currentProduct,
                    rois: editorState.rois
                };

                const response = await fetch(
                    `/api/products/${editorState.currentProduct}/config`,
                    {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(config)
                    }
                );

                if (!response.ok) {
                    throw new Error(`Server returned ${response.status}`);
                }

                const result = await response.json();
                showNotification(`✓ ROI ${roiId} deleted and synced to server`, 'success');
                console.log('✅ Server sync successful:', result);
            } catch (error) {
                console.error('❌ Failed to sync deletion to server:', error);
                showNotification(`⚠️ ROI deleted locally but server sync failed: ${error.message}`, 'warning');
            }
        } else {
            if (!editorState.connected) {
                showNotification('⚠️ ROI deleted locally only (not connected to server)', 'warning');
            }
            if (!editorState.currentProduct) {
                showNotification('⚠️ ROI deleted locally only (no product selected)', 'warning');
            }
        }
    }
}

// ==================== Canvas Drawing ====================
function redrawCanvas() {
    const ctx = editorState.ctx;
    const canvas = editorState.canvas;

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (!editorState.image) return;

    ctx.save();

    // Apply transformations
    ctx.translate(editorState.panOffset.x, editorState.panOffset.y);
    ctx.scale(editorState.zoom, editorState.zoom);

    // Draw image
    ctx.drawImage(editorState.image, 0, 0);

    // Draw ROIs
    editorState.rois.forEach(roi => {
        drawROI(ctx, roi, roi === editorState.selectedROI);
    });

    ctx.restore();
}

function drawROI(ctx, roi, isSelected) {
    const coords = ROI.getCoords(roi);
    const [x1, y1, x2, y2] = coords;
    const typeName = ROI.getType(roi);
    const roiId = ROI.getId(roi);

    ctx.save();

    // Set style based on type and selection
    if (isSelected) {
        ctx.strokeStyle = '#FF9800';
        ctx.lineWidth = 3 / editorState.zoom;
    } else {
        ctx.strokeStyle = getROIColor(typeName);
        ctx.lineWidth = 2 / editorState.zoom;
    }

    // Draw rectangle
    ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);

    // Draw label
    ctx.fillStyle = isSelected ? '#FF9800' : getROIColor(typeName);
    ctx.font = `${14 / editorState.zoom}px Arial`;

    const label = `ROI ${roiId} (${typeName})`;
    const labelWidth = ctx.measureText(label).width;
    const padding = 4 / editorState.zoom;

    ctx.fillRect(x1, y1 - 20 / editorState.zoom, labelWidth + padding * 2, 20 / editorState.zoom);
    ctx.fillStyle = 'white';
    ctx.fillText(label, x1 + padding, y1 - 6 / editorState.zoom);

    ctx.restore();
}

function getROIColor(type) {
    const colors = {
        'barcode': '#4CAF50',  // Green
        'ocr': '#2196F3',      // Blue
        'compare': '#9C27B0',  // Purple
        'color': '#00BCD4'     // Cyan/Light Blue (not red - red is for failures)
    };
    return colors[type] || '#757575';
}

// ==================== UI Updates ====================
function updateROIList() {
    const listEl = document.getElementById('roiList');

    if (editorState.rois.length === 0) {
        listEl.innerHTML = '<p class="empty-state">No ROIs defined</p>';
        return;
    }

    listEl.innerHTML = '';

    editorState.rois.forEach(roi => {
        const item = document.createElement('div');
        item.className = 'roi-item';
        if (roi === editorState.selectedROI) {
            item.classList.add('selected');
        }

        // Add device barcode badge if applicable
        // Handle both server format (idx, type, coords) and client format (roi_id, roi_type_name, coordinates)
        const roiId = roi.idx || roi.roi_id;
        const roiType = roi.type || roi.roi_type_name;
        const coords = roi.coords || roi.coordinates;
        const deviceId = roi.device_location || roi.device_id;

        // Map type number to name
        const typeMap = { 1: 'barcode', 2: 'compare', 3: 'ocr', 4: 'color' };
        const typeName = typeof roiType === 'number' ? typeMap[roiType] : roiType;

        const deviceBarcodeBadge = (typeName === 'barcode' && roi.is_device_barcode)
            ? '<span class="device-barcode-badge" title="Device Barcode (Priority 0)">📱</span>'
            : '';

        item.innerHTML = `
            <div class="roi-item-header">
                <span class="roi-item-id">ROI ${roiId}${deviceBarcodeBadge}</span>
                <span class="roi-item-type">${typeName}</span>
            </div>
            <div class="roi-item-device">Device ${deviceId}</div>
            <div class="roi-item-coords">[${coords.join(', ')}]</div>
        `;

        item.onclick = () => {
            editorState.selectedROI = roi;
            updateROIList();
            updatePropertiesPanel();
            redrawCanvas();
        };

        listEl.appendChild(item);
    });
}

function updatePropertiesPanel() {
    const panel = document.getElementById('propertiesPanel');

    if (!editorState.selectedROI) {
        panel.innerHTML = '<p class="empty-state">Select an ROI to edit properties</p>';
        return;
    }

    // Clone template
    const template = document.getElementById('roiPropertiesTemplate');
    const form = template.content.cloneNode(true);

    panel.innerHTML = '';
    panel.appendChild(form);

    // Populate form with ROI data
    const roi = editorState.selectedROI;
    const coords = ROI.getCoords(roi);
    const roiType = ROI.getType(roi);

    document.getElementById('roiId').value = ROI.getId(roi);
    document.getElementById('roiType').value = roiType;
    document.getElementById('deviceId').value = ROI.getDevice(roi);
    document.getElementById('x1').value = coords[0];
    document.getElementById('y1').value = coords[1];
    document.getElementById('x2').value = coords[2];
    document.getElementById('y2').value = coords[3];

    // AI Threshold: enabled for compare ROIs, null for color/barcode/OCR ROIs per v3.2
    const aiThresholdInput = document.getElementById('aiThreshold');
    if (roiType === 'compare') {
        // Compare ROI: AI threshold is required and enabled
        aiThresholdInput.value = roi.ai_threshold !== null && roi.ai_threshold !== undefined ? roi.ai_threshold : 0.8;
        aiThresholdInput.disabled = false;
        aiThresholdInput.placeholder = '0.0 - 1.0';
    } else {
        // Color/Barcode/OCR ROIs: AI threshold is not used
        aiThresholdInput.value = '';
        aiThresholdInput.disabled = true;
        aiThresholdInput.placeholder = 'N/A for this ROI type';
    }

    document.getElementById('focus').value = roi.focus || 305;
    document.getElementById('exposure').value = roi.exposure || 1200;
    document.getElementById('enabled').checked = roi.enabled !== false;
    document.getElementById('notes').value = roi.notes || '';

    // Update type-specific fields
    updateTypeSpecificFields();
}

function updateTypeSpecificFields() {
    const typeFieldsContainer = document.getElementById('typeSpecificFields');
    const roiType = document.getElementById('roiType').value;
    const roi = editorState.selectedROI;

    typeFieldsContainer.innerHTML = '';

    let template;
    switch (roiType) {
        case 'barcode':
            template = document.getElementById('barcodeFieldsTemplate');
            break;
        case 'ocr':
            template = document.getElementById('ocrFieldsTemplate');
            break;
        case 'compare':
            template = document.getElementById('compareFieldsTemplate');
            break;
        case 'color':
            template = document.getElementById('colorFieldsTemplate');
            break;
    }

    if (template) {
        const fields = template.content.cloneNode(true);
        typeFieldsContainer.appendChild(fields);

        // Populate type-specific fields with ROI data
        if (roi) {
            switch (roiType) {
                case 'barcode':
                    if (document.getElementById('expectedPattern')) {
                        document.getElementById('expectedPattern').value = roi.expected_pattern || '';
                    }
                    if (document.getElementById('isDeviceBarcode')) {
                        document.getElementById('isDeviceBarcode').checked = roi.is_device_barcode || false;
                    }
                    break;

                case 'ocr':
                    if (document.getElementById('expectedText')) {
                        document.getElementById('expectedText').value = roi.expected_text || '';
                    }
                    if (document.getElementById('ocrRotation')) {
                        document.getElementById('ocrRotation').value = roi.rotation || 0;
                    }
                    if (document.getElementById('caseSensitive')) {
                        document.getElementById('caseSensitive').checked = roi.case_sensitive || false;
                    }
                    break;

                case 'compare':
                    if (document.getElementById('detectionMethod')) {
                        // Server format uses feature_method, client format uses detection_method
                        document.getElementById('detectionMethod').value = roi.feature_method || roi.detection_method || 'mobilenet';
                    }
                    break;

                case 'color':
                    if (document.getElementById('expectedColor')) {
                        // Server v3.2 format: expected_color is directly on ROI object
                        const colorValue = roi.expected_color;

                        // Handle RGB array from server [r, g, b]
                        if (Array.isArray(colorValue) && colorValue.length === 3) {
                            const hexValue = rgbToHex(colorValue);
                            document.getElementById('expectedColor').value = hexValue;

                            // Sync color picker
                            if (document.getElementById('expectedColorPicker')) {
                                document.getElementById('expectedColorPicker').value = hexValue;
                            }
                        }
                        // Handle hex string (legacy or from text input)
                        else if (colorValue && typeof colorValue === 'string') {
                            document.getElementById('expectedColor').value = colorValue;

                            if (document.getElementById('expectedColorPicker') && colorValue.startsWith('#')) {
                                document.getElementById('expectedColorPicker').value = colorValue;
                            }
                        }
                    }
                    if (document.getElementById('colorTolerance')) {
                        // Server v3.2: color_tolerance is directly on ROI object
                        document.getElementById('colorTolerance').value = roi.color_tolerance || 10;
                    }
                    if (document.getElementById('minPixelPercentage')) {
                        // Server v3.2: min_pixel_percentage is directly on ROI object
                        document.getElementById('minPixelPercentage').value = roi.min_pixel_percentage || 5.0;
                    }
                    break;
            }
        }
    }
}

function updateROIProperty(property, value) {
    if (!editorState.selectedROI) return;

    // Handle detection_method -> feature_method mapping for server format
    if (property === 'detection_method') {
        editorState.selectedROI.feature_method = value;
    }
    // Handle roi_type_name -> type mapping and set appropriate defaults per v3.2
    else if (property === 'roi_type_name') {
        const typeMap = { 'barcode': 1, 'compare': 2, 'ocr': 3, 'color': 4 };
        const typeNum = typeMap[value] || 2;

        editorState.selectedROI.type = typeNum;
        editorState.selectedROI.roi_type_name = value; // Keep for compatibility

        // Set defaults and nulls according to server v3.2 validation
        if (value === 'color') {
            // Color ROI v3.2: Set required field with default, null the incompatible fields
            if (!editorState.selectedROI.expected_color) {
                editorState.selectedROI.expected_color = [0, 0, 0]; // Default black
            }
            // Optional fields (server adds defaults if missing)
            if (editorState.selectedROI.color_tolerance === undefined) {
                editorState.selectedROI.color_tolerance = 10;
            }
            if (editorState.selectedROI.min_pixel_percentage === undefined) {
                editorState.selectedROI.min_pixel_percentage = 5.0;
            }
            // Null incompatible fields for color ROIs
            editorState.selectedROI.ai_threshold = null;
            editorState.selectedROI.feature_method = null;
            editorState.selectedROI.expected_text = null;
            editorState.selectedROI.is_device_barcode = null;
        } else if (value === 'compare') {
            // Compare ROI: needs ai_threshold and feature_method
            if (editorState.selectedROI.ai_threshold === null) {
                editorState.selectedROI.ai_threshold = 0.8;
            }
            if (!editorState.selectedROI.feature_method) {
                editorState.selectedROI.feature_method = 'mobilenet';
            }
        } else if (value === 'barcode' || value === 'ocr') {
            // Barcode/OCR: ai_threshold is null/optional
            editorState.selectedROI.ai_threshold = null;
            editorState.selectedROI.feature_method = null;
        }

        // Refresh the properties panel to update field states (enable/disable AI threshold)
        updatePropertiesPanel();
    }
    // Server v3.2: color properties are directly on ROI object, not wrapped
    else {
        editorState.selectedROI[property] = value;
    }

    updateROIList();
    updateSummary();
    redrawCanvas();
}

// Color picker helper functions
function hexToRgb(hex) {
    // Remove # if present
    hex = hex.replace(/^#/, '');

    // Parse hex to RGB
    const r = parseInt(hex.substring(0, 2), 16);
    const g = parseInt(hex.substring(2, 4), 16);
    const b = parseInt(hex.substring(4, 6), 16);

    return [r, g, b];
}

function rgbToHex(rgb) {
    if (Array.isArray(rgb) && rgb.length === 3) {
        return '#' + rgb.map(x => {
            const hex = Math.max(0, Math.min(255, x)).toString(16);
            return hex.length === 1 ? '0' + hex : hex;
        }).join('');
    }
    return '#000000';
}

function updateColorFromPicker(hexValue) {
    const colorNameInput = document.getElementById('expectedColor');
    const rgbArray = hexToRgb(hexValue);

    if (colorNameInput) {
        // Display hex for user readability
        colorNameInput.value = hexValue;
    }

    // Store RGB array - server v3.2: expected_color directly on ROI object
    if (editorState.selectedROI) {
        editorState.selectedROI.expected_color = rgbArray;
        updateROIList();
        updateSummary();
        redrawCanvas();
    }
}

function updatePickerFromText(value) {
    const colorPicker = document.getElementById('expectedColorPicker');

    // Check if it's a hex value
    if (colorPicker && value.startsWith('#') && /^#[0-9A-Fa-f]{6}$/.test(value)) {
        colorPicker.value = value;
        // Convert to RGB array - server v3.2: expected_color directly on ROI object
        if (editorState.selectedROI) {
            editorState.selectedROI.expected_color = hexToRgb(value);
            updateROIList();
            updateSummary();
            redrawCanvas();
        }
    }
}

function selectPresetColor(hexValue, colorName) {
    const colorPicker = document.getElementById('expectedColorPicker');
    const colorInput = document.getElementById('expectedColor');
    const rgbArray = hexToRgb(hexValue);

    if (colorPicker) colorPicker.value = hexValue;
    if (colorInput) {
        // Show both name and hex for clarity
        colorInput.value = `${colorName} (${hexValue})`;
    }

    // Store RGB array - server v3.2: expected_color directly on ROI object
    if (editorState.selectedROI) {
        editorState.selectedROI.expected_color = rgbArray;
        updateROIList();
        updateSummary();
        redrawCanvas();
    }

    // Visual feedback - highlight selected button
    document.querySelectorAll('.color-preset-btn').forEach(btn => {
        btn.classList.remove('selected');
    });
    event.target.closest('.color-preset-btn').classList.add('selected');
}

function updateCoordinates() {
    if (!editorState.selectedROI) return;

    const x1 = parseInt(document.getElementById('x1').value);
    const y1 = parseInt(document.getElementById('y1').value);
    const x2 = parseInt(document.getElementById('x2').value);
    const y2 = parseInt(document.getElementById('y2').value);

    ROI.setCoords(editorState.selectedROI, [x1, y1, x2, y2]);
    updateROIList();
    redrawCanvas();
}

function updateSummary() {
    document.getElementById('roiCount').textContent = editorState.rois.length;

    const devices = new Set(editorState.rois.map(r => ROI.getDevice(r)));
    document.getElementById('deviceCount').textContent = devices.size;

    const summaryEl = document.getElementById('configSummary');

    if (editorState.rois.length === 0) {
        summaryEl.innerHTML = '<p class="empty-state">No configuration loaded</p>';
        return;
    }

    // Count ROIs by type
    const typeCounts = {};
    editorState.rois.forEach(roi => {
        typeCounts[roi.roi_type_name] = (typeCounts[roi.roi_type_name] || 0) + 1;
    });

    summaryEl.innerHTML = '';
    Object.entries(typeCounts).forEach(([type, count]) => {
        const item = document.createElement('div');
        item.className = 'summary-item';
        item.innerHTML = `
            <span class="summary-label">${type}:</span>
            <span class="summary-value">${count}</span>
        `;
        summaryEl.appendChild(item);
    });
}

// ==================== Configuration Save/Export ====================
function validateConfiguration() {
    const errors = [];

    if (!editorState.currentProduct) {
        errors.push('No product selected');
    }

    if (editorState.rois.length === 0) {
        errors.push('No ROIs defined');
    }

    // Check for duplicate ROI IDs
    const ids = editorState.rois.map(r => ROI.getId(r));
    const uniqueIds = new Set(ids);
    if (ids.length !== uniqueIds.size) {
        errors.push('Duplicate ROI IDs found');
    }

    // Check for invalid coordinates
    editorState.rois.forEach(roi => {
        const [x1, y1, x2, y2] = ROI.getCoords(roi);
        if (x1 >= x2 || y1 >= y2) {
            errors.push(`ROI ${ROI.getId(roi)} has invalid coordinates`);
        }
    });

    // Validate color ROIs per v3.2 requirements
    editorState.rois.forEach(roi => {
        const roiType = ROI.getType(roi);
        const roiId = ROI.getId(roi);

        if (roiType === 'color') {
            // Required field: expected_color
            if (!roi.expected_color || !Array.isArray(roi.expected_color) || roi.expected_color.length !== 3) {
                errors.push(`ROI ${roiId}: Color ROI must have 'expected_color' as RGB array [R, G, B]`);
            } else {
                // Validate color values are 0-255
                const invalidColors = roi.expected_color.some(c => c < 0 || c > 255);
                if (invalidColors) {
                    errors.push(`ROI ${roiId}: Color values must be between 0 and 255`);
                }
            }
        }
    });

    if (errors.length > 0) {
        showNotification('Validation failed:\n' + errors.join('\n'), 'error');
        return false;
    }

    showNotification('✓ Configuration is valid', 'success');
    return true;
}

async function saveConfiguration() {
    if (!validateConfiguration()) return;

    if (!editorState.connected) {
        showNotification('Not connected to server', 'error');
        return;
    }

    try {
        showNotification('Saving configuration...', 'info');

        const config = {
            product_name: editorState.currentProduct,
            rois: editorState.rois
        };

        // Use client proxy endpoint to avoid CORS
        const response = await fetch(
            `/api/products/${editorState.currentProduct}/config`,
            {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(config)
            }
        );

        if (!response.ok) throw new Error('Save failed');

        const result = await response.json();
        showNotification('✓ Configuration saved to server', 'success');
    } catch (error) {
        showNotification(`Failed to save: ${error.message}`, 'error');
    }
}

function exportConfiguration() {
    if (editorState.rois.length === 0) {
        showNotification('No configuration to export', 'error');
        return;
    }

    const config = {
        product_name: editorState.currentProduct,
        rois: editorState.rois,
        exported_at: new Date().toISOString()
    };

    const blob = new Blob([JSON.stringify(config, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);

    const a = document.createElement('a');
    a.href = url;
    a.download = `${editorState.currentProduct}_roi_config.json`;
    a.click();

    URL.revokeObjectURL(url);
    showNotification('Configuration exported', 'success');
}

// ==================== Theme Management ====================
function toggleTheme() {
    editorState.theme = editorState.theme === 'light' ? 'dark' : 'light';
    document.body.className = `${editorState.theme}-theme`;
    localStorage.setItem('theme', editorState.theme);
    redrawCanvas();
}

function loadTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    editorState.theme = savedTheme;
    document.body.className = `${savedTheme}-theme`;
}

// ==================== Toast Notifications ====================
function showNotification(message, type = 'info') {
    const container = document.getElementById('toasts');

    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    // Icon based on type
    const icons = {
        success: '✓',
        error: '✕',
        warning: '⚠',
        info: 'ℹ'
    };

    // Create toast structure
    toast.innerHTML = `
        <div class="toast-icon">${icons[type] || icons.info}</div>
        <div class="toast-message">${message}</div>
    `;

    container.appendChild(toast);

    // Auto-remove after 5 seconds
    setTimeout(() => {
        toast.remove();
    }, 5000);
}
