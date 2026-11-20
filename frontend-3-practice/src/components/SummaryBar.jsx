import { formatDateWithWeekday, hasDay } from '../utils/date.js';

// Нижняя панель: показывает выбранную дату и время.
// Дата выводится с днём недели и годом: «среда, 18 ноября 2026».
function SummaryBar({
  year,
  month,
  selectedDay,
  selectedTime,
  isConfirmed,
  onNext,
}) {
  const daySelected = hasDay(selectedDay);
  const canProceed = daySelected && Boolean(selectedTime);

  return (
    <aside className="summary" aria-label="Итог записи">
      <div className="summary__info">
        <p className="summary__label">
          {isConfirmed ? 'Запись подтверждена' : 'Ваша запись'}
        </p>
        <p className="summary__value">
          <span className="summary__date">
            {formatDateWithWeekday(year, month, selectedDay)}
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
        <button
          className="button button--primary"
          type="button"
          disabled={!canProceed}
          aria-disabled={!canProceed}
          onClick={onNext}
        >
          {isConfirmed
            ? 'Запись подтверждена'
            : daySelected
              ? selectedTime
                ? 'Далее'
                : 'Выберите время'
              : 'Выберите дату'}
        </button>
      </div>
    </aside>
  );
}

export default SummaryBar;
