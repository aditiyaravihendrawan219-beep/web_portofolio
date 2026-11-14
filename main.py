import os
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, url_for, session
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "KunciRahasiaRongawi2026")

# Satpam 1: Ekstensi file gambar yang diizinkan untuk mencegah upload file berbahaya
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Konfigurasi folder upload gambar
UPLOAD_FOLDER = os.path.join('static', 'assets')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def get_konten():
    res = supabase.table("konten_web").select("*").eq("id", 1).execute()
    return res.data[0] if res.data else {}

# ==================== HALAMAN PUBLIK ====================

@app.route('/')
def index():
    res_proyek = supabase.table("proyek").select("*").order("id").execute()
    proyek_list = res_proyek.data if res_proyek.data else []
    konten = get_konten()
    return render_template('indeks.html', proyek=proyek_list, konten=konten)

@app.route('/about')
def about():
    konten = get_konten()
    res_exp = supabase.table("pengalaman").select("*").order("urutan").order("id").execute()
    pengalaman_list = res_exp.data if res_exp.data else []
    return render_template('about.html', konten=konten, pengalaman=pengalaman_list)

# ==================== AUTENTIKASI ADMIN (DENGAN SATPAM HASHING) ====================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        try:
            response = supabase.table("admin").select("*").eq("username", username).execute()
            if response.data and len(response.data) > 0:
                admin_row = response.data[0]
                db_password = admin_row.get('password', '')
                
                # Cek apakah password di database sudah di-hash atau masih teks biasa
                is_valid = False
                if db_password.startswith('pbkdf2:sha256:') or db_password.startswith('scrypt:'):
                    is_valid = check_password_hash(db_password, password)
                else:
                    # Fallback otomatis: jika masih teks biasa, langsung amankan dan update ke database dengan hash!
                    if db_password == password:
                        hashed_pw = generate_password_hash(password)
                        supabase.table("admin").update({"password": hashed_pw}).eq("username", username).execute()
                        is_valid = True

                if is_valid:
                    session['user'] = username
                    return redirect(url_for('admin_dashboard'))
            
            return render_template('login.html', error="Username atau Password salah, Yang Mulia!")
        except Exception as e:
            return render_template('login.html', error=f"Error Database: {str(e)}")
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

# ==================== DASHBOARD ADMIN (DILINDUNGI SESSION) ====================

@app.route('/admin')
def admin_dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
        
    res_proyek = supabase.table("proyek").select("*").order("id").execute()
    proyek_list = res_proyek.data if res_proyek.data else []
    
    res_exp = supabase.table("pengalaman").select("*").order("urutan").order("id").execute()
    pengalaman_list = res_exp.data if res_exp.data else []
    
    konten = get_konten()
    return render_template('admin.html', proyek=proyek_list, pengalaman=pengalaman_list, konten=konten)

# --- CRUD 1: KONTEN PROFIL & PEMBUKA ABOUT (DENGAN FILTER UPLOAD) ---

@app.route('/admin/update-konten', methods=['POST'])
def update_konten():
    if 'user' not in session:
        return redirect(url_for('login'))
        
    konten_lama = get_konten()
    nama_foto = konten_lama.get('foto_profil', 'fotoku.png')
    
    file_foto = request.files.get('file_foto')
    if file_foto and file_foto.filename != '':
        if allowed_file(file_foto.filename):
            filename = secure_filename(file_foto.filename)
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            file_foto.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            nama_foto = filename

    data_update = {"foto_profil": nama_foto}
    if request.form.get('profil_singkat') is not None:
        data_update["profil_singkat"] = request.form.get('profil_singkat')
    if request.form.get('about_intro') is not None:
        data_update["about_intro"] = request.form.get('about_intro')

    supabase.table("konten_web").update(data_update).eq("id", 1).execute()
    return redirect(url_for('admin_dashboard'))

# --- CRUD 2: PROJECT SHOWCASE ---

