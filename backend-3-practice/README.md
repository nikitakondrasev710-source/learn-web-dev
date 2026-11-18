# Салон «БРИТВА» — база данных

Учебный проект по лекции **«SQLAlchemy и Alembic»** модуля Backend.

## Что внутри

| Файл | Назначение |
|---|---|
| `solution.py` | Модели SQLAlchemy, наполнение базы, запросы через ORM, бизнес-логика свободных слотов |
| `migrations/env.py` | Конфигурация Alembic |
| `migrations/versions/0001_initial.py` | Первая миграция: создание всех таблиц |

## Структура базы

```
categories ──< services ──< appointments >── masters
                   │                            │
                   └──── master_services ───────┘
```

- `categories` — категории услуг (стрижки, ногтевой сервис, барбер);
- `services` — услуги с ценой и длительностью, ссылка на категорию;
- `masters` — мастера салона;
- `master_services` — связь «многие-ко-многим»: какой мастер какие услуги делает;
- `appointments` — записи клиентов со временем начала и окончания.

## Запуск

```bash
pip install sqlalchemy alembic

# Создать базу и наполнить данными
python solution.py

# Либо применить миграции
alembic upgrade head

# Откатить всё
alembic downgrade base
```

## Что демонстрируется

1. **Декларативные модели** через `DeclarativeBase` и `Mapped`/`mapped_column`.
2. **Связи**: один-ко-многим (`Category → Service`, `Master → Appointment`)
   и многие-ко-многим (`Master ↔ Service` через `master_services`).
3. **Запросы через ORM**: `select`, `join`, `group_by`, `func.count`, `func.sum`,
   фильтры `where`, сортировка `order_by`.
4. **Бизнес-логика**: `free_slots()` вычисляет свободные слоты мастера на день
   на основе реальных записей из базы, а не захардкоженного массива.
5. **Миграции**: миграция `0001_initial` создаёт схему, `downgrade` её удаляет.

## Проверка

```
Категорий: 3
Услуг: 6
Мастеров: 3
Записей: 2
```
