// JavaScript для страницы выбора даты и времени.
// Барбершоп «БРИТВА» — нативный JS, без фреймворков и сборщиков.
//
// Структура файла:
//   1. ДАННЫЕ
//   2. СОСТОЯНИЕ
//   3. ЧИСТЫЕ ФУНКЦИИ
//   4. ОТРИСОВКА И ОБРАБОТЧИКИ
//   5. ИНИЦИАЛИЗАЦИЯ

// ============================================================
// 1. ДАННЫЕ
// ============================================================

// «Сегодня» — захардкожено для стабильной проверки задания.
// Что взять текущую дату, раскомментируйте строку с new Date().
const TODAY = { year: 2026, month: 10, day: 19 }; // month: 0 = январь, 10 = ноябрь

const MONTH_NAMES = [
  'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
  'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь',
];

const MONTH_NAMES_GENITIVE = [
  'января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
  'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря',
];

const WEEKDAY_NAMES = [
  'Воскресенье', 'Понедельник', 'Вторник', 'Среда',
  'Четверг', 'Пятница', 'Суббота',
];

// Слоты захардкожены. У каждого слота есть занятость.
const SLOT_GROUPS = [
  {
    title: 'Утро',
    slots: [
      { time: '09:00', available: false },
      { time: '10:00', available: true },
      { time: '11:00', available: true },
      { time: '12:00', available: false },
    ],
  },
  {
    title: 'День',
    slots: [
      { time: '13:00', available: true },
      { time: '14:00', available: true },
      { time: '15:00', available: true },
      { time: '16:00', available: true },
    ],
  },
  {
    title: 'Вечер',
    slots: [
      { time: '17:00', available: true },
      { time: '18:00', available: false },
      { time: '19:00', available: true },
      { time: '20:00', available: false },
    ],
  },
];

// ============================================================
// 2. СОСТОЯНИЕ
// ============================================================

const state = {
  year: TODAY.year,
  month: TODAY.month,
  selectedDay: TODAY.day,
  selectedTime: null,
};

// ============================================================
// 3. ЧИСТЫЕ ФУНКЦИИ
// ============================================================

// Строит сетку календаря: массив недель по 7 ячеек.
function buildCalendarGrid(year, month) {
  const firstDay = new Date(year, month, 1);
  const lastDay = new Date(year, month + 1, 0);
  const daysInMonth = lastDay.getDate();
  const startDayOfWeek = firstDay.getDay();
  const offset = startDayOfWeek === 0 ? 6 : startDayOfWeek - 1;
  const prevMonthLastDay = new Date(year, month, 0).getDate();

  const cells = [];

  for (let i = offset - 1; i >= 0; i--) {
    cells.push({ day: prevMonthLastDay - i, otherMonth: true });
  }
  for (let d = 1; d <= daysInMonth; d++) {
    cells.push({ day: d, otherMonth: false });
  }
  const totalCells = Math.ceil(cells.length / 7) * 7;
  let nextDay = 1;
  while (cells.length < totalCells) {
    cells.push({ day: nextDay, otherMonth: true });
    nextDay++;
  }

  const weeks = [];
  for (let i = 0; i < cells.length; i += 7) {
    weeks.push(cells.slice(i, i + 7));
  }
  return weeks;
}

// Сравнение двух дат: -1 (a раньше b), 0 (равны), 1 (a позже b).
function compareDates(a, b) {
  const d1 = new Date(a.year, a.month, a.day);
  const d2 = new Date(b.year, b.month, b.day);
  if (d1 < d2) return -1;
  if (d1 > d2) return 1;
  return 0;
}

// Можно ли выбрать день: не раньше «сегодня».
function isSelectable(year, month, day) {
  return compareDates({ year, month, day }, TODAY) >= 0;
}

// Форматирование даты для нижней панели: «Среда, 18 ноября 2026».
function formatFullDate(year, month, day) {
  const weekday = WEEKDAY_NAMES[new Date(year, month, day).getDay()];
  return `${weekday}, ${day} ${MONTH_NAMES_GENITIVE[month]} ${year}`;
}

// Короткая форма: «18 ноября».
function formatShortDate(month, day) {
  return `${day} ${MONTH_NAMES_GENITIVE[month]}`;
}

// Склонение слова «слот».
function pluralSlots(n) {
  const mod10 = n % 10;
  const mod100 = n % 100;
  if (mod10 === 1 && mod100 !== 11) return 'слот';
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 10 || mod100 >= 20)) return 'слота';
  return 'слотов';
}

// Количество свободных слотов.
function countAvailable() {
  return SLOT_GROUPS.reduce(
    (sum, group) => sum + group.slots.filter((s) => s.available).length,
    0
  );
}

// ============================================================
// 4. ОТРИСОВКА И ОБРАБОТЧИКИ
// ============================================================

const gridEl = document.getElementById('calendar-grid');
const monthTitleEl = document.getElementById('calendar-title');
const yearEl = document.querySelector('.calendar__year');
const slotsGroupsEl = document.getElementById('slots-groups');
const slotsDateEl = document.getElementById('slots-date');
const slotsBadgeEl = document.getElementById('slots-badge');
const summaryValueEl = document.getElementById('summary-value');

