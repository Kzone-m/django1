import os, lxml.html, cssselect
from pymongo import MongoClient
from urllib.parse import urljoin


def parse_url(url):
    '''parse url as html

    :type url: str
    :param url: target url parsed by lxml
    :rtype: lxml.html.HtmlElement or NoneType
    :return: HtmlElement containing url's html info
    '''
    try:
        tree = lxml.html.parse(url)
        html = tree.getroot()
    except OSError:
        html = None
    return html


def union_urls(base_url, urls, new_urls):
    '''avoid making url duplicate before saving urls into db

    :type base_url: str
    :param base_url: hepling creating absolute url
    :type urls: list
    :param urls: containing target urls, not crawled yet
    :type new_urls: list
    :param new_urls: containing new target urls, possibly have crawled url
    :rtype: None
    :return: None
    '''
    for new_url in new_urls:
        new_url = urljoin(base_url, new_url.get('href'))
        if new_url not in urls:
            urls.append(new_url)


def save(urls):
    '''connect Mongo DB and save each url

    :type urls: list
    :param urls: crawled urls
    :rtype pymongo.collection.Collection
    :return: Collection
    '''
    client = MongoClient('localhost', 27017)    # connect mongo db
    db = client.scraping_test_db    # creating db
    collection = db.urls    # creating collection
    collection.delete_many({ })    # deleating info before saving in case
    for url in urls:
        collection.insert_one({'url': url})    # insert url into db
    return collection


def get_urls(seed_url, max_depth):
    '''parsing seed url, collecting urls related to seed url, and saving collected urls into DB

    :type seed_url: str
    :param seed_url: first url starting scraping
    :type max_depth: int
    :param max_depth: controlling how many pages this agent crawls
    :rtype pymongo.collection.Collection
    :return: Collection
    '''
    crawl_lst = [seed_url]    # list of targets scraping
    crawled_lst = []    # container for saving crawled urls
    next_depth = []    # temporaly container which will contain list of next targets at each depth, and it will be initialized when scraping moves to next depth
    depth = 0    # showing the depth when scraping
    while crawl_lst and depth <= max_depth:
        base_url = crawl_lst.pop()
        html = parse_url(base_url)
        if not html:
            continue
        new_url_lst = html.cssselect('a')   # select all a_tags from html
        if base_url not in crawled_lst:
            union_urls(base_url, next_depth, new_url_lst)
            crawled_lst.append(base_url)
        if not crawl_lst:
            crawl_lst, next_depth = next_depth, []
            depth = depth + 1
    return save(crawled_lst)


def print_urls(collection):
    '''print urls saved in Mongo DB

    :type collection: pymongo.collection.Collection
    :param collection: collection of urls saved into db
    :rtype: None
    :return: None
    '''
    for url in collection.find().sort('_id'):
        print(url['url'])
        # print(url['_id'], url['url'])

urls = get_urls(input('enter seed url: '), int(input('enter depth: ')))
print_urls(urls)


# Note:
# os.getcwd()
# os.mkdir('scraping_test')
# os.chdir('scraping_test')
# os.getcwd()
# 自分のDjnago Projectをparseする -> url = 'http://127.0.0.1:8000/'
