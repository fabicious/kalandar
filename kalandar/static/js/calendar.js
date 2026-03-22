document.addEventListener('DOMContentLoaded', function() {
    // Display today's Gregorian date
    const standardDateInfo = document.getElementById('standard-date-info');
    if (standardDateInfo) {
        const today = new Date();
        const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
        standardDateInfo.textContent = today.toLocaleDateString(undefined, options);
    }

    const monthNames = ['Astira', 'Grin', 'Train', 'Windugi', 'Kus'];
    const weekdayNames = ['Antag', 'Zwitag', 'Tretag', 'Vietig', 'Fürtag',
                          'Sechsa', 'Septag', 'Achtag', 'Nune', 'Entag'];

    const todayYear = window.CALENDAR_CONFIG.todayYear;
    const todayMonth = window.CALENDAR_CONFIG.todayMonth;
    const todayDay = window.CALENDAR_CONFIG.todayDay;

    let currentYear = todayYear;
    let currentMonth = todayMonth;
    let events = [];

    fetchEvents();

    function isLeapYear(year) {
        return ((year % 4 === 0) && (year % 100 !== 0)) || (year % 400 === 0);
    }

    function getDaysInMonth(month, year) {
        return month < 4 ? 90 : (isLeapYear(year) ? 6 : 5);
    }

    /**
     * Returns true if the given event falls on the specified custom calendar day.
     * Strategy 1: Direct custom date match (year-sensitive).
     * Strategy 2: Gregorian month/day match via date mappings (year-independent fallback).
     */
    function eventMatchesDay(event, month, day, year, gregorianDateText) {
        if (String(year) === String(event.customStart.year) &&
            String(month) === String(event.customStart.month) &&
            String(day) === String(event.customStart.day)) {
            return true;
        }

        const eventDate = event.start.substring(0, 10); // YYYY-MM-DD
        if (gregorianDateText && eventDate) {
            const gregMonthDay = gregorianDateText.substring(0, 5); // "MM/DD"
            const eventMonthDay = eventDate.substring(5, 10);       // "MM-DD"
            if (gregMonthDay === eventMonthDay.replace('-', '/')) {
                return true;
            }
        }

        return false;
    }

    function fetchEvents() {
        fetch('/get-events')
            .then(response => response.json())
            .then(data => {
                events = data;
                renderCalendar();
            })
            .catch(error => {
                console.error('Error fetching events:', error);
            });
    }

    function updateNavDisplay() {
        document.getElementById('current-year').textContent = currentYear;
        document.getElementById('current-month-name').textContent = monthNames[currentMonth];

        // Update month tab active states
        document.querySelectorAll('.month-tab').forEach(tab => {
            tab.classList.toggle('active', parseInt(tab.dataset.month) === currentMonth);
        });
    }

    function renderCalendar() {
        const calendarEl = document.getElementById('custom-calendar');
        calendarEl.innerHTML = '';

        updateNavDisplay();

        fetch(`/get-date-mappings/${currentYear}`)
            .then(response => response.json())
            .then(newMappings => {
                window.dateMappings = newMappings;
                renderMonth(currentMonth);
            })
            .catch(error => {
                console.error('Error fetching date mappings:', error);
                renderMonth(currentMonth);
            });
    }

    function renderMonth(month) {
        const calendarEl = document.getElementById('custom-calendar');
        calendarEl.innerHTML = '';

        const daysGrid = document.createElement('div');
        daysGrid.className = 'days-grid';

        // Weekday headers
        for (let i = 0; i < 10; i++) {
            const dayHeader = document.createElement('div');
            dayHeader.className = 'day-header';
            dayHeader.textContent = weekdayNames[i];
            daysGrid.appendChild(dayHeader);
        }

        const daysInMonth = getDaysInMonth(month, currentYear);

        for (let day = 1; day <= daysInMonth; day++) {
            const dayCell = document.createElement('div');
            dayCell.className = 'day-cell';

            if (currentYear === todayYear && month === todayMonth && day === todayDay) {
                dayCell.classList.add('today');
            }

            const dayNumber = document.createElement('div');
            dayNumber.className = 'day-number';
            dayNumber.textContent = day;
            dayCell.appendChild(dayNumber);

            const gregorianDate = document.createElement('div');
            gregorianDate.className = 'gregorian-date';

            if (!window.dateMappings) {
                window.dateMappings = window.CALENDAR_CONFIG.initialDateMappings;
            }

            let gregorianDateText = '';
            if (window.dateMappings[month] && window.dateMappings[month][day]) {
                gregorianDateText = window.dateMappings[month][day];
                gregorianDate.textContent = gregorianDateText;
            }

            dayCell.appendChild(gregorianDate);

            const matchingEvents = events.filter(e =>
                eventMatchesDay(e, month, day, currentYear, gregorianDateText)
            );

            if (matchingEvents.length > 0) {
                dayCell.classList.add('has-event');

                const eventIndicators = document.createElement('div');
                eventIndicators.className = 'event-indicators';
                eventIndicators.style.textAlign = 'center';

                const dotsToShow = Math.min(matchingEvents.length, 3);
                for (let i = 0; i < dotsToShow; i++) {
                    const dot = document.createElement('span');
                    dot.className = 'event-indicator';
                    eventIndicators.appendChild(dot);
                }

                dayCell.appendChild(eventIndicators);
            }

            dayCell.addEventListener('click', function() {
                showDayEvents(month, day, currentYear);
            });

            daysGrid.appendChild(dayCell);
        }

        // Fill empty cells for last row of Kus
        if (daysInMonth < 10) {
            for (let i = daysInMonth; i < 10; i++) {
                const emptyCell = document.createElement('div');
                emptyCell.className = 'day-cell empty-cell';
                daysGrid.appendChild(emptyCell);
            }
        }

        calendarEl.appendChild(daysGrid);
    }

    function navigateMonth(delta) {
        currentMonth += delta;
        if (currentMonth > 4) {
            currentMonth = 0;
            currentYear++;
        } else if (currentMonth < 0) {
            currentMonth = 4;
            currentYear--;
        }
        renderCalendar();
    }

    function showDayEvents(month, day, year) {
        const addEventBtn = document.getElementById('add-event-btn');
        if (addEventBtn) {
            addEventBtn.href = `/event?year=${year}&month=${month}&day=${day}`;
        }

        const loadingIndicator = document.getElementById('day-events-loading');
        const eventsList = document.getElementById('dayEventsList');

        if (loadingIndicator) {
            loadingIndicator.classList.remove('d-none');
        }

        const modal = new bootstrap.Modal(document.getElementById('dayEventsModal'));
        modal.show();

        fetch('/get-events')
            .then(response => response.json())
            .then(data => {
                events = data;

                const dayEvents = events.filter(event => {
                    let gregorianDateText = '';
                    if (window.dateMappings[month] && window.dateMappings[month][day]) {
                        gregorianDateText = window.dateMappings[month][day];
                    }
                    return eventMatchesDay(event, month, day, year, gregorianDateText);
                });

                document.getElementById('dayEventsTitle').textContent =
                    `Events on ${monthNames[month]} ${day}`;

                Array.from(eventsList.children).forEach(child => {
                    if (!child.id || child.id !== 'day-events-loading') {
                        eventsList.removeChild(child);
                    }
                });

                if (dayEvents.length === 0) {
                    const noEvents = document.createElement('p');
                    noEvents.textContent = 'No events on this day.';
                    eventsList.appendChild(noEvents);
                } else {
                    const ul = document.createElement('ul');
                    ul.className = 'list-group';

                    dayEvents.forEach(event => {
                        const li = document.createElement('li');
                        li.className = 'list-group-item';

                        const titleRow = document.createElement('div');
                        titleRow.className = 'd-flex align-items-center gap-2';
                        const title = document.createElement('h5');
                        title.className = 'mb-0';
                        title.textContent = event.title;
                        titleRow.appendChild(title);
                        if (event.category) {
                            const badge = document.createElement('span');
                            badge.className = 'category-badge';
                            badge.textContent = event.category;
                            titleRow.appendChild(badge);
                        }

                        const description = document.createElement('p');
                        description.className = 'mt-1 mb-1';
                        description.textContent = event.description || 'No description';

                        const actions = document.createElement('div');
                        actions.className = 'd-flex gap-2 mt-1';

                        const editBtn = document.createElement('a');
                        editBtn.href = `/event/${event.id}`;
                        editBtn.className = 'btn btn-sm btn-outline-primary';
                        editBtn.textContent = 'Edit';

                        const deleteBtn = document.createElement('button');
                        deleteBtn.className = 'btn btn-sm btn-danger';
                        deleteBtn.textContent = 'Delete';
                        deleteBtn.addEventListener('click', function() {
                            deleteEvent(event.id);
                        });

                        actions.appendChild(editBtn);
                        actions.appendChild(deleteBtn);

                        li.appendChild(titleRow);
                        li.appendChild(description);
                        li.appendChild(actions);
                        ul.appendChild(li);
                    });

                    eventsList.appendChild(ul);
                }

                if (loadingIndicator) {
                    loadingIndicator.classList.add('d-none');
                }
            })
            .catch(error => {
                console.error('Error fetching events:', error);
                eventsList.innerHTML = '<p>Error loading events. Please try again.</p>';
                if (loadingIndicator) {
                    loadingIndicator.classList.add('d-none');
                }
            });
    }

    function deleteEvent(eventId) {
        if (!confirm('Delete this event?')) return;
        fetch('/delete-event', {
            method: 'POST',
            body: JSON.stringify({ eventId: eventId }),
            headers: { 'Content-Type': 'application/json' }
        }).then(() => {
            fetchEvents();
            bootstrap.Modal.getInstance(document.getElementById('dayEventsModal')).hide();
        });
    }

    // Month navigation
    document.getElementById('prev-month').addEventListener('click', function() {
        navigateMonth(-1);
    });

    document.getElementById('next-month').addEventListener('click', function() {
        navigateMonth(1);
    });

    // Year navigation
    document.getElementById('prev-year').addEventListener('click', function() {
        currentYear--;
        renderCalendar();
    });

    document.getElementById('next-year').addEventListener('click', function() {
        currentYear++;
        renderCalendar();
    });

    document.getElementById('go-to-today').addEventListener('click', function() {
        currentYear = todayYear;
        currentMonth = todayMonth;
        renderCalendar();
    });

    // Click year to edit
    const yearDisplay = document.getElementById('current-year');
    const yearInput = document.getElementById('year-input');

    yearDisplay.addEventListener('click', function() {
        yearInput.value = currentYear;
        yearDisplay.classList.add('d-none');
        yearInput.classList.remove('d-none');
        yearInput.focus();
    });

    yearInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            const newYear = parseInt(yearInput.value, 10);
            if (!isNaN(newYear)) {
                currentYear = newYear;
                renderCalendar();
            }
            yearInput.classList.add('d-none');
            yearDisplay.classList.remove('d-none');
        } else if (e.key === 'Escape') {
            yearInput.classList.add('d-none');
            yearDisplay.classList.remove('d-none');
        }
    });

    yearInput.addEventListener('blur', function() {
        yearInput.classList.add('d-none');
        yearDisplay.classList.remove('d-none');
    });

    // Month tabs
    document.querySelectorAll('.month-tab').forEach(tab => {
        tab.addEventListener('click', function() {
            currentMonth = parseInt(this.dataset.month);
            renderCalendar();
        });
    });

    // Keyboard navigation
    document.addEventListener('keydown', function(e) {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
        if (document.querySelector('.modal.show')) return;

        if (e.key === 'ArrowLeft') {
            navigateMonth(-1);
        } else if (e.key === 'ArrowRight') {
            navigateMonth(1);
        }
    });
});
