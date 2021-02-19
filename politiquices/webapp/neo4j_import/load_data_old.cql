LOAD CSV FROM 'file:///nodes_page_rank.csv' AS line
CREATE (:Person { name: line[1], id: line[0], pagerank:toFloat(line[2])});


# LOAD CSV FROM "file:///edges_opposes.csv" AS line
# MATCH (p1:Person {id: line[0]})
# MATCH (p2:Person {id: line[1]})
# CREATE (p1)-[r:ACUSA { freq: toInteger(line[2]) }]->(p2);

# LOAD CSV FROM "file:///edges_supports.csv" AS line
# MATCH (p1:Person {id: line[0]})
# MATCH (p2:Person {id: line[1]})
# CREATE (p1)-[r:APOIA { freq: toInteger(line[2]) }]->(p2);

LOAD CSV FROM "file:///all_edges.csv" AS line
MATCH (p1:Person {id: line[0]})
MATCH (p2:Person {id: line[1]})
CREATE (p1)-[r:line[4] { data: line[2], url: line[3] }]->(p2);