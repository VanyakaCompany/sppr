from utils import to_subscript, get_valid_input
from tabulate import tabulate
import argparse
import json


def parse_config(path):
    """
    Извлечение данных из конфига
    Args:
        path: путь к конфигурационному файлу
    """

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        raise ValueError(f"Файл не найден: {path}")
    except json.JSONDecodeError:
        raise ValueError("Ошибка чтения JSON (некорректный формат)")

    required_fields = ["method", "options_count", "conditions_count", "matrix"]
    missing = [field for field in required_fields if field not in data]

    if missing:
        raise ValueError(f"В конфиге отсутствуют обязательные поля({', '.join(missing)})")

    method = data["method"]
    options_count = data["options_count"]
    conditions_count = data["conditions_count"]
    q = data.get("q", [])
    matrix = data["matrix"]

    if method not in [1, 2]:
        raise ValueError("Указан некорректный индекс метода")
    if options_count <= 0:
        raise ValueError("Указано некорректное кол-во вариантов")
    if conditions_count <= 0:
        raise ValueError("Указано некорректное кол-во состояний")

    # Валидация q
    if method == 2:
        if len(q) != conditions_count:
            raise ValueError("Количество вероятностей q должно совпадать с количеством состояний")
        if not all(isinstance(x, (int, float)) for x in q):
            raise ValueError("Все значения q должны быть числами")
        if not all(0 <= x <= 1 for x in q):
            raise ValueError("Все q должны быть в диапазоне [0, 1]")
        if abs(sum(q) - 1.0) >= 1e-9:
            raise ValueError("Сумма q должна быть равна 1")

    # Валидация матрицы
    if len(matrix) != options_count:
        raise ValueError("Размер матрицы не совпадает с количеством вариантов")
    for row in matrix:
        if len(row) != conditions_count:
            raise ValueError("Размер строки матрицы не совпадает с количеством состояний")

    return method, options_count, conditions_count, q, matrix


def manual_input():
    """Ручной ввод данных"""

    method = get_valid_input("1) MM\n2) BL\nВыберете метод: ", int, lambda x: x in [1, 2])
    options_count = get_valid_input("Введите кол-во вариантов: ", int, lambda x: x > 0)
    conditions_count = get_valid_input("Введите кол-во условий: ", int, lambda x: x > 0)

    q = []
    if method == 2:
        while True:
            print("Заполните вероятности событий")
            for i in range(conditions_count):
                prompt = f"q{to_subscript(i + 1)}: "
                q.append(get_valid_input(prompt, float, lambda x: x >= 0 and x <= 1))
            if abs(sum(q) - 1.0) < 1e-9:
                break
            else:
                print("Сумма вероятностей всех событий должна равняться единице!")
                q = []

    matrix = []
    print("Заполните матрицу:")
    for i in range(options_count):
        matrix.append([])
        for j in range(conditions_count):
            prompt = f"e{to_subscript(str(i) + str(j))}: "
            matrix[i].append(get_valid_input(prompt, float))

    print()

    return method, options_count, conditions_count, q, matrix


def parse_args():
    """Формирование подсказки и парсинг параметров вызова"""
    parser = argparse.ArgumentParser(
        description="Программа поддержки принятия решений, на основе алгоритмов многокритериальных методов.",
        epilog="Пример: python main.py --config config.json",
        add_help=False,
    )
    parser.add_argument("-h", "--help", action="help", help="Показать эту справку и выйти")
    parser.add_argument("--config", type=str, help="Путь к JSON конфигу")
    return parser.parse_args()


def main():
    args = parse_args()

    try:
        method, options_count, conditions_count, q, matrix = (
            parse_config(args.config) if args.config else manual_input()
        )
    except Exception as e:
        print(f"Ошибка загрузки конфига: {e}")
        return

    print(f"Метод: {['MM', 'BL'][method - 1]}")
    print(f"Кол-во вариантов: {options_count}")
    print(f"Кол-во условий: {conditions_count}")
    if method == 2:
        print("Вероятности событий: ", q)
    print("Матрица исходных данных: ", matrix)

    rows = [f"E{to_subscript(i + 1)}" for i in range(options_count)]
    headers = [f"F{to_subscript(i + 1)}{f" ({q[i]})" if i < len(q) else ""}" for i in range(conditions_count)]
    table = [[row_name] + row for row_name, row in zip(rows, matrix)]
    print(tabulate(table, headers=headers, tablefmt="grid"))


if __name__ == "__main__":
    main()
