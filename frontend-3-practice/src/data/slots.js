// Данные страницы «Выбор даты и времени».
// Слотов с сервера пока нет: базовое расписание захардкожено,
// а доступность конкретного времени считается для выбранной даты.
//
// Главное отличие от первой версии: в расписании больше нет флага
// available. Доступность зависит от даты (прошёл ли день, который час,
// работает ли мастер в этот день недели), поэтому её нельзя держать
// константой — она считается в getSlotGroupsFor().

// «Сегодня» — реальная текущая дата на момент загрузки страницы.
// Если зафиксировать дату числом, то на следующий день прошедшие дни
// перестанут блокироваться, поэтому берём её из new Date().
const NOW = new Date();

export const TODAY = {
  year: NOW.getFullYear(),
  month: NOW.getMonth(), // 0 = январь, 10 = ноябрь
  day: NOW.getDate(),
};

// Расписание мастера: только время приёма, без признака занятости.
export const SCHEDULE = [
  {
    title: 'Утро',
    times: ['09:00', '10:00', '11:00', '12:00'],
  },
  {
    title: 'День',
    times: ['13:00', '14:00', '15:00', '16:00'],
  },
  {
    title: 'Вечер',
    times: ['17:00', '18:00', '19:00', '20:00'],
  },
];

// Обеденный перерыв: в это время запись недоступна всегда.
const LUNCH_TIMES = ['13:00'];

// Занятые часы зависят от чётности числа. Так видно, что при смене
// даты расписание действительно пересчитывается, а не берётся готовым.
const BUSY_BY_PARITY = {
  even: ['10:00', '12:00', '16:00', '18:00'],
  odd: ['09:00', '11:00', '15:00', '19:00'],
};

// В воскресенье мастер не принимает.
const CLOSED_WEEKDAY = 0;

// Текущее время в формате «ЧЧ:ММ» — чтобы блокировать прошедшие часы.
export function getCurrentTime() {
  const now = new Date();
  const hours = String(now.getHours()).padStart(2, '0');
  const minutes = String(now.getMinutes()).padStart(2, '0');
  return `${hours}:${minutes}`;
}

// Совпадают ли две даты (год, месяц, день).
function isSameDate(a, b) {
  return !!a && !!b && a.year === b.year && a.month === b.month && a.day === b.day;
}

// Расписание на конкретную дату.
//
// Возвращает ту же структуру, что и раньше: [{ title, slots: [{ time, available }] }].
// Правила:
//   - дата не выбрана (null) — все слоты недоступны;
//   - воскресенье — мастер не работает;
//   - обед и занятые часы этого дня — недоступны;
//   - если выбран сегодняшний день — прошедшие часы недоступны.
export function getSlotGroupsFor(year, month, day, today = TODAY) {
  const hasDay = Number.isInteger(day) && day >= 1 && day <= 31;
  const weekday = hasDay ? new Date(year, month, day).getDay() : null;
  const isClosedDay = !hasDay || weekday === CLOSED_WEEKDAY;

  const isToday = hasDay && isSameDate({ year, month, day }, today);
  const currentTime = getCurrentTime();
  const busyTimes = hasDay ? BUSY_BY_PARITY[day % 2 === 0 ? 'even' : 'odd'] : [];

  return SCHEDULE.map((group) => ({
    title: group.title,
    slots: group.times.map((time) => {
      let available =
        !isClosedDay && !LUNCH_TIMES.includes(time) && !busyTimes.includes(time);

      // Прошедшее сегодня время записать нельзя.
      if (available && isToday && time <= currentTime) {
        available = false;
      }

      return { time, available };
    }),
  }));
}

// Количество свободных слотов в группах.
export function countAvailable(groups) {
  if (!Array.isArray(groups)) return 0;

  return groups.reduce(
    (sum, group) => sum + group.slots.filter((slot) => slot.available).length,
    0
  );
}
