# PaperChainExplorer

**An interactive graph-based application to explore academic paper connections.**  
PaperChainExplorer helps researchers, students, and academic professionals visualize and analyze the relationships between academic papers, authors, and institutions. With an easy-to-use interface, users can explore citation chains and co-authorships within the research domain.

> **Note:** The concept of "topics" has not yet been integrated into the application. It is planned as a future enhancement.

## 🧙‍♂️ Inspiration
Inspired by the idea of uncovering hidden connections in academic research, this project seeks to help researchers and students rediscover forgotten ideas and foster innovation.

## 🚀 Features
- Visualize relationships between academic papers, authors, and (future) topics with interactive graphs.
- Query paths between papers (e.g., "How is my paper connected to the Transformer paper?").
- Explore citation networks and shared authorships interactively.
- Wondering if your *mediocre* paper connects to a groundbreaking one like *"Attention Is All You Need"*? PaperChainExplorer helps uncover these surprising relationships.
- Simple and intuitive user interface built with **Streamlit**.

## 🛠️ Tech Stack
- **Backend**: Python - Handles application logic, integrates with Neo4j, and fetches data from external sources.
- **Database**: Neo4j - Graph database used to store and query relationships between academic papers, authors.
- **Frontend**: Streamlit - Provides an interactive user interface for visualizing the graph and performing queries.
- **APIs**: OpenAlex API - Fetches data on academic papers, authors, and institutions for use in the application.

## 📂 Project Structure
```
paper-chain-explorer/
├── data/                  # (Unused) Scripts to fetch and preprocess data from OpenAlex API
├── src/                   # Core application code
│   ├── setup_database.py  # Database setup scripts for Neo4j
│   ├── app.py             # Main Streamlit app entry point
│   ├── graph.py           # (Unused) Functions for interacting with Neo4j
│   └── visualize.py       # (Unused) Logic for graph visualization in Streamlit
├── queries/               # (Unused) Predefined Cypher queries for common operations
├── notebooks/             # (Unused) Jupyter notebooks for prototyping and experimentation
├── tests/                 # Unit tests for backend and frontend functionality
├── docs/                  # (Unused) Documentation for users and developers
├── .gitignore             # Git ignore rules
├── requirements.txt       # Python dependencies
└── README.md              # Project overview
```
> **Note:** The following files and directories are currently unused but are included for future development:
> - `data/`
> - `src/graph.py`
> - `src/visualize.py`
> - `queries/`
> - `notebooks/`
> - `docs/`

## 🧩 Deployment
To deploy the app to your own server, follow these steps:

1. Clone the repository:
   ```bash
   git clone https://github.com/koyonkym/paper-chain-explorer.git
   ```
2. Set up the environment:
   ```bash
   cd paper-chain-explorer
   python -m venv venv
   source venv/bin/activate  # For Linux/Mac
   venv\Scripts\activate     # For Windows
   pip install -r requirements.txt
   ```
3. Set up a Neo4j instance (locally or in the cloud) and configure the connection.

4. Set up the following environment variables:
   - `NEO4J_URI` - URI of the Neo4j instance.
   - `NEO4J_USERNAME` - Username for Neo4j authentication.
   - `NEO4J_PASSWORD` - Password for Neo4j authentication.
   - `OPENALEX_EMAIL` - Email address for OpenAlex API usage.
   - `OPENAI_API_KEY` - API key for OpenAI services.

   Example setup in Linux/Mac:
   ```bash
   export NEO4J_URI="bolt://localhost:7687"
   export NEO4J_USERNAME="neo4j"
   export NEO4J_PASSWORD="password"
   export OPENALEX_EMAIL="your-email@example.com"
   export OPENAI_API_KEY="your-openai-api-key"
   ```

5. Create the graph in the Neo4j database by running the following command:
   ```bash
   python src/setup_database.py
   ```
   This step fetches data from the OpenAlex API and populates the Neo4j database with the initial graph.

6. Start the Streamlit application:
   ```bash
   streamlit run src/app.py
   ```

## 🧪 Running Tests
To run the tests, use the following command:
```bash
pytest tests/
```
This will run all the unit tests located in the `tests/` directory.

## 🔍 Example Query
- "How is Paper A connected to Paper B?"
   - This query will visualize citation chains or shared authors between the two papers.

- "Who are the authors of the paper 'Attention Is All You Need'?"
   - This will retrieve and visualize the authorship relationship of the paper.

- "Find all papers related to 'Transformer models'"
   - **Future Work**: This query is not currently supported as the app does not use vector embeddings for semantic similarity. Currently, only citation-based connections are displayed. Enhancing the app to include this feature is planned for a future update.

## 🌐 Reference Web Pages
Here are the key resources used for data and development:
- [J535D165/pyalex: A Python library for OpenAlex (openalex.org)](https://github.com/J535D165/pyalex)
- [Introduction - Cypher Manual](https://neo4j.com/docs/cypher-manual/current/introduction/)
- [API Documentation — Neo4j Python Driver 5.27](https://neo4j.com/docs/api/python-driver/current/api.html)
- [GraphRAG for Python — neo4j-graphrag-python  documentation](https://neo4j.com/docs/neo4j-graphrag-python/current/index.html)
- [Streamlit documentation](https://docs.streamlit.io/)
- [ChrisDelClea/streamlit-agraph: A Streamlit Graph Vis](https://github.com/ChrisDelClea/streamlit-agraph)

## 🌟 Contribution
We welcome contributions to improve PaperChainExplorer! Here are ways you can help:
- **Report bugs**: Open an issue describing the bug or error.
- **Suggest features**: Open an issue with new feature requests.
- **Submit code improvements**: Fork the repository, make your changes, and open a pull request.

## 📜 License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
