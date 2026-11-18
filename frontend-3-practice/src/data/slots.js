// Данные страницы: слоты и «сегодня».
// Слотов пока нет с сервера — они захардкожены.

export const TODAY = { year: 2026, month: 10, day: 19 };

// Группы слотов. У каждого слота — время и флаг доступности.
export const SLOT_GROUPS = [
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

// Количество свободных слотов во всех группах.
export function countAvailable(groups) {
  return groups.reduce(
    (sum, group) => sum + group.slots.filter((slot) => slot.available).length,
    0
  );
}
