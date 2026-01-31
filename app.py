import os
import importlib.util
import glob
import sys
from flask import Flask, send_from_directory, session, render_template_string

app = Flask(__name__, static_folder='assets')
app.secret_key = 'super-tajny-klucz-manus'

funkcje_folder = os.path.join(os.path.dirname(__file__), 'assets', 'Funkcje')
for filepath in glob.glob(os.path.join(funkcje_folder, '*.py')):
    module_name = os.path.splitext(os.path.basename(filepath))[0]
    spec = importlib.util.spec_from_file_location(module_name, filepath)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    globals()[module_name] = module
    
    if hasattr(module, 'init_auth_routes'):
        module.init_auth_routes(app)
    if hasattr(module, 'init_map_routes'):
        module.init_map_routes(app)

@app.route('/')
def index():
    return send_from_directory('.', 'pl.html')

@app.route('/<path:path>')
def static_proxy(path):
    if path.endswith('.html'):
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            user = session.get('user')
            return render_template_string(content, user=user)
    return send_from_directory('.', path)

if __name__ == '__main__':
    app.run(debug=True, port=5500)
