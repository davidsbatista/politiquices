## Generate triples graph


```
python prepare_for_extraction.py <dir_with_crawled_data>
```

```
python extract_relationships.py --arquivo titles_processed.jsonl --chave titles_processed.jsonl --arquivo titles_processed.jsonl
```

```
python create_rdf_graph.py --publico ../scripts/2020-12-28_publico/titles_processed.jsonl --chave ../scripts/2021-02-12_CHAVE/titles_processed.jsonl --arquivo ../scripts/2020-12-28_arquivo/titles_processed.jsonl
```

will produce:

```
politiquices_<date_time>.ttl
```