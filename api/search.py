from http.server import BaseHTTPRequestHandler
from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
from sentence_transformers import SentenceTransformer, util
import os
import json
import ast
import numpy as np
from typing import List, Dict, Any
from dotenv import load_dotenv
import logging
import sys
from supabase import create_client, Client

# Set up logging to stdout
logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Load environment variables
load_dotenv()

# Initialize Supabase client
try:
    supabase_url = os.environ.get('SUPABASE_URL')
    supabase_key = os.environ.get('SUPABASE_KEY')
    logging.info(f"Attempting to connect to Supabase at URL: {supabase_url[:20]}...")
    supabase: Client = create_client(supabase_url, supabase_key)
    logging.info("Successfully initialized Supabase client")
except Exception as e:
    logging.error(f"Failed to initialize Supabase client: {str(e)}")
    raise

# Initialize the model
model = SentenceTransformer('all-mpnet-base-v2')

app = Flask(__name__)
CORS(app)

def get_all_sites() -> List[Dict[str, Any]]:
    """Fetch all sites from Supabase."""
    try:
        response = supabase.table('sites').select('*').execute()
        if not response.data:
            return []
            
        sites = []
        for site in response.data:
            # Convert embeddings string to list of floats
            embeddings_str = site.get('embeddings', '')
            if embeddings_str:
                try:
                    embeddings = [float(x) for x in embeddings_str.split()]
                    site['embeddings'] = embeddings
                except Exception as e:
                    logging.error(f"Error converting embeddings for site {site.get('site_name')}: {str(e)}")
                    site['embeddings'] = []
            else:
                site['embeddings'] = []
                
            sites.append(site)
            
        return sites
        
    except Exception as e:
        logging.error(f"Error fetching sites: {str(e)}")
        raise

def search_sites(query: str, sites: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
    """Search sites using semantic similarity."""
    try:
        # Generate query embedding
        query_embedding = model.encode(query)
        
        # Calculate similarities
        similarities = []
        for site in sites:
            if not site.get('embeddings'):
                continue
                
            site_embedding = np.array(site['embeddings'])
            similarity = util.pytorch_cos_sim(query_embedding, site_embedding)[0][0].item()
            similarities.append((site, similarity))
            
        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Return top k results
        return [site for site, _ in similarities[:top_k]]
        
    except Exception as e:
        logging.error(f"Error searching sites: {str(e)}")
        raise

@app.route('/api/search', methods=['GET'])
def search():
    try:
        query = request.args.get('query', '')
        if not query:
            return jsonify({"error": "Query parameter is required"}), 400
            
        # Get all sites
        sites = get_all_sites()
        
        # Search sites
        results = search_sites(query, sites)
        
        # Format results
        formatted_results = []
        for site in results:
            formatted_results.append({
                'name': site['site_name'],
                'description': site['description'],
                'latitude': site['latitude'],
                'longitude': site['longitude'],
                'photo_url': site.get('photo_url')
            })
            
        return jsonify({"results": formatted_results})
        
    except Exception as e:
        logging.error(f"Error in search: {str(e)}")
        return jsonify({"error": str(e)}), 500

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/api/search'):
            query = self.path.split('?query=')[1] if '?query=' in self.path else ''
            request.args = {'query': query}
            response = search()
            self.send_response(response.status_code)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
            self.wfile.write(json.dumps(response.get_json()).encode())
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Not found"}).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers() 