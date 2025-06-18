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

@app.route('/api/process_search', methods=['POST'])
def process_search():
    try:
        data = request.get_json()
        query = f"{data.get('query')}"
        
        print(f"Received search query: {query}")

        top_sites = find_similar_sites(query)
        
        if not top_sites:
            return jsonify({
                "message": "No matching sites found",
                "query": query
            })
        
        site_names = [site['site_name'] for site in top_sites]
        
        return jsonify({
            "message": f"Top 3 recommended sites for you: {', '.join(site_names)}",
            "query": query,
            "sites": [{
                'name': site['site_name'],
                'description': site['description'],
                'similarity': site['similarity'],
                'photo_url': site.get('photo_url'),
                'latitude': site['latitude'],
                'longitude': site['longitude']
            } for site in top_sites]
        })
        
    except Exception as e:
        print(f"Error in process_search: {str(e)}")
        return jsonify({"error": str(e)}), 500

def find_similar_sites(query, top_k=3):
    """Finds the top_k most similar national park sites to a given search query based on embeddings."""
    try:
        response = supabase.table('sites').select('*').execute()
        sites = response.data
        
        if not sites:
            print("No sites found in database")
            return []
            
        similarity_scores = []
        search_embedding = model.encode(query)
        
        for site in sites:
            try:
                embedding_str = site['embeddings']
                embedding_list = [float(x) for x in embedding_str.strip('[]').split()]
                similarity_score = util.cos_sim(embedding_list, search_embedding).item()
                similarity_scores.append(similarity_score)
                
            except Exception as e:
                print(f"Error processing site {site['site_name']}: {str(e)}")
                print(f"Problematic embedding string: {embedding_str[:200]}...")
                similarity_scores.append(0)

        for site, score in zip(sites, similarity_scores):
            site['similarity'] = score

        sorted_sites = sorted(sites, key=lambda x: x['similarity'], reverse=True)[:top_k]
        print(f"\nTop {top_k} sites found with scores: {[site['similarity'] for site in sorted_sites]}")

        return sorted_sites

    except Exception as e:
        print(f"An error occurred in find_similar_sites: {str(e)}")
        return []

# This is the handler for Vercel serverless functions
def handler(request):
    return app(request) 