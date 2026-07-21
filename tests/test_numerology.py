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
