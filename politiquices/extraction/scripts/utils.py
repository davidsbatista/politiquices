import json
import requests
from newspaper import Article, ArticleException


def get_text_from_file(url, f_name='extracted_texts.jsonl'):
    with open(f_name, 'rt') as f_in:
        for line in f_in:
            entry = json.loads(line)
            if entry['url'] == url:
                return entry['text']
    return None


def get_text(url):
    if text := get_text_from_file(url):
        return text
    original_url = '/'.join(url.split("/")[5:])
    crawl_date = url.split("/")[4]
    base_url = "https://arquivo.pt/textextracted"
    params = {'m': original_url+'/'+crawl_date}
    try:
        print("Getting extracted text from arquivo.pt for", url)
        response = requests.request("GET", base_url, params=params)
        if response.status_code == 200:
            text = response.text
            entry = {'url': url, 'text': text}
            with open('extracted_texts.jsonl', 'a') as f_out:
                f_out.write(json.dumps(entry)+'\n')
            return text
    except Exception as e:
        raise e


def get_text_newspaper(url):
    if text := get_text_from_file(url, f_name='extracted_texts_newspaper.jsonl'):
        return text
    url_no_frame = url.replace('/wayback/', '/noFrame/replay/')
    article = Article(url_no_frame)
    try:
        print("downloading: ", url_no_frame)
        article.download()
        article.parse()
        entry = {'url': url, 'text': article.text}
        with open('extracted_texts_newspaper.jsonl', 'a') as f_out:
            f_out.write(json.dumps(entry) + '\n')
    except ArticleException as e:
        print(e)
        with open('download_error.txt', 'a+') as f_out:
            f_out.write(url+'\t'+url_no_frame+'\n')
    return article.text
