let currentOrder = 'asc';  // Default order
let currentOrderBy = 'date_of_task'; // Default sort column

function toggleOrder() {
    currentOrder = currentOrder === 'asc' ? 'desc' : 'asc';
    return currentOrder;
}

$('#filterModal').on('show.bs.modal', function () {
    document.getElementById('filterTitle').value = '{{ filter_title }}';
    document.getElementById('filterStartDate').value = '{{ filter_start_date }}';
    document.getElementById('filterEndDate').value = '{{ filter_end_date }}';
    // Set checkboxes for urgency based on 'filter_urgencies' array
    document.getElementById('veryImportantCheck').checked = "{{ '1' in filter_urgencies }}";
    document.getElementById('filterStatus').value = '{{ filter_status }}';
});


let currentFilters = {};  // Global object to hold the current filters

function applyFilters() {
    // Gather filter data from form inputs
    currentFilters = {
        title: document.getElementById('filterTitle').value,
        startDate: document.getElementById('filterStartDate').value,
        endDate: document.getElementById('filterEndDate').value,
        status: document.getElementById('filterStatus').value,
        urgency: document.getElementById('filterUrgency').value,
        order_by: document.getElementById('dropdown_sort').value,
        order: document.getElementById('dropdown_order').value
    };

    // Trigger sorting with filters
    loadSortedTasks(currentFilters.order_by, currentFilters.order); // Assume default sort
}


function loadSortedTasks(orderBy, order) {
    currentOrderBy = orderBy; // Update the current sorting column
    let orderToggle = toggleOrder(); // Toggle the sorting order

    // Include filter parameters in the fetch request
    let urlParams = new URLSearchParams({
        ...currentFilters,
        order_by: orderBy,
        order: orderToggle
    }).toString();

    fetch(`/sort-tasks?${urlParams}`)
        .then(response => response.json())
        .then(data => {
            const tableBody = document.getElementById('tasks');
            tableBody.innerHTML = ''; // Clear the current rows
            data.tasks.forEach(task => {
                // Ensure each task row maintains all functionalities
                tableBody.innerHTML += `<tr>
                    <td><a href="/task/${task.id}/detail" style="color: black">${task.task}</a></td>
                    <td>${task.date_of_task}</td>
                    <td>${task.day}</td>
                    <td>${task.urgency}</td>
                    <td>${task.status}</td>
                    <td><a class="btn btn-primary" href="/task/${task.id}/edit">Edit Task</a></td>
                </tr>`;
            });
        })
        .catch(error => {
            console.error('Error loading sorted tasks:', error);
        });
}

document.getElementById('urgency-sort-button').addEventListener('click', function () {
    loadSortedTasks('urgency_id');
});
document.getElementById('status-sort-button').addEventListener('click', function () {
    loadSortedTasks('status_id');
});
document.getElementById('date-sort-button').addEventListener('click', function () {
    loadSortedTasks('date_of_task');
});
function loadWeeklySchedule() {
    fetch('/weekly')
        .then(response => response.json())
        .then(tasks => {
            const tableBody = document.getElementById('tasks');
            tableBody.innerHTML = ''; // Clear current tasks
            tasks.forEach(task => {
                tableBody.innerHTML += `
                <tr>
                    <td><a href="/task/${task.id}/detail" style="color: black">${task.task}</a></td>
                    <td>${task.date_of_task}</td>
                    <td>${task.day}</td>
                    <td>${task.urgency}</td>
                    <td>${task.status}</td>
                    <td><a class="btn btn-primary" href="/task/${task.id}/edit">Edit</a></td>
                </tr>
            `;
            });
        })
        .catch(error => console.error('Error loading weekly tasks:', error));

}