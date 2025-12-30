import os
import json

from flask import Flask, render_template, jsonify, request, send_file
from flask_cors import CORS
from dotenv import load_dotenv

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}}, expose_headers=["X-Report-Path"], allow_headers=["Content-Type", "X-Report-Path"])
load_dotenv()

DEFAULT_PATH = r"\\172.20.75.5\suporte\Bruno_Terribile\Relatórios Personalizados"

def get_base_path():
    header_path = request.headers.get('X-Report-Path')

    if header_path and os.path.exists(header_path):
        return header_path

    return DEFAULT_PATH


@app.route('/')
def health():
    return render_template('index.html')


@app.route('/api/list', methods=['GET'])
def listar():
    base_path = get_base_path()
    if not os.path.exists(base_path):
        return jsonify({"error": True, "success": f"Caminho inacessível: {base_path}"})

    lista_final = []
    try:
        itens = os.listdir(base_path)
        folders = [p for p in itens if os.path.isdir(os.path.join(base_path, p))]

        for folder in folders:
            path_abs = os.path.join(base_path, folder)
            files = os.listdir(path_abs)

            xml_file = next((f for f in files if f.lower().endswith('.xml')), None)
            sql_file = next((f for f in files if f.lower().endswith('.sql')), None)

            sql_content = ""
            if sql_file:
                try:
                    with open(os.path.join(path_abs, sql_file), 'r', encoding='utf-8', errors='ignore') as f:
                        sql_content = f.read()
                except:
                    sql_content = "-- Erro ao ler arquivo SQL"

            metadata_file = os.path.join(path_abs, "metadata.json")

            title = folder.replace("_", " ")
            description = ""
            tags = []
            report_type = "R"

            if os.path.exists(metadata_file):
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    if isinstance(data, dict):
                        title = data.get("title") or title
                        tags = data.get("tags", [])
                        description = data.get("description", "")
                        report_type = data.get("type", "R")
                except Exception as e:
                    print(f"Erro ao ler metadata em {folder}: {e}")

            lista_final.append({
                "title": title,
                "type": report_type,
                "folder": folder,
                "xml": xml_file or "",
                "hasXml": xml_file is not None,
                "sql": sql_content,
                "sqlFile": sql_file or "",
                "folderPath": path_abs,
                "description": description,
                "tags": tags
            })

        return jsonify({"error": False, "data": lista_final, "currentPath": base_path})
    except Exception as e:
        return jsonify({"error": True, "success": str(e)})


@app.route('/api/save', methods=['PUT'])
def save():
    data = request.json
    base_path = get_base_path()

    old_folder_name = data.get('folder')
    report_data = data.get('report')
    new_title = report_data.get('title')

    new_folder_name = new_title

    old_folder_path = os.path.join(base_path, old_folder_name)
    new_folder_path = os.path.join(base_path, new_folder_name)

    try:
        if old_folder_name != new_folder_name:
            if os.path.exists(new_folder_path):
                return jsonify({
                    "success": False,
                    "message": "Já existe uma pasta com esse nome."
                }), 400

            os.rename(old_folder_path, new_folder_path)
            current_active_path = new_folder_path
        else:
            current_active_path = old_folder_path

        metadata_file_path = os.path.join(current_active_path, "metadata.json")

        DEFAULT_METADATA = {
            "title": "",
            "type": "R",
            "tags": [],
            "description": "",
            "folderPath": ""
        }

        if os.path.exists(metadata_file_path):
            with open(metadata_file_path, 'r', encoding='utf-8') as f:
                current_metadata = json.load(f)
        else:
            current_metadata = DEFAULT_METADATA.copy()

        current_metadata.update(report_data)
        current_metadata['folderPath'] = current_active_path

        with open(metadata_file_path, 'w', encoding='utf-8') as f:
            json.dump(current_metadata, f, indent=4, ensure_ascii=False)

        return jsonify({
            "success": True,
            "newFolder": new_folder_name
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Erro ao processar alteração: {str(e)}"
        }), 500


@app.route('/api/download/<folder>/<filename>', methods=['GET'])
def download(folder, filename):
    base_path = get_base_path()
    file_path = os.path.join(base_path, folder, filename)

    if not os.path.exists(file_path):
        return jsonify({
            "error": True,
            "message": "Arquivo não encontrado."
        }), 404

    try:
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        return jsonify({"error": True, "message": str(e)}), 500


@app.route('/api/create', methods=['POST'])
def create():
    base_path = get_base_path()

    xml_file = request.files.get('xml')
    sql_file = request.files.get('sql')

    metadata_raw = request.form.get('metadata')
    incoming_metadata = json.loads(metadata_raw) if metadata_raw else {}

    title = incoming_metadata.get('title')

    if not title:
        if xml_file:
            title = xml_file.filename.rsplit('.', 1)[0].replace("_", " ").title()
        else:
            title = "Relatorio_Sem_Titulo"

    report_type = incoming_metadata.get('type') or "R"
    description = incoming_metadata.get('description') or ""

    folder_name = title.replace(" ", "_").replace("-", "_")
    folder_path = os.path.join(base_path, folder_name)  # Usa base_path
    metadata_file_path = os.path.join(folder_path, "metadata.json")

    try:
        os.makedirs(folder_path, exist_ok=True)

        if xml_file:
            xml_file.save(os.path.join(folder_path, "config.xml"))

        if sql_file:
            sql_file.save(os.path.join(folder_path, "query.sql"))

        metadata_content = {
            "title": title,
            "type": report_type,
            "tags": incoming_metadata.get('tags') or [],
            "description": description,
            "folderPath": folder_path
        }

        with open(metadata_file_path, 'w', encoding='utf-8') as f:
            json.dump(metadata_content, f, indent=4, ensure_ascii=False)

        print(f"✅ Pasta e Metadata criados: {title} em {base_path}")

        return jsonify({
            "success": True,
            "message": "Estrutura criada com sucesso!",
            "folder": folder_name
        })

    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)