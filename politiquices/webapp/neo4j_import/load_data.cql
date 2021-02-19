LOAD CSV FROM 'file:///nodes_page_rank.csv' AS line
CREATE (:Person { name: line[1], id: line[0], pagerank:toFloat(line[2])});

LOAD CSV FROM "file:///all_edges_opposes_urls.csv" AS line
MATCH (p1:Person {id: line[0]})
MATCH (p2:Person {id: line[1]})
CREATE (p1)-[r:ACUSA { data: date(line[2]), url: line[3] }]->(p2);

LOAD CSV FROM "file:///all_edges_supports_urls.csv" AS line
MATCH (p1:Person {id: line[0]})
MATCH (p2:Person {id: line[1]})
CREATE (p1)-[r:APOIA { data: date(line[2]), url: line[3] }]->(p2);
