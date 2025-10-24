const RECENT_MSEC = 10 * 1000;
let currentSortField = null;
let resortTimer = null;
let allParticipantsData = {};
let currentStatusFilter = '';

function flashGreen($ele) {
    $ele.css('background-color', 'green');
    $ele.animate({
            backgroundColor: "white"
        },
        10000
    );
}

function initWebSocket(socketUrl, $tbody, visitedParticipants, $msgRefreshed) {
    $msgRefreshed.hide();
    monitorSocket = makeReconnectingWebSocket(socketUrl);
    monitorSocket.onmessage = function (e) {
        var data = JSON.parse(e.data);
        if (data.type === 'update_waiting_for_list') {
            updateWaitingForList($tbody[0], data.ids, data.note);
        } else {
            let updatedIds = refreshTable(data.rows, $tbody, visitedParticipants);
            let msg = recentlyActiveParticipantsMsg(updatedIds);
            if (msg) {
                $msgRefreshed.text(msg);
                $msgRefreshed.stop(true, true);
                $msgRefreshed.show();
                $msgRefreshed.css('opacity', 1);
                $msgRefreshed.fadeOut(RECENT_MSEC);
            }
        }
    }
}

function recentlyActiveParticipantsMsg(newIds) {
    if (newIds.length === 0) return '';
    let d = recentlyActiveParticipants;
    let now = Date.now();
    for (let id of newIds) {
        d[id] = now;
    }
    for (let [k, v] of Object.entries(d)) {
        if (v < now - RECENT_MSEC) delete d[k];
    }
    let listing = Object.keys(d).slice(0, 10).sort().map(id => 'P' + id.toString()).join(', ');
    return `Updates: ${listing}`;
}

function advanceUsers() {
    let csrftoken = document.querySelector("[name=csrftoken]").value;
    let advancemode = document.querySelector('[name=advance_participants_mode]').value;

    let serverErrorDiv = $("#auto_advance_server_error");
    $.ajax({
        url: advanceUrl,
        type: 'POST',
        data: {
            csrftoken,
            advancemode
        },
        error: function (jqXHR, textStatus) {
            serverErrorDiv.show();
            // enable the button so they can try again?
        },
        success: function () {
            serverErrorDiv.hide();
        }
    });
}

function advanceSelectedUser() {
    let csrftoken = document.querySelector("[name=csrftoken]").value;
    let selectedRadio = document.querySelector('[name=selected_participant]:checked');
    let selected_participant = selectedRadio ? selectedRadio.value : null;

    let serverErrorDiv = $("#auto_advance_server_error");
    $.ajax({
        url: advanceUrl,
        type: 'POST',
        data: {
            csrftoken,
            selected_participant
        },
        error: function (jqXHR, textStatus) {
            serverErrorDiv.show();
            // enable the button so they can try again?
        },
        success: function () {
            serverErrorDiv.hide();
        }
    });
}

function getNthBodyRowSelector(n) {
    return `tr:nth-of-type(${n + 1})`;
    //return `tr:eq(${n})`;
}

function updateWaitingForList(tbody, ids, note) {
    for (let id of ids) {
        if (visitedParticipants.includes(id)) {
            updateRow(tbody, id, {_monitor_note_json: note});
        }
    }
}

function makeMonitorCellSortKey(values, fieldName) {
    let fieldValue = values[fieldName];
    if (fieldName === '_numeric_label') {
        return values['id_in_session'];
    }
    if (fieldName === '_current_page_of_total') {
        return -fieldValue[0];
    }
    if (fieldName === '_presence') {
        return {
            '🟢': 0,
            '🟡': 1,
            '⚪': 2,
            '': 2
        }[fieldValue];
    }
    if (fieldName === '_monitor_note_json') {
        return -JSON.parse(fieldValue).length;
    }
    return fieldValue;
}


function makeMonitorCellDisplayValue(value, fieldName) {
    if (value === null) {
        return '';
    }
    if (fieldName === 'id_in_session') {
        return `P${value}`;
    }
    if (fieldName === '_last_page_timestamp') {
        let date = new Date(parseFloat(value) * 1000);
        let dateString = date.toISOString();
        return `<time class="timeago" datetime="${dateString}"></time>`;
    }
    if (fieldName === '_current_page_of_total') {
        return `${value[0]}/${value[1]}`;
    }
    if (fieldName === '_monitor_note_json') {
        return JSON.parse(value).join(', ');
    }

    return value.toString();
}

