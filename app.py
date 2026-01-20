import os
import json

from flask import Flask, render_template, jsonify, request, send_file
from flask_cors import CORS
from dotenv import load_dotenv
import shutil
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}}, expose_headers=["X-Report-Path"],
     allow_headers=["Content-Type", "X-Report-Path"])
load_dotenv()

DEFAULT_PATH = r"\\172.20.75.5\suporte\Bruno_Terribile\Relatórios Personalizados"
TAGS_JSON_PATH = os.path.join(os.path.dirname(__file__), 'tags.json')
CATEGORIES_JSON_PATH = os.path.join(os.path.dirname(__file__), 'categories.json')

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
    base_path = get_base_path()

    try:
        old_folder_name = request.form.get('folder')
        report_json_str = request.form.get('report')

        if not old_folder_name or not report_json_str:
            return jsonify({"success": False, "message": "Dados incompletos (folder ou report missing)."}), 400

        report_data = json.loads(report_json_str)
        new_folder_name = report_data.get('title')

        old_folder_path = os.path.join(base_path, old_folder_name)
        new_folder_path = os.path.join(base_path, new_folder_name)

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
        DEFAULT_METADATA = {"title": "", "type": "R", "tags": [], "description": "", "folderPath": ""}

        if os.path.exists(metadata_file_path):
            with open(metadata_file_path, 'r', encoding='utf-8') as f:
                current_metadata = json.load(f)
        else:
            current_metadata = DEFAULT_METADATA.copy()

        current_metadata.update(report_data)
        current_metadata['folderPath'] = current_active_path

        with open(metadata_file_path, 'w', encoding='utf-8') as f:
            json.dump(current_metadata, f, indent=4, ensure_ascii=False)

        def remove_old_files_by_extension(path, extension):
            for file in os.listdir(path):
                if file.lower().endswith(extension):
                    try:
                        os.remove(os.path.join(path, file))
                    except Exception as e:
                        print(f"Erro ao remover arquivo antigo {file}: {e}")

        xml_file = request.files.get('xml')

        if xml_file:
            remove_old_files_by_extension(current_active_path, '.xml')
            xml_file.save(os.path.join(current_active_path, xml_file.filename.title().upper()))

        sql_file = request.files.get('sql')
        if sql_file:
            remove_old_files_by_extension(current_active_path, '.sql')
            sql_file.save(os.path.join(current_active_path, "query.sql"))

        return jsonify({
            "success": True,
            "newFolder": new_folder_name
        })

    except Exception as e:
        print(f"Erro no save: {e}")
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

    try:
        # 1. Recuperar arquivos e metadados
        xml_file = request.files.get('xml')
        sql_file = request.files.get('sql')
        metadata_raw = request.form.get('metadata')
        incoming_metadata = json.loads(metadata_raw) if metadata_raw else {}

        # 2. Sanitizar o título para ser um nome de pasta seguro
        # Se não houver título no JSON, usa o nome do XML ou um padrão
        raw_title = incoming_metadata.get('title') or (xml_file.filename if xml_file else "Relatorio_Sem_Titulo")
        folder_name = secure_filename(raw_title)

        folder_path = os.path.join(base_path, folder_name)
        os.makedirs(folder_path, exist_ok=True)

        # 3. Salvar o arquivo XML (se existir)
        if xml_file:
            # Mantém o nome original sanitizado ou define um padrão
            xml_filename = secure_filename(xml_file.filename).upper()
            xml_file.save(os.path.join(folder_path, xml_filename))

        # 4. Salvar o arquivo SQL (se existir)
        if sql_file:
            sql_file.save(os.path.join(folder_path, "query.sql"))

        # 5. Criar o arquivo de metadados
        metadata_content = {
            "title": raw_title,  # Mantemos o título original (com espaços/acentos) para exibição
            "type": incoming_metadata.get('type', "R"),
            "tags": incoming_metadata.get('tags', []),
            "description": incoming_metadata.get('description', ""),
            "folderPath": folder_path
        }

        metadata_file_path = os.path.join(folder_path, "metadata.json")
        with open(metadata_file_path, 'w', encoding='utf-8') as f:
            json.dump(metadata_content, f, indent=4, ensure_ascii=False)

        return jsonify({
            "success": True,
            "message": "Estrutura criada com sucesso!",
            "folder": folder_name
        }), 201

    except json.JSONDecodeError:
        return jsonify({"success": False, "message": "Metadata JSON inválido"}), 400
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/delete-file', methods=['DELETE'])
def delete_file():
    data = request.json
    folder, filename = data.get('folder'), data.get('filename')
    base_path = get_base_path()
    file_path = os.path.join(base_path, folder, filename)

    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            return jsonify({"success": True, "message": f"Arquivo {filename} removido."})
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500
    return jsonify({"success": False, "message": "Arquivo não encontrado."}), 404


