NEO4J_SCHEMA = """
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

EXAMPLES = [
    "USER INPUT: 'Who wrote \"Attention Is All You Need\"?' QUERY: MATCH (a:Author)-[r:AUTHORED]->(w:Work {title: 'Attention Is All You Need'}) RETURN a, r, w",
    "USER INPUT: 'How is Koyo's \"Liver segmentation\" paper connected to \"Attention Is All You Need\" paper?' QUERY: MATCH p = SHORTEST 1 (a:Author)-[:AUTHORED]->(b:Work)-[*]-(c:Work) WHERE a.display_name CONTAINS 'Koyo' AND b.title CONTAINS 'Liver segmentation' AND c.title = 'Attention Is All You Need' RETURN p",
    "USER INPUT: '「Attention Is All You Need」を書いたのは誰ですか？' QUERY: MATCH (a:Author)-[r:AUTHORED]->(w:Work {title: 'Attention Is All You Need'}) RETURN a, r, w",
    "USER INPUT: 'Koyo の「Liver segmentation」の論文は、「Attention Is All You Need」の論文とどのようにつながっていますか？' QUERY: MATCH p = SHORTEST 1 (a:Author)-[:AUTHORED]->(b:Work)-[*]-(c:Work) WHERE a.display_name CONTAINS 'Koyo' AND b.title CONTAINS 'Liver segmentation' AND c.title = 'Attention Is All You Need' RETURN p",
]
