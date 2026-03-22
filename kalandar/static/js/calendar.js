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

    function renderCalendar() {
        const calendarEl = document.getElementById('custom-calendar');
        calendarEl.innerHTML = '';

        document.getElementById('current-year').textContent = currentYear;

        fetch(`/get-date-mappings/${currentYear}`)
            .then(response => response.json())
            .then(newMappings => {
                window.dateMappings = newMappings;
                renderMonths();
            })
            .catch(error => {
                console.error('Error fetching date mappings:', error);
                renderMonths();
            });
    }

    function renderMonths() {
        const calendarEl = document.getElementById('custom-calendar');
        calendarEl.innerHTML = '';

        for (let month = 0; month < 5; month++) {
            const monthContainer = document.createElement('div');
            monthContainer.className = 'month-container';

            const monthHeader = document.createElement('div');
            monthHeader.className = 'month-header';
            monthHeader.textContent = monthNames[month];
            monthContainer.appendChild(monthHeader);

            const daysGrid = document.createElement('div');
            daysGrid.className = 'days-grid';

            for (let i = 0; i < 10; i++) {
                const dayHeader = document.createElement('div');
                dayHeader.className = 'day-header';
                dayHeader.textContent = weekdayNames[i];
                daysGrid.appendChild(dayHeader);
            }

            const daysInMonth = getDaysInMonth(month, currentYear);
            const weeksInMonth = Math.ceil(daysInMonth / 10);

            for (let week = 0; week < weeksInMonth; week++) {
                const weekLabel = document.createElement('div');
                weekLabel.className = 'week-label';
                weekLabel.textContent = `Week ${week + 1}`;
                daysGrid.appendChild(weekLabel);

                const startDay = week * 10 + 1;
                const endDay = Math.min(startDay + 9, daysInMonth);

                for (let day = startDay; day <= endDay; day++) {
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

                if (endDay < daysInMonth && (endDay % 10) !== 0) {
                    const emptyCellsNeeded = 10 - (endDay % 10);
                    for (let i = 0; i < emptyCellsNeeded; i++) {
                        const emptyCell = document.createElement('div');
                        emptyCell.className = 'day-cell';
                        emptyCell.style.visibility = 'hidden';
                        daysGrid.appendChild(emptyCell);
                    }
                }

                if (week < weeksInMonth - 1) {
                    const weekSeparator = document.createElement('div');
                    weekSeparator.className = 'week-separator';
                    daysGrid.appendChild(weekSeparator);
                }
            }

            monthContainer.appendChild(daysGrid);
            calendarEl.appendChild(monthContainer);
        }
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
                    `Events on ${monthNames[month]} Day ${day}`;

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

                        const title = document.createElement('h5');
                        title.textContent = event.title;

                        const description = document.createElement('p');
                        description.textContent = event.description || 'No description';

                        const deleteBtn = document.createElement('button');
                        deleteBtn.className = 'btn btn-sm btn-danger mt-2';
                        deleteBtn.textContent = 'Delete';
                        deleteBtn.addEventListener('click', function() {
                            deleteEvent(event.id);
                        });

                        li.appendChild(title);
                        li.appendChild(description);
                        li.appendChild(deleteBtn);
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

    document.getElementById('prev-year').addEventListener('click', function() {
        currentYear--;
        updateCalendarYear(currentYear);
    });

    document.getElementById('next-year').addEventListener('click', function() {
        currentYear++;
        updateCalendarYear(currentYear);
    });

    document.getElementById('go-to-today').addEventListener('click', function() {
        currentYear = todayYear;
        updateCalendarYear(currentYear);
    });

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
                updateCalendarYear(currentYear);
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

    function updateCalendarYear(year) {
        fetch(`/get-date-mappings/${year}`)
            .then(response => response.json())
            .then(newMappings => {
                window.dateMappings = newMappings;
                renderCalendar();
            })
            .catch(error => {
                console.error('Error fetching date mappings:', error);
                renderCalendar();
            });
    }
});
