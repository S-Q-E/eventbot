def get_match_word(number: int) -> str:
    """
    Возвращает правильное склонение слова 'матч' для заданного числа.
    """
    if 11 <= number % 100 <= 14:
        return "матчей"
    last_digit = number % 10
    if last_digit == 1:
        return "матч"
    if 2 <= last_digit <= 4:
        return "матча"
    return "матчей"
