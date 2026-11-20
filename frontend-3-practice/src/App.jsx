import { useState } from 'react';

import Header from './components/Header.jsx';
import Footer from './components/Footer.jsx';
import StepIndicator from './components/StepIndicator.jsx';
import Calendar from './components/Calendar.jsx';
import SlotsPanel from './components/SlotsPanel.jsx';
import SummaryBar from './components/SummaryBar.jsx';

import { TODAY, getSlotGroupsFor } from './data/slots.js';
import { isSelectable, getFirstSelectableDay } from './utils/date.js';

// App — корневой компонент.
// Здесь живёт всё состояние страницы: месяц, выбранный день, время.
function App() {
  // Было: переменные state.year, state.month, state.selectedDay, state.selectedTime.
  // Стало: независимые useState.
  // selectedDay = null означает «дата не выбрана»: так бывает,
  // когда пользователь ушёл в месяц, где выбирать уже нечего.
  const [year, setYear] = useState(TODAY.year);
  const [month, setMonth] = useState(TODAY.month);
  const [selectedDay, setSelectedDay] = useState(TODAY.day);
  const [selectedTime, setSelectedTime] = useState(null);
  const [isConfirmed, setIsConfirmed] = useState(false);

  // Слоты пересчитываются под выбранную дату: занятые часы зависят
  // от дня, а прошедшие часы сегодняшнего дня блокируются.
  const slotGroups = getSlotGroupsFor(year, month, selectedDay, TODAY);

  // Клик по дню: выделяем его и обязательно сбрасываем время.
  function handleSelectDay(day) {
    if (!isSelectable(year, month, day, TODAY)) return;

    setSelectedDay(day);
    setSelectedTime(null);
    setIsConfirmed(false);
  }

  // Клик по слоту: повторный клик по тому же времени снимает выбор.
  function handleSelectTime(time) {
    setSelectedTime((current) => (current === time ? null : time));
    setIsConfirmed(false);
  }

  // Приводит выбранный день к допустимому в новом месяце.
  // Если выбирать нечего (месяц целиком прошёл) — ставим null,
  // а не первое число: первое число в прошедшем месяце недоступно.
  function normalizeSelectedDay(nextYear, nextMonth) {
    const daysInMonth = new Date(nextYear, nextMonth + 1, 0).getDate();

    // Такого числа в новом месяце нет (например, было 31, стал февраль).
    let day = selectedDay;
    if (day !== null && day > daysInMonth) {
      day = daysInMonth;
    }

    if (day !== null && isSelectable(nextYear, nextMonth, day, TODAY)) {
      setSelectedDay(day);
      return;
    }

    // Ищем первый допустимый день месяца, начиная с выбранного.
    const startDay = day ?? 1;
    for (let candidate = startDay; candidate <= daysInMonth; candidate += 1) {
      if (isSelectable(nextYear, nextMonth, candidate, TODAY)) {
        setSelectedDay(candidate);
        return;
      }
    }

    // Месяц уже прошёл — дата не выбрана, время отключено.
    const firstSelectable = getFirstSelectableDay(nextYear, nextMonth, TODAY);
    setSelectedDay(firstSelectable ?? null);
  }

  // Стрелки листают месяцы с переходом через год.
  function handlePrevMonth() {
    const nextYear = month === 0 ? year - 1 : year;
    const nextMonth = month === 0 ? 11 : month - 1;

    setYear(nextYear);
    setMonth(nextMonth);
    setSelectedTime(null);
    setIsConfirmed(false);
    normalizeSelectedDay(nextYear, nextMonth);
  }

  function handleNextMonth() {
    const nextYear = month === 11 ? year + 1 : year;
    const nextMonth = month === 11 ? 0 : month + 1;

    setYear(nextYear);
    setMonth(nextMonth);
    setSelectedTime(null);
    setIsConfirmed(false);
    normalizeSelectedDay(nextYear, nextMonth);
  }

  // Кнопка «Далее»: подтверждаем запись на выбранные дату и время.
  function handleConfirm() {
    if (!selectedDay || !selectedTime) return;
    setIsConfirmed(true);
  }

  return (
    <div className="page" id="page">
      <Header />

      <main className="booking">
        <div className="booking__topbar">
          <a className="back-link" href="#">
            <span className="back-link__icon" aria-hidden="true">
              ←
            </span>
            <span className="back-link__text">К выбору услуги</span>
          </a>
          <StepIndicator currentStep={2} />
        </div>

        <div className="booking__headline">
          <p className="booking__eyebrow">Стрижка · Борода · Бритьё</p>
          <h1 className="booking__title">Выбор даты и времени</h1>
          <p className="booking__hint">
            Свободные слоты отмечены светлым. Занятые — недоступны для записи.
          </p>
        </div>

        <div className="booking__columns">
          <Calendar
            year={year}
            month={month}
            selectedDay={selectedDay}
            today={TODAY}
            onSelectDay={handleSelectDay}
            onPrevMonth={handlePrevMonth}
            onNextMonth={handleNextMonth}
          />
          <SlotsPanel
            groups={slotGroups}
            year={year}
            month={month}
            selectedDay={selectedDay}
            selectedTime={selectedTime}
            onSelectTime={handleSelectTime}
          />
        </div>

        <SummaryBar
          year={year}
          month={month}
          selectedDay={selectedDay}
          selectedTime={selectedTime}
          isConfirmed={isConfirmed}
          onNext={handleConfirm}
        />
      </main>

      <Footer />
    </div>
  );
}

export default App;
