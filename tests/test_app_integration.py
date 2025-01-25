from src.app import add_node, prepare_graph_data, get_neo4j_driver, vector_search
from neo4j.graph import Node as Neo4jNode, Graph
from unittest.mock import Mock, MagicMock, patch


def test_add_node():
    mock_graph = Mock(spec=Graph)

    neo4j_node = Neo4jNode(
        graph=mock_graph,
        element_id="1",
        id_=1,
        n_labels=["Work"],
        properties={"id": "1", "title": "Test Paper"}
    )

    nodes = []
    id_history = set()

    add_node(neo4j_node, "title", nodes, id_history)

    assert len(nodes) == 1
    assert nodes[0].id == "1"
    assert nodes[0].title == "Test Paper"
    assert "1" in id_history


# def test_add_relationship():


def test_prepare_graph_data():
    mock_graph = Mock(spec=Graph)

    records = [[
        Neo4jNode(
            graph=mock_graph,
            element_id="1",
            id_=1,
            n_labels=["Author"],
            properties={"id": "1", "display_name": "Author 1"}
        ),
        Neo4jNode(
            graph=mock_graph,
            element_id="2",
            id_=1,
            n_labels=["Work"],
            properties={"id": "2", "title": "Test Paper"}
        )
    ]]
    nodes, edges, config = prepare_graph_data(records)

    assert len(nodes) == 2
    assert len(edges) == 0
    assert nodes[0].id == "1"
    assert config.height == "500px"


def test_neo4j_connection():
    with patch("neo4j.GraphDatabase.driver") as mock_driver_constructor:
        mock_driver = MagicMock()
        mock_driver.verify_connectivity.return_value = True
        mock_driver_constructor.return_value = mock_driver

        driver = get_neo4j_driver("bolt://localhost:7687", "user", "password")
        mock_driver.verify_connectivity.assert_called_once()
        assert driver is mock_driver


def test_vector_search():
    mock_driver = MagicMock()
    mock_embedder = MagicMock()
    mock_embedder.embed_query.return_value = [0.1, 0.2, 0.3]
    mock_driver.execute_query.return_value = ([("Test Paper", 0.99)], None, None)

    query_text = "Find Test Paper"
    records = vector_search(mock_driver, mock_embedder, query_text)

    assert len(records) == 1
    assert records[0][0] == "Test Paper"
    assert records[0][1] == 0.99


def test_query_workflow():
    mock_graph = Mock(spec=Graph)
    mock_driver = MagicMock()
    mock_embedder = MagicMock()
    mock_retriever = MagicMock()

    mock_embedder.embed_query.return_value = [0.1, 0.2, 0.3]
    mock_driver.execute_query.return_value = ([("Test Paper", 0.99)], None, None)

    mock_retriever.get_search_results.return_value = MagicMock(
        records=[[
            Neo4jNode(
                graph=mock_graph,
                element_id="1",
                id_=1,
                n_labels=["Work"],
                properties={"id": "1", "title": "Test Paper"}
            )
        ]],
        metadata={"cypher": "MATCH (w:Work {title: 'Test Paper'}) RETURN w"}
    )

    query_text = "Find Test Paper"
    results = mock_retriever.get_search_results(query_text=query_text)

    nodes, edges, config = prepare_graph_data(results.records)

    assert len(nodes) == 1
    assert len(edges) == 0
    assert nodes[0].title == "Test Paper"
    assert results.metadata["cypher"] == "MATCH (w:Work {title: 'Test Paper'}) RETURN w"
