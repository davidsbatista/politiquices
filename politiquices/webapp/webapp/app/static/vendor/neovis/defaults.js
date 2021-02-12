new NeoVis({
// Normal neovis config
neo4j: {
		neo4jUri: 'bolt://192.168.0.14:7687',
		neo4jUser: 'neo4j',
		neo4jPassword: 's3cr3t',

},
visConfig: {
   // Full vis-network config you want to override
   // Can be found here: https://visjs.github.io/vis-network/docs/network/
}
})