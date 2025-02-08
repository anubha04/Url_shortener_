from flask import Flask, request, render_template, redirect
from flask_sqlalchemy import SQLAlchemy
import hashlib

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Model for storing URLs
class URL(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_url = db.Column(db.String(500), nullable=False, unique=True)
    short_code = db.Column(db.String(10), unique=True, nullable=False)

# Function to generate a consistent short hash
def generate_short_code(original_url):
    return hashlib.sha256(original_url.encode()).hexdigest()[:6]  # First 6 chars of SHA-256 hash

# Home Page
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        original_url = request.form.get('original_url')

        if not original_url:
            return "Error: No URL provided", 400

        # Check if the URL already exists
        existing_url = URL.query.filter_by(original_url=original_url).first()
        if existing_url:
            return render_template('index.html', short_url=request.host_url + existing_url.short_code)

        # Generate a new short code (deterministic)
        short_code = generate_short_code(original_url)

        # Handle collision (append last digit of hash if needed)
        while URL.query.filter_by(short_code=short_code).first():
            short_code = generate_short_code(original_url + short_code[-1])

        # Save to database
        new_url = URL(original_url=original_url, short_code=short_code)
        db.session.add(new_url)
        db.session.commit()

        return render_template('index.html', short_url=request.host_url + short_code)

    return render_template('index.html', short_url=None)

# Redirect to original URL
@app.route('/<short_code>')
def redirect_to_original(short_code):
    url_entry = URL.query.filter_by(short_code=short_code).first()
    if url_entry:
        return redirect(url_entry.original_url)
    return "URL not found", 404

# Run the app
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Ensure database and table creation
    app.run(debug=True)
