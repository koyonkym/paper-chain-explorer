import os
import time
import pyalex
from pyalex import Works, Authors, Institutions
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

    def add_work(self, work: Works) -> None:
        id = work["id"].replace("https://openalex.org/", "")
        if id not in self.id_histoty:
            self.add_to_batch(
                "MERGE (n:Work {id: $id, title: $title})",
                {"id": id, "title": work["title"]}
            )
            self.id_histoty.append(id)

    def add_author(self, author: Authors) -> None:
        id = author["id"].replace("https://openalex.org/", "")
        if id not in self.id_histoty:
            self.add_to_batch(
                "MERGE (n:Author {id: $id, display_name: $display_name})",
                {"id": id, "display_name": author["display_name"]}
            )
            self.id_histoty.append(id)
    
    def add_institution(self, institution: Institutions) -> None:
        id = institution["id"].replace("https://openalex.org/", "")
        if id not in self.id_histoty:
            self.add_to_batch(
                "MERGE (n:Institution {id: $id, display_name: $display_name})",
                {"id": id, "display_name": institution["display_name"]}
            )
            self.id_histoty.append(id)

    def add_referenced(self, work1: Works, work2: Works) -> None:
        """
        `work1` referenced `work2`
        """
        id1 = work1["id"].replace("https://openalex.org/", "")
        id2 = work2["id"].replace("https://openalex.org/", "")
        self.add_to_batch(
            "MATCH (n1:Work {id: $id1}), (n2:Work {id: $id2})"
            "MERGE (n1)-[r:REFERENCED]->(n2)"
            "RETURN r",
            {"id1": id1, "id2": id2}
        )

    def add_authored(self, author: Authors, work: Works) -> None:
        id1 = author["id"].replace("https://openalex.org/", "")
        id2 = work["id"].replace("https://openalex.org/", "")
        self.add_to_batch(
            "MATCH (n1:Author {id: $id1}), (n2:Work {id: $id2})"
            "MERGE (n1)-[r:AUTHORED]->(n2)"
            "RETURN r",
            {"id1": id1, "id2": id2}
        )

    def add_affiliated_with(self, author: Authors, institution: Institutions) -> None:
        id1 = author["id"].replace("https://openalex.org/", "")
        id2 = institution["id"].replace("https://openalex.org/", "")
        self.add_to_batch(
            "MATCH (n1:Author {id: $id1}), (n2:Institution {id: $id2})"
            "MERGE (n1)-[r:AFFILIATED_WITH]->(n2)"
            "RETURN r",
            {"id1": id1, "id2": id2}
        )

    def traverse_and_add_works(self, initial_work: Works, depth: int = 3) -> None:
        self.add_work(initial_work)
        author_ids = [authorship["author"]["id"].replace("https://openalex.org/", "") for authorship in initial_work["authorships"]]
        authors = []
        if len(author_ids) != 0:
            for i in range(len(author_ids) // 100 + 1):
                try:
                    authors = authors + Authors().filter(openalex_id="|".join(author_ids[i*100:(i+1)*100])).get(per_page=100)
                    time.sleep(0.1)
                except Exception as e:
                    print(f"Error fetching authors: {e}")
        for author in authors:
            self.add_author(author)
            self.add_authored(author, initial_work)
            institution_ids = [affiliation["institution"]["id"].replace("https://openalex.org/", "") for affiliation in author["affiliations"]]
            institutions = []
            if len(institution_ids) != 0:
                for i in range(len(institution_ids) // 100 + 1):
                    try:
                        institutions = institutions + Institutions().filter(openalex_id="|".join(institution_ids[i*100:(i+1)*100])).get(per_page=100)
                        time.sleep(0.1)
                    except Exception as e:
                        print(f"Error fetching institutions: {e}")
            for institution in institutions:
                self.add_institution(institution)
                self.add_affiliated_with(author, institution)
        if depth > 0:
            referenced_work_ids = [referenced_work.replace("https://openalex.org/", "") for referenced_work in initial_work["referenced_works"]]
            works = []
            if len(referenced_work_ids) != 0:
                for i in range(len(referenced_work_ids) // 100 + 1):
                    try:
                        works = works + Works().filter(openalex_id="|".join(referenced_work_ids[i*100:(i+1)*100])).get(per_page=100)
                        time.sleep(0.1)
                    except Exception as e:
                        print(f"Error fetching works: {e}")
            for work in works:
                self.traverse_and_add_works(work, depth - 1)
                self.add_referenced(initial_work, work)

    def build_graph_from_work(self, initial_work: Works, depth: int = 3) -> None:
        self.traverse_and_add_works(initial_work, depth)
        self.flush()


if __name__ == "__main__":
    pyalex.config.email = os.getenv("OPENALEX_EMAIL")

    neo4j_handler = Neo4jHandler(
        uri=os.getenv("NEO4J_URI"),
        username=os.getenv("NEO4J_USERNAME"),
        password=os.getenv("NEO4J_PASSWORD")
    )

    # neo4j_handler.execute_query(
    #     "MATCH (n)"
    #     "DETACH DELETE n"
    # )

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
        neo4j_handler.build_graph_from_work(work, 1)

    neo4j_handler.close()