function createTableRowMonitor(values, id_in_session) {
    let tr = document.createElement('tr');
    tr.dataset.id_in_session = id_in_session;
    for (let [field, value] of Object.entries(values)) {
        // Skip status field - it's used for filtering but not displayed in table
        if (field === 'status') continue;

        let td = document.createElement('td');
        td.dataset.field = field;
        let newRowSortKey = makeMonitorCellSortKey(values, field);
        td.dataset.sortkey = JSON.stringify(newRowSortKey);
        td.innerHTML = makeMonitorCellDisplayValue(value, field);
        tr.appendChild(td)
    }

    tr.insertAdjacentHTML(
        'beforeend',
        // better to use radio than checkbox because then you never
        // forget to uncheck someone else and unintentionally advance them.
        // use <label> to get a bigger hit area
        // 2025-09-07: add this back in later
        // `<td><label style="display: block"><input type="radio" name="selected_participant" value="${row.code}"></label></td>`
        `<td></td>`
    );

    return tr;
}


function updateRow(tbody, id_in_session, newValues) {
    let didUpdate = false;
    let tr = tbody.querySelector(`[data-id_in_session='${id_in_session}']`);
    for (let fieldName of Object.keys(newValues)) {
        // Skip status field - it's used for filtering but not displayed in table
        if (fieldName === 'status') continue;

        let cell = tr.querySelector(`td[data-field='${fieldName}']`);

        let prev = JSON.parse(cell.dataset.sortkey);
        let newSortKey = makeMonitorCellSortKey(newValues, fieldName);
        if (prev !== newSortKey) {
            cell.dataset.sortkey = JSON.stringify(newSortKey);
            cell.innerHTML = makeMonitorCellDisplayValue(newValues[fieldName], fieldName);
            flashGreen($(cell));
            didUpdate = true;
        }
    }
    return didUpdate;
}

function sortTable(fieldName) {
    if (fieldName) {
        currentSortField = fieldName;
        updateSortIndicators(fieldName);
    }

    if (!currentSortField) return;

    let tbody = document.querySelector('#monitor-table tbody');
    let rows = Array.from(tbody.querySelectorAll('tr'));

    // FLIP: First - record initial positions by row element
    const firstPositions = new Map();
    rows.forEach(row => {
        const rect = row.getBoundingClientRect();
        firstPositions.set(row, rect.top);
    });

    rows.sort((a, b) => {
        let cellA = a.querySelector(`td[data-field='${currentSortField}']`);
        let cellB = b.querySelector(`td[data-field='${currentSortField}']`);

        let sortKeyA = JSON.parse(cellA.dataset.sortkey);
        let sortKeyB = JSON.parse(cellB.dataset.sortkey);

        let comparison = 0;
        if (sortKeyA < sortKeyB) comparison = -1;
        if (sortKeyA > sortKeyB) comparison = 1;

        // Stable sort: if equal, sort by id_in_session
        if (comparison === 0) {
            let idA = parseInt(a.dataset.id_in_session);
            let idB = parseInt(b.dataset.id_in_session);
            comparison = idA - idB;
        }

        return comparison;
    });

    // FLIP: Last - reorder DOM
    rows.forEach(row => tbody.appendChild(row));

    // FLIP: Invert & Play - animate from old to new positions
    rows.forEach(row => {
        const firstTop = firstPositions.get(row);
        const lastTop = row.getBoundingClientRect().top;
        const deltaY = firstTop - lastTop;

        if (deltaY !== 0) {
            row.style.transform = `translateY(${deltaY}px)`;
            row.style.transition = 'transform 0s';

            requestAnimationFrame(() => {
                row.style.transition = 'transform 0.3s ease';
                row.style.transform = 'translateY(0)';
            });
        }
    });
}

function updateSortIndicators(fieldName) {
    document.querySelectorAll('th a[data-sortable]').forEach(link => {
        link.textContent = link.textContent.replace('▼ ', '');
    });

    let currentHeader = document.querySelector(`th a[data-field='${fieldName}']`);
    currentHeader.textContent = '▼ ' + currentHeader.textContent;
}

function initSortableHeaders() {
    document.querySelectorAll('th a[data-sortable="true"]').forEach(link => {
        link.style.cursor = 'pointer';
        link.addEventListener('click', (e) => {
            e.preventDefault();
            let fieldName = link.dataset.field;
            sortTable(fieldName);
        });
    });
}

function debouncedResort() {
    if (!currentSortField) return;

    // Clear existing timer
    if (resortTimer) {
        clearTimeout(resortTimer);
    }

    // Set new timer for 1.5 seconds
    resortTimer = setTimeout(() => {
        sortTable();
        resortTimer = null;
    }, 1000);
}