@app.route('/admin/tambah', methods=['POST'])
def tambah_proyek():
    if 'user' not in session:
        return redirect(url_for('login'))
        
    nama_gambar = request.form.get('gambar', '')
    file_gambar = request.files.get('file_gambar')
    if file_gambar and file_gambar.filename != '':
        if allowed_file(file_gambar.filename):
            filename = secure_filename(file_gambar.filename)
            folder_proyek = os.path.join(app.config['UPLOAD_FOLDER'], 'proyek')
            os.makedirs(folder_proyek, exist_ok=True)
            file_gambar.save(os.path.join(folder_proyek, filename))
            nama_gambar = filename

    supabase.table("proyek").insert({
        "judul": request.form.get('judul'),
        "deskripsi": request.form.get('deskripsi'),
        "link_drive": request.form.get('link_drive'),
        "gambar": nama_gambar
    }).execute()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/edit/<int:id>', methods=['POST'])
def edit_proyek(id):
    if 'user' not in session:
        return redirect(url_for('login'))
        
    nama_gambar = request.form.get('gambar', '')
    file_gambar = request.files.get('file_gambar')
    if file_gambar and file_gambar.filename != '':
        if allowed_file(file_gambar.filename):
            filename = secure_filename(file_gambar.filename)
            folder_proyek = os.path.join(app.config['UPLOAD_FOLDER'], 'proyek')
            os.makedirs(folder_proyek, exist_ok=True)
            file_gambar.save(os.path.join(folder_proyek, filename))
            nama_gambar = filename

    supabase.table("proyek").update({
        "judul": request.form.get('judul'),
        "deskripsi": request.form.get('deskripsi'),
        "link_drive": request.form.get('link_drive'),
        "gambar": nama_gambar
    }).eq("id", id).execute()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/hapus/<int:id>')
def hapus_proyek(id):
    if 'user' not in session:
        return redirect(url_for('login'))
        
    supabase.table("proyek").delete().eq("id", id).execute()
    return redirect(url_for('admin_dashboard'))

# --- CRUD 3: RIWAYAT PENGALAMAN ---

@app.route('/admin/pengalaman/tambah', methods=['POST'])
def tambah_pengalaman():
    if 'user' not in session:
        return redirect(url_for('login'))
        
    supabase.table("pengalaman").insert({
        "kategori": request.form.get('kategori'),
        "isi": request.form.get('isi'),
        "urutan": int(request.form.get('urutan') or 1)
    }).execute()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/pengalaman/edit/<int:id>', methods=['POST'])
def edit_pengalaman(id):
    if 'user' not in session:
        return redirect(url_for('login'))
        
    supabase.table("pengalaman").update({
        "kategori": request.form.get('kategori'),
        "isi": request.form.get('isi'),
        "urutan": int(request.form.get('urutan') or 1)
    }).eq("id", id).execute()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/pengalaman/hapus/<int:id>')
def hapus_pengalaman(id):
    if 'user' not in session:
        return redirect(url_for('login'))
        
    supabase.table("pengalaman").delete().eq("id", id).execute()
    return redirect(url_for('admin_dashboard'))

# --- RUTE GANTI PASSWORD ---
@app.route('/ganti-password', methods=['GET', 'POST'])
def ganti_password():
    error = None
    success = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password_lama = request.form.get('password_lama', '').strip()
        password_baru = request.form.get('password_baru', '').strip()
        
        try:
            response = supabase.table("admin").select("*").eq("username", username).execute()
            if response.data and len(response.data) > 0:
                admin_row = response.data[0]
                db_password = admin_row.get('password', '')
                
                # Validasi password lama
                is_valid = False
                if db_password.startswith('pbkdf2:sha256:') or db_password.startswith('scrypt:'):
                    is_valid = check_password_hash(db_password, password_lama)
                else:
                    is_valid = (db_password == password_lama)

                if is_valid:
                    # Update dengan password baru yang di-hash
                    hashed_baru = generate_password_hash(password_baru)
                    supabase.table("admin").update({"password": hashed_baru}).eq("username", username).execute()
                    success = "Password berhasil diubah, Yang Mulia! Silakan login kembali."
                else:
                    error = "Username atau Password Lama salah!"
            else:
                error = "Username tidak ditemukan di database!"
        except Exception as e:
            error = f"Error Database: {str(e)}"
            
    return render_template('ganti_password.html', error=error, success=success)

if __name__ == '__main__':
    app.run(debug=True)