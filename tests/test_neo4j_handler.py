import pytest
from unittest.mock import MagicMock, patch
from neo4j.exceptions import ServiceUnavailable
from src.setup_database import Neo4jHandler


@pytest.fixture
def mock_neo4j_handler():
    """
    Fixture for mocking the Neo4jHandler instance.
    """
    with patch("neo4j.GraphDatabase.driver") as mock_driver:
        mock_driver_instance = MagicMock()
        mock_driver.return_value = mock_driver_instance

        # Mock verify_connectivity to prevent connection issues during tests
        mock_driver_instance.verify_connectivity.return_value = None

        handler = Neo4jHandler(uri="bolt://localhost:7687", username="user", password="password")
        yield handler
        handler.close()


def test_initialization_success(mock_neo4j_handler):
    """
    Test that the Neo4jHandler is successfully initialized and the driver is not None.
    """
    assert mock_neo4j_handler.driver is not None


def test_initialization_service_unavailable():
    """
    Test Neo4jHandler fallback logic when ServiceUnavailable is raised during initialization.
    """
    with patch("neo4j.GraphDatabase.driver") as mock_driver:
        mock_driver.side_effect = [ServiceUnavailable("Service unavailable"), MagicMock()]
        handler = Neo4jHandler(uri="neo4j+s://localhost:7687", username="user", password="password")
        assert handler.driver is not None


def test_execute_query(mock_neo4j_handler):
    """
    Test that the execute_query method calls the driver's execute_query method.
    """
    query = "MATCH (n) RETURN n"
    parameters = {}

    mock_neo4j_handler.execute_query(query, **parameters)
    mock_neo4j_handler.driver.execute_query.assert_called_once_with(query, **parameters)


def test_add_to_batch(mock_neo4j_handler):
    """
    Test that add_to_batch correctly adds a query and parameters to the buffer.
    """
    query = "CREATE (n:Test {id: $id})"
    parameters = {"id": "W0123456789"}

    mock_neo4j_handler.add_to_batch(query, parameters)
    assert len(mock_neo4j_handler.query_buffer) == 1
    assert mock_neo4j_handler.query_buffer[0] == (query, parameters)


def test_flush_success(mock_neo4j_handler):
    """
    Test that flush clears the query buffer after executing all queries in a session.
    """
    query = "CREATE (n:Test {id: $id})"
    parameters = {"id": "W0123456789"}
    mock_neo4j_handler.add_to_batch(query, parameters)

    # Mock the session and transaction behavior
    with patch.object(mock_neo4j_handler.driver, "session") as mock_session:
        mock_transaction = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_transaction

        mock_neo4j_handler.flush()
        mock_transaction.execute_write.assert_called_once()
        assert len(mock_neo4j_handler.query_buffer) == 0


def test_add_work(mock_neo4j_handler):
    """
    Test that add_work adds a valid query for creating a Work node.
    """
    mock_work = {
        "id": "https://openalex.org/W0123456789",
        "title": "Test Work"
    }

    # Mock the embed_query method in OpenAIEmbeddings
    mock_embedder = MagicMock()
    mock_embedder.embed_query.return_value = [0.1, 0.2, 0.3]
    mock_neo4j_handler.embedder = mock_embedder

    mock_neo4j_handler.add_work(mock_work)
    assert len(mock_neo4j_handler.query_buffer) == 1
    query, params = mock_neo4j_handler.query_buffer[0]
    assert query == "MERGE (n:Work {id: $id}) ON CREATE SET n.title = $title, n.vectorProperty = $vectorProperty ON MATCH SET n.title = $title, n.vectorProperty = $vectorProperty"
    assert params == {
        "id": "W0123456789",
        "title": "Test Work",
        "vectorProperty": [0.1, 0.2, 0.3]
    }


def test_add_author(mock_neo4j_handler):
    """
    Test that add_author adds a valid query for creating an Author node.
    """
    mock_author = {
        "id": "https://openalex.org/A0123456789",
        "display_name": "Test Author"
    }

    mock_neo4j_handler.add_author(mock_author)
    assert len(mock_neo4j_handler.query_buffer) == 1
    query, params = mock_neo4j_handler.query_buffer[0]
    assert query == "MERGE (n:Author {id: $id, display_name: $display_name})"
    assert params == {"id": "A0123456789", "display_name": "Test Author"}


def test_add_institution(mock_neo4j_handler):
    """
    Test that add_institution adds a valid query for creating an Institution node.
    """
    mock_institution = {
        "id": "https://openalex.org/I0123456789",
        "display_name": "Test Institution"
    }

    mock_neo4j_handler.add_institution(mock_institution)
    assert len(mock_neo4j_handler.query_buffer) == 1
    query, params = mock_neo4j_handler.query_buffer[0]
    assert query == "MERGE (n:Institution {id: $id, display_name: $display_name})"
    assert params == {"id": "I0123456789", "display_name": "Test Institution"}


def test_add_referenced(mock_neo4j_handler):
    """
    Test that add_referenced adds a valid query for creating a REFERENCED relationship.
    """
    mock_work1 = {
        "id": "https://openalex.org/W0123456789",
        "title": "Test Work 1"
    }
    mock_work2 = {
        "id": "https://openalex.org/W9876543210",
        "title": "Test Work 2"
    }

    mock_neo4j_handler.add_referenced(mock_work1, mock_work2)
    assert len(mock_neo4j_handler.query_buffer) == 1
    query, params = mock_neo4j_handler.query_buffer[0]
    assert query == "MATCH (n1:Work {id: $id1}), (n2:Work {id: $id2})MERGE (n1)-[r:REFERENCED]->(n2)RETURN r"
    assert params == {"id1": "W0123456789", "id2": "W9876543210"}


def test_add_authored(mock_neo4j_handler):
    """
    Test that add_authored adds a valid query for creating an AUTHORED relationship.
    """
    mock_author = {
        "id": "https://openalex.org/A0123456789",
        "display_name": "Test Author"
    }
    mock_work = {
        "id": "https://openalex.org/W0123456789",
        "title": "Test Work"
    }

    mock_neo4j_handler.add_authored(mock_author, mock_work)
    assert len(mock_neo4j_handler.query_buffer) == 1
    query, params = mock_neo4j_handler.query_buffer[0]
    assert query == "MATCH (n1:Author {id: $id1}), (n2:Work {id: $id2})MERGE (n1)-[r:AUTHORED]->(n2)RETURN r"
    assert params == {"id1": "A0123456789", "id2": "W0123456789"}


def test_add_affiliated_with(mock_neo4j_handler):
    """
    Test that add_affiliated_with adds a valid query for creating an AFFILIATED_WITH relationship.
    """
    mock_author = {
        "id": "https://openalex.org/A0123456789",
        "display_name": "Test Author"
    }
    mock_institution = {
        "id": "https://openalex.org/I0123456789",
        "display_name": "Test Institution"
    }

    mock_neo4j_handler.add_affiliated_with(mock_author, mock_institution)
    assert len(mock_neo4j_handler.query_buffer) == 1
    query, params = mock_neo4j_handler.query_buffer[0]
    assert query == "MATCH (n1:Author {id: $id1}), (n2:Institution {id: $id2})MERGE (n1)-[r:AFFILIATED_WITH]->(n2)RETURN r"
    assert params == {"id1": "A0123456789", "id2": "I0123456789"}