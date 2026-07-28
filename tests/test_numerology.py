import pytest
from datetime import date
from bot.services.numerology import NumerologyEngine

def test_life_path_number():
    engine = NumerologyEngine()
    # Test: 01.01.2000 = 0+1+0+1+2+0+0+0 = 4
    assert engine.life_path_number(date(2000, 1, 1)) == 4

def test_reduce_to_single():
    engine = NumerologyEngine()
    assert engine.reduce_to_single(28) == 1  # 2+8=10 -> 1+0=1
    assert engine.reduce_to_single(11) == 11  # Master number
    assert engine.reduce_to_single(22) == 22  # Master number
    assert engine.reduce_to_single(123) == 6  # 1+2+3=6

def test_soul_number():
    engine = NumerologyEngine()
    # "Анна" = vowels: А(1) + а(1) = 2
    assert engine.soul_number("Анна") == 2

def test_basic_numbers():
    engine = NumerologyEngine()
    numbers = engine.get_basic_numbers(date(1990, 5, 15), "Иван Иванов")
    assert "life_path" in numbers
    assert "soul" in numbers
    assert "personality" in numbers
    assert "destiny" in numbers
    assert "birthday" in numbers

def test_get_calc_breakdown_life_path():
    engine = NumerologyEngine()
    # 14.09.1965 → 1+4+0+9+1+9+6+5 = 35 → 3+5 = 8
    result = engine.get_calc_breakdown("life_path", date(1965, 9, 14))
    assert result == "14.09.1965 → 1+4+0+9+1+9+6+5 = 35 → 3+5 = 8"

def test_get_calc_breakdown_life_path_no_reduction():
    engine = NumerologyEngine()
    # 01.01.2000 → 0+1+0+1+2+0+0+0 = 4 (already single digit)
    result = engine.get_calc_breakdown("life_path", date(2000, 1, 1))
    assert result == "01.01.2000 → 0+1+0+1+2+0+0+0 = 4"

def test_get_calc_breakdown_life_path_master_number():
    engine = NumerologyEngine()
    # 11.11.1992 → 1+1+1+1+1+9+9+2 = 25 → 2+5 = 7
    result = engine.get_calc_breakdown("life_path", date(1992, 11, 11))
    assert result == "11.11.1992 → 1+1+1+1+1+9+9+2 = 25 → 2+5 = 7"

def test_get_calc_breakdown_birthday():
    engine = NumerologyEngine()
    # Day 14 → 1+4 = 5
    result = engine.get_calc_breakdown("birthday", date(1965, 9, 14))
    assert result == "День 14 → 1+4 = 5"

def test_get_calc_breakdown_birthday_double_digit():
    engine = NumerologyEngine()
    # Day 29 → 2+9 = 11 → 1+1 = 2
    result = engine.get_calc_breakdown("birthday", date(1990, 5, 29))
    assert result == "День 29 → 2+9 = 11 → 1+1 = 2"

def test_get_calc_breakdown_birthday_single_digit():
    engine = NumerologyEngine()
    # Day 5 → 5 (already single digit)
    result = engine.get_calc_breakdown("birthday", date(1990, 5, 5))
    assert result == "День 5 → 5 = 5"

def test_get_calc_breakdown_soul():
    engine = NumerologyEngine()
    # "Иван" → vowels: И(1) + а(1) = 2
    result = engine.get_calc_breakdown("soul", date(1965, 9, 14), "Иван")
    assert result == "Иван → И(1) + а(1) = 2"

def test_get_calc_breakdown_personality():
    engine = NumerologyEngine()
    # "Иван" → consonants: в(3) + н(6) = 9
    result = engine.get_calc_breakdown("personality", date(1965, 9, 14), "Иван")
    assert result == "Иван → в(3) + н(6) = 9"

def test_get_calc_breakdown_destiny_master_number():
    engine = NumerologyEngine()
    # "Иван" → all: И(1) + в(3) + а(1) + н(6) = 11 (master number, no reduction)
    result = engine.get_calc_breakdown("destiny", date(1965, 9, 14), "Иван")
    assert result == "Иван → И(1) + в(3) + а(1) + н(6) = 11"

def test_get_calc_breakdown_destiny_with_reduction():
    engine = NumerologyEngine()
    # "Алексей" → all: А(1) + л(4) + е(6) + к(3) + с(1) + е(6) + й(2) = 23 → 2+3 = 5
    result = engine.get_calc_breakdown("destiny", date(1990, 5, 15), "Алексей")
    assert result == "Алексей → А(1) + л(4) + е(6) + к(3) + с(1) + е(6) + й(2) = 23 → 2+3 = 5"

def test_get_calc_breakdown_name_based_empty_name():
    engine = NumerologyEngine()
    # Empty name should return None
    assert engine.get_calc_breakdown("soul", date(1965, 9, 14), "") is None
    assert engine.get_calc_breakdown("personality", date(1965, 9, 14), "") is None
    assert engine.get_calc_breakdown("destiny", date(1965, 9, 14), "") is None

def test_get_calc_breakdown_name_based_no_vowels():
    engine = NumerologyEngine()
    # Name with no vowels → soul returns None
    assert engine.get_calc_breakdown("soul", date(1965, 9, 14), "Птр") is None

def test_get_calc_breakdown_unknown_type_returns_none():
    engine = NumerologyEngine()
    assert engine.get_calc_breakdown("unknown", date(1965, 9, 14)) is None


def test_fate_matrix_basic():
    engine = NumerologyEngine()
    # 14.09.1965 → digits: 1+4+0+9+1+9+6+5 = 35
    result = engine.fate_matrix(date(1965, 9, 14))
    assert result["day"] == 14
    assert result["month"] == 9
    assert result["year"] == 1965
    assert result["a"] == 35  # sum of all digits
    assert result["b"] == 8  # 3+5 = 8 (life path)
    assert result["c"] == 1  # |1 - (2*1)| = 1
    assert result["d"] == 1  # sum of digits of C
    assert result["life_path"] == 8


def test_fate_matrix_matrix_structure():
    engine = NumerologyEngine()
    result = engine.fate_matrix(date(1965, 9, 14))
    matrix = result["matrix"]
    assert len(matrix) == 3  # 3 rows
    assert all(len(row) == 3 for row in matrix)  # 3 columns each
    # Row 1: day, month, year
    assert matrix[0] == [14, 9, 1965]
    # Row 2: A, B, C
    assert matrix[1] == [35, 8, 1]
    # Row 3: D, life_path, D
    assert matrix[2] == [1, 8, 1]


def test_fate_matrix_cell_meanings():
    engine = NumerologyEngine()
    result = engine.fate_matrix(date(1965, 9, 14))
    assert "cell_meanings" in result
    assert len(result["cell_meanings"]) == 9
    assert result["cell_meanings"][1] == "Тело, здоровье, физическая сила"
    assert result["cell_meanings"][5] == "Цель жизни, главное предназначение, смысл"
    assert result["cell_meanings"][8] == "Жизненный путь, основная миссия"


def test_fate_matrix_single_digit_sum():
    engine = NumerologyEngine()
    # 01.01.2000 → digits: 0+1+0+1+2+0+0+0 = 4
    result = engine.fate_matrix(date(2000, 1, 1))
    assert result["a"] == 4
    assert result["b"] == 4
    assert result["life_path"] == 4


def test_fate_matrix_date_str_and_digits():
    engine = NumerologyEngine()
    result = engine.fate_matrix(date(1965, 9, 14))
    assert result["date_str"] == "14091965"
    assert result["digits"] == [1, 4, 0, 9, 1, 9, 6, 5]

