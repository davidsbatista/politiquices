
# quem acusa uma pessoa o Sócrates
MATCH p=(:Person)-[:ACUSA]->(p1:Person { id: 'Q182367' }) 
RETURN p 
LIMIT 1


MATCH p=(:Person)-[:ACUSA]->(:Person) RETURN p LIMIT 10


# rede de uma pessoa
MATCH p1=(:Person)-[r1:ACUSA|APOIA]->(p:Person { id: 'Q3186409' })
MATCH (p:Person { id: 'Q3186409' })-[r2:ACUSA|APOIA]->(p2:Person)
RETURN p1,p2,r1,r2 LIMIT 25


# filter by date
MATCH p=()-[r:ACUSA]->()
WHERE r.data >= date('2002-01-01') AND r.data <= date('2002-12-31') 
RETURN r 
LIMIT 2


MATCH (s)-[r:ACUSA]->(t) 
WHERE r.data >= date('2011-01-01') AND r.data <= date('2011-12-31')
RETURN s,r,t


MATCH (s)-[r:ACUSA]->(t) 
WHERE r.data >= date('2011-01-01') AND r.data <= date('2011-12-31')
RETURN s,t count(r)


MATCH (s)-[r:ACUSA]->(t) 
WHERE r.data >= date('2011-01-01') AND r.data <= date('2011-12-31')
RETURN s as source, t as target, count(r) as frequency