/*
Lame trick...I increment the filename when I release a new version of this file,
because on runserver, Chrome caches it, so all oTree users developing on Chrome
would need to Ctrl+F5.
 */

function flashGreen($ele) {
    $ele.css('background-color', 'green');
    $ele.animate(
        {
            backgroundColor: "white"
        },
        10000
    );
}

function populateTableBody(tbody, rows) {
    for (let i = 0; i < rows.length; i++) {
        tbody.appendChild(createTableRow(rows[i], i));
    }
}

let groupIsFiltered = false;

function filterGroup(rowIdx) {

    if (groupIsFiltered) {
        for (let table of tables) {
            let tbody = table.querySelector('tbody');
            let trs = tbody.querySelectorAll('tr');
            for (let tr of trs) {
                tr.style.display = '';
            }
        }

        for (let th of document.getElementsByClassName(`id-in-session`)) {
            th.style.backgroundColor = 'white';
        }
        groupIsFiltered = false;

    } else {
        for (let tid = 0; tid < tables.length; tid++) {
            let table = tables[tid];
            let data = old_json[tid];
            let tbody = table.querySelector('tbody');
            let trs = tbody.querySelectorAll('tr');

            let curGroup = data[rowIdx][1];  // Group column is now at index 1
            let rowsInSameGroup = [];
            for (let i = 0; i < data.length; i++) {
                if (data[i][1] === curGroup)  // Group column is now at index 1
                    rowsInSameGroup.push(i);
            }
            for (let i = 0; i < trs.length; i++) {
                if (!rowsInSameGroup.includes(i)) {
                    trs[i].style.display = 'none';
                }
            }
        }
        for (let th of document.getElementsByClassName(`row-idx-${rowIdx}`))
            th.style.backgroundColor = 'yellow';

        groupIsFiltered = true;
    }
}

function createTableRow(row, row_number) {
    let tr = document.createElement('tr');
    tr.dataset.jsonindex = row_number;
    tr.innerHTML = `<th class='id-in-session row-idx-${row_number}'>P${row_number + 1}</th>`;
    for (let i = 0; i < row.length; i++) {
        let value = row[i];
        let td = document.createElement('td');
        if (i === 1) {
            // i === 1 is now the group column (participant.label is at i === 0)
            td.innerHTML = `<a href="#" onclick="filterGroup(${row_number})">${value}</a>`;
        } else {
            td.innerHTML = makeCellDisplayValue(value);
        }
        tr.appendChild(td)
    }
    return tr;
}


function truncateStringEllipsis(str, num) {
    if (str.length > num) {
        return str.slice(0, num) + "…";
    } else {
        return str;
    }
}


function makeCellDisplayValue(value, fieldName) {
    if (value === null) {
        return '';
    }
    if (fieldName === '_last_page_timestamp') {
        let date = new Date(parseFloat(value) * 1000);
        let dateString = date.toISOString();
        return `<time class="timeago" datetime="${dateString}"></time>`;
    }
    return value.toString();
}



function updateDataTable($table, new_json, old_json, field_headers) {
    let changeDescriptions = [];
    let $tbody = $table.find('tbody');
    // build table for the first time
    let numRows = new_json[0].length;
    for (let i = 0; i < new_json.length; i++) {
        let rowChanges = [];
        for (let j = 0; j < numRows; j++) {
            if (new_json[i][j] !== old_json[i][j]) {
                let rawValue = new_json[i][j];
                // Find row by data-jsonindex instead of DOM position
                let $cell = $tbody.find(`tr[data-jsonindex="${i}"]`).find(`td:eq(${j})`);
                let new_value = makeCellDisplayValue(rawValue);
                $cell.text(new_value);
                flashGreen($cell);
                let fieldName = field_headers[j];
                let newValueTrunc = truncateStringEllipsis(new_value, 7);
                rowChanges.push(`${fieldName}=${newValueTrunc}`);
            }
        }
        if (rowChanges.length > 0) {
            // @ makes it easier to scan visually
            changeDescriptions.push(`@P${i + 1}: ${rowChanges.join(', ')}`)
        }
    }
    return changeDescriptions;
}

// Sorting functionality
let currentSortField = {};  // Track by table index
let currentSortDirection = {};  // 1 for ascending, -1 for descending

function applySortWithoutToggle(tableIndex, fieldIndex, direction) {
    let table = tables[tableIndex];
    let tbody = table.querySelector('tbody');
    let data = old_json[tableIndex];

    if (!data || data.length === 0) return;

    updateSortIndicators(tableIndex, fieldIndex, direction);

    let rows = Array.from(tbody.querySelectorAll('tr'));

    // FLIP: First - record initial positions
    const firstPositions = new Map();
    rows.forEach(row => {
        const rect = row.getBoundingClientRect();
        firstPositions.set(row, rect.top);
    });

    // Sort rows based on JSON data or original index
    rows.sort((a, b) => {
        let indexA = parseInt(a.dataset.jsonindex);
        let indexB = parseInt(b.dataset.jsonindex);

        // Special case: fieldIndex === -1 means sort by original index
        if (fieldIndex === -1) {
            return (indexA - indexB) * direction;
        }

        let valueA = data[indexA][fieldIndex];
        let valueB = data[indexB][fieldIndex];

        // Handle null and empty string values - always put them last regardless of direction
        let isEmptyA = valueA === null || valueA === '';
        let isEmptyB = valueB === null || valueB === '';

        if (isEmptyA && isEmptyB) return 0;
        if (isEmptyA) return 1;
        if (isEmptyB) return -1;

        // Compare non-empty values
        let comparison = 0;
        if (valueA < valueB) comparison = -1;
        if (valueA > valueB) comparison = 1;

        // Stable sort: if equal, maintain original order
        if (comparison === 0) {
            comparison = indexA - indexB;
        }

        // Apply direction
        return comparison * direction;
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

function sortTable(tableIndex, fieldIndex) {
    // Toggle direction if clicking the same field
    if (currentSortField[tableIndex] === fieldIndex) {
        currentSortDirection[tableIndex] = -currentSortDirection[tableIndex];
    } else {
        currentSortField[tableIndex] = fieldIndex;
        currentSortDirection[tableIndex] = 1;
    }

    let direction = currentSortDirection[tableIndex];
    applySortWithoutToggle(tableIndex, fieldIndex, direction);
}

function updateSortIndicators(tableIndex, fieldIndex, direction) {
    let table = tables[tableIndex];
    let links = table.querySelectorAll('th a[data-sortable]');

    links.forEach(link => {
        link.innerHTML = link.innerHTML.replace(/^[▲▼] /, '');
    });

    let currentLink = table.querySelector(`th a[data-field-index='${fieldIndex}']`);
    if (currentLink) {
        let arrow = direction === 1 ? '▲' : '▼';
        currentLink.innerHTML = arrow + ' ' + currentLink.innerHTML;
    }
}

function initSortableHeaders() {
    for (let i = 0; i < tables.length; i++) {
        let table = tables[i];
        let links = table.querySelectorAll('th a[data-sortable="true"]');

        links.forEach(link => {
            link.style.cursor = 'pointer';
            link.addEventListener('click', (e) => {
                e.preventDefault();
                let fieldIndex = parseInt(link.dataset.fieldIndex);
                let tableId = parseInt(link.dataset.tableId);
                sortTable(tableId, fieldIndex);
            });
        });
    }
}
