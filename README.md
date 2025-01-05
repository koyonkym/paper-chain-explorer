# PaperChainExplorer

**An interactive graph-based application to explore academic paper connections.**

## 🚀 Features
- Visualize relationships between academic papers, authors, and topics.
- Query paths between papers (e.g., "How is my paper connected to the Transformer paper?").
- Explore citation networks and shared topics interactively.
- Simple and intuitive interface built with **Streamlit**.

## 🛠️ Tech Stack
- **Backend**: Neo4j (graph database)
- **Frontend**: Streamlit
- **Data Sources**: OpenAlex API
- **Language**: Python (for backend and frontend integration)

## 📂 Project Structure
```
paper-chain-explorer/
├── data/                  # Scripts to fetch and preprocess data
├── src/                   # Core application code
│   ├── setup_database.py  #
│   ├── app.py             # Streamlit app entry point
│   ├── graph.py           # Functions for Neo4j interactions
│   └── visualize.py       # Graph visualization logic
├── queries/               # Graph queries (e.g., Cypher scripts)
├── notebooks/             # Jupyter notebooks for prototyping
├── tests/                 # Test cases
├── docs/                  # Documentation
├── .gitignore             # Git ignore rules
├── requirements.txt       # Python dependencies
└── README.md              # Project overview
```

## 🧩 Usage
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
3. Start the Streamlit application:
   ```bash
   streamlit run src/app.py
   ```

## 🔍 Example Query
- "How is Paper A connected to Paper B?"
  - Visualizes citation chains, shared authors, or common topics.

## 🌐 Reference Web Pages
Here are the key resources used for data and development:
- [J535D165/pyalex: A Python library for OpenAlex (openalex.org)](https://github.com/J535D165/pyalex)
- [Introduction - Cypher Manual](https://neo4j.com/docs/cypher-manual/current/introduction/)
- [API Documentation — Neo4j Python Driver 5.27](https://neo4j.com/docs/api/python-driver/current/api.html)
- [GraphRAG for Python — neo4j-graphrag-python  documentation](https://neo4j.com/docs/neo4j-graphrag-python/current/index.html)
- [Streamlit documentation](https://docs.streamlit.io/)
- [ChrisDelClea/streamlit-agraph: A Streamlit Graph Vis](https://github.com/ChrisDelClea/streamlit-agraph)

## 🌟 Contribution
Contributions are welcome! Feel free to open issues or submit pull requests.

## 📜 License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## 🧙‍♂️ Inspiration
Inspired by the quest to rediscover forgotten ideas and foster innovation in research.
