import { countAvailable } from '../data/slots.js';
import { formatFullDate, hasDay, pluralSlots } from '../utils/date.js';

// Блок со слотами времени.
// Слоты приходят пропсом groups и уже посчитаны под выбранную дату:
// прошедшие часы и занятое время помечены как недоступные.
function SlotsPanel({
  groups,
  year,
  month,
  selectedDay,
  selectedTime,
  onSelectTime,
}) {
  const daySelected = hasDay(selectedDay);
  const available = countAvailable(groups);

  return (
    <section className="card slots" aria-labelledby="slots-title">
      <header className="slots__head">
        <div className="slots__head-text">
          <h2 className="slots__title" id="slots-title">
            Свободное время
          </h2>
          <p className="slots__date">
            {daySelected
              ? formatFullDate(year, month, selectedDay)
              : 'Выберите день в календаре'}
          </p>
        </div>
        <span className="slots__badge">
          {available} {pluralSlots(available)}
        </span>
      </header>

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

      {!daySelected && (
        <p className="slots__empty">
          В этом месяце записаться уже нельзя — вернитесь к актуальному месяцу.
        </p>
      )}

      <p className="slots__note">
        Продолжительность визита — 60 минут. Мастер: Алиса Морозова.
      </p>
    </section>
  );
}

export default SlotsPanel;
