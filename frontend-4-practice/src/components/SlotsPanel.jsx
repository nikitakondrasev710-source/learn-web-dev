import { formatFullDate, pluralSlots } from '../utils/date.js';

// Блок со слотами времени.
// Слоты приходят с сервера массивом [{ time, available }].

// Разбиваем слоты на группы по времени суток.
function groupSlots(slots) {
  const groups = [
    { title: 'Утро', slots: [] },
    { title: 'День', slots: [] },
    { title: 'Вечер', slots: [] },
  ];

  slots.forEach((slot) => {
    const hour = parseInt(slot.time.slice(0, 2), 10);
    if (hour < 12) {
      groups[0].slots.push(slot);
    } else if (hour < 17) {
      groups[1].slots.push(slot);
    } else {
      groups[2].slots.push(slot);
    }
  });

  // Пустые группы не показываем.
  return groups.filter((group) => group.slots.length > 0);
}

function SlotsPanel({
  slots,
  loading,
  error,
  year,
  month,
  selectedDay,
  selectedTime,
  onSelectTime,
}) {
  const available = slots.filter((slot) => slot.available).length;
  const groups = groupSlots(slots);
  const hasSlots = slots.length > 0;

  return (
    <section className="card slots" aria-labelledby="slots-title">
      <header className="slots__head">
        <div className="slots__head-text">
          <h2 className="slots__title" id="slots-title">
            Свободное время
          </h2>
          <p className="slots__date">{formatFullDate(year, month, selectedDay)}</p>
        </div>
        {!loading && !error && hasSlots && (
          <span className="slots__badge">
            {available} {pluralSlots(available)}
          </span>
        )}
      </header>

      {loading && (
        <p className="slots__state slots__state--loading">Загрузка слотов…</p>
      )}

      {error && !loading && (
        <p className="slots__state slots__state--error">
          Не удалось загрузить слоты: {error}
        </p>
      )}

      {!loading && !error && !hasSlots && (
        <p className="slots__state">На этот день свободных слотов нет.</p>
      )}

      {!loading && !error && hasSlots && (
        <div className="slots__groups">
          {groups.map((group) => (
            <div className="slots__group" key={group.title}>
              <h3 className="slots__group-title">{group.title}</h3>
              <ul className="slots__list">
                {group.slots.map((slot) => {
                  const classes = ['slot'];
                  if (!slot.available) {
                    classes.push('slot--busy');
                  } else if (selectedTime === slot.time) {
                    classes.push('slot--active');
                  }

                  return (
                    <li className="slots__item" key={slot.time}>
                      <button
                        className={classes.join(' ')}
                        type="button"
                        disabled={!slot.available}
                        onClick={() => onSelectTime(slot.time)}
                      >
                        {slot.time}
                      </button>
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </div>
      )}

      <p className="slots__note">
        Продолжительность визита — 60 минут. Мастер: Алиса Морозова.
      </p>
    </section>
  );
}

export default SlotsPanel;
