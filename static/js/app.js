/**
 * Nmap Dashboard — Frontend JavaScript
 *
 * Handles scan type selection, form validation, search filtering,
 * loading states, and AJAX interactions.
 */

document.addEventListener('DOMContentLoaded', function () {
    initScanTypeSelector();
    initSearchFilter();
    initScanForm();
    initFlashDismiss();
});

/* --- Scan Type Selector (New Scan Page) --- */
function initScanTypeSelector() {
    const scanTypeCards = document.querySelectorAll('.scan-type-option');
    const hiddenInput = document.getElementById('scan_type_input');

    if (!scanTypeCards.length || !hiddenInput) return;

    scanTypeCards.forEach(function (card) {
        card.addEventListener('click', function () {
            // Toggle selection for this card
            card.classList.toggle('selected');
            
            // Collect all selected scan types
            const selectedCards = document.querySelectorAll('.scan-type-option.selected');
            const selectedTypes = Array.from(selectedCards).map(c => c.dataset.scanType);
            
            hiddenInput.value = selectedTypes.join(',');
        });
    });
}

/* --- Search / Filter on Tables --- */
function initSearchFilter() {
    const searchInput = document.getElementById('table-search');
    if (!searchInput) return;

    searchInput.addEventListener('input', function () {
        const query = this.value.toLowerCase().trim();
        const tableBody = document.querySelector('.filterable-table tbody');
        if (!tableBody) return;

        const rows = tableBody.querySelectorAll('tr');
        rows.forEach(function (row) {
            const text = row.textContent.toLowerCase();
            row.style.display = text.includes(query) ? '' : 'none';
        });
    });
}

/* --- Scan Form Validation & Loading --- */
function initScanForm() {
    const form = document.getElementById('scan-form');
    if (!form) return;

    form.addEventListener('submit', function (e) {
        const target = document.getElementById('target-input');
        const scanType = document.getElementById('scan_type_input');

        // Validate target
        if (!target || !target.value.trim()) {
            e.preventDefault();
            showAlert('Please enter a target IP address or hostname.', 'danger');
            target.focus();
            return;
        }

        // Validate scan type selected
        if (!scanType || !scanType.value) {
            e.preventDefault();
            showAlert('Please select a scan type.', 'danger');
            return;
        }

        // Validate target format
        var pattern = /^[a-zA-Z0-9][a-zA-Z0-9.\-:/,\s]*$/;
        if (!pattern.test(target.value.trim())) {
            e.preventDefault();
            showAlert('Target contains invalid characters. Only letters, numbers, dots, hyphens, colons, slashes, and commas are allowed.', 'danger');
            target.focus();
            return;
        }

        // Show loading overlay
        showLoadingOverlay();
    });
}

/* --- Loading Overlay --- */
function showLoadingOverlay() {
    var overlay = document.createElement('div');
    overlay.className = 'spinner-overlay';
    overlay.id = 'loading-overlay';
    overlay.innerHTML =
        '<div class="scan-spinner"></div>' +
        '<p class="spinner-text">Executing Nmap scan... This may take a while.</p>';
    document.body.appendChild(overlay);
}

function hideLoadingOverlay() {
    var overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.remove();
    }
}

/* --- Flash Message Alert --- */
function showAlert(message, type) {
    var container = document.getElementById('flash-container');
    if (!container) return;

    var alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-custom alert-' + type + ' alert-dismissible fade show';
    alertDiv.setAttribute('role', 'alert');

    var iconMap = {
        'success': '✓',
        'danger': '✕',
        'warning': '⚠',
        'info': 'ℹ'
    };

    alertDiv.innerHTML =
        '<span>' + (iconMap[type] || 'ℹ') + '</span> ' +
        '<span>' + message + '</span>' +
        '<button type="button" class="btn-close btn-close-white" data-bs-dismiss="alert" aria-label="Close"></button>';

    container.insertBefore(alertDiv, container.firstChild);

    // Auto-dismiss after 5 seconds
    setTimeout(function () {
        if (alertDiv.parentNode) {
            alertDiv.classList.remove('show');
            setTimeout(function () { alertDiv.remove(); }, 300);
        }
    }, 5000);
}

/* --- Auto-Dismiss Flash Messages --- */
function initFlashDismiss() {
    var alerts = document.querySelectorAll('.alert-custom');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            if (alert.parentNode) {
                alert.classList.remove('show');
                setTimeout(function () { alert.remove(); }, 300);
            }
        }, 8000);
    });
}
