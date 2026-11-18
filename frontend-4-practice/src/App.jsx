import { useEffect, useState } from 'react';

import Header from './components/Header.jsx';
import Footer from './components/Footer.jsx';
import StepIndicator from './components/StepIndicator.jsx';
import Calendar from './components/Calendar.jsx';
import SlotsPanel from './components/SlotsPanel.jsx';
import SummaryBar from './components/SummaryBar.jsx';

import { fetchToday, fetchSlots } from './api.js';
import { isSelectable } from './utils/date.js';

// App — корневой компонент.
// Данные теперь приходят с сервера: «сегодня» и слоты на дату.
function App() {
  // «Сегодня» с сервера: три состояния загрузки.
  const [today, setToday] = useState(null);
  const [todayLoading, setTodayLoading] = useState(true);
  const [todayError, setTodayError] = useState(null);

  // Слоты на выбранную дату: тоже три состояния.
  const [slots, setSlots] = useState([]);
  const [slotsLoading, setSlotsLoading] = useState(false);
  const [slotsError, setSlotsError] = useState(null);

  // Состояние календаря.
  const [year, setYear] = useState(null);
  const [month, setMonth] = useState(null);
  const [selectedDay, setSelectedDay] = useState(null);
  const [selectedTime, setSelectedTime] = useState(null);

  // 1. Загружаем «сегодня» при открытии страницы.
  useEffect(() => {
    let cancelled = false;

    async function loadToday() {
      try {
        setTodayLoading(true);
        setTodayError(null);
        const data = await fetchToday();
        if (cancelled) return;

        setToday(data);
        // Инициализируем календарь по «сегодня» с сервера.
        setYear(data.year);
        setMonth(data.month);
        setSelectedDay(data.day);
      } catch (err) {
        if (!cancelled) setTodayError(err.message);
      } finally {
        if (!cancelled) setTodayLoading(false);
      }
    }

    loadToday();

    return () => {
      cancelled = true;
    };
  }, []);

  // 2. Загружаем слоты, когда известна выбранная дата.
  useEffect(() => {
    if (year === null || month === null || selectedDay === null) return;

    let cancelled = false;

    async function loadSlots() {
      try {
        setSlotsLoading(true);
        setSlotsError(null);
        const data = await fetchSlots({ day: selectedDay, month, year });
        if (cancelled) return;

        // Защита от гонки: если ответ пришёл по другой дате — игнорируем.
        if (
          data.date.day !== selectedDay ||
          data.date.month !== month ||
          data.date.year !== year
        ) {
          return;
        }

        setSlots(data.slots);
      } catch (err) {
        if (!cancelled) {
          setSlotsError(err.message);
          setSlots([]);
        }
      } finally {
        if (!cancelled) setSlotsLoading(false);
      }
    }

    loadSlots();

    return () => {
      cancelled = true;
    };
  }, [year, month, selectedDay]);

  // Клик по дню: выделяем и обязательно сбрасываем время.
  function handleSelectDay(day) {
    setSelectedDay(day);
    setSelectedTime(null);
  }

  // Клик по слоту: повторный клик снимает выбор.
  function handleSelectTime(time) {
    setSelectedTime((current) => (current === time ? null : time));
  }

  // Приводит выбранный день к допустимому в новом месяце.
  function normalizeSelectedDay(nextYear, nextMonth) {
    const daysInMonth = new Date(nextYear, nextMonth + 1, 0).getDate();
    const startDay = Math.min(selectedDay, daysInMonth);

    for (let day = startDay; day <= daysInMonth; day++) {
      if (isSelectable(nextYear, nextMonth, day, today)) {
        setSelectedDay(day);
        return;
      }
    }

    // Если весь месяц в прошлом — выбираем первый день.
    setSelectedDay(1);
  }

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

  // Заглушка, пока не загрузилось «сегодня».
  if (todayLoading) {
    return (
      <div className="page" id="page">
        <Header />
        <main className="booking">
          <p className="booking__state">Загрузка данных календаря…</p>
        </main>
        <Footer />
      </div>
    );
  }

  // Ошибка загрузки «сегодня».
  if (todayError) {
    return (
      <div className="page" id="page">
        <Header />
        <main className="booking">
          <p className="booking__state booking__state--error">
            Не удалось загрузить данные: {todayError}
          </p>
        </main>
        <Footer />
      </div>
    );
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
            today={today}
            onSelectDay={handleSelectDay}
            onPrevMonth={handlePrevMonth}
            onNextMonth={handleNextMonth}
          />
          <SlotsPanel
            slots={slots}
            loading={slotsLoading}
            error={slotsError}
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
