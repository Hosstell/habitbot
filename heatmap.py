import datetime
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap


def plot_habit_heatmap_binary(habits, start_date, end_date, output_file=None, title=None):
    """
    Рисует бинарную тепловую карту:
      • белый квадрат — привычка НЕ выполнена
      • зелёный квадрат — привычка выполнена хотя бы раз
    Параметры:
      habits: dict с датами 'ГГГГ-ММ-ДД' и значением 0/1
      start_date: 'ГГГГ-ММ-ДД' начало периода
      end_date:   'ГГГГ-ММ-ДД' конец периода
      output_file: путь для сохранения изображения (None — показать)
      title: заголовок графика (строка). Если None — не устанавливается.
    Добавлено:
      – названия месяцев по оси X (полные)
      – полные дни недели по оси Y (сверху Понедельник, внизу Воскресенье)
      – тонкая сетка по границам каждого дня
      – отметка первого дня месяца цифрой "1"
    """
    # Преобразование строк в даты
    start = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
    end   = datetime.datetime.strptime(end_date,   "%Y-%m-%d").date()
    # Сдвиг начала на ближайший понедельник
    start -= datetime.timedelta(days=start.weekday())
    # Подсчет недель
    total_days = (end - start).days + 1
    num_weeks  = (total_days + start.weekday()) // 7 + 1

    # Формирование матрицы и списка дат
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

    # Цветовая карта: 0 → белый, 1 → зелёный
    cmap = ListedColormap(['#FFFFFF', '#4CAF50'])

    # Рисование
    fig, ax = plt.subplots(figsize=(num_weeks * 0.25, 3))
    ax.imshow(heatmap, aspect='auto', cmap=cmap, interpolation='nearest', origin='upper', vmin=0, vmax=1)

    # Настройка оси Y (дни недели)
    dow_labels = ['Понедельник','Вторник','Среда','Четверг','Пятница','Суббота','Воскресенье']
    ax.set_yticks(range(7))
    ax.set_yticklabels(dow_labels)

    # Настройка оси X (месяцы)
    ru_months = ['', 'Январь','Февраль','Март','Апрель','Май','Июнь','Июль','Август','Сентябрь','Октябрь','Ноябрь','Декабрь']
    month_pos, month_lbl = [], []
    seen = set()
    for week, dow, date in all_dates:
        if date.day == 1 and week not in seen:
            month_pos.append(week)
            month_lbl.append(ru_months[date.month])
            seen.add(week)
    ax.set_xticks(month_pos)
    ax.set_xticklabels(month_lbl)

    # Тонкая сетка по границам ячеек
    ax.set_xticks([i - 0.5 for i in range(1, num_weeks)], minor=True)
    ax.set_yticks([i - 0.5 for i in range(1, 7)], minor=True)
    ax.grid(which='minor', color='lightgrey', linewidth=0.5)

    # Отметка первого дня месяца цифрой '1'
    for week, dow, date in all_dates:
        if date.day == 1 and start_date <= date.strftime("%Y-%m-%d") <= end_date:
            ax.text(week, dow, '1', ha='center', va='center', fontsize=6, color='grey')

    # Установка заголовка, если передан
    if title is not None:
        ax.set_title(title)

    plt.tight_layout()
    if output_file:
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        plt.close(fig)
    else:
        plt.show()


if __name__ == "__main__":
    from random import randint

    today = datetime.date.today()
    one_year_ago = today - datetime.timedelta(days=365)
    habits = {}
    d = one_year_ago
    while d <= today:
        habits[d.strftime("%Y-%m-%d")] = randint(0, 1)
        d += datetime.timedelta(days=1)

    # Пример с передачей custom title
    plot_habit_heatmap_binary(
        habits,
        start_date=one_year_ago.strftime("%Y-%m-%d"),
        end_date=today.strftime("%Y-%m-%d"),
        output_file="habit_tracker_binary.png",
        title="Мой трекер привычек"
    )
    print("Готово! Изображение сохранено в habit_tracker_binary.png")
