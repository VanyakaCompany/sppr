from utils import parse_args, to_subscript, get_valid_input, format_float, save_json
from tabulate import tabulate
import json
import math


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
        raise ValueError(f"В конфиге отсутствуют обязательные поля ({', '.join(missing)})")

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

    return method - 1, options_count, conditions_count, q, matrix


def manual_input():
    """Ручной ввод данных"""

    method = get_valid_input(
        "1) MM\n2) BL\nВыберете метод: ",
        int,
        lambda x: x in [1, 2],
        "Выберите один из предложенных вариантов!",
    )
    options_count = get_valid_input(
        "Введите кол-во вариантов: ", int, lambda x: x > 0, "Введите целое положительное число!"
    )
    conditions_count = get_valid_input(
        "Введите кол-во условий: ", int, lambda x: x > 0, "Введите целое положительное число!"
    )

    q = []
    if method == 2:
        while True:
            print("Заполните вероятности событий")
            for i in range(conditions_count):
                prompt = f"q{to_subscript(i + 1)}: "
                q.append(
                    get_valid_input(prompt, float, lambda x: x >= 0 and x <= 1, "Введите число от 0 до 1")
                )
            if math.isclose(sum(q), 1, rel_tol=1e-9):
                break
            else:
                print("Сумма вероятностей всех событий должна равняться единице!")
                q = []

    matrix = []
    print("Заполните матрицу:")
    for i in range(options_count):
        matrix.append([])
        for j in range(conditions_count):
            prompt = f"e{to_subscript(str(i + 1) + str(j + 1))}: "
            matrix[i].append(get_valid_input(prompt, float, error_message="Введите число!"))

    print()

    return method - 1, options_count, conditions_count, q, matrix


def MM_simplify(matrix):
    """
    Определение наихудшего исхода для каждой альтернативы (строки)
    Args:
        matrix: матрица оценок
    Returns:
        Массив минимальных значений для каждой строки
    """
    return [min(matrix[i]) for i in range(len(matrix))]


def BL_simplify(matrix, q):
    """
    Вычисление математического ожидания (средневзвешенной суммы) для каждой альтернативы (строки) с учетом вероятностей
    Args:
        matrix: матрица оценок
        q: массив вероятностей для каждого состояния (столбца)
    Returns:
        Массив математических ожиданий для каждой строки
    """
    result = []

    for i in range(len(matrix)):
        result.append(sum([matrix[i][j] * q[j] for j in range(len(matrix[i]))]))

    return result


def main():
    args = parse_args()

    try:
        method, options_count, conditions_count, q, matrix = (
            parse_config(args.input) if args.input else manual_input()
        )
    except Exception as e:
        print(f"Ошибка загрузки конфига: {e}")
        return

    FORMULAS = [
        {  # MM
            "e_ir": f"e{to_subscript('ir')} = min e{to_subscript('ij')}",
            "z": f"Z{to_subscript('MM')} = max e{to_subscript('ir')}",
            "E_o": f"E{to_subscript('o')} = {{ E{to_subscript('io')} | E{to_subscript('io')} ∈ E ∧ e{to_subscript('io')} = Z{to_subscript('MM')} }}",
        },
        {  # BL
            "e_ir": f"e{to_subscript('ir')} = Σ e{to_subscript('ij')} * q{to_subscript('j')}",
            "z": f"Z{to_subscript('BL')} = max e{to_subscript('ir')}",
            "E_o": f"E{to_subscript('o')} = {{ E{to_subscript('io')} | E{to_subscript('io')} ∈ E ∧ e{to_subscript('io')} = Z{to_subscript('BL')} ∧ Σ q{to_subscript('j')} = 1 }}",
        },
    ]

    print(f"Метод: {["MM", "BL"][method]}")
    print("Исходные данные:")
    rows = [f"E{to_subscript(i + 1)}" for i in range(options_count)]
    headers = [f"F{to_subscript(i + 1)}{f" ({q[i]})" if i < len(q) else ""}" for i in range(conditions_count)]
    table = [[row_name] + row for row_name, row in zip(rows, matrix)]
    print(tabulate(table, headers=headers, tablefmt="grid"))

    Fr = MM_simplify(matrix) if method == 0 else BL_simplify(matrix, q)
    Z = max(Fr)

    print(f"\nУпрощаем многокритериальную матрицу ({FORMULAS[method]["e_ir"]}):")
    headers += [f"F{to_subscript('r')}"]
    table = [row + [e_ir] for row, e_ir in zip(table, Fr)]
    print(tabulate(table, headers=headers, tablefmt="grid"))

    print(
        f"\nПрименям к столбцу F{to_subscript('r')} оценочную ф-ю метода:\n{FORMULAS[method]['z']} = {format_float(Z)}"
    )

    print(f"\nВыбираем оптимальные варианты ({FORMULAS[method]['E_o']}):")
    Eo = [f"E{to_subscript(i + 1)}" for i in range(len(Fr)) if math.isclose(Fr[i], Z, rel_tol=1e-9)]
    print(f"E{to_subscript('o')} = {{ {', '.join(Eo)} }}")

    if args.output:
        data = {
            "method": method + 1,
            "options_count": options_count,
            "conditions_count": conditions_count,
            "q": q,
            "matrix": matrix,
            "F_r": Fr,
            "Z": Z,
            "Eo": Eo,
        }
        save_json(data, args.output)


if __name__ == "__main__":
    main()
