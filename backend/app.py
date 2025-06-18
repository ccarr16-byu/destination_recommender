from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
from sentence_transformers import SentenceTransformer, util
import os
import json
import ast  # Add this import for safely evaluating string representations of lists
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

# Load environment variables from .env file only in development
if not os.environ.get('VERCEL'):
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))
    logging.info("Running in development mode - loaded .env file")
else:
    logging.info("Running in production mode - using Vercel environment variables")

# Log environment variable status (without exposing values)
logging.info(f"SUPABASE_URL is {'set' if os.environ.get('SUPABASE_URL') else 'not set'}")
logging.info(f"SUPABASE_KEY is {'set' if os.environ.get('SUPABASE_KEY') else 'not set'}")
logging.info(f"OPENAI_API_KEY is {'set' if os.environ.get('OPENAI_API_KEY') else 'not set'}")

# Initialize OpenAI client
client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

# Initialize Supabase client
try:
    supabase_url = os.environ.get('SUPABASE_URL')
    supabase_key = os.environ.get('SUPABASE_KEY')
    logging.info(f"Attempting to connect to Supabase at URL: {supabase_url[:20]}...")  # Only log part of URL for security
    supabase: Client = create_client(supabase_url, supabase_key)
    logging.info("Successfully initialized Supabase client")
except Exception as e:
    logging.error(f"Failed to initialize Supabase client: {str(e)}")
    raise

fdir = os.path.dirname(__file__)
def getPath(fname):
    return os.path.join(fdir, fname)

app = Flask(__name__)
CORS(app)  # This allows requests from your Next.js frontend

# Initialize the model once at startup
model = SentenceTransformer('all-mpnet-base-v2')

def get_place_photo(place_name: str, location: tuple[float, float]) -> Optional[str]:
    """Fetch a photo for a place using Google Places API."""
    try:
        # First, search for the place to get its place_id
        search_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        search_params = {
            "query": place_name,
            "location": f"{location[0]},{location[1]}",
            "radius": "1000",  # 1km radius
            "key": os.environ.get("GOOGLE_MAPS_API_KEY")
        }
        
        search_response = requests.get(search_url, params=search_params)
        search_data = search_response.json()
        
        if search_data["status"] != "OK" or not search_data["results"]:
            return None
            
        place_id = search_data["results"][0]["place_id"]
        
        # Then, get the place details to get photo reference
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
        
        # Construct the photo URL
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
        return description  # Return original description if enhancement fails

@app.route('/process_search', methods=['POST'])
def process_search():
    try:
        # Get the search query from the request
        data = request.get_json()
        query = f"{data.get('query')}"
        
        print(f"Received search query: {query}")

        top_sites = find_similar_sites(query)
        
        if not top_sites:
            return jsonify({
                "message": "No matching sites found",
                "query": query
            })
        
        # Convert the pandas Series objects to dictionaries
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
    """
    Finds the top_k most similar national park sites to a given search query based on embeddings.
    """
    try:
        # Fetch all sites from Supabase
        response = supabase.table('sites').select('*').execute()
        sites = response.data
        
        if not sites:
            print("No sites found in database")
            return []
            
        similarity_scores = []
        search_embedding = model.encode(query)
        
        # Process each site's embeddings
        for site in sites:
            try:
                # Get the embedding string and convert it to a list of floats
                embedding_str = site['embeddings']
                # Split by whitespace and convert to float, handling scientific notation
                embedding_list = [float(x) for x in embedding_str.strip('[]').split()]
                
                # Calculate similarity
                similarity_score = util.cos_sim(embedding_list, search_embedding).item()
                similarity_scores.append(similarity_score)
                
            except Exception as e:
                print(f"Error processing site {site['site_name']}: {str(e)}")
                print(f"Problematic embedding string: {embedding_str[:200]}...")
                similarity_scores.append(0)

        # Add similarity scores to sites
        for site, score in zip(sites, similarity_scores):
            site['similarity'] = score

        # Sort by similarity and get top_k
        sorted_sites = sorted(sites, key=lambda x: x['similarity'], reverse=True)[:top_k]
        print(f"\nTop {top_k} sites found with scores: {[site['similarity'] for site in sorted_sites]}")

        return sorted_sites

    except Exception as e:
        print(f"An error occurred in find_similar_sites: {str(e)}")
        return []

@app.route('/all_sites', methods=['GET'])
def get_all_sites():
    try:
        logging.info("=== Starting get_all_sites request ===")
        
        # Test Supabase connection first
        try:
            logging.info("Testing Supabase connection...")
            test_response = supabase.table('sites').select('count').execute()
            logging.info(f"Supabase connection test successful. Count: {test_response.data}")
        except Exception as e:
            logging.error(f"Supabase connection test failed: {str(e)}")
            return jsonify({"error": f"Database connection error: {str(e)}"}), 500

        # Fetch all sites
        logging.info("Fetching all sites from Supabase...")
        response = supabase.table('sites').select('*').order('site_name').execute()
        sites = response.data
        
        logging.info(f"Raw response from Supabase: {response}")
        logging.info(f"Number of sites retrieved: {len(sites) if sites else 0}")
        
        if not sites:
            logging.warning("No sites found in database")
            return jsonify({"sites": []})
        
        # Transform the data to match the expected format
        formatted_sites = []
        for site in sites:
            try:
                logging.info(f"Processing site: {site.get('site_name', 'unknown')}")
                formatted_site = {
                    'name': site['site_name'],
                    'description': site['description'],
                    'latitude': float(site['latitude']),
                    'longitude': float(site['longitude']),
                    'photo_url': site.get('photo_url')
                }
                formatted_sites.append(formatted_site)
                logging.info(f"Successfully formatted site: {formatted_site['name']}")
            except KeyError as e:
                logging.error(f"Missing required field in site data: {str(e)}")
                logging.error(f"Problematic site data: {site}")
                continue
            except ValueError as e:
                logging.error(f"Error converting coordinates for site {site.get('site_name', 'unknown')}: {str(e)}")
                continue
        
        logging.info(f"Successfully formatted {len(formatted_sites)} sites")
        logging.info("=== Completed get_all_sites request ===")
        
        return jsonify({
            "sites": formatted_sites
        })
    except Exception as e:
        logging.error(f"Error in get_all_sites: {str(e)}")
        logging.error(f"Full error details: {str(e.__class__.__name__)}: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/submit_site', methods=['POST'])
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
            'embeddings': ' '.join(map(str, embedding))  # Convert list to space-separated string
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

if __name__ == '__main__':
    app.run(port=5000, debug=True) 