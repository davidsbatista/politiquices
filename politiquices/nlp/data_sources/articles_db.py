import json
from newspaper import Article, ArticleException
from politiquices.nlp.utils.utils import publico_urls


class ArticlesDB:

    def __init__(self):
        self.publico_cached = "../data_sources/full_text_cache/publico_full_text.txt"
        self.chave_cached = "../data_sources/full_text_cache/CHAVE-Publico_94_95.jsonl"
        self.arquivo_cached = "../data_sources/full_text_cache/extracted_texts_newspaper.jsonl"
        self.publico_texts = self._load_publico_texts()
        self.chave_texts = self._load_chave_texts()
        self.arquivo_texts = self._load_arquivo_texts()

    def _load_publico_texts(self):
        texts = dict()
        print("Loading cache publico.pt texts")
        with open(self.publico_cached) as f_in:
            for line in f_in:
                try:
                    parts = line.split("\t")
                    url = parts[1]
                    text = " ".join(parts[3:])
                    texts[url] = text
                except Exception as e:
                    continue
            return texts

    def _load_chave_texts(self):
        texts = dict()
        print("Loading CHAVE texts")
        with open(self.chave_cached) as f_in:
            for line in f_in:
                entry = json.loads(line)
                texts["https://www.linguateca.pt/CHAVE?" + entry["id"]] = entry["text"]
            return texts

    def _load_arquivo_texts(self):
        texts = dict()
        print("Loading arquivo.pt cached texts")
        with open(self.arquivo_cached) as f_in:
            for line in f_in:
                entry = json.loads(line)
                texts[entry["url"]] = entry["text"]
            return texts

    def _get_from_arquivo(self, url):
        # try to get the text from cache
        if text := self.arquivo_texts.get(url):
            return text

        # if not in cache download it from arquivo.pt
        url_no_frame = url.replace("/wayback/", "/noFrame/replay/")
        article = Article(url_no_frame)
        try:
            print("downloading: ", url_no_frame)
            article.download()
            article.parse()
            entry = {"url": url, "text": article.text}
            with open(
                "../data_sources/full_text_cache/extracted_texts_newspaper.jsonl", "a"
            ) as f_out:
                f_out.write(json.dumps(entry) + "\n")
        except ArticleException as e:
            print(e)
            with open("download_error.txt", "a+") as f_out:
                f_out.write(url_no_frame+"\n")

        return article.text

    def get_article_full_text(self, url):
        if url.startswith("https://www.linguateca.pt/CHAVE?"):
            return self.chave_texts[url]
        if url.startswith(publico_urls):
            try:
                return self.publico_texts[url]
            except KeyError:
                print("Can't get text for {url}")  # ToDo: replace by a logger
                exit(-1)

        if url.startswith("https://arquivo.pt"):
            return self._get_from_arquivo(url)
