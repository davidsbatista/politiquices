import json
import requests


def get_text_from_file(url):
    with open('extracted_texts.jsonl', 'rt') as f_in:
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
    pass
    """
    url = "https://arquivo.pt/noFrame/replay/20190215190414/https://jornaleconomico.sapo.pt/noticias/inqueritoenergia-vieira-da-silva-delegou-em-zorrinho-mas-subscreve-decisoes-401616"
    article = Article(url)
    article.download()
    article.parse()
    article.text
    """