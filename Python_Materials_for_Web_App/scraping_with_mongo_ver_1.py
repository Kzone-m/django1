import os, lxml.html, cssselect
from pymongo import MongoClient


def get_html(url):
    '''parse url as html
    '''
    tree = lxml.html.parser(url)
    html = tree.getroot()
    return html


def union_urls(urls, new_urls):
    '''avoid duplicating url before saving urls into db
    '''
    for url in new_urls:
        u = url.get('href')
        if u not in urls:
            links.append(u)


def save(urls):
    '''connect Mongo DB and save each url
    '''
    client = MongoClient('localhost', 27017)
    db = client.scraping_test_db
    collection = db.urls
    # collection.delete_many({ })
    for url in urls:
        collection.insert_one({'url': url})
    return collection


def get_urls(seed_url):
    '''get urls collection by parsing seed url
    '''
    to_crawl = [seed_url]
    crawled = []
    while to_crawl:
        url = to_crawl.pop()
        html = get_html(url)
        urls = html.cssselect('a')
        if url not in crawled:
            union_urls(to_crawl, urls)
            crawled.append(html)
    return save(crawled)


def print_urls(collection):
    '''print urls saved in Mongo DB
    '''
    for url in collection.find().sort('_id'):
        print(link['_id'], link['url'])

urls = parse_urls(input())
print_urls(urls)

# Note:
# os.getcwd()
# os.mkdir('scraping_test')
# os.chdir('scraping_test')
# os.getcwd()
# 自分のDjnago Projectをparseする -> url = 'http://127.0.0.1:8000/'
