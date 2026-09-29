from gofood_scraper.cli import invalid_number_input


def test_accepts_value_within_range():
    assert invalid_number_input("5", 1, 10) is False


def test_accepts_boundary_values():
    assert invalid_number_input("1", 1, 10) is False
    assert invalid_number_input("10", 1, 10) is False


def test_rejects_value_below_range():
    assert invalid_number_input("0", 1, 10) is True


def test_rejects_value_above_range():
    assert invalid_number_input("11", 1, 10) is True


def test_rejects_non_numeric_input():
    assert invalid_number_input("abc", 1, 10) is True
    assert invalid_number_input("", 1, 10) is True
