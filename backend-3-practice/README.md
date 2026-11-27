# Backend. Задание 3. SQLAlchemy и Alembic

Учебный проект базы данных барбершопа «БРИТВА». Используются SQLAlchemy 2.x, SQLite и Alembic.

## Состав проекта

- solution.py — ORM-модели, связи, демонстрационные данные, запросы и бизнес-логика записи.
- alembic.ini — конфигурация Alembic.
- migrations/env.py — подключение метаданных моделей к Alembic.
- migrations/versions/0001_initial.py — начальная миграция схемы.
- tests/ — автоматические проверки моделей, запросов, бизнес-логики и миграций.
- requirements.txt — зависимости.

## Структура базы данных

В базе пять таблиц:

1. categories — категории услуг.
2. services — услуги с ценой и продолжительностью.
3. masters — мастера.
4. master_services — связь многие-ко-многим между мастерами и услугами.
5. appointments — записи клиентов.

Связи: Category → Service — один ко многим; Master ↔ Service — многие ко многим; Master → Appointment и Service → Appointment — один ко многим.

## Установка и запуск

Выполняйте команды из папки backend-3-practice.

    python -m venv .venv
    .venv\Scripts\activate
    pip install -r requirements.txt
    alembic upgrade head
    python solution.py seed
    python solution.py queries

Проверка свободных интервалов:

    python solution.py slots --master-id 1 --service-id 1 --date 2030-01-16

Запуск тестов:

    pytest -q

## Миграции

Применить миграции: alembic upgrade head

Проверить текущую версию: alembic current

Проверить расхождения моделей и миграций: alembic check

Откатить последнюю миграцию: alembic downgrade -1

Откатить все миграции: alembic downgrade base

После отката для повторного создания схемы выполните alembic upgrade head.

Таблицы не создаются при импорте solution.py. Alembic является основным способом управления схемой. Команда python solution.py init-db предназначена только для учебной демонстрации создания схемы напрямую и не должна выполняться перед alembic upgrade head на той же пустой базе.

## Что демонстрируется

1. Декларативные модели SQLAlchemy 2.0 с DeclarativeBase, Mapped и mapped_column.
2. Связи один-ко-многим и многие-ко-многим.
3. Внешние ключи, ограничения CHECK, уникальность и индексы.
4. ORM-запросы select, join, outerjoin, where, order_by, group_by, count и sum.
5. Расчёт свободных интервалов с учётом продолжительности услуги, занятых и отменённых записей.
6. Создание и отмена записи.
7. Миграции Alembic с поддержкой чистой установки и отката.

## Демонстрационные данные

При первом выполнении python solution.py seed создаются:

- 3 категории;
- 6 услуг;
- 3 мастера;
- 2 записи.

Повторный запуск seed не дублирует данные.

Для SQLite включена проверка внешних ключей через PRAGMA foreign_keys=ON. Переменная окружения DATABASE_URL позволяет указать альтернативную базу данных для тестирования и запуска.
