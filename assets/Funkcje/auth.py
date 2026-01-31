import os
import json
import hashlib
from datetime import datetime
from flask import request, session, redirect, url_for, render_template_string

# Ścieżka do folderu z kontami
KONTA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'konta')

def hash_password(password):
    """Szyfrowanie hasła za pomocą SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, email, password):
    """Rejestracja nowego użytkownika."""
    if not username or not email or not password:
        return "Wszystkie pola są wymagane!"

    # Sprawdzenie czy użytkownik już istnieje
    for filename in os.listdir(KONTA_DIR):
        if filename.endswith('.json'):
            with open(os.path.join(KONTA_DIR, filename), 'r', encoding='utf-8') as f:
                data = json.load(f)
                if data.get('username') == username:
                    return "Taki nick już istnieje!"
                if data.get('email') == email:
                    return "Dany adres email już istnieje!"

    # Tworzenie pliku JSON
    now = datetime.now()
    # Format: <Godzina-Minuta/sekunda/data>-<login>.json
    # Uwaga: "/" w nazwie pliku jest niedozwolone, użyję "-" lub "."
    timestamp = now.strftime("%H-%M-%S-%d-%m-%Y")
    filename = f"{timestamp}-{username}.json"
    filepath = os.path.join(KONTA_DIR, filename)

    user_data = {
        "username": username,
        "email": email,
        "password": hash_password(password),
        "created_at": now.isoformat()
    }

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(user_data, f, indent=4, ensure_ascii=False)

    return True

def login_user(username, password):
    """Logowanie użytkownika."""
    hashed_pw = hash_password(password)
    for filename in os.listdir(KONTA_DIR):
        if filename.endswith('.json'):
            with open(os.path.join(KONTA_DIR, filename), 'r', encoding='utf-8') as f:
                data = json.load(f)
                if data.get('username') == username and data.get('password') == hashed_pw:
                    session['user'] = username
                    return True
    return "Nieprawidłowy login lub hasło!"

def init_auth_routes(app):
    """Inicjalizacja tras Flask dla autoryzacji."""
    
    @app.route('/register', methods=['POST'])
    def handle_register():
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        result = register_user(username, email, password)
        if result is True:
            return json.dumps({"success": True})
        else:
            return json.dumps({"success": False, "message": result})

    @app.route('/login', methods=['POST'])
    def handle_login():
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        result = login_user(username, password)
        if result is True:
            return json.dumps({"success": True})
        else:
            return json.dumps({"success": False, "message": result})

    @app.route('/logout')
    def handle_logout():
        session.pop('user', None)
        return redirect('/pl.html')

    @app.route('/api/update-profile', methods=['POST'])
    def handle_update_profile():
        if 'user' not in session:
            return json.dumps({"success": False, "message": "Musisz być zalogowany!"})
        
        old_username = session['user']
        new_nickname = request.form.get('nickname')
        description = request.form.get('description')
        logo_file = request.files.get('logo')
        
        # Znajdź plik użytkownika
        old_filename = None
        for filename in os.listdir(KONTA_DIR):
            if filename.endswith(f"-{old_username}.json"):
                old_filename = filename
                break
        
        if not old_filename:
            return json.dumps({"success": False, "message": "Nie znaleziono profilu!"})
            
        user_file_path = os.path.join(KONTA_DIR, old_filename)
        with open(user_file_path, 'r', encoding='utf-8') as f:
            user_data = json.load(f)
            
        # Aktualizacja danych
        if new_nickname and new_nickname != old_username:
            # Sprawdź czy nowy nick już istnieje
            for filename in os.listdir(KONTA_DIR):
                if filename.endswith(f"-{new_nickname}.json"):
                    return json.dumps({"success": False, "message": "Ten nick jest już zajęty!"})
            
            user_data['username'] = new_nickname
            user_data['nickname'] = new_nickname
            
            # Zmień nazwę pliku
            new_filename = old_filename.replace(f"-{old_username}.json", f"-{new_nickname}.json")
            new_file_path = os.path.join(KONTA_DIR, new_filename)
            
            # Zapisz pod nową nazwą i usuń stary plik
            with open(new_file_path, 'w', encoding='utf-8') as f:
                json.dump(user_data, f, indent=4, ensure_ascii=False)
            os.remove(user_file_path)
            
            # Aktualizuj sesję
            session['user'] = new_nickname
            user_file_path = new_file_path
            current_username = new_nickname
        else:
            current_username = old_username
            if new_nickname:
                user_data['nickname'] = new_nickname

        if description is not None:
            user_data['description'] = description
            
        # Obsługa logo
        if logo_file:
            avatar_dir = os.path.join(os.path.dirname(KONTA_DIR), 'images', 'avatars')
            if not os.path.exists(avatar_dir):
                os.makedirs(avatar_dir)
            
            ext = os.path.splitext(logo_file.filename)[1]
            avatar_filename = f"{current_username}{ext}"
            avatar_path = os.path.join(avatar_dir, avatar_filename)
            logo_file.save(avatar_path)
            user_data['avatar'] = f"/assets/images/avatars/{avatar_filename}"
            
        with open(user_file_path, 'w', encoding='utf-8') as f:
            json.dump(user_data, f, indent=4, ensure_ascii=False)
            
        # Aktualizuj plik profilu publicznego jeśli istnieje
        public_profile_path = os.path.join(os.path.dirname(KONTA_DIR), 'pl', 'profile', f"{current_username}.html")
        if os.path.exists(public_profile_path):
            with open(public_profile_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Aktualizuj avatar i opis
            avatar_url = user_data.get('avatar', '/assets/images/avatar_default.png')
            desc = user_data.get('description', 'Gracz serwisu Najlepsze polskie mapy')
            
            content = re.sub(r'class="profile-avatar" src=".*?"', f'class="profile-avatar" src="{avatar_url}"', content)
            content = re.sub(r'<p class="profile-desc">.*?</p>', f'<p class="profile-desc">{desc}</p>', content)
            
            # Jeśli nick się zmienił, zmień też nagłówek i tytuł
            if new_nickname and new_nickname != old_username:
                content = content.replace(f"<h1>{old_username}</h1>", f"<h1>{new_nickname}</h1>")
                content = content.replace(f"<title>Profil gracza {old_username}", f"<title>Profil gracza {new_nickname}")
                
                # Zmień nazwę pliku profilu publicznego
                new_public_profile_path = os.path.join(os.path.dirname(KONTA_DIR), 'pl', 'profile', f"{new_nickname}.html")
                with open(new_public_profile_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                os.remove(public_profile_path)
            else:
                with open(public_profile_path, 'w', encoding='utf-8') as f:
                    f.write(content)

        return json.dumps({"success": True})

    @app.route('/api/get-profile')
    def handle_get_profile():
        if 'user' not in session:
            return json.dumps({"success": False})
            
        username = session['user']
        for filename in os.listdir(KONTA_DIR):
            if filename.endswith(f"-{username}.json"):
                with open(os.path.join(KONTA_DIR, filename), 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Nie wysyłaj hasła
                    data.pop('password', None)
                    return json.dumps({"success": True, "data": data})
        return json.dumps({"success": False})