// Рисует календарь на текущий месяц из состояния.
function renderCalendar() {
  monthTitleEl.textContent = MONTH_NAMES[state.month];
  yearEl.textContent = state.year;

  const weeks = buildCalendarGrid(state.year, state.month);
  let html = '';

  weeks.forEach((week) => {
    week.forEach((cell) => {
      const classes = ['calendar__day'];

      if (cell.otherMonth) {
        classes.push('calendar__day--muted');
      } else {
        const selectable = isSelectable(state.year, state.month, cell.day);
        if (!selectable) {
          classes.push('calendar__day--muted', 'calendar__day--disabled');
        }
        if (
          state.year === TODAY.year &&
          state.month === TODAY.month &&
          cell.day === TODAY.day
        ) {
          classes.push('calendar__day--today');
        }
        if (
          !cell.otherMonth &&
          state.selectedDay === cell.day
        ) {
          classes.push('calendar__day--selected');
        }
      }

      const clickable = !cell.otherMonth && isSelectable(state.year, state.month, cell.day);
      const attrs = clickable
        ? ` role="button" tabindex="0" data-day="${cell.day}"`
        : '';

      html += `<span class="${classes.join(' ')}"${attrs}>${cell.day}</span>`;
    });
  });

  gridEl.innerHTML = html;
  attachDayHandlers();
}

// Обновляет заголовок блока слотов и счётчик.
function renderSlotsHeader() {
  const dateLabel = formatFullDate(state.year, state.month, state.selectedDay);
  slotsDateEl.textContent = dateLabel;

  const available = countAvailable();
  slotsBadgeEl.textContent = `${available} ${pluralSlots(available)}`;
}

// Рисует группы слотов. Выбранный слот подсвечивается.
function renderSlots() {
  let html = '';

  SLOT_GROUPS.forEach((group) => {
    html += '<div class="slots__group">';
    html += `<h3 class="slots__group-title">${group.title}</h3>`;
    html += '<ul class="slots__list">';

    group.slots.forEach((slot) => {
      const classes = ['slot'];
      if (!slot.available) {
        classes.push('slot--busy');
      } else if (state.selectedTime === slot.time) {
        classes.push('slot--active');
      }

      const disabled = !slot.available ? ' disabled' : '';
      const dataAttr = slot.available ? ` data-time="${slot.time}"` : '';

      html += '<li class="slots__item">';
      html += `<button class="${classes.join(' ')}" type="button"${dataAttr}${disabled}>${slot.time}</button>`;
      html += '</li>';
    });

    html += '</ul>';
    html += '</div>';
  });

  slotsGroupsEl.innerHTML = html;
  attachSlotHandlers();
}

// Обновляет нижнюю панель.
function renderSummary() {
  const datePart = formatShortDate(state.month, state.selectedDay);

  if (state.selectedTime) {
    summaryValueEl.innerHTML =
      `<span class="summary__date">${datePart}</span>` +
      '<span class="summary__divider">·</span>' +
      `<span class="summary__time">${state.selectedTime}</span>`;
  } else {
    summaryValueEl.innerHTML =
      `<span class="summary__date">${datePart}</span>` +
      '<span class="summary__divider">·</span>' +
      '<span class="summary__time summary__time--empty">время не выбрано</span>';
  }
}

// Полная перерисовка страницы.
function renderAll() {
  renderCalendar();
  renderSlotsHeader();
  renderSlots();
  renderSummary();
}

// Обработчик клика по дню.
function onDayClick(event) {
  const day = parseInt(event.currentTarget.dataset.day, 10);
  if (!day) return;

  state.selectedDay = day;
  state.selectedTime = null; // обязательно сбрасываем время

  renderAll();
}

// Обработчик клика по слоту.
function onSlotClick(event) {
  const time = event.currentTarget.dataset.time;
  if (!time) return;

  state.selectedTime = state.selectedTime === time ? null : time;

  renderSlots();
  renderSummary();
}

// Навешивает обработчики на дни календаря после перерисовки.
function attachDayHandlers() {
  gridEl.querySelectorAll('[data-day]').forEach((el) => {
    el.addEventListener('click', onDayClick);
    el.addEventListener('keydown', (event) => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        onDayClick(event);
      }
    });
  });
}

// Навешивает обработчики на слоты после перерисовки.
function attachSlotHandlers() {
  slotsGroupsEl.querySelectorAll('[data-time]').forEach((el) => {
    el.addEventListener('click', onSlotClick);
  });
}

// Стрелки переключения месяцев.
function onPrevMonth() {
  state.month -= 1;
  if (state.month < 0) {
    state.month = 11;
    state.year -= 1;
  }
  clampSelectionToMonth();
  renderAll();
}

function onNextMonth() {
  state.month += 1;
  if (state.month > 11) {
    state.month = 0;
    state.year += 1;
  }
  clampSelectionToMonth();
  renderAll();
}

// При смене месяца держим выбор в допустимых границах:
// нельзя оставаться на прошедшем дне.
function clampSelectionToMonth() {
  const daysInMonth = new Date(state.year, state.month + 1, 0).getDate();

  if (state.selectedDay > daysInMonth) {
    state.selectedDay = daysInMonth;
  }

  if (!isSelectable(state.year, state.month, state.selectedDay)) {
    // Если весь месяц в прошлом — переносим выбор на первое число.
    state.selectedDay = 1;
  }

  state.selectedTime = null;
}

// ============================================================
// 5. ИНИЦИАЛИЗАЦИЯ
// ============================================================

document.getElementById('prev-month').addEventListener('click', onPrevMonth);
document.getElementById('next-month').addEventListener('click', onNextMonth);

renderAll();
