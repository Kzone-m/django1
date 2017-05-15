import os, lxml.html, cssselect, re, time, urllib, MeCab
from pymongo import MongoClient
from urllib.parse import urljoin
from urllib.request import urlopen
from reppy.cache import RobotsCache


def confirm_robots_txt(target_url, max_capacity):
    '''confirm that target url is allowed to crawl

    :type target_url: str
    :param target_url: agent wanna crawl
    :type max_capacity: int
    :param max_capacity: limit of max crawling pages
    :rtype: bool
    :return: weather it is possible to scrape
    '''
    robots = RobotsCache(max_capacity)
    return robots.allowed(target_url, 'python program')


def prepare_parsing_url(url):
    '''access this url, decode its info as html contents, and pass them to parse_url function

    :type url: str
    :param url: target url parsed by lxml
    :rtype: lxml.html.HtmlElement or NoneType
    :return: HtmlElement containing url's html info
    '''
    file_name = 'scraping_sample.html'
    try:
        f = urlopen(url)
        encoding = f.info().get_content_charset(failobj='utf-8')
        text = f.read().decode(encoding)
        if not os.path.exists(file_name):
            with open(file_name, 'w') as f:
                f.write(text)
        if os.path.exists(file_name):
            html = parse_url(file_name)
            os.remove(file_name)
        else:
            html = None
    except (UnicodeDecodeError, urllib.error.HTTPError):
        html = None
    return html


def parse_url(url):
    '''parse url as html

    :type url: str
    :param url: target url parsed by lxml
    :rtype: lxml.html.HtmlElement or NoneType
    :return: HtmlElement containing url's html info
    '''
    try:
        time.sleep(2)
        tree = lxml.html.parse(url)
        html = tree.getroot()
    except OSError:
        html = None
    return html


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
    words_lst = []
    target_tag_lst = ['h1', 'p', 'a']
    for tag_name in target_tag_lst:
        split_html_tags_into_words(html, tag_name, words_lst)
    for word in words_lst:
        word = re.sub(r'[\s\[\]\{\}\<\>\-\/\'\"*+=!#%:;.,。、]', '', word)
        pattern = re.compile(u'[一-龥ぁ-んァ-ン]')
        if len(word) == 0:
            continue
        if re.search(pattern, word):
            tagger = MeCab.Tagger()
            tagger.parse('')
            node = tagger.parseToNode(word)
            while node:
                word_ja = node.surface
                print(word_ja)
                if len(word_ja) != 0:
                    add_to_index(index, word_ja, url)
                node = node.next
        else:
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


def scraping(seed_url, max_depth, max_capacity):
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
    index = {}    # {keyword, [url1, url2], keyword, [url1, url2], ...}
    graph = {}    # {<url>, [list of pages it links to]}
    html = None    # html's dom info
    while crawl_lst and depth <= max_depth:
        base_url = crawl_lst.pop()
        if confirm_robots_txt(base_url, max_capacity):
            html = prepare_parsing_url(base_url)
            if not html:    # if html is NontType
                continue
            if base_url not in crawled_lst:
                outlinks = html.cssselect('a')   # select all a-tags projected to another html
                add_page_to_index(index, base_url, html)
                graph[base_url] = [urljoin(base_url, outlink.get('href')) for outlink in outlinks]
                union_urls(base_url, next_depth, outlinks)
                crawled_lst.append(base_url)
            if not crawl_lst:
                crawl_lst, next_depth = next_depth, []
                depth = depth + 1
        else:
            continue
    return save(crawled_lst), index, graph


def compute_ranks(graph):
    d = 0.8 # damping factor
    numloops = 10
    ranks = {}
    npages = len(graph)
    for page in graph:
        ranks[page] = 1.0 / npages
    for i in range(0, numloops):
        newranks = {}
        for page in graph:
            newrank = (1 - d) / npages
            for node in graph:
                if page in graph[node]:
                    newrank = newrank + d * (ranks[node] / len(graph[node]))
            newranks[page] = newrank
        ranks = newranks
    return ranks


def lookup(index, keyword):
    '''search coressponding urls based on passed keyword

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


def sort_ranks_by_descending(ranks, index, keyword):
    '''return descending order of rank value and corresponding url

    :type ranks: dict
    :param ranks: dict containing url as a key and rank value
    :type index: dict
    :param index: container which stores key word and corresponding url
    :type keyword: str
    :param keyword: index to help finding out url
    :rtype: double list or None
    :return: double list of descending order of url and rank value or None
    '''
    pages = lookup(index, keyword)    # [url1, url2, ...]
    sorted_ranks = []
    if pages:
        for page in pages:
            if page in ranks:
                sorted_ranks.append([page, ranks[page]])
        return sorted_ranks
    else:
        return None


def print_urls(collection):
    '''print urls saved in Mongo DB

    :type collection: pymongo.collection.Collection
    :param collection: collection of urls saved into db
    :rtype: None
    :return: None
    '''
    for url in collection.find().sort('_id'):
        print(url['url'])


collection, index, graph = scraping(input('enter seed url: '), int(input('enter depth: ')), int(input('decide capacity: ')))
ranks = compute_ranks(graph)
sorted_ranks = sort_ranks_by_descending(ranks, index, keyword = input('enter what you wanna search: '))
print_urls(collection)
