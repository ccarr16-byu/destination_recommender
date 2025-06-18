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

def get_place_photo(place_name: str, location: tuple[float, float]) -> Optional[str]:
    """Fetch a photo for a place using Google Places API."""
    try:
        search_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        search_params = {
            "query": place_name,
            "location": f"{location[0]},{location[1]}",
            "radius": "1000",
            "key": os.environ.get("GOOGLE_MAPS_API_KEY")
        }
        
        search_response = requests.get(search_url, params=search_params)
        search_data = search_response.json()
        
        if search_data["status"] != "OK" or not search_data["results"]:
            return None
            
        place_id = search_data["results"][0]["place_id"]
        
        details_url = "https://maps.googleapis.com/maps/api/place/details/json"
        details_params = {
            "place_id": place_id,
            "fields": "photos",
            "key": os.environ.get("GOOGLE_MAPS_API_KEY")
        }
        
        details_response = requests.get(details_url, params=details_params)
        details_data = details_response.json()
        
        if details_data["status"] != "OK" or not details_data["result"].get("photos"):
            return None
            
        photo_reference = details_data["result"]["photos"][0]["photo_reference"]
        photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=800&photoreference={photo_reference}&key={os.environ.get('GOOGLE_MAPS_API_KEY')}"
        return photo_url
        
    except Exception as e:
        print(f"Error fetching photo: {str(e)}")
        return None

def generate_embedding(text: str) -> list[float]:
    """Generate embedding for a text using the SentenceTransformer model."""
    return model.encode(text).tolist()

def enhance_description(description: str, site_name: str) -> str:
    """Enhance a site description using ChatGPT."""
    try:
        prompt = f"""Please enhance this description of {site_name} to be more engaging and informative, while maintaining the key facts. 
        Keep it under 30 words and focus on what makes this place special. 
        Original description: {description}"""
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that enhances descriptions of places to be more engaging while staying concise."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=100,
            temperature=0.7
        )
        
        enhanced_description = response.choices[0].message.content.strip()
        logging.info(f"Enhanced description for {site_name}: {enhanced_description}")
        return enhanced_description
        
    except Exception as e:
        logging.error(f"Error enhancing description: {str(e)}")
        return description

@app.route('/api/submit_site', methods=['POST'])
def submit_site():
    try:
        data = request.get_json()
        logging.info(f"Received submission data: {data}")
        
        # Validate required fields
        required_fields = ['name', 'description', 'latitude', 'longitude']
        for field in required_fields:
            if field not in data:
                logging.error(f"Missing required field: {field}")
                return jsonify({"error": f"Missing required field: {field}"}), 400

        # Enhance the description using ChatGPT
        original_description = data['description']
        enhanced_description = enhance_description(original_description, data['name'])
        data['description'] = enhanced_description
        
        # Generate embedding for the enhanced description
        embedding = generate_embedding(enhanced_description)
        
        # Try to fetch photo, but don't fail if it doesn't work
        photo_url = None
        try:
            photo_url = get_place_photo(data['name'], (data['latitude'], data['longitude']))
            logging.info(f"Fetched photo URL: {photo_url}")
        except Exception as e:
            logging.warning(f"Failed to fetch photo: {str(e)}")
        
        # Prepare the site data for Supabase
        site_data = {
            'site_name': data['name'],
            'description': enhanced_description,
            'latitude': data['latitude'],
            'longitude': data['longitude'],
            'photo_url': photo_url,
            'embeddings': ' '.join(map(str, embedding))
        }
        
        # Insert the new site into Supabase
        response = supabase.table('sites').insert(site_data).execute()
        
        if not response.data:
            raise Exception("Failed to insert site into database")
            
        logging.info(f"Successfully inserted site into database: {data['name']}")
        
        return jsonify({
            "message": "Site submitted successfully",
            "photo_url": photo_url,
            "original_description": original_description,
            "enhanced_description": enhanced_description
        })
        
    except Exception as e:
        logging.error(f"Error in submit_site: {str(e)}")
        return jsonify({"error": str(e)}), 500

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/api/submit_site':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            request.json = json.loads(post_data.decode('utf-8'))
            response = submit_site()
            self.send_response(response.status_code)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
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
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers() 