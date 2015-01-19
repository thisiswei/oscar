import re
import random
from itertools import islice

import requests
import grequests
from pprint import pprint
from pho import Pho


BASE_URL = 'http://en.wikipedia.org%s'
MAIN_URL = 'http://en.wikipedia.org/wiki/Academy_Award_for_Best_Picture'

YEAR_REGEX = re.compile('(19|20)\d{2}')
BUDGET_REGEXS = [ re.compile('(?i)budget(?:.|\n)*?\$(.*?)<'),
                  re.compile('(\d+) million'),
                  re.compile('\$(\d+)'),
                 ]
MIL = 1000000
BUDGET_BOTTOM_LINE = 1000
BATCH_SIZE = 10

USER_AGENTS = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:11.0) Gecko/20100101 Firefox/11.0',
               'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:22.0) Gecko/20100 101 Firefox/22.0',
               'Mozilla/5.0 (Windows NT 6.1; rv:11.0) Gecko/20100101 Firefox/11.0',
               'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_4) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.46 Safari/536.5',
               'Mozilla/5.0 (Windows; Windows NT 6.1) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.46 Safari/536.5',)


def get(size, limit=None, serialize=False):
    urls = _get_urls()[:limit]
    to_return = []
    for _urls in _batch(urls, size):
        contents = _get_pages(_urls, serialize=serialize)
        to_return += [_get_summary(content=c) for c in contents]
    return to_return

def _get_urls():
    page = _get_page(MAIN_URL)
    html = Pho(page)
    winners = html.find_all('tr', {'style': 'background:#FAEB86'})
    return [BASE_URL % w.find('a')['href'] for w in winners]

def _batch(seq, size=BATCH_SIZE):
    return [islice(seq, i, i+size) for i in range(0, len(seq), size)]

def _get_pages(urls, serialize=False):
    if serialize:
        return [_get_page(url) for url in urls]
    else:
        gs = (grequests.get(url, headers={'User-Agent': random.choice(USER_AGENTS)}, proxies=_get_proxies()) for url in urls)
        rs = grequests.map(gs)
        return [r.text for r in rs]

def _get_page(url):
    return requests.get(url, headers={'User-Agent': random.choice(USER_AGENTS)}, proxies=_get_proxies()).text

def _get_summary(url=None, content=None):
    content = content or _get_page(url)
    html = Pho(content)
    table = html.find('table', {'style': 'width:22em;font-size:90%;'})
    budget = _get_budget(table.html)
    name = table.find('th').get_text().lower()
    year = int(YEAR_REGEX.search(table.html).group())

    return {
        'budget': budget,
        'name': name,
        'year': year,
    }

def _get_budget(html):
    for regex in BUDGET_REGEXS:
        try:
            t = regex.search(html).group(1).replace(',', '')
            b = int(t)
            return b * MIL if b < BUDGET_BOTTOM_LINE else b
        except:
            continue
    return None

def _get_proxies():
    return {}

def _avg(rs):
    rs = filter(lambda r: r.get('budget'), rs)
    return sum(r['budget'] for r in rs) / len(rs)+0.


def main():
    define('size', type=int, default=BATCH_SIZE)
    define('limit', type=int, default=None)
    define('serialize', type=bool, default=False)

    parse_command_line()
    basicConfig(options=options)

    rs = get(options.size, limit=options.limit)
    pprint(rs)
    pprint(_avg(rs))


if __name__ == '__main__':
    from utensils.options import define
    from utensils.options import options
    from utensils.options import parse_command_line
    from utensils.loggingutils import basicConfig
    exit(main())
