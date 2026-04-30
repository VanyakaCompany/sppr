def to_subscript(text):
    """
    Перевод в нижний индекс

    Args:
        text: произвольный текст

    Returns:
        Полученный текст в нижнем индексе или через нижнее подчёркивание (если хоть один символ не получилось перевести в нижний индекс)
    """

    sub_map = {
        # цифры
        "0": "₀",
        "1": "₁",
        "2": "₂",
        "3": "₃",
        "4": "₄",
        "5": "₅",
        "6": "₆",
        "7": "₇",
        "8": "₈",
        "9": "₉",
        # буквы (доступные в Unicode)
        "a": "ₐ",
        "e": "ₑ",
        "h": "ₕ",
        "i": "ᵢ",
        "j": "ⱼ",
        "k": "ₖ",
        "l": "ₗ",
        "m": "ₘ",
        "n": "ₙ",
        "o": "ₒ",
        "p": "ₚ",
        "r": "ᵣ",
        "s": "ₛ",
        "t": "ₜ",
        # некоторые символы
        "+": "₊",
        "-": "₋",
        "=": "₌",
        "(": "₍",
        ")": "₎",
    }
    result = []

    for ch in str(text):
        if ch in sub_map:
            result.append(sub_map[ch.lower()])
        else:
            return "_" + text

    return "".join(result)


def get_valid_input(prompt, input_type=str, validator=None, error_message=None):
    """
    Общий метод для ввода данных с валидацией

    Args:
        prompt: Текст приглашения для ввода
        input_type: Тип данных для преобразования (int, float)
        validator: Функция-валидатор, которая принимает значение и возвращает bool
        error_message: Сообщение об ошибке

    Returns:
        Введенное и валидированное значение
    """
    while True:
        try:
            value = input_type(input(prompt))

            if validator is None or validator(value):
                return value
            elif error_message:
                print(error_message)
        except ValueError:
            if error_message:
                print(error_message)
