// Чистые функции для работы с датами.
// Не зависят от React и DOM — можно переиспользовать в любом месте.

export const MONTH_NAMES = [
  'Январь',
  'Февраль',
  'Март',
  'Апрель',
  'Май',
  'Июнь',
  'Июль',
  'Август',
  'Сентябрь',
  'Октябрь',
  'Ноябрь',
  'Декабрь',
];

export const MONTH_NAMES_GENITIVE = [
  'января',
  'февраля',
  'марта',
  'апреля',
  'мая',
  'июня',
  'июля',
  'августа',
  'сентября',
  'октября',
  'ноября',
  'декабря',
];

export const WEEKDAY_NAMES = [
  'Воскресенье',
  'Понедельник',
  'Вторник',
  'Среда',
  'Четверг',
  'Пятница',
  'Суббота',
];

// Строит сетку календаря: массив недель по 7 ячеек.
export function buildCalendarGrid(year, month) {
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
export function compareDates(a, b) {
  const d1 = new Date(a.year, a.month, a.day);
  const d2 = new Date(b.year, b.month, b.day);
  if (d1 < d2) return -1;
  if (d1 > d2) return 1;
  return 0;
}

// Можно ли выбрать день: не раньше «сегодня».
export function isSelectable(year, month, day, today) {
  if (!today) return false;
  return compareDates({ year, month, day }, today) >= 0;
}

// Первый день месяца, который можно выбрать.
// Если весь месяц в прошлом — возвращает null.
export function getFirstSelectableDay(year, month, today) {
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  for (let day = 1; day <= daysInMonth; day++) {
    if (isSelectable(year, month, day, today)) return day;
  }
  return null;
}

// «Среда, 18 ноября 2026»
export function formatFullDate(year, month, day) {
  const weekday = WEEKDAY_NAMES[new Date(year, month, day).getDay()];
  return `${weekday}, ${day} ${MONTH_NAMES_GENITIVE[month]} ${year}`;
}

// «18 ноября»
export function formatShortDate(month, day) {
  return `${day} ${MONTH_NAMES_GENITIVE[month]}`;
}

// Склонение слова «слот».
export function pluralSlots(n) {
  const mod10 = n % 10;
  const mod100 = n % 100;
  if (mod10 === 1 && mod100 !== 11) return 'слот';
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 10 || mod100 >= 20)) return 'слота';
  return 'слотов';
}
