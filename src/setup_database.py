import os
import time
import pyalex
from pyalex import Works, Authors, Institutions
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable
from neo4j_graphrag.indexes import create_vector_index
from neo4j_graphrag.embeddings import OpenAIEmbeddings


class Neo4jHandler:
    def __init__(self, uri: str, username: str, password: str):
        try:
            self.driver = GraphDatabase.driver(uri, auth=(username, password))
            self.driver.verify_connectivity()
        except ServiceUnavailable:
            uri = uri.replace("neo4j+s", "neo4j+ssc")
            self.driver = GraphDatabase.driver(uri, auth=(username, password))
            self.driver.verify_connectivity()
        except Exception as e:
            raise RuntimeError(f"Failed to connect to Neo4j: {e}")
        self.query_buffer = []
        self.id_histoty = []
        self.embedder = OpenAIEmbeddings(model="text-embedding-3-small")

    def close(self):
        self.driver.close()

    def execute_query(self, query, **parameters) -> None:
        try:
            self.driver.execute_query(query, **parameters)
        except ServiceUnavailable as e:
            raise RuntimeError(f"Service unavailable while executing query: {e}")
        except Exception as e:
            raise RuntimeError(f"An error occurred while executing query: {e}")

    def create_vector_index(self, index_name: str, label: str, embedding_property: str, dimensions: int, similarity_fn: str = "euclidean"):
        try:
            create_vector_index(
                self.driver,
                index_name,
                label=label,
                embedding_property=embedding_property,
                dimensions=dimensions,
                similarity_fn=similarity_fn,
            )
        except Exception as e:
            raise RuntimeError(f"Failed to create vector index: {e}")

    def add_to_batch(self, query: str, parameters: dict = None) -> None:
        self.query_buffer.append((query, parameters or {}))

    def flush(self):
        if not self.query_buffer:
            return
        try:
            with self.driver.session() as session:
                session.execute_write(
                    lambda tx: [tx.run(query, **params) for query, params in self.query_buffer]
                )
            self.query_buffer.clear()
            self.id_histoty.clear()
        except Exception as e:
            raise RuntimeError(f"An error occurred while flushing queries: {e}")

    def clean_openalex_id(self, full_id: str) -> str:
        return full_id.replace("https://openalex.org/", "")

    def add_work(self, work: Works) -> None:
        id = self.clean_openalex_id(work["id"])
        if id not in self.id_histoty:
            vector = self.embedder.embed_query(text=work["title"])
            self.add_to_batch(
                # "MERGE (n:Work {id: $id, title: $title, vectorProperty: $vectorProperty})",
                "MERGE (n:Work {id: $id}) ON CREATE SET n.title = $title, n.vectorProperty = $vectorProperty ON MATCH SET n.title = $title, n.vectorProperty = $vectorProperty",
                {"id": id, "title": work["title"], "vectorProperty": vector}
            )
            self.id_histoty.append(id)

    def add_author(self, author: Authors) -> None:
        id = self.clean_openalex_id(author["id"])
        if id not in self.id_histoty:
            self.add_to_batch(
                "MERGE (n:Author {id: $id}) ON CREATE SET n.display_name = $display_name ON MATCH SET n.display_name = $display_name",
                {"id": id, "display_name": author["display_name"]}
            )
            self.id_histoty.append(id)

    def add_institution(self, institution: Institutions) -> None:
        id = self.clean_openalex_id(institution["id"])
        if id not in self.id_histoty:
            self.add_to_batch(
                "MERGE (n:Institution {id: $id}) ON CREATE SET n.display_name = $display_name ON MATCH SET n.display_name = $display_name",
                {"id": id, "display_name": institution["display_name"]}
            )
            self.id_histoty.append(id)

    def add_referenced(self, work1: Works, work2: Works) -> None:
        """
        `work1` referenced `work2`
        """
        id1 = self.clean_openalex_id(work1["id"])
        id2 = self.clean_openalex_id(work2["id"])
        self.add_to_batch(
            "MATCH (n1:Work {id: $id1}), (n2:Work {id: $id2})"
            "MERGE (n1)-[r:REFERENCED]->(n2)"
            "RETURN r",
            {"id1": id1, "id2": id2}
        )

    def add_authored(self, author: Authors, work: Works) -> None:
        id1 = self.clean_openalex_id(author["id"])
        id2 = self.clean_openalex_id(work["id"])
        self.add_to_batch(
            "MATCH (n1:Author {id: $id1}), (n2:Work {id: $id2})"
            "MERGE (n1)-[r:AUTHORED]->(n2)"
            "RETURN r",
            {"id1": id1, "id2": id2}
        )

    def add_affiliated_with(self, author: Authors, institution: Institutions) -> None:
        id1 = self.clean_openalex_id(author["id"])
        id2 = self.clean_openalex_id(institution["id"])
        self.add_to_batch(
            "MATCH (n1:Author {id: $id1}), (n2:Institution {id: $id2})"
            "MERGE (n1)-[r:AFFILIATED_WITH]->(n2)"
            "RETURN r",
            {"id1": id1, "id2": id2}
        )

    def traverse_and_add_works(self, initial_work: Works, depth: int = 1) -> None:
        self.add_work(initial_work)
        author_ids = [self.clean_openalex_id(authorship["author"]["id"]) for authorship in initial_work["authorships"]]
        authors = OpenAlexFetcher.fetch_authors(author_ids)
        for author in authors:
            self.add_author(author)
            self.add_authored(author, initial_work)
            institution_ids = [self.clean_openalex_id(affiliation["institution"]["id"]) for affiliation in author["affiliations"]]
            institutions = OpenAlexFetcher.fetch_institutions(institution_ids)
            for institution in institutions:
                self.add_institution(institution)
                self.add_affiliated_with(author, institution)
        if depth > 0:
            referenced_work_ids = [self.clean_openalex_id(referenced_work) for referenced_work in initial_work["referenced_works"]]
            works = OpenAlexFetcher.fetch_works(referenced_work_ids)
            for work in works:
                self.traverse_and_add_works(work, depth - 1)
                self.add_referenced(initial_work, work)

    def build_graph_from_work(self, initial_work: Works, depth: int = 1) -> None:
        self.traverse_and_add_works(initial_work, depth)
        self.flush()


