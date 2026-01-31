import os
import json
import random
import string
import re
from datetime import datetime
from flask import request, session, redirect, url_for

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

def generate_id():
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choice(chars) for _ in range(6))

def update_html_lists(map_info):
    """Dodaje nową mapę do pliku mapy.html oraz profilu gracza"""
    
    # 1. Aktualizacja /pl/mapy.html
    mapy_html_path = os.path.join(BASE_DIR, "pl/mapy.html")
    if os.path.exists(mapy_html_path):
        with open(mapy_html_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Logo to pierwsze zdjęcie
        logo_url = map_info['zdjecia'][0] if map_info['zdjecia'] else '/assets/images/tło/tło1.png'
        
        new_card = f"""
        <div class="map-card" id="map-{map_info['id']}" data-category="{map_info['typ']}" data-name="{map_info['nazwa'].lower()}">
            <img src="{logo_url}" alt="Mapa">
            <div class="map-card-content">
                <h3>{map_info['nazwa']}</h3>
                <p>{map_info['opis'][:100]}...</p>
                <div class="map-card-meta">
                    <span>Typ: <b>{map_info['typ']}</b></span>
                    <span>Wersja: <b>{map_info['wersja']}</b></span>
                    <span>Autor: <a href="/pl/profile/{map_info['autor']}.html" style="color: gold; text-decoration: none;"><b>{map_info['autor']}</b></a></span>
                    <span>Dodano: <b>{map_info['data_dodania']}</b></span>
                </div>
            </div>
            <div class="map-card-footer">
                <a href="/pl/mapy/{map_info['id']}.html" class="btn-view">ZOBACZ WIĘCEJ</a>
                <a href="{map_info['link']}" class="btn-download-small"><i class="bx bx-download"></i> POBIERZ</a>
            </div>
        </div><!-- END map-{map_info['id']} -->
        """
        
        if '<div class="maps-container">' in content:
            content = content.replace('<div class="maps-container">', f'<div class="maps-container">\n{new_card}')
            
        with open(mapy_html_path, 'w', encoding='utf-8') as f:
            f.write(content)

    # 2. Aktualizacja /pl/profile/<login>.html (Publiczny profil)
    user_profile_path = os.path.join(BASE_DIR, f"pl/profile/{map_info['autor']}.html")
    template_profile_path = os.path.join(BASE_DIR, "pl/profile/template_profil.html")
    
    author_data = {"avatar": "/assets/images/avatar_default.png", "description": "Gracz serwisu Najlepsze polskie mapy"}
    konta_dir = os.path.join(BASE_DIR, 'assets', 'konta')
    if os.path.exists(konta_dir):
        for filename in os.listdir(konta_dir):
            if filename.endswith(f"-{map_info['autor']}.json"):
                with open(os.path.join(konta_dir, filename), 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    author_data["avatar"] = data.get("avatar", author_data["avatar"])
                    author_data["description"] = data.get("description", author_data["description"])
                break

    if not os.path.exists(user_profile_path) and os.path.exists(template_profile_path):
        with open(template_profile_path, 'r', encoding='utf-8') as f:
            profile_content = f.read().replace("{{ login }}", map_info['autor'])
            profile_content = profile_content.replace("{{ avatar }}", author_data["avatar"])
            profile_content = profile_content.replace("{{ opis }}", author_data["description"])
    elif os.path.exists(user_profile_path):
        with open(user_profile_path, 'r', encoding='utf-8') as f:
            profile_content = f.read()
            profile_content = re.sub(r'class="profile-avatar" src=".*?"', f'class="profile-avatar" src="{author_data["avatar"]}"', profile_content)
            profile_content = re.sub(r'<p class="profile-desc">.*?</p>', f'<p class="profile-desc">{author_data["description"]}</p>', profile_content)
    else:
        profile_content = None

    if profile_content:
        new_profile_card = f"""
                <div class="map-card" id="map-{map_info['id']}">
                    <img src="{map_info['zdjecia'][0] if map_info['zdjecia'] else '/assets/images/tło/tło1.png'}" alt="Mapa">
                    <div class="map-card-content">
                        <h3>{map_info['nazwa']}</h3>
                        <div class="map-card-footer">
                            <a href="/pl/mapy/{map_info['id']}.html" class="btn-view">ZOBACZ</a>
                        </div>
                    </div>
                </div><!-- END map-{map_info['id']} -->
        """
        if '<!-- MAPY_START -->' in profile_content:
            profile_content = profile_content.replace('<!-- MAPY_START -->', f'<!-- MAPY_START -->\n{new_profile_card}')
        with open(user_profile_path, 'w', encoding='utf-8') as f:
            f.write(profile_content)

    # 3. Aktualizacja /pl/profil.html
    settings_profile_path = os.path.join(BASE_DIR, "pl/profil.html")
    if os.path.exists(settings_profile_path):
        with open(settings_profile_path, 'r', encoding='utf-8') as f:
            settings_content = f.read()
        
        new_settings_card = f"""
            <div class="map-card-mini" id="my-map-{map_info['id']}" style="background: rgba(0,0,0,0.8); border: 1px solid gold; border-radius: 10px; overflow: hidden; position: relative;">
                <img src="{map_info['zdjecia'][0] if map_info['zdjecia'] else '/assets/images/tło/tło1.png'}" style="width: 100%; aspect-ratio: 16/9; object-fit: cover;">
                <div style="padding: 15px;">
                    <h4 style="margin: 0; color: gold;">{map_info['nazwa']}</h4>
                    <div style="display: flex; justify-content: space-between; margin-top: 10px;">
                        <a href="/pl/mapy/{map_info['id']}.html" style="color: lime; text-decoration: none; font-size: 0.9em;">ZOBACZ</a>
                        <button onclick="deleteMap('{map_info['id']}')" style="background: #ff4444; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer; font-size: 0.8em;">USUŃ</button>
                    </div>
                </div>
            </div><!-- END my-map-{map_info['id']} -->
        """
        
        if '<div class="maps-grid"' in settings_content:
            settings_content = re.sub(r'(<div class="maps-grid"[^>]*>)', r'\1' + new_settings_card, settings_content)
            
        with open(settings_profile_path, 'w', encoding='utf-8') as f:
            f.write(settings_content)

def save_map_data(user_login, map_data, files):
    map_id = generate_id()
    
    # Tworzenie folderu na zdjęcia: /assets/mapy/<id-mapy>/
    map_images_dir = os.path.join(BASE_DIR, f"assets/mapy/{map_id}")
    if not os.path.exists(map_images_dir):
        os.makedirs(map_images_dir)
    
    zdjecia_urls = []
    # Zapisywanie plików: <numer>.png
    for i in range(1, 6):
        file_key = f'file_{i}'
        if file_key in files:
            file = files[file_key]
            if file.filename != '':
                file_path = os.path.join(map_images_dir, f"{i}.png")
                file.save(file_path)
                zdjecia_urls.append(f"/assets/mapy/{map_id}/{i}.png")
    
    # Folder na JSON użytkownika
    user_maps_dir = os.path.join(BASE_DIR, f"assets/mapy/{user_login}")
    if not os.path.exists(user_maps_dir):
        os.makedirs(user_maps_dir)
    
    json_path = os.path.join(user_maps_dir, f"{map_id}.json")
    
    map_info = {
        "id": map_id,
        "autor": user_login,
        "nazwa": map_data.get("nazwa"),
        "opis": map_data.get("opis"),
        "link": map_data.get("link"),
        "typ": map_data.get("typ"),
        "wersja": map_data.get("wersja"),
        "data_dodania": datetime.now().strftime("%d.%m.%Y"),
        "zdjecia": zdjecia_urls
    }
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(map_info, f, ensure_ascii=False, indent=4)
    
    template_path = os.path.join(BASE_DIR, "pl/mapy/template_mapa.html")
    output_html_path = os.path.join(BASE_DIR, f"pl/mapy/{map_id}.html")
    
    if os.path.exists(template_path):
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        html_content = template_content.replace("{{ nazwa_mapy }}", map_info["nazwa"])
        html_content = html_content.replace("{{ opis_mapy }}", map_info["opis"])
        html_content = html_content.replace("{{ typ_mapy }}", map_info["typ"])
        html_content = html_content.replace("{{ wersja_mapy }}", map_info["wersja"])
        html_content = html_content.replace("{{ data_dodania }}", map_info["data_dodania"])
        html_content = html_content.replace("{{ link_pobierania }}", map_info["link"])
        html_content = html_content.replace("{{ autor }}", f'<a href="/pl/profile/{map_info["autor"]}.html" style="color: gold; text-decoration: none; font-weight: bold;">{map_info["autor"]}</a>')
        
        zdjecia_html = ""
        for img in map_info["zdjecia"]:
            zdjecia_html += f'<img src="{img}" alt="Zdjęcie mapy">'
        
        if not zdjecia_html:
            zdjecia_html = '<img src="/assets/images/tło/tło1.png" alt="Zdjęcie mapy">'
            
        html_content = re.sub(r'<!-- ZDJECIA_START -->.*?<!-- ZDJECIA_END -->', f'<!-- ZDJECIA_START -->\n{zdjecia_html}\n<!-- ZDJECIA_END -->', html_content, flags=re.DOTALL)
        html_content = html_content.replace('{% for img in zdjecia %}', '').replace('{% endfor %}', '')
        
        with open(output_html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
    update_html_lists(map_info)
    return map_id

def delete_map_from_files(user_login, map_id):
    """Usuwa mapę z systemu"""
    # 1. Usuń JSON
    json_path = os.path.join(BASE_DIR, f"assets/mapy/{user_login}/{map_id}.json")
    if os.path.exists(json_path):
        os.remove(json_path)
    
    # 2. Usuń folder ze zdjęciami
    import shutil
    images_dir = os.path.join(BASE_DIR, f"assets/mapy/{map_id}")
    if os.path.exists(images_dir):
        shutil.rmtree(images_dir)

    # 3. Usuń HTML podstronę
    html_path = os.path.join(BASE_DIR, f"pl/mapy/{map_id}.html")
    if os.path.exists(html_path):
        os.remove(html_path)
        
    # 4. Usuń z listy mapy.html
    mapy_html_path = os.path.join(BASE_DIR, "pl/mapy.html")
    if os.path.exists(mapy_html_path):
        with open(mapy_html_path, 'r', encoding='utf-8') as f:
            content = f.read()
        pattern = rf'<div class="map-card" id="map-{map_id}".*?><!-- END map-{map_id} -->'
        content = re.sub(pattern, '', content, flags=re.DOTALL)
        with open(mapy_html_path, 'w', encoding='utf-8') as f:
            f.write(content)

    # 5. Usuń z profilu publicznego
    user_profile_path = os.path.join(BASE_DIR, f"pl/profile/{user_login}.html")
    if os.path.exists(user_profile_path):
        with open(user_profile_path, 'r', encoding='utf-8') as f:
            content = f.read()
        pattern = rf'<div class="map-card" id="map-{map_id}".*?><!-- END map-{map_id} -->'
        content = re.sub(pattern, '', content, flags=re.DOTALL)
        with open(user_profile_path, 'w', encoding='utf-8') as f:
            f.write(content)

    # 6. Usuń z profilu ustawień
    settings_profile_path = os.path.join(BASE_DIR, "pl/profil.html")
    if os.path.exists(settings_profile_path):
        with open(settings_profile_path, 'r', encoding='utf-8') as f:
            content = f.read()
        pattern = rf'<div class="map-card-mini" id="my-map-{map_id}".*?><!-- END my-map-{map_id} -->'
        content = re.sub(pattern, '', content, flags=re.DOTALL)
        with open(settings_profile_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    return True

def init_map_routes(app):
    @app.route('/api/dodaj-mape', methods=['POST'])
    def handle_add_map():
        if 'user' not in session:
            return json.dumps({"success": False, "message": "Musisz być zalogowany!"})
        
        data = request.form
        files = request.files
        
        map_data = {
            "nazwa": data.get('nazwa'),
            "opis": data.get('opis'),
            "link": data.get('link'),
            "typ": data.get('typ'),
            "wersja": data.get('wersja')
        }
        
        # Walidacja po stronie serwera
        file_count = int(data.get('file_count', 0))
        if file_count < 2:
            return json.dumps({"success": False, "message": "Musisz dodać minimum 2 zdjęcia!"})

        map_id = save_map_data(session['user'], map_data, files)
        return json.dumps({"success": True, "map_id": map_id})

    @app.route('/api/usun-mape/<map_id>', methods=['POST'])
    def handle_delete_map(map_id):
        if 'user' not in session:
            return json.dumps({"success": False, "message": "Musisz być zalogowany!"})
        
        result = delete_map_from_files(session['user'], map_id)
        return json.dumps({"success": result})
