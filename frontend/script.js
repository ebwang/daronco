// frontend/script.js - Host management through the REST API (Python/FastAPI)

// Detects the current browser hostname (e.g. localhost, 127.0.0.1 or a network IP)
const host = window.location.hostname || 'localhost';
const API_URL = `http://${host}:8000/api/hosts`;

document.addEventListener('DOMContentLoaded', function () {
    const hostForm = document.getElementById('hostForm');
    const tableBody = document.getElementById('hostsTableBody');
    const counterBadge = document.getElementById('hostCounter');
    const apiAlert = document.getElementById('apiAlert');

    // Loads the host list from the Python API on page load
    fetchHosts();

    // Listener for the form submission
    if (hostForm) {
        hostForm.addEventListener('submit', async function (e) {
            e.preventDefault();

            // Native Bootstrap validation
            if (!hostForm.checkValidity()) {
                e.stopPropagation();
                hostForm.classList.add('was-validated');
                return;
            }

            const newHost = {
                hostname: document.getElementById('hostHostname').value.trim(),
                manufacturer: document.getElementById('hostManufacturer').value.trim(),
                model: document.getElementById('hostModel').value.trim(),
                cpu: document.getElementById('hostCpu').value.trim(),
                cpu_count: parseInt(document.getElementById('hostCpuCount').value, 10) || 1,
                ram: document.getElementById('hostRam').value.trim(),
                disk: document.getElementById('hostDisk').value.trim(),
                storage_type: document.getElementById('hostStorageType').value,
                interfaces: document.getElementById('hostInterfaces').value.trim(),
                ips: document.getElementById('hostIps').value.trim(),
                location: document.getElementById('hostLocation').value.trim()
            };

            try {
                // Sends the POST request to the Python server
                const response = await fetch(API_URL, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(newHost)
                });

                if (!response.ok) {
                    throw new Error('Failed to create the host in the API');
                }

                const savedHost = await response.json();
                addHostToTable(savedHost);

                // Resets the form
                hostForm.reset();
                hostForm.classList.remove('was-validated');
                hideApiAlert();
            } catch (error) {
                console.error('Error in the POST request:', error);
                showApiAlert();
            }
        });
    }

    // Listener for host deletion (event delegation)
    if (tableBody) {
        tableBody.addEventListener('click', async function (e) {
            const deleteBtn = e.target.closest('.btn-delete');
            if (deleteBtn) {
                const row = deleteBtn.closest('tr');
                const hostId = deleteBtn.getAttribute('data-id');

                if (row && hostId) {
                    try {
                        const response = await fetch(`${API_URL}/${hostId}`, {
                            method: 'DELETE'
                        });

                        if (response.ok) {
                            row.remove();
                            updateCounter();
                            hideApiAlert();
                        } else {
                            throw new Error('Failed to delete the host in the API');
                        }
                    } catch (error) {
                        console.error('Error while deleting the host:', error);
                        showApiAlert();
                    }
                }
            }
        });
    }

    /**
     * Fetches every host stored in the Python API and renders them in the table
     */
    async function fetchHosts() {
        try {
            const response = await fetch(API_URL);
            if (!response.ok) throw new Error('Server unavailable');
            
            const hosts = await response.json();
            tableBody.innerHTML = '';
            hosts.forEach(addHostToTable);
            updateCounter();
            hideApiAlert();
        } catch (error) {
            console.warn('API offline or not found:', error);
            showApiAlert();
        }
    }

    /**
     * Renders one Host row in the HTML table
     * @param {Object} host Host data returned by the API
     */
    function addHostToTable(host) {
        const tr = document.createElement('tr');

        let badgeClass = 'bg-secondary';
        if (host.storage_type === 'SSD') badgeClass = 'bg-success';
        else if (host.storage_type === 'NVMe') badgeClass = 'bg-primary';
        else if (host.storage_type === 'Hybrid') badgeClass = 'bg-info text-dark';

        tr.innerHTML = `
            <td>${escapeHtml(host.hostname)}</td>
            <td>${escapeHtml(host.manufacturer)}</td>
            <td>${escapeHtml(host.model)}</td>
            <td>${escapeHtml(host.cpu)}</td>
            <td>${escapeHtml(host.cpu_count)}</td>
            <td>${escapeHtml(host.ram)}</td>
            <td>${escapeHtml(host.disk)}</td>
            <td><span class="badge ${badgeClass}">${escapeHtml(host.storage_type)}</span></td>
            <td>${escapeHtml(host.interfaces)}</td>
            <td>${escapeHtml(host.ips)}</td>
            <td>${escapeHtml(host.location)}</td>
            <td class="text-center">
                <button class="btn btn-sm btn-outline-danger btn-delete" data-id="${host.id}" title="Delete Host">
                    <i class="bi bi-trash"></i>
                </button>
            </td>
        `;

        tableBody.appendChild(tr);
        updateCounter();
    }

    /**
     * Updates the visual host counter badge
     */
    function updateCounter() {
        if (counterBadge && tableBody) {
            const total = tableBody.children.length;
            counterBadge.textContent = `Total: ${total} host${total !== 1 ? 's' : ''}`;
        }
    }

    function showApiAlert() {
        if (apiAlert) apiAlert.classList.remove('d-none');
    }

    function hideApiAlert() {
        if (apiAlert) apiAlert.classList.add('d-none');
    }

    function escapeHtml(str) {
        if (!str && str !== 0) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }
});
