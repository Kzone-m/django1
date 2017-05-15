import os, lxml.html, cssselect, re
from pymongo import MongoClient
from urllib.parse import urljoin
from urllib.request import urlopen

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
    :param new_urls: containing new target urls, some of which possibly have crawled url
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


"""
def split_html_into_words(url):
    f = urlopen(url)
    encoding = f.info().get_content_charset(failobj='utf-8')
    content = f.read().decode(encoding)
    body_start = content.find('<body>')
    body_end = content.find('</body>')
    content = content[body_start:body_end]
    content = re.sub(r'<!--[\s\w\d/<>]*-->', '', content)
    content = re.sub(r'</?a\s*[\w\s\d\'\"/=.:|%+-]*>', '', content)
    pattern = re.compile(r'<[\w\d/]*>')
    words = []
    for word in content.split():
        word = re.sub(pattern, '', word).strip()
        if word != '':
            words.append(word)
    return words
"""


def split_html_tags_into_words(html, tag_name, words_lst):
    ''' based on tag name, extract text, split it into a word, and add them to words lst.

    :type html: lxml.html.HtmlElement
    :param html: containing its html dom info
    :type tag_name: str
    :param tag_name: tag name which user wanna know
    :type words_lst: list
    :param words_lst: container of words to create index dict
    '''
    for tag_content in html.cssselect(tag_name):
        if not isinstance(None, type(tag_content.text)):
            words_lst += tag_content.text.split()


def add_page_to_index(index, url, html):
    '''get keywords' list and pass it to add_to_index function

    :type index: dict
    :param index: container which stores key word and corresponding url
    :type url: str
    :param url: crawling url
    :type html: lxml.html.HtmlElement
    :param html: containing its html dom info
    '''
    # words = split_html_into_words(url)
    words_lst = []
    target_tag_lst = ['h1', 'p', 'a']
    for tag_name in target_tag_lst:
        split_html_tags_into_words(html, tag_name, words_lst)
    for word in words_lst:
        '''あとで改良するよ!!!'''
        pattern = re.compile(r'=')
        if re.search(pattern, word):
            continue
        add_to_index(index, word, url)


def add_to_index(index, keyword, url):
    '''add keyword and corresponding url to index dict

    :type index: dict
    :param index: container which stores key word and corresponding url
    :type keyword: str
    :param keyword: index to help finding out url
    :type url: str
    :param url: crawling url
    '''
    if keyword in index:
        if url not in index[keyword]:
            index[keyword].append(url)
    else:
        index[keyword] = [url]


def lookup(index, keyword):
    '''connect Mongo DB and save each url

    :type index: dict
    :param index: container which stores key word and corresponding url
    :type keyword: str
    :param keyword: index to help finding out url
    :rtype: list or None
    :return: list of urls which corresponds to keyword or None
    '''
    if keyword in index:
        return index[keyword]
    else:
        return None


def scraping(seed_url, max_depth):
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
    index = {}
    while crawl_lst and depth <= max_depth:
        base_url = crawl_lst.pop()
        html = parse_url(base_url)
        if not html:
            continue
        new_url_lst = html.cssselect('a')   # select all a_tags from html
        if base_url not in crawled_lst:
            add_page_to_index(index, base_url, html)  # index = {'', []}
            union_urls(base_url, next_depth, new_url_lst)
            crawled_lst.append(base_url)
        if not crawl_lst:
            crawl_lst, next_depth = next_depth, []
            depth = depth + 1
    return save(crawled_lst), index


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

collection, index = scraping(input('enter seed url: '), int(input('enter depth: ')))
print_urls(urls)
