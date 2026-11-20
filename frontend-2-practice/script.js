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

// «Сегодня» — реальная текущая дата на момент загрузки страницы.
// Берём её из new Date(): с фиксированной датой прошедшие дни
// перестают блокироваться, как только наступает следующий день.
// month — 0-индексный, как в Date: 0 = январь, 10 = ноябрь.
const NOW = new Date();
const TODAY = {
  year: NOW.getFullYear(),
  month: NOW.getMonth(),
  day: NOW.getDate(),
};

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
  selectedDay: TODAY.day, // null — дату выбрать нельзя (месяц уже прошёл)
  selectedTime: null,
  confirmed: false, // запись подтверждена кнопкой «Далее»
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

// Первый день месяца, который можно выбрать.
// Если весь месяц уже в прошлом — возвращает null: выбирать нечего.
function getFirstSelectableDay(year, month) {
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  for (let day = 1; day <= daysInMonth; day++) {
    if (isSelectable(year, month, day)) return day;
  }
  return null;
}

// Выбрана ли сейчас допустимая (не прошедшая) дата.
function hasValidSelection() {
  return (
    state.selectedDay !== null &&
    isSelectable(state.year, state.month, state.selectedDay)
  );
}

// «Сейчас» в формате «ЧЧ:ММ» — нужно, чтобы блокировать прошедшие часы.
function currentTimeString() {
  const now = new Date();
  const hh = String(now.getHours()).padStart(2, '0');
  const mm = String(now.getMinutes()).padStart(2, '0');
  return `${hh}:${mm}`;
}

// Выбранный день — это сегодня?
function isSelectedToday() {
  return (
    hasValidSelection() &&
    state.year === TODAY.year &&
    state.month === TODAY.month &&
    state.selectedDay === TODAY.day
  );
}

// Слот уже прошёл: записаться на прошедшее время сегодня нельзя.
function isSlotInPast(time) {
  return isSelectedToday() && time <= currentTimeString();
}

// Доступен ли слот: он есть в расписании, свободен и ещё не прошёл.
function isSlotAvailable(time) {
  if (!time || !hasValidSelection() || isSlotInPast(time)) return false;

  return SLOT_GROUPS.some((group) =>
    group.slots.some((slot) => slot.time === time && slot.available)
  );
}

// Форматирование даты для нижней панели: «Среда, 18 ноября 2026».
function formatFullDate(year, month, day) {
  const weekday = WEEKDAY_NAMES[new Date(year, month, day).getDay()];
  return `${weekday}, ${day} ${MONTH_NAMES_GENITIVE[month]} ${year}`;
}

// Дата с днём недели и годом: «Среда, 18 ноября 2026».
// Если дата не выбрана — так и пишем в нижней панели.
function formatDateWithWeekday(year, month, day) {
  if (day === null || day === undefined) return 'Дата не выбрана';
  return formatFullDate(year, month, day);
}

// Склонение слова «слот».
function pluralSlots(n) {
  const mod10 = n % 10;
  const mod100 = n % 100;
  if (mod10 === 1 && mod100 !== 11) return 'слот';
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 10 || mod100 >= 20)) return 'слота';
  return 'слотов';
}

// Количество свободных слотов на выбранную дату.
// Если допустимой даты нет — свободных слотов тоже нет.
function countAvailable() {
  if (!hasValidSelection()) return 0;

  return SLOT_GROUPS.reduce(
    (sum, group) =>
      sum +
      group.slots.filter((slot) => slot.available && !isSlotInPast(slot.time))
        .length,
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
const slotsEmptyEl = document.getElementById('slots-empty');
const summaryValueEl = document.getElementById('summary-value');
const nextStepBtn = document.getElementById('next-step');

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
        if (state.selectedDay === cell.day) {
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
// Если допустимой даты нет — так и пишем в заголовке.
function renderSlotsHeader() {
  slotsDateEl.textContent = hasValidSelection()
    ? formatFullDate(state.year, state.month, state.selectedDay)
    : 'Дата не выбрана';

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
      // Слот кликабелен, только если день допустимый, слот свободен
      // и его время ещё не прошло (для сегодняшнего дня).
      const enabled = isSlotAvailable(slot.time);

      const classes = ['slot'];
      if (!enabled) {
        classes.push('slot--busy');
      } else if (state.selectedTime === slot.time) {
        classes.push('slot--active');
      }

      const disabled = enabled ? '' : ' disabled';
      const dataAttr = enabled ? ` data-time="${slot.time}"` : '';

      html += '<li class="slots__item">';
      html += `<button class="${classes.join(' ')}" type="button"${dataAttr}${disabled}>${slot.time}</button>`;
      html += '</li>';
    });

    html += '</ul>';
    html += '</div>';
  });

  slotsGroupsEl.innerHTML = html;
  attachSlotHandlers();

  // Подсказка вместо пустой сетки: слотов нет, потому что нет даты.
  if (slotsEmptyEl) {
    slotsEmptyEl.hidden = hasValidSelection();
  }
}

