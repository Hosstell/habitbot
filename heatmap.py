import datetime
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import io


def plot_habit_heatmap_binary(habits, start_date, end_date, title=None):
    """
    Формирует бинарную тепловую карту привычек и возвращает изображение в формате PNG для отправки через Telegram.

    Параметры:
      habits: dict с датами 'ГГГГ-ММ-ДД' и значением 0/1
      start_date: date
      end_date: date
      title: заголовок графика (строка). Если None — без заголовка.

    Возвращает:
      bytes: PNG-изображение тепловой карты
    """
    # Преобразование строк в даты
    start = start_date
    end   = end_date
    start_date = str(start_date)
    end_date = str(end_date)
    start -= datetime.timedelta(days=start.weekday())  # сдвиг на понедельник

    # Число недель
    total_days = (end - start).days + 1
    num_weeks  = (total_days + start.weekday()) // 7 + 1

    # Сбор матрицы и дат
    heatmap = []
    all_dates = []
    for dow in range(7):
        row = []
        for week in range(num_weeks):
            current = start + datetime.timedelta(weeks=week, days=dow)
            all_dates.append((week, dow, current))
            executed = 1 if start_date <= current.strftime("%Y-%m-%d") <= end_date and habits.get(current.strftime("%Y-%m-%d"), 0) > 0 else 0
            row.append(executed)
        heatmap.append(row)

    # Построение
    cmap = ListedColormap(['#FFFFFF', '#4CAF50'])
    fig, ax = plt.subplots(figsize=(num_weeks * 0.25, 3))
    ax.imshow(heatmap, aspect='auto', cmap=cmap, interpolation='nearest', origin='upper', vmin=0, vmax=1)

    # Дни недели
    dow_labels = ['Понедельник','Вторник','Среда','Четверг','Пятница','Суббота','Воскресенье']
    ax.set_yticks(range(7))
    ax.set_yticklabels(dow_labels)

    # Месяцы
    ru_months = ['', 'Январь','Февраль','Март','Апрель','Май','Июнь','Июль','Август','Сентябрь','Октябрь','Ноябрь','Декабрь']
    month_pos, month_lbl, seen = [], [], set()
    for week, dow, date in all_dates:
        if date.day == 1 and week not in seen:
            month_pos.append(week)
            month_lbl.append(ru_months[date.month])
            seen.add(week)
    ax.set_xticks(month_pos)
    ax.set_xticklabels(month_lbl)

    # Сетка по ячейкам
    ax.set_xticks([i - 0.5 for i in range(1, num_weeks)], minor=True)
    ax.set_yticks([i - 0.5 for i in range(1, 7)], minor=True)
    ax.grid(which='minor', color='lightgrey', linewidth=0.5)

    # Отметка первого дня месяца
    for week, dow, date in all_dates:
        if date.day == 1 and start_date <= date.strftime("%Y-%m-%d") <= end_date:
            ax.text(week, dow, '1', ha='center', va='center', fontsize=6, color='grey')

    # Заголовок
    if title:
        ax.set_title(title)

    plt.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=150)
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


# Пример использования
if __name__ == '__main__':
    from random import randint
    today = datetime.date.today()
    one_year_ago = today - datetime.timedelta(days=365)
    habits = {}
    d = one_year_ago
    while d <= today:
        habits[d.strftime('%Y-%m-%d')] = randint(0, 1)
        d += datetime.timedelta(days=1)

    img_bytes = plot_habit_heatmap_binary(
        habits,
        start_date=one_year_ago.strftime('%Y-%m-%d'),
        end_date=today.strftime('%Y-%m-%d'),
        title='Мой трекер привычек'
    )
    # Теперь img_bytes можно отправить через Telegram API
