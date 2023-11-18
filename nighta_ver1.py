# 検索キーワードがdatabaseに含まればよい
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from SPARQLWrapper import SPARQLWrapper, JSON

keywords = ["cyber security"]  # 検索キーワード

endpoint_url = "http://dbpedia.org/sparql"
def fetch_data_from_dbpedia(endpoint_url, keyword):
    keyword = keyword.replace("'", "\\'")  # シングルクォートをエスケープする
    
    query = f"""
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

    SELECT ?resource
    WHERE {{
        ?resource rdfs:label ?label .
        FILTER (regex(?label, "{keyword}", "i"))
        FILTER (STRSTARTS(STR(?resource), "http://dbpedia.org/resource/"))
        FILTER (!STRSTARTS(STR(?resource), "http://dbpedia.org/resource/Category:"))
    }}
    LIMIT 5
    """
    
    sparql = SPARQLWrapper(endpoint_url)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    return results["results"]["bindings"]

data_from_dbpedia = []
for keyword in keywords:
    for data in fetch_data_from_dbpedia(endpoint_url, keyword):
        data['abstract']={}
        data["related_keyword"] = []
        
        resource_name = str(data["resource"]["value"]).split("resource/")[-1]
        data["resource"]["name"] = resource_name
        
        query = f"""
        PREFIX dbo: <http://dbpedia.org/ontology/>

        SELECT ?abstract
        WHERE {{
            <http://dbpedia.org/resource/{resource_name}> dbo:abstract ?abstract.
        }}
        """
        sparql = SPARQLWrapper(endpoint_url)
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        abstract_info = sparql.query().convert()
        if 'results' in abstract_info:
            if 'bindings' in abstract_info['results']:
                for item in abstract_info['results']['bindings']:
                    if 'abstract' in item:
                        if 'xml:lang' in item['abstract'] and item['abstract']['xml:lang'] == 'en':
                            abstract_value = item['abstract']['value']
                            abstract_type = item['abstract']['type']
                            data['abstract']['type'] = abstract_type
                            data['abstract']['value'] = abstract_value
                            print(data["resource"]["name"], "abstract")
        query = f"""
        PREFIX dbo: <http://dbpedia.org/ontology/>
        PREFIX dbc: <http://dbpedia.org/resource/Category/>

        SELECT ?abstract ?wikiLink
        WHERE {{
            <http://dbpedia.org/resource/{resource_name}> dbo:wikiPageWikiLink ?link.
            OPTIONAL {{
                ?link dbo:abstract ?abstract.
            }}
            FILTER(LANG(?abstract) = 'en')
            BIND(?link AS ?wikiLink) 
        }}
        LIMIT 5
        """
        sparql = SPARQLWrapper(endpoint_url)
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        related_keyword_info = sparql.query().convert()
        
        for item in related_keyword_info['results']["bindings"]:
            #print(item)
            if 'abstract' and 'wikiLink' in item:
                abstract_value = item['abstract']['value']
                abstract_type = item['abstract']['type']
                wikilink_type = item['wikiLink']['type']
                wikilink_value = item['wikiLink']['value']
                keyword_name = str(wikilink_value).split("resource/")[-1]
                data_item = {"name": keyword_name, "abstract": {"type": abstract_type, "value": abstract_value}, "wikilink": {"type": wikilink_type, "value": wikilink_value}}
                data["related_keyword"].append(data_item)

        data_from_dbpedia.append(data)
               

# data{subject:{name, abstract, link}, \
    #   related_keyword:{{name, abstract, link}, \
    #                   {}, ...}}


class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # データを返す
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data_from_dbpedia).encode('utf-8'))

# サーバー起動
def run_server():
    port = 8000
    server_address = ('', port)
    httpd = HTTPServer(server_address, RequestHandler)
    print(f'Starting server on port {port}')
    httpd.serve_forever()

if __name__ == '__main__':
    run_server()


"""トリプル形式（database内の記述と完全一致しないとダメ）
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX dbo: <http://dbpedia.org/ontology/>

SELECT ?subject ?predicate ?object
WHERE {
    ?subject ?predicate ?object .
    ?subject dcterms:subject/skos:broader{0,0} <http://dbpedia.org/resource/Category:Computer_security> .
    ?object dcterms:subject/skos:broader{0,4} <http://dbpedia.org/resource/Category:Computer_security> .
}
    """
    
"""一つのキーワード（database内の記述と完全一致しないとダメ）
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX dbo: <http://dbpedia.org/ontology/>

SELECT ?subject
WHERE {
    ?subject dcterms:subject/skos:broader{0,0} <http://dbpedia.org/resource/Category:Computer_security> .
}
    
    """

"""キーワード検索（入力文が含まれたラベルと取ってくる）
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?resource
WHERE {
  ?resource rdfs:label ?label .
  FILTER (regex(?label, "computer security", "i"))
}
LIMIT 100 
"""
    
"""abstractの抽出
PREFIX dbo: <http://dbpedia.org/ontology/>

SELECT ?abstract
WHERE {
  <http://dbpedia.org/resource/Zero-knowledge_service> dbo:abstract ?abstract.
  FILTER(LANG(?abstract) = 'en')
}
    """
    
    
"""関連キーワードのabstractとリンクの抽出
PREFIX dbo: <http://dbpedia.org/ontology/>
PREFIX dbc: <http://dbpedia.org/resource/Category/>

SELECT ?abstract ?wikiLink
WHERE {
  <http://dbpedia.org/resource/Zero-knowledge_service> dbo:wikiPageWikiLink ?link.
  OPTIONAL {
    ?link dbo:abstract ?abstract.
  }
  FILTER(LANG(?abstract) = 'en')
  BIND(?link AS ?wikiLink) 
}
    """
    
    
    
"""
query = f
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX dbo: <http://dbpedia.org/ontology/>

SELECT ?subject
WHERE {{
    ?subject dcterms:subject/skos:broader{{0,0}} <http://dbpedia.org/resource/Category:{keyword}> . 
}}

"""