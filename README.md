# API de Gerenciamento de Relatórios Personalizados 📈

Esta API Flask foi desenvolvida para oferecer uma solução robusta e flexível para o gerenciamento de relatórios personalizados. Ela permite que desenvolvedores e usuários criem, visualizem, baixem, salvem e excluam relatórios que podem incluir dados em formatos XML, SQL e metadados JSON. Além disso, a plataforma organiza os relatórios através de um sistema de categorias e tags.

## Tecnologias Usadas

*   **Linguagem:** Python
*   **Frameworks:**
    *   Flask: Microframework web para a construção da API.
    *   Flask-CORS: Extensão para habilitar o Cross-Origin Resource Sharing (CORS).

## Como Instalar e Rodar

Siga os passos abaixo para configurar e executar o projeto localmente:

1.  **Clone o repositório:**
    ```bash
    git clone https://github.com/Bruno2202/report-repository-api.git
    cd report-repository-api
    ```

2.  **Crie e ative um ambiente virtual:**
    ```bash
    python -m venv venv
    # No Windows:
    .\venv\Scripts\activate
    # No macOS/Linux:
    source venv/bin/activate
    ```

3.  **Instale as dependências:**
    Crie um arquivo `requirements.txt` com as dependências (e.g., `Flask`, `Flask-CORS`) e instale-as:
    ```bash
    pip install -r requirements.txt
    ```
    (Exemplo de `requirements.txt` esperado: `Flask`, `Flask-CORS`)

4.  **Configure as variáveis de ambiente:**
    A aplicação carrega configurações de variáveis de ambiente. Crie um arquivo `.env` na raiz do projeto ou configure-as diretamente no seu ambiente. Exemplo:
    ```
    FLASK_APP=app.py
    FLASK_ENV=development
    ```

5.  **Inicialize o armazenamento de dados (opcional):**
    Crie os arquivos `categories.json` e `tags.json` na raiz do projeto, caso não existam, com o formato inicial esperado:
    *   `categories.json`: `{"last_id": 0, "categories": []}`
    *   `tags.json`: `{"last_id": 0, "tags": []}`
    Crie também uma pasta `reports/` para armazenar os arquivos dos relatórios.

6.  **Execute a aplicação:**
    ```bash
    flask run
    ```
    A API estará acessível em `http://127.0.0.1:5000` por padrão.

## Estrutura do Projeto

*   `app.py`: O coração da aplicação Flask, definindo os endpoints da API para gerenciamento de relatórios (listar, criar, salvar, baixar, excluir), tags e categorias.
*   `categories.json`: Arquivo JSON que armazena a lista de categorias disponíveis para os relatórios, incluindo seus IDs e nomes.
*   `tags.json`: Arquivo JSON que contém a lista de tags, com seus IDs, nomes e referências a categorias.
*   `templates/`: Diretório que armazena os modelos HTML.
    *   `templates/index.html`: A página de saúde (health check) da API, indicando que o serviço está operacional.
*   `reports/` (inferido): Diretório para armazenar os arquivos XML, SQL e JSON de metadados de cada relatório personalizado.

## Como Contribuir

Agradecemos o seu interesse em contribuir para este projeto! Siga estas diretrizes para submeter suas contribuições:

1.  Faça um "fork" do repositório.
2.  Clone o seu "fork" para a sua máquina local.
3.  Crie uma nova "branch" para suas alterações: `git checkout -b minha-nova-feature`.
4.  Faça suas alterações e certifique-se de que o código passa por todos os testes (se houver).
5.  Commit suas alterações com mensagens claras e descritivas.
6.  Envie suas alterações para o seu "fork": `git push origin minha-nova-feature`.
7.  Abra um "Pull Request" (PR) para a "branch" principal deste repositório, descrevendo suas mudanças e o problema que elas resolvem.

## Licença

A licença deste projeto não foi especificada.

---

*Este README foi gerado automaticamente pelo README.ai.*

Acesse o repositório do README.ai em: [https://github.com/Bruno2202/readme-ai](https://github.com/Bruno2202/readme-ai)
