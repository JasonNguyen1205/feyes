document.addEventListener('DOMContentLoaded', () => {
    const serverStatus = document.getElementById('server-status');
    const cameraStatus = document.getElementById('camera-status');
    const productSelect = document.getElementById('product-select');
    const cameraSelect = document.getElementById('camera-select');
    const initCameraBtn = document.getElementById('init-camera-btn');
    const captureBtn = document.getElementById('capture-btn');
    const exportBtn = document.getElementById('export-results-btn');
    const cameraFeed = document.getElementById('camera-feed');
    const resultsOverview = document.getElementById('results-overview');
    const resultsDetails = document.getElementById('results-details');

    let lastResults = null;

    // --- Status and Initialization ---

    function updateStatus(element, status) {
        element.className = 'status-indicator';
        element.classList.add(status); // 'connected', 'disconnected', 'pending'
    }

    async function checkServerStatus() {
        try {
            const response = await fetch('/api/health');
            if (response.ok) {
                updateStatus(serverStatus, 'connected');
                return true;
            }
        } catch (e) {
            // fall through
        }
        updateStatus(serverStatus, 'disconnected');
        return false;
    }

    async function loadInitialData() {
        if (await checkServerStatus()) {
            // Load products
            const products = await (await fetch('/api/products')).json();
            productSelect.innerHTML = products.map(p => `<option value="${p}">${p}</option>`).join('');

            // Load cameras
            const cameras = await (await fetch('/api/cameras')).json();
            cameraSelect.innerHTML = cameras.map(c => `<option value="${c.serial}">${c.name} (${c.serial})</option>`).join('');
            updateStatus(cameraStatus, cameras.length > 0 ? 'pending' : 'disconnected');
        }
    }

    // --- Camera and Capture ---

    initCameraBtn.addEventListener('click', async () => {
        const serial = cameraSelect.value;
        if (!serial) {
            alert('Please select a camera.');
            return;
        }
        updateStatus(cameraStatus, 'pending');
        const response = await fetch('/api/camera/initialize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ serial: serial })
        });
        if (response.ok) {
            updateStatus(cameraStatus, 'connected');
            startCameraFeed();
        } else {
            updateStatus(cameraStatus, 'disconnected');
            alert('Failed to initialize camera.');
        }
    });

    function startCameraFeed() {
        // Use a timestamp to prevent caching
        cameraFeed.src = `/api/camera/feed?t=${new Date().getTime()}`;
        cameraFeed.onload = () => {
            // To create a continuous stream, request the next frame upon successful load
            setTimeout(startCameraFeed, 100); // Adjust delay as needed
        };
        cameraFeed.onerror = () => {
            console.error('Camera feed error. Stopping.');
            updateStatus(cameraStatus, 'disconnected');
        };
    }

    captureBtn.addEventListener('click', async () => {
        const product = productSelect.value;
        const response = await fetch('/api/inspect', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ product: product })
        });
        const results = await response.json();
        lastResults = results;
        displayResults(results);
    });

    // --- Results Display ---

    function displayResults(results) {
        // Display overview
        const overallPass = results.devices.every(d => d.pass);
        resultsOverview.innerHTML = `Overall Status: <span class="${overallPass ? 'pass' : 'fail'}">${overallPass ? 'PASS' : 'FAIL'}</span>`;
        resultsOverview.className = overallPass ? 'pass' : 'fail';

        // Display details
        resultsDetails.innerHTML = '';
        for (const device of results.devices) {
            const deviceDiv = document.createElement('div');
            deviceDiv.className = 'device-result';

            const header = document.createElement('div');
            header.className = `device-header ${device.pass ? 'pass' : 'fail'}`;
            header.textContent = `Device ${device.id}: ${device.pass ? 'PASS' : 'FAIL'} (Barcode: ${device.barcode || 'N/A'})`;
            deviceDiv.appendChild(header);

            for (const roi of device.rois) {
                const roiP = document.createElement('p');
                roiP.className = `roi-result ${roi.pass ? 'pass' : 'fail'}`;
                roiP.textContent = `ROI ${roi.id} (${roi.type}): ${roi.pass ? 'Pass' : 'Fail'} - ${roi.details}`;
                deviceDiv.appendChild(roiP);
            }
            resultsDetails.appendChild(deviceDiv);
        }
    }

    // --- Export ---

    exportBtn.addEventListener('click', () => {
        if (!lastResults) {
            alert('No results to export. Please run an inspection first.');
            return;
        }
        const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(lastResults, null, 2));
        const downloadAnchorNode = document.createElement('a');
        downloadAnchorNode.setAttribute("href", dataStr);
        downloadAnchorNode.setAttribute("download", `inspection_results_${new Date().toISOString()}.json`);
        document.body.appendChild(downloadAnchorNode);
        downloadAnchorNode.click();
        downloadAnchorNode.remove();
    });

    // --- Initial Load ---

    setInterval(checkServerStatus, 10000); // Check server status every 10 seconds
    loadInitialData();
});
