import pylibfinder
import pytest


@pytest.fixture
def query():
    return "power"


def test_find_similar_basic(query):
    """Test basic semantic similarity search."""
    result = pylibfinder.find_similar(query)

    # Assert that the result is a list
    assert isinstance(result, list)

    # Assert that we found at least one match
    assert len(result) > 0

    # Assert that each item in the list is a dictionary
    for item in result:
        assert isinstance(item, dict)

        # Assert that each dictionary contains required keys
        assert "Module" in item
        assert "Function" in item
        assert "Score" in item

        # Assert that the values are of correct types
        assert isinstance(item["Module"], str)
        assert isinstance(item["Function"], str)
        assert isinstance(item["Score"], float)

        # Assert that similarity score is valid (0.0 to 1.0)
        assert 0.0 <= item["Score"] <= 1.0


def test_find_similar_with_threshold():
    """Test semantic similarity with custom threshold."""
    result = pylibfinder.find_similar("print", 0.9)

    # Assert that the result is a list
    assert isinstance(result, list)

    # Assert that all results meet the threshold
    for item in result:
        assert item["Score"] >= 0.9


def test_find_similar_exact_match():
    """Test exact match returns high similarity."""
    result = pylibfinder.find_similar("print", 0.5)

    # Find the exact match in results
    exact_match = None
    for item in result:
        if item["Function"] == "print" and item["Module"] == "builtins":
            exact_match = item
            break

    # Assert that exact match was found
    assert exact_match is not None

    # Assert that exact match has perfect or near-perfect score
    assert exact_match["Score"] >= 0.99


def test_find_similar_substring_match():
    """Test that substring matches get boosted similarity."""
    result = pylibfinder.find_similar("print_function", 0.5)

    # Assert that we found results
    assert len(result) > 0

    # Assert that print_function substring provides matches
    found_print_related = False
    for item in result:
        if "print" in item["Function"].lower():
            found_print_related = True
            break

    assert found_print_related
