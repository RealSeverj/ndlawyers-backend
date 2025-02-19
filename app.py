from flask import Flask, request, jsonify, send_file, send_from_directory, session
from flask_cors import CORS
from datetime import datetime
from docx import Document
import os
import secrets
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()
app = Flask(__name__)
CORS(app, supports_credentials=True)

# Configure database connection
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://nd_lawyers:admin@localhost/ndlawyers_data'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = secrets.token_hex(16)

db.init_app(app)
migrate = Migrate(app, db)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(512), nullable=False)

    def set_username(self, username):
        self.username = username

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

# Define Article model
class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sort = db.Column(db.String(50), nullable=False)
    time = db.Column(db.DateTime, nullable=False)
    image_path = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    content = db.Column(db.Text, nullable=False)
    views = db.Column(db.Integer, default=0)
    file_path = db.Column(db.String(255), nullable=False)  # New field

# Create database tables
with app.app_context():
    db.create_all()

def save_image_locally(image_file):
    upload_folder = 'uploads/images/'
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    image_path = os.path.join(upload_folder, image_file.filename)
    image_file.save(image_path)
    return image_path

def save_file_locally(file):
    upload_folder = 'uploads/files/'
    file_path = os.path.join(upload_folder, file.filename)
    file.save(file_path)
    return file_path

# Function to read Word document content
def read_word_content(file_path):
    doc = Document(file_path)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return '\n'.join(full_text)


@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()

    # Check if there are no users in the database
    if User.query.count() == 0:
        new_user = User()
        new_user.set_username(username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        session['user_id'] = new_user.id
        print('User created and login successful!')
        return jsonify({'message': 'User created and login successful!'}), 201

    if user and user.check_password(password):
        session['user_id'] = user.id
        return jsonify({'message': 'Login successful!'}), 200
    else:
        return jsonify({'error': 'Invalid username or password'}), 401

@app.route('/api/change_password', methods=['PUT'])
def change_password():
    data = request.get_json()
    user_id = 2
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    print(f'user_id: {user_id}')

    user = User.query.get(user_id)

    if user and user.check_password(old_password):
        user.set_password(new_password)
        db.session.commit()
        return jsonify({'message': 'Password changed successfully!'}), 200
    else:
        return jsonify({'error': 'Invalid old password'}), 401

# Create article from Word document
@app.route('/api/articles', methods=['POST'])
def create_article():
    data = request.form
    file = request.files['file']
    image = request.files['image']
    image_path = save_image_locally(image)
    file_path = save_file_locally(file)  # Save file locally
    content = read_word_content(file)

    new_article = Article(
        sort=data['sort'],
        time=datetime.strptime(data['time'], '%Y-%m-%d %H:%M:%S'),
        image_path=image_path,
        title=data['title'],
        description=data['description'],
        content=content,
        views=data['views'],
        file_path=file_path
    )
    db.session.add(new_article)
    db.session.commit()
    return jsonify({'message': '文章上传成功!'}), 201

@app.route('/api/articles/<int:id>/file', methods=['GET'])
def get_article_file(id):
    article = Article.query.get_or_404(id)
    return send_file(
        article.file_path,
        download_name=f"{article.title}.docx",
        as_attachment=True
    )

@app.route('/api/articles', methods=['GET'])
def get_all_articles():
    articles = Article.query.order_by(Article.time.desc()).all()
    articles_data = [
        {
            'id': article.id,
            'sort': article.sort,
            'time': article.time.strftime('%Y-%m-%d %H:%M:%S'),
            'image_path': article.image_path,
            'file_path': article.file_path,
            'title': article.title,
            'description': article.description,
            'content': article.content,
            'views': article.views
        }
        for article in articles
    ]
    return jsonify(articles_data), 200

@app.route('/api/articles/<string:sort>', methods=['GET'])
def get_articles_by_sort(sort):
    articles = Article.query.filter_by(sort=sort).order_by(Article.time.desc()).all()
    articles_data = [
        {
            'id': article.id,
            'sort': article.sort,
            'time': article.time.strftime('%Y-%m-%d %H:%M:%S'),
            'image_path': article.image_path,
            'file_path': article.file_path,
            'title': article.title,
            'description': article.description,
            'content': article.content,
            'views': article.views
        }
        for article in articles
    ]
    return jsonify(articles_data), 200

@app.route('/api/articles/<int:id>', methods=['GET'])
def get_article_by_id(id):
    article = Article.query.filter_by(id=id).order_by(Article.time.desc()).first_or_404()
    article_data = {
        'id': article.id,
        'sort': article.sort,
        'time': article.time.strftime('%Y-%m-%d %H:%M:%S'),
        'image_path': article.image_path,
        'file_path': article.file_path,
        'title': article.title,
        'description': article.description,
        'content': article.content,
        'views': article.views
    }
    return jsonify(article_data), 200

@app.route('/api/articles/<int:id>', methods=['DELETE'])
def delete_article(id):
    article = Article.query.get_or_404(id)
    db.session.delete(article)
    db.session.commit()
    return jsonify({'message': 'Article deleted successfully!'}), 200

# Route to serve files from the uploads directory
@app.route('/uploads/<path:filename>')
def serve_uploads(filename):
    return send_from_directory('uploads', filename)

@app.route('/api/articles/<int:id>/views', methods=['PUT'])
def update_article_views(id):
    article = Article.query.get_or_404(id)
    data = request.get_json()
    if 'views' in data:
        article.views = data['views']
        db.session.commit()
        return jsonify({'message': 'Views updated successfully!'}), 200
    else:
        return jsonify({'error': 'Missing views field in request data'}), 400

@app.route('/api/articles/<int:id>/download', methods=['GET'])
def download_article_file(id):
    article = Article.query.get_or_404(id)
    return send_file(
        article.file_path,
        download_name=f"{article.title}.docx",
        as_attachment=True
    )

@app.route('/api/articles/search', methods=['GET'])
def search_articles():
    keyword = request.args.get('keyword', '')
    if not keyword:
        return jsonify({'error': '请输入关键词'}), 400

    search = f"%{keyword}%"
    articles = Article.query.filter(
        (Article.title.like(search)) | (Article.content.like(search))
    ).order_by(Article.time.desc()).all()

    articles_data = [
        {
            'id': article.id,
            'sort': article.sort,
            'time': article.time.strftime('%Y-%m-%d %H:%M:%S'),
            'image_path': article.image_path,
            'file_path': article.file_path,
            'title': article.title,
            'description': article.description,
            'content': article.content,
            'views': article.views
        }
        for article in articles
    ]
    return jsonify(articles_data), 200

if __name__ == "__main__":
    app.run(debug=True)
