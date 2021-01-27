
# quem acusa uma pessoa o Sócrates
MATCH p=(:Person)-[:ACUSA]->(p1:Person { id: 'Q182367' }) 
RETURN p 
LIMIT 10


MATCH p=(:Person)-[:ACUSA]->(:Person) RETURN p LIMIT 10