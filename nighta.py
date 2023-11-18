from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from SPARQLWrapper import SPARQLWrapper, JSON

related_keywords = ["Computer_security"]  # 検索キーワード

endpoint_url = "http://dbpedia.org/sparql"
def fetch_data_from_dbpedia(endpoint_url, keyword):
    
    query = f"""
    PREFIX dcterms: <http://purl.org/dc/terms/>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    PREFIX dbo: <http://dbpedia.org/ontology/>

    SELECT ?subject
    WHERE {{
        ?subject dcterms:subject/skos:broader{{0,0}} <http://dbpedia.org/resource/Category:{keyword}> . 
    }}
    """
    
    sparql = SPARQLWrapper(endpoint_url)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    return results["results"]["bindings"]

# キーワードに関連する情報をDBpediaから取得
data_from_dbpedia = []
for keyword in related_keywords:
    #data_from_dbpedia.extend(fetch_data_from_dbpedia(keyword))
    for data in fetch_data_from_dbpedia(endpoint_url, keyword):
        data["abstract"] = {}
        
        subject_name = str(data["subject"]["value"]).split("resource/")[-1]
        data["subject"]["name"] = subject_name
        
        query = f"""
        PREFIX dbo: <http://dbpedia.org/ontology/>

        SELECT ?abstract
        WHERE {{
            <http://dbpedia.org/resource/{subject_name}> dbo:abstract ?abstract.
            FILTER(LANG(?abstract) = 'en')
        }}
        """
        sparql = SPARQLWrapper(endpoint_url)
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        abstract_info = sparql.query().convert()
        if 'results' in abstract_info:
            if 'bindings' in abstract_info['results']:
                first_result = abstract_info['results']['bindings']
                if 'abstract' in first_result:
                    abstract_value = first_result['abstract']['value']
                    abstract_type = first_result['abstract']['type']
                    data['abstract']['type'] = abstract_type
                    data['abstract']['value'] = abstract_value
        
        query = f"""
        PREFIX dbo: <http://dbpedia.org/ontology/>
        PREFIX dbc: <http://dbpedia.org/resource/Category/>

        SELECT ?abstract ?wikiLink
        WHERE {{
            <http://dbpedia.org/resource/{subject_name}> dbo:wikiPageWikiLink ?link.
            OPTIONAL {{
                ?link dbo:abstract ?abstract.
            }}
            FILTER(LANG(?abstract) = 'en')
            BIND(?link AS ?wikiLink) 
        }}
        """
        sparql = SPARQLWrapper(endpoint_url)
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        related_keyword_info = sparql.query().convert()
        
        data["related_keyword"] = []
        for item in related_keyword_info['results']["bindings"]:
            if 'abstract' and 'wikiLink' in item:
                abstract_value = item['abstract']['value']
                abstract_type = item['abstract']['type']
                wikilink_type = item['wikiLink']['type']
                wikilink_value = item['wikiLink']['value']
                keyword_name = str(wikilink_value).split("resource/")[-1]
                data_item = {"name": keyword_name, "abstract": {"type": abstract_type, "value": abstract_value}, "wikilink": {"type": wikilink_type, "value": wikilink_value}}
                data["related_keyword"].append(data_item)


# data{subject:{name, abstract, link}, \
    #   related_keyword:{{name, abstract, link}, \
    #                   {}, ...}}



class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # データを返す
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

# サーバー起動
def run_server():
    port = 8000
    server_address = ('', port)
    httpd = HTTPServer(server_address, RequestHandler)
    print(f'Starting server on port {port}')
    httpd.serve_forever()

if __name__ == '__main__':
    run_server()

