import pytest
from hidden_dataset.bad_syntax import calculate_sum
from hidden_dataset.logic_bug import count_down
from hidden_dataset.messy_code import f

def test_calculate_sum_positive_integers():
    assert calculate_sum(1, 2) == 3

def test_calculate_sum_mixed_integers():
    assert calculate_sum(-5, 10) == 5

def test_calculate_sum_floats():
    assert calculate_sum(3.5, 2.5) == 6.0

def test_calculate_sum_string_concatenation():
    assert calculate_sum("hello", " world") == "hello world"

def test_calculate_sum_type_error():
    with pytest.raises(TypeError):
        calculate_sum(10, "invalid")

def test_count_down_positive_number(capsys):
    count_down(3)
    captured = capsys.readouterr()
    assert captured.out == "3\n2\n1\n"

def test_count_down_one(capsys):
    count_down(1)
    captured = capsys.readouterr()
    assert captured.out == "1\n"

def test_count_down_zero(capsys):
    count_down(0)
    captured = capsys.readouterr()
    assert captured.out == ""

def test_count_down_negative_number(capsys):
    count_down(-5)
    captured = capsys.readouterr()
    assert captured.out == ""

def test_f_in_range():
    assert f(50) is True

def test_f_just_above_lower_bound():
    assert f(0.1) is True

def test_f_at_lower_bound():
    assert f(0) is False

def test_f_at_upper_bound():
    assert f(100) is False

def test_f_outside_range_negative():
    assert f(-5) is False