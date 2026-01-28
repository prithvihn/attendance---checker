// Update current date and time
function updateDateTime() {
    const dateElement = document.getElementById('current-date');
    const timeElement = document.getElementById('current-time');

    if (dateElement && timeElement) {
        const now = new Date();
        const dateOptions = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
        const timeOptions = { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true };

        dateElement.textContent = now.toLocaleDateString('en-US', dateOptions);
        timeElement.textContent = now.toLocaleTimeString('en-US', timeOptions);
    }
}

// Update date and time every second
setInterval(updateDateTime, 1000);
updateDateTime();

// Modal functionality
const modal = document.getElementById('attendance-modal');
const markPresentBtn = document.getElementById('mark-present');
const markAbsentBtn = document.getElementById('mark-absent');
const closeBtn = document.querySelector('.close');
const cancelBtn = document.getElementById('cancel-btn');

if (markPresentBtn) {
    markPresentBtn.addEventListener('click', () => {
        modal.style.display = 'block';
    });
}

if (markAbsentBtn) {
    markAbsentBtn.addEventListener('click', () => {
        modal.style.display = 'block';
    });
}

if (closeBtn) {
    closeBtn.addEventListener('click', () => {
        modal.style.display = 'none';
    });
}

if (cancelBtn) {
    cancelBtn.addEventListener('click', () => {
        modal.style.display = 'none';
    });
}

// Close modal when clicking outside of it
window.addEventListener('click', (event) => {
    if (event.target === modal) {
        modal.style.display = 'none';
    }
});

// Form submission
const attendanceForm = document.querySelector('.modal-content form');
if (attendanceForm) {
    attendanceForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const studentId = document.getElementById('student-id').value;
        const status = document.getElementById('attendance-status').value;
        const remarks = document.getElementById('remarks').value;

        console.log({
            studentId,
            status,
            remarks,
            timestamp: new Date().toISOString()
        });

        alert(`Attendance marked successfully!\nStudent ID: ${studentId}\nStatus: ${status}`);
        modal.style.display = 'none';
        attendanceForm.reset();
    });
}

// Search functionality
const searchInput = document.getElementById('search-input');
if (searchInput) {
    searchInput.addEventListener('keyup', (e) => {
        const searchTerm = e.target.value.toLowerCase();
        const tableRows = document.querySelectorAll('.attendance-table tbody tr');

        tableRows.forEach(row => {
            const text = row.textContent.toLowerCase();
            if (text.includes(searchTerm)) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    });
}

// Filter by class
const classFilter = document.getElementById('class-filter');
if (classFilter) {
    classFilter.addEventListener('change', filterTable);
}

// Filter by status
const statusFilter = document.getElementById('status-filter');
if (statusFilter) {
    statusFilter.addEventListener('change', filterTable);
}

function filterTable() {
    const selectedClass = document.getElementById('class-filter').value;
    const selectedStatus = document.getElementById('status-filter').value;
    const tableRows = document.querySelectorAll('.attendance-table tbody tr');

    tableRows.forEach(row => {
        const classCell = row.cells[2].textContent;
        const statusCell = row.cells[4].textContent.toLowerCase();

        let showRow = true;

        if (selectedClass && !classCell.includes(selectedClass)) {
            showRow = false;
        }

        if (selectedStatus && !statusCell.includes(selectedStatus)) {
            showRow = false;
        }

        row.style.display = showRow ? '' : 'none';
    });
}

// Delete button functionality
const deleteButtons = document.querySelectorAll('.btn-icon.delete');
deleteButtons.forEach(btn => {
    btn.addEventListener('click', () => {
        if (confirm('Are you sure you want to delete this record?')) {
            btn.closest('tr').style.opacity = '0.5';
            setTimeout(() => {
                btn.closest('tr').remove();
                alert('Record deleted successfully!');
            }, 300);
        }
    });
});

// Edit button functionality
const editButtons = document.querySelectorAll('.btn-icon.edit');
editButtons.forEach(btn => {
    btn.addEventListener('click', () => {
        alert('Edit functionality to be implemented');
    });
});

// Download Report button
const downloadReportBtn = document.getElementById('view-report');
if (downloadReportBtn) {
    downloadReportBtn.addEventListener('click', () => {
        alert('PDF Report generation feature coming soon!');
    });
}

// Export to Excel button
const exportExcelBtn = document.getElementById('export-excel');
if (exportExcelBtn) {
    exportExcelBtn.addEventListener('click', () => {
        alert('Excel export feature coming soon!');
    });
}

// Add smooth scroll behavior for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({ behavior: 'smooth' });
        }
    });
});

// Log page initialization
console.log('Attendance Management System loaded successfully!');
