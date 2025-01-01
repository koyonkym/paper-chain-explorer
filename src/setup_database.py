import os
import pyalex
from pyalex import Works, Authors
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable


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

    def close(self):
        self.driver.close()

    def execute_query(self, query, **parameters) -> None:
        try:
            self.driver.execute_query(query, **parameters)
        except ServiceUnavailable as e:
            raise RuntimeError(f"Service unavailable while executing query: {e}")
        except Exception as e:
            raise RuntimeError(f"An error occurred while executing query: {e}")

    def add_to_batch(self, query: str) -> None:
        self.query_buffer.append(query)

    def flush(self):
        if not self.query_buffer:
            return
        else:
            self.execute_query(" ".join(self.query_buffer))
            self.query_buffer.clear()
            self.id_histoty.clear()

    # def add_work(self, work: Works) -> None:
    #     self.execute_query(
    #         "MERGE (n:Work {id: $id, title: $title})",
    #         id=work["id"].replace("https://openalex.org/", ""),
    #         title=work["title"]
    #     )

    def add_work(self, work: Works) -> None:
        id = work["id"].replace("https://openalex.org/", "")
        if id not in self.id_histoty:
            self.add_to_batch(
                "MERGE (" + id + ":Work {id: '" + id + "', title: '" + work["title"] + "'})"
            )
            self.id_histoty.append(id)

    # def add_author(self, author: Authors) -> None:
    #     self.execute_query(
    #         "MERGE (n:Author {id: $id, display_name: $display_name})",
    #         id=author["id"].replace("https://openalex.org/", ""),
    #         display_name=author["display_name"]
    #     )

    def add_author(self, author: Authors) -> None:
        id = author["id"].replace("https://openalex.org/", "")
        if id not in self.id_histoty:
            self.add_to_batch(
                "MERGE (" + id + ":Author {id: '" + id + "', display_name: '" + author["display_name"] + "'})"
            )
            self.id_histoty.append(id)

    # def add_referenced(self, work1: Works, work2: Works) -> None:
    #     """
    #     `work1` referenced `work2`
    #     """
    #     self.execute_query(
    #         "MATCH (n1:Work {id: $id1}), (n2:Work {id: $id2})"
    #         "MERGE (n1)-[r:REFERENCED]->(n2)"
    #         "RETURN r",
    #         id1=work1["id"].replace("https://openalex.org/", ""),
    #         id2=work2["id"].replace("https://openalex.org/", "")
    #     )

    def add_referenced(self, work1: Works, work2: Works) -> None:
        """
        `work1` referenced `work2`
        """
        id1 = work1["id"].replace("https://openalex.org/", "")
        id2 = work2["id"].replace("https://openalex.org/", "")
        self.add_to_batch(
            "MERGE (" + id1 + ")-[" + id1 + id2 + ":REFERENCED]->(" + id2 + ")"
        )

    # def add_authored(self, author: Authors, work: Works) -> None:
    #     self.execute_query(
    #         "MATCH (n1:Author {id: $id1}), (n2:Work {id: $id2})"
    #         "MERGE (n1)-[r:AUTHORED]->(n2)"
    #         "RETURN r",
    #         id1=author["id"].replace("https://openalex.org/", ""),
    #         id2=work["id"].replace("https://openalex.org/", "")
    #     )

    def add_authored(self, author: Authors, work: Works) -> None:
        id1 = author["id"].replace("https://openalex.org/", "")
        id2 = work["id"].replace("https://openalex.org/", "")
        self.add_to_batch(
            "MERGE (" + id1 + ")-[" + id1 + id2 + ":AUTHORED]->(" + id2 + ")"
        )

    # def add_works(self, initial_work: Works, depth: int = 3) -> None:
    #     self.add_work(initial_work)
    #     for authorship in initial_work["authorships"]:
    #         author = Authors()[authorship["author"]["id"]]
    #         self.add_author(author)
    #         self.add_authored(author, initial_work)
    #     if depth > 0:
    #         for referenced_work in initial_work["referenced_works"]:
    #             work = Works()[referenced_work]
    #             self.add_works(work, depth - 1)
    #             self.add_referenced(initial_work, work)

    def add_works(self, initial_work: Works, depth: int = 3) -> None:
        self.add_work(initial_work)
        for authorship in initial_work["authorships"]:
            author = Authors()[authorship["author"]["id"]]
            self.add_author(author)
            self.add_authored(author, initial_work)
        if depth > 0:
            for referenced_work in initial_work["referenced_works"]:
                work = Works()[referenced_work]
                self.add_works(work, depth - 1)
                self.add_referenced(initial_work, work)

    def create_graph_by_seed_work(self, initial_work: Works, depth: int = 3) -> None:
        self.query_buffer.clear()
        self.add_works(initial_work, depth)
        self.flush()


pyalex.config.email = os.getenv("OPENALEX_EMAIL")

neo4j_handler = Neo4jHandler(
    uri=os.getenv("NEO4J_URI"),
    username=os.getenv("NEO4J_USERNAME"),
    password=os.getenv("NEO4J_PASSWORD")
)

neo4j_handler.execute_query(
    "MATCH (n)"
    "DETACH DELETE n"
)

neo4j_handler.execute_query(
    "CREATE TEXT INDEX node_text_index_id IF NOT EXISTS FOR (n:Work) ON (n.id)"
)

dois = [
    "https://doi.org/10.1007/s11548-019-01929-x",
    "https://dx.doi.org/10.3748/wjg.v29.i9.1427",
    "https://doi.org/10.48550/arXiv.1706.03762"
]

for doi in dois:
    work = Works()[doi]
    # neo4j_handler.add_works(work, 0)
    neo4j_handler.create_graph_by_seed_work(work, 1)

neo4j_handler.close()