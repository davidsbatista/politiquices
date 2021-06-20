import json
from pathlib import Path

from newspaper import Article, ArticleException
from politiquices.nlp.utils.utils import publico_urls, minimize_publico_urls


def get_caches_dir() -> str:
    d = str(Path(__file__).absolute().parent)
    return d


class ArticlesDB:

    def __init__(self):
        self.publico_cached = get_caches_dir()+"/full_text_cache/publico_full_texts_cache.jsonl"
        self.chave_cached = get_caches_dir()+"/full_text_cache/CHAVE-Publico_94_95.jsonl"
        self.arquivo_cached = get_caches_dir()+"/full_text_cache/extracted_texts_newspaper.jsonl"
        self.publico_texts = self._load_publico_texts()
        self.chave_texts = self._load_chave_texts()
        self.arquivo_texts = self._load_arquivo_texts()

    def _load_publico_texts(self):
        texts = dict()
        print("Loading publico.pt cached texts")
        with open(self.publico_cached) as f_in:
            for line in f_in:
                entry = json.loads(line)
                texts[entry["url"]] = entry["text"]
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
        print("downloading: ", url_no_frame)
        try:
            article.download()
            article.parse()
            entry = {"url": url, "text": article.text}
            # only cache article's text if actually some text was extracted
            if article.text:
                f_path = get_caches_dir()+"/full_text_cache/extracted_texts_newspaper.jsonl"
                with open(f_path, 'a') as f_out:
                    f_out.write(json.dumps(entry) + "\n")
        except ArticleException as e:
            pass

        return article.text

    def get_article_full_text(self, url):

        if url.startswith("https://www.linguateca.pt/CHAVE?"):
            return self.chave_texts[url]

        if url.startswith(publico_urls):
            minimized_url = minimize_publico_urls(url)
            try:
                return self.publico_texts[minimized_url]
            except KeyError:
                print(f"Can't get text for {url}")

        if url.startswith("https://arquivo.pt"):
            return self._get_from_arquivo(url)
