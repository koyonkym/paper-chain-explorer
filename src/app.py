import os
import neo4j.graph
import streamlit as st
from streamlit_agraph import agraph, Node, Edge, Config
import neo4j
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable
from neo4j_graphrag.retrievers import Text2CypherRetriever
from neo4j_graphrag.llm import OpenAILLM


# Streamlit App
st.title("Paper Chain Explorer")
st.markdown("""
This app visualizes relationships between academic papers, authors, and institutions based on your queries.
- **Natural Language Queries**: Ask questions like **Who wrote "Attention Is All You Need"?**
""")

col1, col2 = st.columns([5, 1], vertical_alignment="bottom")

with col1:
    query_text = st.text_input("Enter your query:", placeholder='E.g., Who wrote "Attention Is All You Need"?')

# Neo4j and Text2Cypher Setup
@st.cache_resource
def get_neo4j_driver(uri: str, username: str, password: str) -> neo4j.Driver:
    try:
        driver = GraphDatabase.driver(uri, auth=(username, password))
        driver.verify_connectivity()
    except ServiceUnavailable:
        uri = uri.replace("neo4j+s", "neo4j+ssc")
        driver = GraphDatabase.driver(uri, auth=(username, password))
        driver.verify_connectivity()
    except Exception as e:
        st.error(f"Failed to connect to Neo4j: {e}")
        raise
    return driver

# @st.cache_resource
def setup_text2cypher(driver: neo4j.Driver) -> Text2CypherRetriever:
    llm = OpenAILLM(model_name="gpt-4o-mini")
    neo4j_schema = """
    Node properties:
    Work {id: STRING, title: STRING}
    Author {id: STRING, display_name: STRING}
    Institution {id: STRING, display_name: STRING}
    Relationship properties:
    REFERENCED {}
    AUTHORED {}
    AFFILIATED_WITH {}
    The relationships:
    (:Work)-[:REFERENCED]->(:Work)
    (:Author)-[:AUTHORED]->(:Work)
    (:Author)-[:AFFILIATED_WITH]->(:Institution)
    """
    examples = [
        "USER INPUT: 'Who wrote \"Attention Is All You Need\"?' QUERY: MATCH (a:Author)-[r:AUTHORED]->(w:Work {title: 'Attention Is All You Need'}) RETURN a, r, w",
        "USER INPUT: 'How is Koyo's \"Liver segmentation\" paper connected to \"Attention Is All You Need\" paper?' QUERY: MATCH p = SHORTEST 1 (a:Author)-[:AUTHORED]->(b:Work)-[*]-(c:Work) WHERE a.display_name CONTAINS 'Koyo' AND b.title CONTAINS 'Liver segmentation' AND c.title = 'Attention Is All You Need' RETURN p"
    ]
    return Text2CypherRetriever(driver=driver, llm=llm, neo4j_schema=neo4j_schema, examples=examples)

# with st.sidebar:
#     st.subheader("Neo4j Configuration")
#     uri = st.text_input("Neo4j URI", os.getenv("NEO4J_URI", ""))
#     username = st.text_input("Neo4j Username", os.getenv("NEO4J_USERNAME", ""))
#     password = st.text_input("Neo4j Password", os.getenv("NEO4J_PASSWORD", ""), type="password")

# Validate environment variables
uri = os.getenv("NEO4J_URI")
username = os.getenv("NEO4J_USERNAME")
password = os.getenv("NEO4J_PASSWORD")

if not uri or not username or not password:
    st.error("Neo4j credentials are not set. Please check your environment variables.")
    st.stop()

# Connect to Neo4j
driver = get_neo4j_driver(
    uri=uri,
    username=username,
    password=password
)
retriever = setup_text2cypher(driver)

# Function to visualize graph
def prepare_graph_data(records):
    nodes = []
    edges = []
    id_history = []

    def add_node(node, label_key: str) -> None:
        node_id = node["id"]
        if node_id not in id_history:
            node_data = {
                "id": node_id,
                "title": node[label_key]
            }
            # Only set 'label' if the node is not of type 'Work'
            if "Work" not in node.labels:
                node_data["label"] = node[label_key]
            nodes.append(Node(**node_data))
            id_history.append(node_id)

    for record in records:
        for item in record:
            if isinstance(item, neo4j.graph.Node):
                add_node(item, "title" if "Work" in item.labels else "display_name")
            elif isinstance(item, neo4j.graph.Path):
                for node in item.nodes:
                    add_node(node, "title" if "Work" in node.labels else "display_name")
                for relationship in item.relationships:
                    add_node(relationship.start_node, "title" if "Work" in relationship.start_node.labels else "display_name")
                    add_node(relationship.end_node, "title" if "Work" in relationship.start_node.labels else "display_name")
                    edges.append(Edge(
                        source=relationship.start_node["id"],
                        label=relationship.type,
                        target=relationship.end_node["id"]
                    ))
            else:
                add_node(item.start_node, "title" if "Work" in item.start_node.labels else "display_name")
                add_node(item._end_node, "title" if "Work" in item._end_node.labels else "display_name")
                edges.append(Edge(
                    source=item.start_node["id"],
                    label=item.type,
                    target=item._end_node["id"]
                ))

    config = Config(height=500)
    return nodes, edges, config

# Initialize session state for graph data
if "graph_data" not in st.session_state:
    st.session_state.graph_data = None

with col2:
    button = st.button("Run Query", use_container_width=True)

# Process Query
if button:
    if not query_text.strip():
        st.error("Please enter a valid query.")
    else:
        with st.spinner("Processing your query..."):
            try:
                # Generate Cypher query from natural language
                results = retriever.get_search_results(query_text=query_text)

                if results.records:
                    st.success("Query executed successfully!")
                    cypher = results.metadata["cypher"]
                    nodes, edges, config = prepare_graph_data(results.records)
                    st.session_state.graph_data = {"cypher": cypher, "nodes": nodes, "edges": edges, "config": config}
                else:
                    st.warning("No results found for your query.")
            except Exception as e:
                st.error(f"An error occurred: {e}")

# Render the graph if data is available
if st.session_state.graph_data:
    st.code(st.session_state.graph_data["cypher"], language="cypher")
    agraph(
        nodes=st.session_state.graph_data["nodes"],
        edges=st.session_state.graph_data["edges"],
        config=st.session_state.graph_data["config"]
    )