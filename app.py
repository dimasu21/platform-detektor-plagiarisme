from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from preprocessing import preprocess_text
from rabin_karp import detect_plagiarism
from models import db, User
from database import init_db, get_db_stats
import os
import uuid
import time

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///plagiarism.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# Initialize database
init_db(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ==================== PUBLIC ROUTES ====================

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user, remember=True)
            user.last_login = db.func.now()
            db.session.commit()
            
            flash(f'Welcome back, {user.name}!', 'success')
            
            # Redirect to next page or dashboard
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        name = request.form.get('name')
        
        # Validation
        if not email or not password or not name:
            flash('All fields are required.', 'error')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template ('register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
            return render_template('register.html')
        
        # Check if email already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered. Please login.', 'error')
            return render_template('register.html')
        
        # Create new user
        new_user = User(
            email=email,
            name=name,
            role='user'
        )
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

# ==================== AUTHENTICATED ROUTES ====================

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    result = None
    suspect_images = []
    source_images = []
    suspect_highlighted = ""
    source_highlighted = ""
    suspect_original = ""
    source_original = ""
    
    if request.method == 'POST':
        from file_parser import extract_text_and_images_from_file
        from highlight_visualizer import highlight_plagiarism_in_images, save_highlighted_image
        from text_highlighter import highlight_text_matches
        
        # Extract text and images from both files
        suspect_data = None
        source_data = None
        
        # Handle Suspect Input
        if 'suspect_file' in request.files and request.files['suspect_file'].filename != '':
            suspect_data = extract_text_and_images_from_file(request.files['suspect_file'])
        else:
            suspect_text = request.form.get('suspect_text', '')
            if suspect_text:
                suspect_data = {'text': suspect_text, 'images': [], 'filename': 'manual_input'}
        
        # Handle Source Input
        if 'source_file' in request.files and request.files['source_file'].filename != '':
            source_data = extract_text_and_images_from_file(request.files['source_file'])
        else:
            source_text = request.form.get('source_text', '')
            if source_text:
                source_data = {'text': source_text, 'images': [], 'filename': 'manual_input'}
        
        if suspect_data and source_data and suspect_data['text'] and source_data['text']:
            # Store original texts for display
            suspect_original = suspect_data['text']
            source_original = source_data['text']
            
            # Preprocess
            suspect_processed = preprocess_text(suspect_data['text'])
            source_processed = preprocess_text(source_data['text'])
            
            print(f"DEBUG: Suspect Processed Length: {len(suspect_processed)}")
            print(f"DEBUG: Source Processed Length: {len(source_processed)}")
            
            if not suspect_processed or not source_processed:
                flash('Teks tidak terbaca dari file.', 'error')
                result = None
            else:
                # Detect plagiarism
                result = detect_plagiarism(suspect_processed, source_processed, k=5)
                
                # Generate highlighted text for visual comparison
                if result['matches']:
                    suspect_highlighted = highlight_text_matches(suspect_original, result['matches'])
                    source_highlighted = highlight_text_matches(source_original, result['matches'])
                else:
                    from html import escape
                    suspect_highlighted = escape(suspect_original)
                    source_highlighted = escape(source_original)
                
                # Generate unique session ID for this check
                session_id = str(uuid.uuid4())[:8]
                timestamp = int(time.time())
                
                # Highlight images if available
                if suspect_data['images'] and result['matches']:
                    print(f"DEBUG: Highlighting {len(suspect_data['images'])} suspect images...")
                    highlighted_suspect = highlight_plagiarism_in_images(
                        suspect_data['images'], 
                        result['matches']
                    )
                    
                    # Save highlighted images
                    for idx, img in enumerate(highlighted_suspect):
                        filename = f"suspect_{session_id}_{timestamp}_page_{idx+1}.png"
                        filepath = os.path.join('static', 'uploads', 'highlighted', filename)
                        save_highlighted_image(img, filepath)
                        suspect_images.append(f"uploads/highlighted/{filename}")
                
                if source_data['images'] and result['matches']:
                    print(f"DEBUG: Highlighting {len(source_data['images'])} source images...")
                    highlighted_source = highlight_plagiarism_in_images(
                        source_data['images'],
                        result['matches']
                    )
                    
                    # Save highlighted images
                    for idx, img in enumerate(highlighted_source):
                        filename = f"source_{session_id}_{timestamp}_page_{idx+1}.png"
                        filepath = os.path.join('static', 'uploads', 'highlighted', filename)
                        save_highlighted_image(img, filepath)
                        source_images.append(f"uploads/highlighted/{filename}")
        else:
            flash('Mohon masukkan teks atau unggah file untuk kedua kolom.', 'error')
            if not suspect_data or not suspect_data['text']:
                flash('Gagal mengekstrak teks dari Suspect File.', 'error')
            if not source_data or not source_data['text']:
                flash('Gagal mengekstrak teks dari Source File.', 'error')
        
    return render_template('dashboard.html', 
                         result=result, 
                         suspect_images=suspect_images,
                         source_images=source_images,
                         suspect_highlighted=suspect_highlighted,
                         source_highlighted=source_highlighted)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'update_profile':
            name = request.form.get('name')
            if name:
                current_user.name = name
                db.session.commit()
                flash('Profile updated successfully!', 'success')
        
        elif action == 'change_password':
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            if not current_user.check_password(current_password):
                flash('Current password is incorrect.', 'error')
            elif new_password != confirm_password:
                flash('New passwords do not match.', 'error')
            elif len(new_password) < 6:
                flash('Password must be at least 6 characters long.', 'error')
            else:
                current_user.set_password(new_password)
                db.session.commit()
                flash('Password changed successfully!', 'success')
        
        return redirect(url_for('profile'))
    
    return render_template('profile.html')

# ==================== ADMIN ROUTES ====================

@app.route('/admin/users')
@login_required
def admin_users():
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    users = User.query.order_by(User.created_at.desc()).all()
    stats = get_db_stats()
    
    return render_template('admin_users.html', users=users, stats=stats)

@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@login_required
def admin_delete_user(user_id):
    if not current_user.is_admin():
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    
    # Prevent deleting yourself
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'error')
        return redirect(url_for('admin_users'))
    
    db.session.delete(user)
    db.session.commit()
    
    flash(f'User {user.email} deleted successfully.', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/users/<int:user_id>/toggle_role', methods=['POST'])
@login_required
def admin_toggle_role(user_id):
    if not current_user.is_admin():
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    
    # Prevent changing your own role
    if user.id == current_user.id:
        flash('You cannot change your own role.', 'error')
        return redirect(url_for('admin_users'))
    
    # Toggle role
    user.role = 'user' if user.role == 'admin' else 'admin'
    db.session.commit()
    
    flash(f'User {user.email} role changed to {user.role}.', 'success')
    return redirect(url_for('admin_users'))

# ==================== BATCH COMPARISON ====================

@app.route('/batch', methods=['GET', 'POST'])
@login_required
def batch_comparison():
    from batch_comparison import compare_all_pairs, get_suspicious_pairs, get_comparison_stats
    
    results = None
    stats = None
    suspicious = None
    matrix = None
    doc_names = None
    
    if request.method == 'POST':
        from file_parser import extract_text_and_images_from_file
        
        files = request.files.getlist('documents')
        
        if len(files) < 2:
            flash('Please upload at least 2 documents to compare.', 'error')
            return render_template('batch.html')
        
        if len(files) > 30:
            flash('Maximum 30 documents allowed.', 'error')
            return render_template('batch.html')
        
        # Extract text from all files
        documents = []
        batch_id = str(uuid.uuid4())[:8]
        
        for idx, f in enumerate(files):
            if f.filename:
                data = extract_text_and_images_from_file(f)
                if data and data['text']:
                    # Save images to files if present
                    image_paths = []
                    if data.get('images'):
                        for img_idx, img in enumerate(data['images']):
                            img_filename = f'batch_{batch_id}_{idx}_{img_idx}.png'
                            img_path = os.path.join('static', 'uploads', img_filename)
                            os.makedirs(os.path.dirname(img_path), exist_ok=True)
                            img.save(img_path, 'PNG')
                            image_paths.append(f'uploads/{img_filename}')
                    
                    documents.append({
                        'name': f.filename,
                        'text': data['text'],
                        'images': image_paths  # Store paths, not PIL objects
                    })
                else:
                    flash(f'Could not extract text from: {f.filename}', 'error')
        
        if len(documents) < 2:
            flash('Need at least 2 valid documents with extractable text.', 'error')
            return render_template('batch.html')
        
        # Run cross-comparison
        results = compare_all_pairs(documents)
        stats = get_comparison_stats(results['pairs'])
        suspicious = get_suspicious_pairs(results['pairs'], threshold=50)
        matrix = results['matrix']
        doc_names = results['document_names']
        
        # Store results in session for detail view and back navigation
        session['batch_results'] = results
    else:
        # GET request - try to load results from session
        results = session.get('batch_results')
        if results:
            stats = get_comparison_stats(results['pairs'])
            suspicious = get_suspicious_pairs(results['pairs'], threshold=50)
            matrix = results['matrix']
            doc_names = results['document_names']
    
    return render_template('batch.html',
                         results=results,
                         stats=stats,
                         suspicious=suspicious,
                         matrix=matrix,
                         doc_names=doc_names)

@app.route('/batch/detail/<int:pair_index>')
@login_required
def batch_detail(pair_index):
    from text_highlighter import highlight_text_matches
    from highlight_visualizer import highlight_plagiarism_in_images
    from PIL import Image
    
    results = session.get('batch_results')
    if not results or pair_index >= len(results['pairs']):
        flash('Comparison data not found. Please run batch comparison again.', 'error')
        return redirect(url_for('batch_comparison'))
    
    pair = results['pairs'][pair_index]
    
    # Generate highlighted text
    suspect_highlighted = highlight_text_matches(pair['doc1_text'], pair['matches'])
    source_highlighted = highlight_text_matches(pair['doc2_text'], pair['matches'])
    
    # Generate highlighted images if raw images exist
    doc1_highlighted = []
    doc2_highlighted = []
    
    raw_doc1_images = pair.get('doc1_images', [])
    raw_doc2_images = pair.get('doc2_images', [])
    matches = pair.get('matches', [])
    
    if raw_doc1_images and matches:
        # Load raw images, apply highlights, save highlighted versions
        pil_images = [Image.open(os.path.join('static', path)) for path in raw_doc1_images]
        highlighted = highlight_plagiarism_in_images(pil_images, matches)
        
        for idx, img in enumerate(highlighted):
            filename = f'highlighted_d1_{pair_index}_{idx}.png'
            path = os.path.join('static', 'uploads', filename)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            img.save(path, 'PNG')
            doc1_highlighted.append(f'uploads/{filename}')
    
    if raw_doc2_images and matches:
        pil_images = [Image.open(os.path.join('static', path)) for path in raw_doc2_images]
        highlighted = highlight_plagiarism_in_images(pil_images, matches)
        
        for idx, img in enumerate(highlighted):
            filename = f'highlighted_d2_{pair_index}_{idx}.png'
            path = os.path.join('static', 'uploads', filename)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            img.save(path, 'PNG')
            doc2_highlighted.append(f'uploads/{filename}')
    
    return render_template('batch_detail.html',
                         pair=pair,
                         pair_index=pair_index,
                         suspect_highlighted=suspect_highlighted,
                         source_highlighted=source_highlighted,
                         doc1_images=doc1_highlighted if doc1_highlighted else raw_doc1_images,
                         doc2_images=doc2_highlighted if doc2_highlighted else raw_doc2_images)

if __name__ == '__main__':
    app.run(debug=True)
