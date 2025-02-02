import json
import os
import neo4j.graph
import streamlit as st
from streamlit_agraph import agraph, Node, Edge, Config
import neo4j
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable
from neo4j_graphrag.retrievers import Text2CypherRetriever
from neo4j_graphrag.llm import OpenAILLM
from neo4j_graphrag.embeddings import OpenAIEmbeddings
from config import NEO4J_SCHEMA, EXAMPLES


# Function to load translations dynamically
def load_translations(language_code):
    file_path = f"src/locales/{language_code}.json"
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

# Language Selector
language = st.sidebar.selectbox("Select Language / 言語を選択", ["English", "日本語"])

# Determine language code based on user selection
language_code = "en" if language == "English" else "ja"
translations = load_translations(language_code)

# Streamlit App
st.title("Paper Chain Explorer")
st.markdown(translations["description"])

col1, col2 = st.columns([5, 1], vertical_alignment="bottom")

with col1:
    query_text = st.text_input(
        translations["query_input_label"],
        placeholder=translations["query_input_placeholder"]
    )

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
        st.error(translations["neo4j_connection_error"].format(e))
        raise
    return driver

# @st.cache_resource
def setup_text2cypher(driver: neo4j.Driver) -> Text2CypherRetriever:
    llm = OpenAILLM(model_name="gpt-4o-mini")
    custom_prompt = """Task: Generate a Cypher statement for querying a Neo4j graph database from a user input.

Schema:
{schema}

Vector Search Results:
{vector_search_results}

Examples:
{examples}

Input:
{query_text}

Instructions:
- Ensure the query returns all nodes and relationships involved in the query.
- Do not use any properties or relationships not included in the schema.
- Do not include triple backticks ``` or any additional text except the generated Cypher statement in your response.

Cypher query:
"""
    return Text2CypherRetriever(driver=driver, llm=llm, neo4j_schema=NEO4J_SCHEMA, examples=EXAMPLES, custom_prompt=custom_prompt)

uri = os.getenv("NEO4J_URI")
username = os.getenv("NEO4J_USERNAME")
password = os.getenv("NEO4J_PASSWORD")

if not uri or not username or not password:
    st.error(translations["neo4j_error"])
    st.stop()

# Connect to Neo4j
driver = get_neo4j_driver(
    uri=uri,
    username=username,
    password=password
)
retriever = setup_text2cypher(driver)
embedder = OpenAIEmbeddings(model="text-embedding-3-small")

# Helper function to add a single node
def add_node(node: neo4j.graph.Node, label_key: str, nodes: list, id_history: set) -> None:
    node_id = node["id"]
    if node_id not in id_history:
        if "Work" in node.labels:
            image_url = "https://raw.githubusercontent.com/koyonkym/paper-chain-explorer/refs/heads/main/src/assets/icons/research-paper.png"
        elif "Author" in node.labels:
            image_url = "https://raw.githubusercontent.com/koyonkym/paper-chain-explorer/refs/heads/main/src/assets/icons/graduation-hat.png"
        elif "Institution" in node.labels:
            image_url = "https://raw.githubusercontent.com/koyonkym/paper-chain-explorer/refs/heads/main/src/assets/icons/institute.png"
        else:
            image_url = None
        node_data = {
            "id": node_id,
            "title": node[label_key],
            "shape": "circularImage",
            "image": image_url
        }
        # Only set 'label' if the node is not of type 'Work'
        if "Work" not in node.labels:
            node_data["label"] = node[label_key]
        nodes.append(Node(**node_data))
        id_history.add(node_id)

# Helper function to add a relationship
def add_relationship(relationship: neo4j.graph.Relationship, nodes: list, edges: list, id_history: set) -> None:
    add_node(relationship.start_node, "title" if "Work" in relationship.start_node.labels else "display_name", nodes, id_history)
    add_node(relationship.end_node, "title" if "Work" in relationship.start_node.labels else "display_name", nodes, id_history)
    edges.append(Edge(
        source=relationship.start_node["id"],
        label=relationship.type,
        target=relationship.end_node["id"]
    ))

def prepare_graph_data(records):
    nodes = []
    edges = []
    id_history = set()

    for record in records:
        for item in record:
            if isinstance(item, neo4j.graph.Node):
                add_node(item, "title" if "Work" in item.labels else "display_name", nodes, id_history)
            elif isinstance(item, neo4j.graph.Path):
                for node in item.nodes:
                    add_node(node, "title" if "Work" in node.labels else "display_name", nodes, id_history)
                for relationship in item.relationships:
                    add_relationship(relationship, nodes, edges, id_history)
            elif isinstance(item, neo4j.graph.Relationship):
                add_relationship(item, nodes, edges, id_history)

    config = Config(height=500)
    return nodes, edges, config

def vector_search(driver, embedder, query_text):
    vector = embedder.embed_query(query_text)
    records, summary, keys = driver.execute_query(
        "CALL db.index.vector.queryNodes('work-vector-index', 3, $vector) YIELD node, score RETURN node.title, score",
        {"vector": vector}
    )
    return records

# Initialize session state for graph data
if "graph_data" not in st.session_state:
    st.session_state.graph_data = None

with col2:
    button = st.button(translations["run_query_button"], use_container_width=True)

# Process Query
if button:
    if not query_text.strip():
        st.error(translations["query_error"])
    else:
        with st.spinner(translations["processing_message"]):
            try:
                records = vector_search(driver, embedder, query_text)
                vector_search_results = "\n".join([f"title: {record[0]}, score: {record[1]}" for record in records])
                # Generate Cypher query from natural language
                results = retriever.get_search_results(query_text=query_text, prompt_params={"schema": NEO4J_SCHEMA, "vector_search_results": vector_search_results})

                if results.records:
                    st.success(translations["success_message"])
                    cypher = results.metadata["cypher"]
                    nodes, edges, config = prepare_graph_data(results.records)
                    st.session_state.graph_data = {"cypher": cypher, "nodes": nodes, "edges": edges, "config": config}
                else:
                    st.code(results.metadata["cypher"])
                    st.warning(translations["no_results_message"])
            except Exception as e:
                st.error(translations["error_message"].format(e))

# Render the graph if data is available
if st.session_state.graph_data:
    st.code(st.session_state.graph_data["cypher"], language="cypher")
    agraph(
        nodes=st.session_state.graph_data["nodes"],
        edges=st.session_state.graph_data["edges"],
        config=st.session_state.graph_data["config"]
    )

st.markdown(
"""
---
### Attribution
- [Academic icons created by Slamlabs - Flaticon](https://www.flaticon.com/free-icons/academic)
- [Graduation hat icons created by Freepik - Flaticon](https://www.flaticon.com/free-icons/graduation-hat)
- [Institute icons created by vectorspoint - Flaticon](https://www.flaticon.com/free-icons/institute)
"""
)