function updateStatusFilterDropdown() {
    let statusCounts = {};
    let inProgressCount = 0;

    for (let [id, data] of Object.entries(allParticipantsData)) {
        let status = data.status || '';
        if (status === '') {
            inProgressCount++;
        } else {
            statusCounts[status] = (statusCounts[status] || 0) + 1;
        }
    }

    let statusFilterDropdown = document.getElementById('status_filter');
    let dropdownContainer = statusFilterDropdown.parentElement;
    let currentValue = statusFilterDropdown.value;

    // Hide dropdown if only status is ''
    if (Object.keys(statusCounts).length === 0) {
        dropdownContainer.style.display = 'none';
        return;
    } else {
        dropdownContainer.style.display = '';
    }

    // Clear and rebuild options
    statusFilterDropdown.innerHTML = '';

    function makeStatusOption(value, displayText, count) {
        let option = document.createElement('option');
        option.value = value;
        option.textContent = `${displayText}: ${count}`;
        statusFilterDropdown.appendChild(option);
    }

    // Add in progress option
    makeStatusOption('', '(default)', inProgressCount);

    // Add other status options sorted alphabetically
    let sortedStatuses = Object.keys(statusCounts).sort();
    for (let status of sortedStatuses) {
        makeStatusOption(status, status, statusCounts[status]);
    }

    // Restore previous selection if it still exists
    if (currentValue !== '' && statusCounts[currentValue]) {
        statusFilterDropdown.value = currentValue;
    } else if (currentValue !== '') {
        // Previous selection no longer exists, reset to in progress
        statusFilterDropdown.value = '';
        currentStatusFilter = '';
    }
}

function updateParticipantStatusCounts() {
    let started = Object.keys(allParticipantsData).length;
    let inProgressCount = 0;

    for (let [id, data] of Object.entries(allParticipantsData)) {
        if (!data.status || data.status === '') {
            inProgressCount++;
        }
    }

    document.getElementById('num_participants_started').textContent = started;
    document.getElementById('num_participants_in_progress').textContent = inProgressCount;

    updateStatusFilterDropdown();
}

function shouldShowParticipant(participantData) {
    let participantStatus = participantData.status || '';
    return participantStatus === currentStatusFilter;
}

function applyStatusFilter() {
    let tbody = document.querySelector('#monitor-table tbody');
    let rows = tbody.querySelectorAll('tr');

    for (let row of rows) {
        let id = row.dataset.id_in_session;
        let participantData = allParticipantsData[id];
        if (participantData && shouldShowParticipant(participantData)) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    }
}

function refreshTable(new_json, $tbody, visitedParticipants) {
    let updatedParticipants = [];
    let tbody = $tbody[0];
    let hasNewParticipant = false;
    let allIds = new Set();

    for (let newValues of new_json) {
        let id_in_session = newValues.id_in_session;
        allIds.add(id_in_session);

        // Store data for all participants
        allParticipantsData[id_in_session] = newValues;

        let index = visitedParticipants.indexOf(id_in_session);
        if (index === -1) {
            // New participant
            index = visitedParticipants.filter((id) => id < id_in_session).length;
            let newRow = createTableRowMonitor(newValues, id_in_session);
            let rowSelector = getNthBodyRowSelector(index);
            if (index === visitedParticipants.length) {
                tbody.appendChild(newRow);
            } else {
                tbody.insertBefore(newRow, tbody.querySelector(rowSelector));
            }
            let tr = tbody.querySelector(rowSelector);

            // Apply filter to new row immediately
            if (!shouldShowParticipant(newValues)) {
                tr.style.display = 'none';
            } else {
                flashGreen($(tr));
            }

            visitedParticipants.splice(index, 0, id_in_session);
            hasNewParticipant = true;
            updatedParticipants.push(id_in_session);
        } else {
            let didUpdate = updateRow(tbody, id_in_session, newValues);
            if (didUpdate) updatedParticipants.push(id_in_session);

            // Reapply filter in case status changed
            let tr = tbody.querySelector(`[data-id_in_session='${id_in_session}']`);
            if (tr) {
                if (!shouldShowParticipant(newValues)) {
                    tr.style.display = 'none';
                } else {
                    tr.style.display = '';
                }
            }
        }
    }

    updateParticipantStatusCounts();
    $(".timeago").timeago();

    // Debounced re-sort: wait 1.5s after last update
    debouncedResort();

    return updatedParticipants;
}