import {
  MONTH_NAMES,
  WEEKDAY_NAMES,
  buildCalendarGrid,
  isSelectable,
} from '../utils/date.js';

const WEEKDAYS_SHORT = WEEKDAY_NAMES.map((name) => name.slice(0, 2));

// Календарь на текущий месяц.
// Получает состояние и колбэки — сам ничего не хранит.
function Calendar({
  year,
  month,
  selectedDay,
  today,
  onSelectDay,
  onPrevMonth,
  onNextMonth,
}) {
  const weeks = buildCalendarGrid(year, month);

  return (
    <section className="card calendar" aria-labelledby="calendar-title">
      <header className="calendar__head">
        <div className="calendar__month-block">
          <h2 className="calendar__title" id="calendar-title">
            {MONTH_NAMES[month]}
          </h2>
          <p className="calendar__year">{year}</p>
        </div>

        <div className="calendar__nav">
          <button
            className="icon-button"
            type="button"
            aria-label="Предыдущий месяц"
            onClick={onPrevMonth}
          >
            ‹
          </button>
          <button
            className="icon-button"
            type="button"
            aria-label="Следующий месяц"
            onClick={onNextMonth}
          >
            ›
          </button>
        </div>
      </header>

      <div className="calendar__weekdays">
        {[0, 1, 2, 3, 4, 5, 6].map((index) => (
          <span className="calendar__weekday" key={index}>
            {['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'][index]}
          </span>
        ))}
      </div>

      <div className="calendar__grid">
        {weeks.map((week, weekIndex) =>
          week.map((cell, cellIndex) => {
            const key = `${weekIndex}-${cellIndex}`;
            const classes = ['calendar__day'];

            if (cell.otherMonth) {
              classes.push('calendar__day--muted');
              return (
                <span className={classes.join(' ')} key={key}>
                  {cell.day}
                </span>
              );
            }

            const selectable = isSelectable(year, month, cell.day, today);
            if (!selectable) {
              classes.push('calendar__day--muted', 'calendar__day--disabled');
            }
            if (
              today &&
              today.year === year &&
              today.month === month &&
              today.day === cell.day
            ) {
              classes.push('calendar__day--today');
            }
            if (selectedDay === cell.day) {
              classes.push('calendar__day--selected');
            }

            if (!selectable) {
              return (
                <span className={classes.join(' ')} key={key}>
                  {cell.day}
                </span>
              );
            }

            return (
              <span
                className={classes.join(' ')}
                key={key}
                role="button"
                tabIndex={0}
                onClick={() => onSelectDay(cell.day)}
                onKeyDown={(event) => {
                  if (event.key === 'Enter' || event.key === ' ') {
                    event.preventDefault();
                    onSelectDay(cell.day);
                  }
                }}
              >
                {cell.day}
              </span>
            );
          })
        )}
      </div>

      <footer className="calendar__legend">
        <span className="legend-item">
          <span className="legend-item__dot legend-item__dot--selected" />
          <span className="legend-item__text">Выбранный день</span>
        </span>
        <span className="legend-item">
          <span className="legend-item__dot legend-item__dot--today" />
          <span className="legend-item__text">Сегодня</span>
        </span>
      </footer>
    </section>
  );
}

export default Calendar;
