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
domain = 'colorstat.com'


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


def get_domain(link):
    return urlparse(link).netloc.replace('www.', '')


app.jinja_env.filters['domain'] = get_domain
app.jinja_env.globals['now'] = datetime.datetime.utcnow


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
    return render_template('home.html', title='Colorstat', articles=articles)


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


if __name__ == '__main__':
    app.run(debug=True)