@app.route('/api/delete-report', methods=['DELETE'])
def delete_report():
    data = request.json
    folder = data.get('folder')
    base_path = get_base_path()

    if not folder:
        return jsonify({"success": False, "message": "Nome da pasta não fornecido."}), 400

    report_path = os.path.join(base_path, folder)

    if os.path.exists(report_path) and os.path.isdir(report_path):
        try:
            shutil.rmtree(report_path)
            return jsonify({
                "success": True,
                "message": f"Relatório '{folder}' excluído com sucesso."
            })
        except Exception as e:
            return jsonify({
                "success": False,
                "message": f"Erro ao excluir pasta: {str(e)}"
            }), 500

    return jsonify({"success": False, "message": "Pasta do relatório não encontrada."}), 404


@app.route('/api/tags', methods=['GET'])
def get_tags():
    try:
        if not os.path.exists(TAGS_JSON_PATH):
            return jsonify({"error": "Arquivo tags.json não encontrado"}), 404

        with open(TAGS_JSON_PATH, 'r', encoding='utf-8') as f:
            tags_data = json.load(f)

        categories_map = {}
        if os.path.exists(CATEGORIES_JSON_PATH):
            with open(CATEGORIES_JSON_PATH, 'r', encoding='utf-8') as f:
                cat_data = json.load(f)
                categories_map = {c['id']: c['name'] for c in cat_data.get('categories', [])}

        tags_com_nome = []
        for tag in tags_data.get('tags', []):
            cat_id = tag.get('category')

            cat_name = categories_map.get(cat_id, "Categoria Não Encontrada")

            tags_com_nome.append({
                "id": tag['id'],
                "name": tag['name'],
                "category": cat_name,
                "categoryId": cat_id
            })

        return jsonify({
            "tags": tags_com_nome,
            "last_id": tags_data.get('last_id', 0)
        })

    except Exception as e:
        return jsonify({"error": f"Erro interno: {str(e)}"}), 500


@app.route('/api/tags', methods=['POST'])
def create_tag():
    try:
        new_tag_data = request.json
        if not new_tag_data or 'name' not in new_tag_data or 'category_id' not in new_tag_data:
            return jsonify({"error": "Nome e ID da categoria são obrigatórios"}), 400

        category_id = int(new_tag_data['category_id'])
        category_exists = False

        if os.path.exists(CATEGORIES_JSON_PATH):
            with open(CATEGORIES_JSON_PATH, 'r', encoding='utf-8') as f:
                cat_data = json.load(f)
                category_exists = any(c['id'] == category_id for c in cat_data.get('categories', []))

        if not category_exists:
            return jsonify({"error": f"Categoria com ID {category_id} não encontrada"}), 404

        if os.path.exists(TAGS_JSON_PATH):
            with open(TAGS_JSON_PATH, 'r', encoding='utf-8') as f:
                tag_file_data = json.load(f)
        else:
            tag_file_data = {"last_id": 0, "tags": []}

        current_last_id = tag_file_data.get('last_id', 0)
        new_tag_id = current_last_id + 1

        new_tag = {
            "id": new_tag_id,
            "name": new_tag_data['name'],
            "category": category_id
        }

        tag_file_data['tags'].append(new_tag)
        tag_file_data['last_id'] = new_tag_id

        with open(TAGS_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(tag_file_data, f, indent=4, ensure_ascii=False)

        return jsonify(new_tag), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/categories', methods=['GET'])
def get_categories():
    try:
        if not os.path.exists(CATEGORIES_JSON_PATH):
            return jsonify({"categories": []})
        with open(CATEGORIES_JSON_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/categories', methods=['POST'])
def create_category():
    try:
        new_cat_data = request.json
        if not new_cat_data or 'name' not in new_cat_data:
            return jsonify({"error": "Nome da categoria obrigatório"}), 400

        if os.path.exists(CATEGORIES_JSON_PATH):
            with open(CATEGORIES_JSON_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = {"last_id": 0, "categories": []}

        current_last_id = data.get('last_id', max([c['id'] for c in data['categories']], default=0))
        next_id = current_last_id + 1

        new_category = {
            "id": next_id,
            "name": new_cat_data['name']
        }

        data['categories'].append(new_category)
        data['last_id'] = next_id

        with open(CATEGORIES_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        return jsonify(new_category), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)