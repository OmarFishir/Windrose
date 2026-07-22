import pytest
from project import Home, get_sector_index, convert, recommend_window

def test_init():
    home1 = Home(["NW","E","S"])
    assert home1.windows == {"NW", "E", "S"}
    with pytest.raises(ValueError):
        Home([1,2,3])

def test_get_sector_index():
    assert get_sector_index(360) == 0
    assert get_sector_index(180) == 4

def test_convert():
    assert convert(["N"]) == "NORTH"
    assert convert(["N", "NW"]) == "NORTH and NORTHWEST"

def test_recommend_window():
    assert "weak" in recommend_window(0, Home(["NE", "NW"]))
    assert "NORTH" in recommend_window(0, Home(["N", "S"]))
    assert "sheltered" in recommend_window(0, Home(["SW", "S", "SE"]))


