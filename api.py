# Create a simple rest api, which manages non-html comments for a web frontend.
# The comments are tied to articles, which are identified by uuid.
# When creating a comment, return a key, which is later used by users who created the comment to edit/remove the comment.
# Please dockerize the app. The rest is on you.

import json
import uuid

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt

from utils import AlchemyEncoder

# Config of the application
def create_app():
    app = Flask(__name__)
    CORS(app)

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = 'super-secret'
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = False
    app.config['JWT_BLACKLIST_ENABLED'] = True
    app.config['JWT_BLACKLIST_TOKEN_CHECKS'] = ['access', 'refresh']

    return app


# Initialize the app
app = create_app()
db = SQLAlchemy(app)
ma = Marshmallow(app)
jwt = JWTManager(app)
bcrypt = Bcrypt(app)

# Create a model for the Articles
class Article(db.Model):
    __tablename__ = 'article'

    id = db.Column(
        'id', 
        db.Text(length=36), 
        default=lambda: str(uuid.uuid4()), 
        primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    body = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(100), nullable=False)
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())
    date_modified = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp())
    comments = db.relationship('Comment', backref='article', lazy=True)

# Create a model for the comments
class Comment(db.Model):
    __tablename__ = 'comment'

    id = db.Column(
        'id', db.Text(length=36),
        default=lambda: str(uuid.uuid4()), 
        primary_key=True)
    comment = db.Column(db.String(500))
    user = db.Column(db.String(50))
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())
    date_modified = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp())
    article_id = db.Column(
        db.Integer,
        db.ForeignKey('article.id'),
        nullable=False)

# Routes

# Run this before the first request is made
@app.before_first_request
def before_first_rq():
    db.create_all()

# Base route
@app.route('/', methods=['GET'])
def index():
    if request.method == 'GET':
        return jsonify({'message': 'Welcome to the API'})

# route populate database
@app.route('/populate', methods=['POST', 'GET'])
def populate():
    db.create_all()

    article1 = Article(
        title='Article 1',
        body='This is the body of article 1',
        author='Author 1')
    db.session.add(article1)
    db.session.commit()

    # Create 10 comments for testing
    for i in range(10):
        comment = Comment(
            comment='This is comment '+ str(i + 1),
            user='User ' + str(i + 1),
            article_id=article1.id)
        db.session.add(comment)

    db.session.commit()
    return jsonify({'message': 'Database populated'})


@app.route('/api/v1/comments', methods=['GET', 'POST', 'DELETE'])
def comments():
    if request.method == 'GET':
        comments = Comment.query.all()
        return json.dumps(comments, cls=AlchemyEncoder)

    if request.method == 'POST':
        comment = request.json['comment']
        user = request.json['user']
        article_id = request.json['article_id']
        new_comment = Comment(
            comment=comment,
            user=user,
            article_id=article_id)
        db.session.add(new_comment)
        db.session.commit()
        return jsonify(new_comment.id)


def deploy_api():
    from waitress import serve
    serve(app, host="0.0.0.0", port=7313)


deploy_api()