// Обновляет нижнюю панель: день недели, число, месяц, год и время.
function renderSummary() {
  const datePart = formatDateWithWeekday(
    state.year,
    state.month,
    state.selectedDay
  );

  if (state.confirmed && state.selectedTime) {
    summaryValueEl.innerHTML =
      '<span class="summary__label-inline">Запись подтверждена:</span>' +
      `<span class="summary__date">${datePart}</span>` +
      '<span class="summary__divider">·</span>' +
      `<span class="summary__time">${state.selectedTime}</span>`;
    return;
  }

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

// Состояние кнопки «Далее»: пока не выбраны дата и время — она заблокирована.
function renderNextStepButton() {
  if (!nextStepBtn) return;

  const ready = hasValidSelection() && Boolean(state.selectedTime);
  nextStepBtn.disabled = !ready;
  nextStepBtn.setAttribute('aria-disabled', String(!ready));

  if (state.confirmed) {
    nextStepBtn.textContent = 'Запись подтверждена';
  } else if (!hasValidSelection()) {
    nextStepBtn.textContent = 'Выберите дату';
  } else if (!state.selectedTime) {
    nextStepBtn.textContent = 'Выберите время';
  } else {
    nextStepBtn.textContent = 'Далее';
  }
}

// Полная перерисовка страницы.
function renderAll() {
  renderCalendar();
  renderSlotsHeader();
  renderSlots();
  renderSummary();
  renderNextStepButton();
}

// Обработчик клика по дню.
function onDayClick(event) {
  const day = parseInt(event.currentTarget.dataset.day, 10);
  if (!day) return;

  // Прошедший день выбрать нельзя, даже если по нему кликнули.
  if (!isSelectable(state.year, state.month, day)) return;

  state.selectedDay = day;
  state.selectedTime = null; // обязательно сбрасываем время
  state.confirmed = false; // и снимаем прошлое подтверждение

  renderAll();
}

// Обработчик клика по слоту.
function onSlotClick(event) {
  const time = event.currentTarget.dataset.time;
  if (!time) return;

  // Занятое, прошедшее время или дата без выборa — не даём записаться.
  if (!isSlotAvailable(time)) return;

  state.selectedTime = state.selectedTime === time ? null : time;
  state.confirmed = false;

  renderSlots();
  renderSummary();
  renderNextStepButton();
}

// Обработчик кнопки «Далее»: подтверждаем запись на выбранные дату и время.
function onNextStep() {
  // Страховка: кнопка заблокирована, но проверяем полный выбор и здесь.
  if (!hasValidSelection() || !state.selectedTime) {
    renderNextStepButton();
    return;
  }

  if (!isSlotAvailable(state.selectedTime)) {
    state.selectedTime = null;
    renderAll();
    return;
  }

  state.confirmed = true;

  renderSummary();
  renderNextStepButton();
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

// При смене месяца держим выбор в допустимых границах.
// Первое число прошедшего месяца недоступно, поэтому если выбирать
// нечего — сбрасываем день в null, а не подставляем 1.
function clampSelectionToMonth() {
  const daysInMonth = new Date(state.year, state.month + 1, 0).getDate();

  // Такого числа в этом месяце нет (например, было 31, стал февраль).
  if (state.selectedDay !== null && state.selectedDay > daysInMonth) {
    state.selectedDay = daysInMonth;
  }

  // Выбранный день оказался в прошлом — берём первый допустимый,
  // а если месяц целиком прошёл — null (дата не выбрана).
  if (
    state.selectedDay === null ||
    !isSelectable(state.year, state.month, state.selectedDay)
  ) {
    state.selectedDay = getFirstSelectableDay(state.year, state.month);
  }

  state.selectedTime = null;
  state.confirmed = false;
}

// ============================================================
// 5. ИНИЦИАЛИЗАЦИЯ
// ============================================================

document.getElementById('prev-month').addEventListener('click', onPrevMonth);
document.getElementById('next-month').addEventListener('click', onNextMonth);
nextStepBtn.addEventListener('click', onNextStep);

renderAll();
