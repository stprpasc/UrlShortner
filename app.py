from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
import string
import random

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///urls.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class Urls(db.Model):
    id_ = db.Column("id_", db.Integer, primary_key=True)
    long = db.Column("long", db.String())
    short = db.Column("short", db.String(3))
    visits = db.Column(db.Integer, default=0)
    date_created = db.Column(db.DateTime, default=datetime.now)

    def __init__(self, long, short):
        self.long = long
        self.short = short


@app.before_first_request
def create_tables():
    db.create_all()


"""
This function creates short url for the long url if it doesn't already exist in the database
"""


def shorten_url():
    letters = string.ascii_lowercase + string.digits
    while True:
        rand_letters = random.choices(letters, k=3)
        rand_letters = "".join(rand_letters)
        short_url = Urls.query.filter_by(short=rand_letters).first()
        if not short_url:
            return rand_letters


"""
This route and function redirects short url back to long url
"""


@app.route('/<short_url>')
def redirection(short_url):
    long_url = Urls.query.filter_by(short=short_url).first()
    if long_url:
        return redirect(long_url.long)
    else:
        return jsonify({'status': '001', 'reason': 'Invalid Short Url'})


"""
This route and function calls shorten url, then maps it with long url and then adds it to database
"""


@app.route('/new', methods=['POST', 'GET'])
def new_url():
    if request.method == "POST":
        url_received = request.form["url"]
        # Check if url already exists in db
        res = Urls.query.filter_by(long=url_received).first()
        if res:
            return jsonify({'status': '002', 'reason': 'URL already exists', 'short_url': res.short})
        else:
            short_url = shorten_url()
            new_url = Urls(url_received, short_url)
            db.session.add(new_url)
            db.session.commit()
            response = {
                'long_url': url_received,
                'short_url': short_url
            }
            return jsonify(response)


"""
This route and function views short url and it's corresponding long url
"""


@app.route('/view/<short_url>')
def view_url(short_url):
    long_url = Urls.query.filter_by(short=short_url).first()
    return render_template('shorturl.html', short_url_display=short_url, long_url=long_url)


"""
This route and function acts as api interface to fetch the json file with short urls and long urls
"""


@app.route('/view/api/<short_url>')
def api_url(short_url):
    long_url = Urls.query.filter_by(short=short_url).first()
    response = {
        'long_url': long_url.long,
        'short_url': short_url
    }
    return jsonify(response)


"""
This route and function acts as api interface to fetch the json file with all urls in database
"""


@app.route('/view_all/api/')
def api_view_all():
    query = Urls.query.all()
    result = []
    for data in query:
        res = {
            'long_url': data.long,
            'short_url': data.short
        }
        result.append(res)
    return jsonify(result)


@app.route('/')
def index():
    res = {
        'view all urls as api response': '/view-all/api',
        'api url': '/view/api/<short_url>',
        'view_url': '/view/<short_url>',
        'new_url': '/new',
        'redirection': '/<short_url>'
    }
    return jsonify(res)


app.run(host='0.0.0.0', port=81, debug=True)
