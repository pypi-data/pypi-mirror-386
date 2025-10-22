import logging
import os
import shutil
import zipfile
import io
from pathlib import Path

from hexss import check_packages
from hexss.path import iterdir, list_drives, last_component

check_packages('Flask', auto_install=True, venv_only=False)

from hexss import get_hostname
from hexss.config import load_config
from hexss.network import get_all_ipv4, close_port
from flask import Flask, render_template, request, send_file, redirect, url_for, jsonify, abort

app = Flask(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
ROOT_DIR = Path("/")


@app.route('/')
def root():
    # return render_template('file_manager2.html')
    return redirect(url_for('path'))


@app.route('/api/get_list_dir')
def listdir():
    try:
        path = ROOT_DIR
        path = path / request.args.get('path', default='', type=str)
        listdir = {
            'path': str(path),
            'folder': [],
            'file': []
        }
        for dir in os.listdir(path):
            if os.path.isdir(path / dir):
                listdir['folder'].append(dir)
            else:
                listdir['file'].append(dir)

        return jsonify({
            'success': True,
            'listdir': listdir
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/iterdir')
def api_path():
    """
    /api/iterdir?p=//it   # UNC host root
    /api/iterdir?p=//it/s # UNC share root
    /api/iterdir?p=C:/    # Local drive
    """
    p = request.args.get('p', default='', type=str).strip()
    response = {
        'success': True,
        'children': []
    }
    if p == '':
        response['children'] = [
            {
                'path': entry['path'],
                'name': f"{last_component(Path(entry['path']))} <{entry['type']}>",
                'type': 'dir'
            } for entry in list_drives()
        ]
        return jsonify(response)

    p = Path(p)
    try:
        children = [
            {
                'path': child.as_posix(),
                'name': last_component(child),
                'type': 'file' if child.is_file() else 'dir',
            } for child in iterdir(p)
        ]
        response['children'] = children
    except Exception as e:
        response['success'] = False
        response['error'] = str(e)

    return jsonify(response)


@app.route('/path/')
@app.route('/path/<path:subpath>')
def path(subpath=''):
    current_path = os.path.normpath(os.path.join(ROOT_DIR, subpath)).replace(os.sep, '/')

    if not os.path.exists(current_path):
        abort(404, description="Path does not exist")

    if os.path.isfile(current_path):
        return send_file(current_path)

    files = []
    directories = []

    for item in os.scandir(current_path):
        if item.is_file():
            files.append(item.name)
        elif item.is_dir():
            directories.append(item.name)

    rel_path = os.path.relpath(current_path, ROOT_DIR).replace("\\", "/")
    parts = rel_path.split("/") if rel_path != "." else []
    breadcrumbs = []
    path_accum = ""
    for part in parts:
        path_accum = f"{path_accum}/{part}" if path_accum else part
        breadcrumbs.append((part, path_accum))

    return render_template('file_manager.html',
                           files=files,
                           directories=directories,
                           current_path=rel_path,
                           breadcrumbs=breadcrumbs)


@app.route('/create_folder', methods=['POST'])
def create_folder():
    folder_path = os.path.normpath(os.path.join(ROOT_DIR, request.form['path']))
    try:
        os.makedirs(folder_path, exist_ok=True)
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, error=str(e)), 500


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    if file:
        file_path = os.path.normpath(os.path.join(ROOT_DIR, request.form['current_path'], file.filename))
        file.save(file_path)
    return redirect(url_for('path', subpath=request.form['current_path']))


@app.route('/delete', methods=['POST'])
def delete_item():
    item_path = os.path.normpath(os.path.join(ROOT_DIR, request.form['path']))
    try:
        if os.path.isfile(item_path):
            os.remove(item_path)
        elif os.path.isdir(item_path):
            shutil.rmtree(item_path)
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, error=str(e)), 500


@app.route('/rename', methods=['POST'])
def rename_item():
    old_path = os.path.normpath(os.path.join(ROOT_DIR, request.form['old_path']))
    new_path = os.path.normpath(os.path.join(ROOT_DIR, request.form['new_path']))
    try:
        os.rename(old_path, new_path)
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, error=str(e)), 500


@app.route('/download', methods=['GET'])  # error if download in directories
def download_item():
    item_path = os.path.normpath(os.path.join(ROOT_DIR, request.args.get('path')))
    if os.path.isfile(item_path):
        return send_file(item_path, as_attachment=True)
    elif os.path.isdir(item_path):
        memory_file = io.BytesIO()
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, _, files in os.walk(item_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, item_path)
                    zf.write(file_path, arcname)
        memory_file.seek(0)
        return send_file(memory_file, mimetype='application/zip', as_attachment=True,
                         download_name=os.path.basename(item_path) + '.zip')
    return jsonify(success=False, message="Item not found"), 404


@app.route('/edit', methods=['GET', 'POST'])
def edit_file():
    file_path = os.path.normpath(os.path.join(ROOT_DIR, request.args.get('path')))
    if request.method == 'POST':
        content = request.form.get('content')
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return jsonify(success=True)
        except Exception as e:
            return jsonify(success=False, error=str(e)), 500
    else:
        if os.path.isfile(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return jsonify(success=True, content=content)
            except Exception as e:
                return jsonify(success=False, error=str(e)), 500
        else:
            return jsonify(success=True, content='')


@app.route('/extract_file', methods=['POST'])
def extract_file():
    zip_path = os.path.normpath(os.path.join(ROOT_DIR, request.form['path']))
    folder_name = request.form.get('folder_name', 'extracted_files')
    extract_path = os.path.normpath(os.path.join(os.path.dirname(zip_path), folder_name))

    try:
        os.makedirs(extract_path, exist_ok=True)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, error=str(e)), 500


def run():
    config = load_config('file_manager_server', {
        "ipv4": '0.0.0.0',
        'port': 2001
    })

    close_port(config['ipv4'], config['port'], verbose=False)
    ipv4 = config['ipv4']
    port = config['port']
    if ipv4 == '0.0.0.0':
        for ipv4_ in {'127.0.0.1', 'localhost', *get_all_ipv4(), get_hostname()}:
            logging.info(f"Running on http://{ipv4_}:{port}")
    else:
        logging.info(f"Running on http://{ipv4}:{port}")
    app.run(config['ipv4'], config['port'], debug=True, use_reloader=False)


if __name__ == '__main__':
    run()
