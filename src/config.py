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
    "USER INPUT: Who wrote \"Attention Is All You Need\"? QUERY: MATCH (a:Author)-[r:AUTHORED]->(w:Work) WHERE lower(w.title) CONTAINS lower('Attention Is All You Need') RETURN a, r, w",
    "USER INPUT: How is Koyo's \"Liver segmentation\" paper connected to \"Attention Is All You Need\" paper? QUERY: MATCH p = SHORTEST 1 (a:Author)-[r1:AUTHORED]->(w1:Work)-[*]-(w2:Work) WHERE lower(a.display_name) CONTAINS lower('Koyo') AND lower(w1.title) CONTAINS lower('liver segmentation') AND lower(w2.title) CONTAINS lower('Attention Is All You Need') RETURN p",
    "USER INPUT: Who are the authors of the paper \"Attention Is All You Need\"? QUERY: MATCH (a:Author)-[r:AUTHORED]->(w:Work) WHERE lower(w.title) CONTAINS lower('Attention Is All You Need') RETURN a, r, w",
    "USER INPUT: Find all papers related to \"Transformer models\" VECTOR SEARCH RESULTS: title: BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding score: 0.4438895583152771 title: Universal Language Model Fine-tuning for Text Classification score: 0.4373946487903595 title: Deep learning score: 0.43673446774482727 QUERY: MATCH (w:Work) WHERE w.title = 'BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding' OR w.title = 'Universal Language Model Fine-tuning for Text Classification' OR w.title = 'Deep learning' RETURN w",
    "USER INPUT: 「Attention Is All You Need」を書いたのは誰ですか？ QUERY: MATCH (a:Author)-[r:AUTHORED]->(w:Work) WHERE lower(w.title) CONTAINS lower('Attention Is All You Need') RETURN a, r, w",
    "USER INPUT: Koyo の「Liver segmentation」の論文は、「Attention Is All You Need」の論文とどのようにつながっていますか？ QUERY: MATCH p = SHORTEST 1 (a:Author)-[r1:AUTHORED]->(w1:Work)-[*]-(w2:Work) WHERE lower(a.display_name) CONTAINS lower('Koyo') AND lower(w1.title) CONTAINS lower('liver segmentation') AND lower(w2.title) CONTAINS lower('Attention Is All You Need') RETURN p",
    "USER INPUT: 「Attention Is All You Need」の著者は誰ですか？ QUERY: MATCH (a:Author)-[r:AUTHORED]->(w:Work) WHERE lower(w.title) CONTAINS lower('Attention Is All You Need') RETURN a, r, w",
    "USER INPUT: 「Transformer」に関連するすべての論文を見つけてください VECTOR SEARCH RESULTS: title: BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding score: 0.3972547650337219 title: Universal Language Model Fine-tuning for Text Classification score: 0.3867345452308655 title: GLUE: A Multi-Task Benchmark and Analysis Platform for Natural Language Understanding score: 0.3862400949001312 QUERY: MATCH (w:Work) WHERE w.title = 'BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding' OR w.title = 'Universal Language Model Fine-tuning for Text Classification' OR w.title = 'GLUE: A Multi-Task Benchmark and Analysis Platform for Natural Language Understanding' RETURN w",
]
