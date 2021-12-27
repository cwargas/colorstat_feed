import datetime
from urllib.parse import urlparse

from flask import Flask, render_template, request
from flask.wrappers import Response
from flask_sqlalchemy import SQLAlchemy
from flask_view_counter import ViewCounter


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
view_counter = ViewCounter(app, db)
domain = 'megafeed.co'


class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500), nullable=False)
    summary = db.Column(db.String(1000), nullable=False)
    published = db.Column(db.DateTime, nullable=False)
    link = db.Column(db.String(500), unique=True, nullable=False)
    category = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return '<Title {}, Published {}, Link {}, Category {}>'.format(
            self.title, self.published, self.link, self.category)

class View(db.Model):
    __tablename__ = 'vc_requests'
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)
    day = db.Column(db.Integer, nullable=False)
    hour = db.Column(db.Integer, nullable=False)
    minute = db.Column(db.Integer, nullable=False)
    ip = db.Column(db.String, nullable=False)
    user_agent = db.Column(db.String, nullable=False)
    path = db.Column(db.String, nullable=False)
    status = db.Column(db.Integer, nullable=False)
    args = db.Column(db.String, nullable=True)

    def __repr__(self):
        return '<{}, {}-{}-{} {}:{}>'.format(self.ip, self.year, self.month, self.day,
        self.hour, self.minute)

def get_views():
    past_week = {}
    for days in range(7, -1, -1):
        date = (datetime.datetime.now() - datetime.timedelta(days=days)).date()
        past_week[date] = 0

    views = View.query.all()
    for view in views:
        date = datetime.date(year=view.year, month=view.month, day=view.day)
        if date not in past_week.keys():
            continue
        past_week[date] += 1

    return ' '.join([f'{date.isoformat()}: {count}' for date, count in past_week.items()])

def get_domain(link):
    return urlparse(link).netloc.replace('www.', '')

def format_time(t):
    #return datetime.datetime.strftime(t, '%m-%d-%Y %I:%M %p')
    return datetime.datetime.strftime(t, '%m-%d-%Y')

app.jinja_env.filters['domain'] = get_domain
app.jinja_env.globals['now'] = datetime.datetime.utcnow
app.jinja_env.filters['format_time'] = format_time

"""create the DB. done only once
from main import db
db.create_all()
"""

"""
export FLASK_APP=main.py
export FLASK_ENV=development
flask run
"""


@app.route('/')
@app.route('/home', methods=['GET'])
@view_counter.count
def home():
    page = request.args.get('page', 1, type=int)
    articles = Article.query.order_by(
        Article.published.desc()).paginate(page=page, per_page=50)
    return render_template('home.html', title='Megafeed', articles=articles, views=get_views())


@app.route('/about', methods=['GET'])
@view_counter.count
def about():
    return render_template('about.html', title='About us')


@app.route('/donate', methods=['GET'])
@view_counter.count
def donate():
    return render_template('donate.html', title='Donate')


@app.route('/robots.txt', methods=['GET'])
@view_counter.count
def robots():
    r = Response(
        response=f"User-Agent: *\nDisallow: /\n\nSitemap: https://{domain}/sitemap.xml", status=200, mimetype="text/plain")
    r.headers["Content-Type"] = "text/plain; charset=utf-8"
    return r


@app.route('/sitemap.xml', methods=['GET'])
@view_counter.count
def sitemap():
    pages = []
    for rule in app.url_map.iter_rules():
        pages.append(
            str(rule.rule)
        )
    sitemap_xml = render_template(
        'sitemap_template.xml', pages=pages, base_url=f'https://{domain}')
    respose = Response(sitemap_xml, content_type='application/xml')
    return respose


import downloader
import threading

LOCAL = False
if LOCAL: # Use below if running on localhost
    if __name__ == '__main__':
        # start downloader in a separate thread
        thread = threading.Thread(target=downloader.start_fetching, args=(10, ))
        thread.start()
        # disable reloader so it doesn't run downloader twice
        app.run(debug=True, use_reloader=False)
else: # Use below code when hosted online
    # start downloader in a separate thread
    thread = threading.Thread(target=downloader.start_fetching, args=(20, ))
    thread.start()
    if __name__ == '__main__':
    # disable reloader so it doesn't run downloader twice
        app.run(debug=True, use_reloader=False)