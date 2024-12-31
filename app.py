import os
import requests
import time
from bs4 import BeautifulSoup
from flask import Flask, render_template, request
from whoosh.index import create_in
from whoosh.fields import Schema, TEXT, ID
from whoosh.qparser import QueryParser
import urllib3

# Désactiver les avertissements SSL si vous ne voulez pas les voir
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Créer le dossier d'index si nécessaire
index_dir = "web_index"
if not os.path.exists(index_dir):
    os.makedirs(index_dir)

# Définir un schéma pour l'index
schema = Schema(url=ID(stored=True), content=TEXT(stored=True))

# Créer un index
ix = create_in(index_dir, schema)

# Fonction pour explorer une page web et récupérer son contenu
def crawl_page(url):
    # Ajouter un délai entre les requêtes pour ne pas surcharger les serveurs
    time.sleep(2)  # Délai de 2 secondes entre les requêtes

    # Utiliser un User-Agent pour imiter un navigateur
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers, verify=False, timeout=10)  # Délai de 10 secondes pour la requête
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            text = soup.get_text()  # Extraire le texte brut de la page
            return text
        else:
            print(f"Erreur HTTP {response.status_code} pour l'URL : {url}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de l'accès à {url}: {e}")
        return None

# Fonction pour ajouter une page à l'index
def add_page_to_index(url, content):
    writer = ix.writer()
    writer.add_document(url=url, content=content)
    writer.commit()

# Initialiser Flask
app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def search():
    if request.method == "POST":
        query = request.form["query"]
        results = []
        
        # Rechercher dans l'index
        with ix.searcher() as searcher:
            query_parser = QueryParser("content", ix.schema)
            query_obj = query_parser.parse(query)
            whoosh_results = searcher.search(query_obj)
            
            # Convertir les résultats en une liste de dictionnaires
            for hit in whoosh_results:
                results.append({
                    "url": hit["url"],
                    "content": hit["content"]
                })
        
        return render_template("search_results.html", results=results)
    
    return render_template("index.html")

@app.route("/indexation", methods=["GET"])
def indexation():
    return render_template("indexation.html")

@app.route("/crawl", methods=["POST"])
def crawl():
    url = request.form["url"]
    
    # Explorer la page et ajouter son contenu à l'index
    page_content = crawl_page(url)
    if page_content:
        add_page_to_index(url, page_content)
        return f"Page {url} ajoutée à l'index !"
    return f"Erreur lors de l'exploration de la page {url}."

if __name__ == "__main__":
    app.run(debug=True)