class OpenAlexFetcher:
    @staticmethod
    def chunk_list(lst: list, chunk_size: int):
        for i in range(0, len(lst), chunk_size):
            yield lst[i:i + chunk_size]

    @staticmethod
    def fetch_works(work_ids: list[str]):
        works = []
        for chunk in OpenAlexFetcher.chunk_list(work_ids, 100):
            try:
                works += Works().filter(openalex_id="|".join(chunk)).get(per_page=100)
                time.sleep(0.1)
            except Exception as e:
                print(f"Error fetching works: {e}")
        return works

    @staticmethod
    def fetch_authors(author_ids: list[str]):
        authors = []
        for chunk in OpenAlexFetcher.chunk_list(author_ids, 100):
            try:
                authors += Authors().filter(openalex_id="|".join(chunk)).get(per_page=100)
                time.sleep(0.1)
            except Exception as e:
                print(f"Error fetching authors: {e}")
        return authors

    @staticmethod
    def fetch_institutions(institution_ids: list[str]):
        institutions = []
        for chunk in OpenAlexFetcher.chunk_list(institution_ids, 100):
            try:
                institutions += Institutions().filter(openalex_id="|".join(chunk)).get(per_page=100)
                time.sleep(0.1)
            except Exception as e:
                print(f"Error fetching institutions: {e}")
        return institutions


if __name__ == "__main__":
    pyalex.config.email = os.getenv("OPENALEX_EMAIL")

    neo4j_handler = Neo4jHandler(
        uri=os.getenv("NEO4J_URI"),
        username=os.getenv("NEO4J_USERNAME"),
        password=os.getenv("NEO4J_PASSWORD")
    )

    # Create vector index
    neo4j_handler.create_vector_index(
        index_name="work-vector-index",
        label="Work",
        embedding_property="vectorProperty",
        dimensions=1536,
        similarity_fn="euclidean",
    )

    neo4j_handler.execute_query(
        "CREATE TEXT INDEX node_text_index_id IF NOT EXISTS FOR (n:Work) ON (n.id)"
    )

    neo4j_handler.execute_query(
        "CREATE CONSTRAINT constraint_unique_work_id IF NOT EXISTS FOR (n:Work) REQUIRE n.id IS UNIQUE"
    )

    neo4j_handler.execute_query(
        "CREATE CONSTRAINT constraint_unique_author_id IF NOT EXISTS FOR (n:Author) REQUIRE n.id IS UNIQUE"
    )

    neo4j_handler.execute_query(
        "CREATE CONSTRAINT constraint_unique_institution_id IF NOT EXISTS FOR (n:Institution) REQUIRE n.id IS UNIQUE"
    )

    dois = [
        "https://doi.org/10.1007/s11548-019-01929-x",
        "https://dx.doi.org/10.3748/wjg.v29.i9.1427",
        "https://doi.org/10.48550/arXiv.1706.03762",
        "https://doi.org/10.48550/arXiv.1810.04805",
        "https://doi.org/10.48550/arXiv.2005.14165",
    ]

    for doi in dois:
        work = Works()[doi]
        neo4j_handler.build_graph_from_work(work, 1)

    neo4j_handler.close()