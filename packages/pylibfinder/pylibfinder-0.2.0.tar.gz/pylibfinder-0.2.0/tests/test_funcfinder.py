import funcfinder
import pytest


@pytest.fixture
def keyword():
    return "eval"


def test_get_module(keyword):
    result = funcfinder.get_module(keyword)

    # Assert that the result is a list
    assert isinstance(result, list)

    # Assert that each item in the list is a dictionary
    for item in result:
        assert isinstance(item, dict)

        # Assert that each dictionary contains the "Module" and "Function" keys
        assert "Module" in item
        assert "Function" in item

        # Assert that the values of "Module" and "Function" are strings
        assert isinstance(item["Module"], str)
        assert isinstance(item["Function"], str)
