from src.utils import greet


def test_greet():
    assert greet("world") == "Hello, world"
