# Habit Tracker Telegram Bot

A simple Telegram bot that helps you build and maintain daily habits. It allows users to create habits, receive daily reminders, mark habits as done or canceled, and view a yearly heatmap of their habit performance.

---

## 🚀 Features

* **Create & Manage Habits**: Add, rename, and delete your habits with intuitive inline menus.
* **Daily Reminders**: Receive a reminder every day at 22:00 local time to update your habit status.
* **Quick Status Updates**: Mark a habit as ✅ Done or ❌ Canceled directly from the reminder.
* **Yearly Heatmap**: Visualize your habit consistency over the past year with a color-coded calendar heatmap.
* **Dockerized**: Easy setup and deployment using Docker.

---

## 📦 Project Structure

```
├── main.py           # Core bot logic and Telegram integration
├── heatmap.py        # Generates habit heatmaps as PNG images
├── run_bot.sh        # Helper script to build and run the Docker container
├── habits.db         # SQLite database file (mounted as a volume)
├── .env.example      # Example environment variables file
├── Dockerfile        # Builds the bot image
└── README.md         # This documentation
```

---

## 🔧 Prerequisites

* Python 3.8 or higher
* Docker & Docker Compose
* A Telegram Bot token (get one from @BotFather)

---

## ⚙️ Setup & Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/yourusername/habit-tracker-bot.git
   cd habit-tracker-bot
   ```

2. **Configure environment variables**

   ```bash
   cp .env.example .env
   # Edit .env and set your BOT_TOKEN
   ```

3. **Build and run with Docker**

   ```bash
   chmod +x run_bot.sh
   ./run_bot.sh
   ```

   This will:

    * Stop and remove any existing `habitbot` container
    * Build a new Docker image tagged `habitbot` from the `Dockerfile`
    * Launch the container, mounting `habits.db` as a volume and loading env variables

4. **Run in development** (without Docker)

   ```bash
   pip install -r requirements.txt
   python main.py
   ```

   The bot will create `habits.db` automatically if it doesn't exist.

---

## 📖 Usage

* **/start** — Display the main menu.
* **➕ Создать привычку** — Add a new habit.
* **📋 Список привычек** — View and select existing habits.

    * **✏️ Переименовать** — Change the habit's name.
    * **🗑️ Удалить** — Remove the habit.
    * **📊 Просмотреть статусы** — Generate the yearly heatmap.
* **Daily Prompt** — At 22:00, you will receive a message for each habit:

    * **✅ Done** — Mark habit as completed for today.
    * **❌ Cancel** — Mark habit as skipped/canceled.

---

## 🗄️ Database Schema

* **habits**

    * `id` (PK)
    * `user_id` (Telegram chat ID)
    * `name` (habit description)

* **statuses**

    * `id` (PK)
    * `habit_id` (FK → habits.id)
    * `date` (YYYY-MM-DD)
    * `status` (`done` or `cancel`)

---

## 🔍 Implementation Details

* **Daily Scheduling**: Uses Python `threading.Timer` to schedule the next reminder at 22:00 each day.
* **Heatmap Generation**: The `heatmap.py` module uses Matplotlib to render a binary heatmap of habit statuses over the past year.

---

## 📈 Customization

* **Change Reminder Time**: Update the `hour` in the `schedule_reminders` function in `main.py`.
* **Adjust Heatmap Style**: Modify colormap or layout in `heatmap.py`.

---

## 👥 Contributing

Contributions are welcome! Please open an issue or submit a pull request.

---

## 📝 License

This project is licensed under the MIT License. See [LICENSE](./LICENSE) for details.

---

# Трекер привычек Telegram бота (Русская версия)

Простой бот для Telegram, который помогает формировать и поддерживать ежедневные привычки. Позволяет создавать привычки, получать ежедневные напоминания, отмечать их как выполненные или пропущенные, а также просматривать годовую тепловую карту ваших результатов.

---

## 🚀 Возможности

* **Создание и управление привычками**: Добавление, переименование и удаление привычек через удобное меню.
* **Ежедневные напоминания**: Получайте уведомление каждый день в 22:00 по местному времени, чтобы обновить статус привычки.
* **Быстрое обновление статуса**: Отмечайте привычку как ✅ Выполнено или ❌ Пропущено прямо из напоминания.
* **Годовая тепловая карта**: Визуализируйте регулярность выполнения привычек за последний год цветовой картой календаря.
* **Работа в Docker**: Легкая настройка и деплой с помощью Docker.

---

## 📦 Структура проекта

```
├── main.py           # Основная логика бота и интеграция с Telegram
├── heatmap.py        # Генерация тепловых карт привычек в формате PNG
├── run_bot.sh        # Скрипт для сборки и запуска Docker-контейнера
├── habits.db         # Файл базы данных SQLite (монтируется как volume)
├── .env.example      # Пример файла с переменными окружения
├── Dockerfile        # Инструкция для сборки Docker-образа
└── README.md         # Эта документация
```

---

## 🔧 Требования

* Python 3.8 и выше
* Docker и Docker Compose
* Токен Telegram-бота (получить у @BotFather)

---

## ⚙️ Установка и запуск

1. **Клонируйте репозиторий**

   ```bash
   git clone https://github.com/yourusername/habit-tracker-bot.git
   cd habit-tracker-bot
   ```

2. **Настройте переменные окружения**

   ```bash
   cp .env.example .env
   # Откройте .env и заполните BOT_TOKEN
   ```

3. **Сборка и запуск через Docker**

   ```bash
   chmod +x run_bot.sh
   ./run_bot.sh
   ```

   Это выполнит следующие действия:

    * Остановит и удалит контейнер `habitbot`, если он существует
    * Соберет новый образ `habitbot` по Dockerfile
    * Запустит контейнер, смонтировав `habits.db` и загрузив переменные окружения

4. **Запуск в режиме разработки** (без Docker)

   ```bash
   pip install -r requirements.txt
   python main.py
   ```

   При первом запуске бот автоматически создаст `habits.db`.

---

## 📖 Использование

* **/start** — Показать главное меню.
* **➕ Создать привычку** — Добавить новую привычку.
* **📋 Список привычек** — Посмотреть и выбрать существующую привычку.

    * **✏️ Переименовать** — Изменить название привычки.
    * **🗑️ Удалить** — Удалить привычку.
    * **📊 Просмотреть статусы** — Сгенерировать годовую тепловую карту.
* **Ежедневное напоминание** — В 22:00 вы получите сообщение для каждой привычки:

    * **✅ Выполнено** — Отметить привычку как выполненную.
    * **❌ Пропущено** — Отметить привычку как пропущенную.

---

## 🗄️ Схема базы данных

* **habits**

    * `id` (PK)
    * `user_id` (Telegram chat ID)
    * `name` (описание привычки)

* **statuses**

    * `id` (PK)
    * `habit_id` (FK → habits.id)
    * `date` (YYYY-MM-DD)
    * `status` (`done` или `cancel`)

---

## 🔍 Подробности реализации

* **Ежедневное расписание**: используется `threading.Timer` для запуска напоминаний каждый день в 22:00.
* **Генерация тепловой карты**: модуль `heatmap.py` использует Matplotlib для рендеринга бинарной тепловой карты статусов привычек за последний год.

---

## 📈 Кастомизация

* **Изменить время напоминания**: обновите значение `hour` в функции `schedule_reminders` в `main.py`.
* **Настроить стиль тепловой карты**: измените colormap или макет в `heatmap.py`.

---

## 👥 Участие

Свои идеи и правки приветствуются! Открывайте issue или присылайте pull request.

---

## 📝 Лицензия

Этот проект распространяется под лицензией MIT. Подробнее в файле [LICENSE](./LICENSE).
