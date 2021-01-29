
# quem acusa uma pessoa o Sócrates
MATCH p=(:Person)-[:ACUSA]->(p1:Person { id: 'Q182367' }) 
RETURN p 
LIMIT 10


MATCH p=(:Person)-[:ACUSA]->(:Person) RETURN p LIMIT 10


# rede de uma pessoa
MATCH p1=(:Person)-[r1:ACUSA|APOIA]->(p:Person { id: 'Q3186409' })
MATCH (p:Person { id: 'Q3186409' })-[r2:ACUSA|APOIA]->(p2:Person)
RETURN p1,p2,r1,r2 LIMIT 25