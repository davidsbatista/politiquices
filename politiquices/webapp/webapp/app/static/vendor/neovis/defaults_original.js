const defaults = {

	neo4j: {
		initialQuery: `MATCH (n) WHERE exists(n.pagerank)
                        WITH (n), RAND() AS random
                        ORDER BY random LIMIT 3000
                        OPTIONAL MATCH (n)-[r]-(m)
                        //WITH n,r,m WHERE exists(n.pagerank) AND exists(m.pagerank) AND exists(m.community)
                        RETURN n, r, m;`,
		neo4jUri: 'bolt://192.168.0.14:7687',
		neo4jUser: 'neo4j',
		neo4jPassword: 's3cr3t',
		encrypted: 'ENCRYPTION_OFF',
		trust: 'TRUST_ALL_CERTIFICATES'
	},

	visJs: {
		nodes: {
			font: {
				size: 26,
				strokeWidth: 7
			},
			scaling: {}
		},
		edges: {
			arrows: {
				to: { enabled: false } // FIXME: handle default value
			},
			length: 200
		},
		layout: {
			improvedLayout: false,
			hierarchical: {
				enabled: false,
				sortMethod: 'hubsize'
			}
		},
		physics: { // TODO: adaptive physics settings based on size of graph rendered
			// enabled: true,
			// timestep: 0.5,
			// stabilization: {
			//     iterations: 10
			// }

			adaptiveTimestep: true,
			// barnesHut: {
			//     gravitationalConstant: -8000,
			//     springConstant: 0.04,
			//     springLength: 95
			// },
			stabilization: {
				iterations: 200,
				fit: true
			}
		}
	}
};

export { defaults };