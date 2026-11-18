import { useState } from 'react';

import Header from './components/Header.jsx';
import Footer from './components/Footer.jsx';
import StepIndicator from './components/StepIndicator.jsx';
import Calendar from './components/Calendar.jsx';
import SlotsPanel from './components/SlotsPanel.jsx';
import SummaryBar from './components/SummaryBar.jsx';

import { TODAY, SLOT_GROUPS } from './data/slots.js';
import { isSelectable, getFirstSelectableDay } from './utils/date.js';

// App — корневой компонент.
// Здесь живёт всё состояние страницы: месяц, выбранный день, время.
function App() {
  // Было: переменные state.year, state.month, state.selectedDay, state.selectedTime.
  // Стало: независимые useState.
  const [year, setYear] = useState(TODAY.year);
  const [month, setMonth] = useState(TODAY.month);
  const [selectedDay, setSelectedDay] = useState(TODAY.day);
  const [selectedTime, setSelectedTime] = useState(null);

  // Клик по дню: выделяем его и обязательно сбрасываем время.
  function handleSelectDay(day) {
    setSelectedDay(day);
    setSelectedTime(null);
  }

  // Клик по слоту: повторный клик по тому же времени снимает выбор.
  function handleSelectTime(time) {
    setSelectedTime((current) => (current === time ? null : time));
  }

  // Приводит выбранный день к допустимому в новом месяце:
  // если день в прошлом — берём первый доступный по порядку.
  function normalizeSelectedDay(nextYear, nextMonth) {
    const daysInMonth = new Date(nextYear, nextMonth + 1, 0).getDate();
    const startDay = Math.min(selectedDay, daysInMonth);

    for (let day = startDay; day <= daysInMonth; day++) {
      if (isSelectable(nextYear, nextMonth, day, TODAY)) {
        setSelectedDay(day);
        return;
      }
    }

    const firstSelectable = getFirstSelectableDay(nextYear, nextMonth, TODAY);
    setSelectedDay(firstSelectable || 1);
  }

  // Стрелки листают месяцы с переходом через год.
  function handlePrevMonth() {
    const nextYear = month === 0 ? year - 1 : year;
    const nextMonth = month === 0 ? 11 : month - 1;

    setYear(nextYear);
    setMonth(nextMonth);
    setSelectedTime(null);
    normalizeSelectedDay(nextYear, nextMonth);
  }

  function handleNextMonth() {
    const nextYear = month === 11 ? year + 1 : year;
    const nextMonth = month === 11 ? 0 : month + 1;

    setYear(nextYear);
    setMonth(nextMonth);
    setSelectedTime(null);
    normalizeSelectedDay(nextYear, nextMonth);
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
            groups={SLOT_GROUPS}
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
        />
      </main>

      <Footer />
    </div>
  );
}

export default App;
