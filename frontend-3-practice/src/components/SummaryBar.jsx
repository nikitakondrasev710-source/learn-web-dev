import { formatShortDate } from '../utils/date.js';

// Нижняя панель: показывает выбранную дату и время.
function SummaryBar({ year, month, selectedDay, selectedTime }) {
  return (
    <aside className="summary" aria-label="Итог записи">
      <div className="summary__info">
        <p className="summary__label">Ваша запись</p>
        <p className="summary__value">
          <span className="summary__date">
            {formatShortDate(month, selectedDay)}
          </span>
          <span className="summary__divider">·</span>
          {selectedTime ? (
            <span className="summary__time">{selectedTime}</span>
          ) : (
            <span className="summary__time summary__time--empty">
              время не выбрано
            </span>
          )}
        </p>
      </div>

      <div className="summary__actions">
        <p className="summary__price">
          <span className="summary__price-label">К оплате</span>
          <span className="summary__price-value">2 400 ₽</span>
        </p>
        <button className="button button--primary" type="button">
          Далее
        </button>
      </div>
    </aside>
  );
}

export default SummaryBar;
