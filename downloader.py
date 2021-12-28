import datetime
import time

import feedparser

from app import Article, db


def get_category(url):
    """Return a category from the feed URL

    Args:
        url ([str]): The URL of the feed

    Returns:
        [str]: Category name
    """
    if 'nypost.com' in url:
        return 'business'
    elif 'nationalreview.com' in url or 'newsmax.com' in url or 'theamericanconservative.com' in url:
        return 'politics'
    elif 'phys.org' in url or 'nasa.gov' in url or 'spacenews.com' in url or 'universetoday.com' in url:
        return 'space'
    elif 'newscientist.com' in url or 'livescience.com' in url:
        return 'science'
    elif 'militarytimes.com' in url:
        return 'defense'
    else:
        return '<unknown>'


def fetch_feeds(feed_urls):
    """Downloads feeds from feed_urls and stores them in the DB

    Args:
        feed_urls ([list]): List of feed URLs
    """
    items = []
    for i, feed_url in enumerate(feed_urls):
        print(f'{i+1}/{len(feed_urls)}: {feed_url}')
        success = False
        for _ in range(5):
            try:
                feed = feedparser.parse(feed_url)
            except Exception as e:
                print(e)
                time.sleep(1)
            else:
                success = True
                break
        if not success:
            continue

        for entry in feed.entries:
            item = {
                'title': entry.title,
                # 'summary': entry.summary,
                'published': datetime.datetime.fromtimestamp(time.mktime(entry.published_parsed)),
                'link': entry.link,
                # 'category': get_category(feed_url),
            }
            if item not in items:
                items.append(item)

    print('Inserting into DB...')
    articles = []
    links = set(result[0] for result in db.session.query(Article.link).all())
    for item in items:
        if item['link'] in links:
            continue
        article = Article(title=item['title'],
                          published=item['published'], link=item['link'],)
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
    'https://nypost.com/opinion/feed/',

    # politics
    'https://www.nationalreview.com/feed/',
    'https://www.newsmax.com/rss/Politics/1/',
    'https://www.theamericanconservative.com/web-categories/politics/feed/',

    # space articles
    'https://phys.org/rss-feed/breaking/space-news/',
    'https://www.nasa.gov/rss/dyn/breaking_news.rss',
    'https://spacenews.com/feed/',
    'https://www.universetoday.com/feed/',
   
    # science
    'https://www.newscientist.com/subject/technology/feed/',
    'https://www.livescience.com/feeds/all',

    # defense
    'https://www.militarytimes.com/arc/outboundfeeds/rss/category/news/?outputType=xml',
]
