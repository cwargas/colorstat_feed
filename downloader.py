import datetime
import time

import feedparser
from dateutil import parser

from app import Article, db


def get_category(url):
    """Return a category from the feed URL

    Args:
        url ([str]): The URL of the feed

    Returns:
        [str]: Category name
    """
    if 'cnbc.com' in url or 'a.dj.com' in url or 'wsj.com' in url or 'economist.com' in url:
        return 'business'
    elif 'nationalreview.com' in url or 'newsmax.com' in url or 'nytimes.com' in url or 'theepochtimes.com' in url:
        return 'politics'
    elif 'dailymail.co.uk' in url or 'nypost.com' in url:
        return 'world'
    elif 'phys.org' in url or 'nasa.gov' in url or 'spacenews.com' in url:
        return 'space'
    elif 'cnet.com' in url or 'techradar.com' in url or 'hnrss.org' in url or 'techrepublic.com' in url:
        return 'tech'
    elif 'newscientist.com' in url or 'livescience.com' in url or 'sciencemag.org' in url:
        return 'science'
    elif 'reason.com' in url or 'washingtontimes.com' in url or 'lifehacker.com' in url:
        return 'general'
    elif 'politico.com' in url or 'defense.gov' in url or 'military.com' in url:
        return 'defense'
    elif 'nypost.com' in url:
        return 'nypost'
    else:
        return '<unknown>'


def fetch_feeds(feed_urls):
    """Downloads feeds from feed_urls and stores them in the DB

    Args:
        feed_urls ([list]): List of feed URLs
    """
    items = []
    for feed_url in feed_urls:
        # print(feed_url)
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            item = {
                'title': entry.title,
                'summary': entry.summary,
                'published': datetime.datetime.fromtimestamp(time.mktime(entry.published_parsed)),
                'link': entry.link,
                'category': get_category(feed_url),
            }
            if item not in items:
                items.append(item)
    # import json
    # with open('db.json', 'w') as f:
    #     json.dump(items, f, indent=2)
    # return
    print('Inserting into DB...')
    articles = []
    links = set(result[0] for result in db.session.query(Article.link).all())
    for item in items:
        if item['link'] in links:
            continue
        article = Article(title=item['title'], summary=item['summary'],
                          published=item['published'], link=item['link'],
                          category=item['category'])
        articles.append(article)
    print('Inserted', len(articles), 'articles')

    db.session.add_all(
       sorted(articles, key=lambda x: x.published, reverse=True))
    db.session.commit()

def start_fetching(delay=15):
    """Fetch feeds every delay minutes

    Args:
        delay (int, optional): [delay in minutes]. Defaults to 15.
    """
    while True:
        print('Getting feeds...')
        fetch_feeds(feed_urls)
        print(f'Sleeping for {delay}...')
        for _ in range(60*delay):
            time.sleep(1)

feed_urls = [
    # business
    'https://www.cnbc.com/id/10001147/device/rss/rss.html',
    'https://feeds.a.dj.com/rss/WSJcomUSBusiness.xml',
    'https://feeds.a.dj.com/rss/RSSOpinion.xml',
    'https://www.economist.com/united-states/rss.xml',
    # politics
    'https://www.nationalreview.com/feed/',
    'https://www.newsmax.com/rss/Politics/1/',
    'https://rss.nytimes.com/services/xml/rss/nyt/Politics.xml',
    'https://www.theepochtimes.com/c-us-features/feed',
    # world
    'https://www.dailymail.co.uk/news/worldnews/index.rss',
    # space
    'https://phys.org/rss-feed/breaking/space-news/',
    'https://www.nasa.gov/rss/dyn/breaking_news.rss',
    'https://rss.nytimes.com/services/xml/rss/nyt/Space.xml',
    'https://spacenews.com/feed/',
    # tech
    'https://www.cnet.com/rss/news/',
    'https://www.techradar.com/rss/news/world-of-tech',
    'https://hnrss.org/best',
    'https://hnrss.org/newest?points=100',
    'https://www.techrepublic.com/rssfeeds/articles/',
    # science
    'https://www.newscientist.com/subject/technology/feed/',
    'https://www.livescience.com/feeds/all',
    'https://rss.nytimes.com/services/xml/rss/nyt/Science.xml',
    'https://www.sciencemag.org/rss/news_current.xml',
    # general
    'https://nypost.com/opinion/feed/',
    'https://reason.com/latest/feed/',
    'https://www.washingtontimes.com/rss/headlines/culture/entertainment/',
    'https://lifehacker.com/rss',
    # defense
    'https://rss.politico.com/defense.xml',
    'https://www.defense.gov/DesktopModules/ArticleCS/RSS.ashx?max=10&ContentType=1&Site=945',
    'https://www.military.com/rss-feeds/content?keyword=headlines&channel=news&type=news',
]
