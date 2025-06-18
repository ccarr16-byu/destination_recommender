from http.server import BaseHTTPRequestHandler
from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
from sentence_transformers import SentenceTransformer, util
import os
import json
import ast
import requests
from typing import Optional
from dotenv import load_dotenv
import logging
import sys
from openai import OpenAI
from supabase import create_client, Client

# Set up logging to stdout
logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

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

@app.route('/api/all_sites', methods=['GET'])
def get_all_sites():
    try:
        # Test Supabase connection first
        try:
            supabase_url = os.environ.get('SUPABASE_URL')
            supabase_key = os.environ.get('SUPABASE_KEY')
            
            if not supabase_url or not supabase_key:
                return jsonify({
                    "error": "Database configuration error",
                    "details": {
                        "supabase_url_set": bool(supabase_url),
                        "supabase_key_set": bool(supabase_key)
                    }
                }), 500

            test_response = supabase.table('sites').select('count').execute()
        except Exception as e:
            return jsonify({
                "error": "Database connection error",
                "details": {
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "supabase_url_set": bool(os.environ.get('SUPABASE_URL')),
                    "supabase_key_set": bool(os.environ.get('SUPABASE_KEY'))
                }
            }), 500

        # Fetch all sites
        response = supabase.table('sites').select('*').order('site_name').execute()
        sites = response.data
        
        if not sites:
            return jsonify({"sites": []})
        
        # Transform the data to match the expected format
        formatted_sites = []
        for site in sites:
            try:
                formatted_site = {
                    'name': site['site_name'],
                    'description': site['description'],
                    'latitude': float(site['latitude']),
                    'longitude': float(site['longitude']),
                    'photo_url': site.get('photo_url')
                }
                formatted_sites.append(formatted_site)
            except KeyError as e:
                return jsonify({
                    "error": "Data format error",
                    "details": {
                        "missing_field": str(e),
                        "site_data": site
                    }
                }), 500
            except ValueError as e:
                return jsonify({
                    "error": "Data conversion error",
                    "details": {
                        "site_name": site.get('site_name', 'unknown'),
                        "error": str(e)
                    }
                }), 500
        
        return jsonify({
            "sites": formatted_sites
        })
    except Exception as e:
        return jsonify({
            "error": "Unexpected error",
            "details": {
                "error_type": type(e).__name__,
                "error_message": str(e)
            }
        }), 500

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/all_sites':
            response = get_all_sites()
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