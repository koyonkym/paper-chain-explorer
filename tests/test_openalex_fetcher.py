from unittest.mock import patch
from src.setup_database import OpenAlexFetcher


def test_chunk_list():
    lst = [1, 2, 3, 4, 5]
    chunk_size = 2
    chunks = list(OpenAlexFetcher.chunk_list(lst, chunk_size))
    assert chunks == [[1, 2], [3, 4], [5]]

    # Edge case: Empty list
    assert list(OpenAlexFetcher.chunk_list([], chunk_size)) == []

    # Edge case: Chunk size larger than list
    assert list(OpenAlexFetcher.chunk_list(lst, 10)) == [[1, 2, 3, 4, 5]]

# Mock Works() filter method
@patch("pyalex.Works.filter")
def test_fetch_works(mock_filter):
    mock_filter.return_value.get.return_value = [
        {"id": "https://openalex.org/W0123456789", "title": "Test Work"}
    ]

    work_ids = ["W0123456789"]
    works = OpenAlexFetcher.fetch_works(work_ids)

    assert len(works) == 1
    assert works[0]["id"] == "https://openalex.org/W0123456789"
    assert works[0]["title"] == "Test Work"

# Mock Authors() filter method
@patch("pyalex.Authors.filter")
def test_fetch_authors(mock_filter):
    mock_filter.return_value.get.return_value = [
        {"id": "https://openalex.org/A0123456789", "display_name": "Test Author"}
    ]

    author_ids = ["A0123456789"]
    authors = OpenAlexFetcher.fetch_authors(author_ids)

    assert len(authors) == 1
    assert authors[0]["id"] == "https://openalex.org/A0123456789"
    assert authors[0]["display_name"] == "Test Author"

# Mock Institutions() filter method
@patch("pyalex.Institutions.filter")
def test_fetch_institutions(mock_filter):
    mock_filter.return_value.get.return_value = [
        {"id": "https://openalex.org/I0123456789", "display_name": "Test Institution"}
    ]

    institution_ids = ["I0123456789"]
    institutions = OpenAlexFetcher.fetch_institutions(institution_ids)

    assert len(institutions) == 1
    assert institutions[0]["id"] == "https://openalex.org/I0123456789"
    assert institutions[0]["display_name"] == "Test Institution"

@patch("pyalex.Works.filter")
def test_fetch_works_with_error(mock_filter):
    mock_filter.side_effect = Exception("API Error")

    work_ids = ["W0123456789"]
    works = OpenAlexFetcher.fetch_works(work_ids)

    assert works == []
