from supabase import create_client, Client
import os
from dotenv import load_dotenv

# Load environment variables from root directory
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

# Get Supabase credentials
supabase_url = os.environ.get('SUPABASE_URL')
supabase_key = os.environ.get('SUPABASE_KEY')

print(f"Supabase URL: {supabase_url}")
print(f"Supabase Key exists: {'Yes' if supabase_key else 'No'}")

# Initialize Supabase client
supabase = create_client(supabase_url, supabase_key)

# Test connection
try:
    # Try to get the count of sites
    response = supabase.table('sites').select('count').execute()
    print(f"Connection successful! Response: {response.data}")
    
    # Add a test site
    test_site = {
        'site_name': 'Yosemite National Park',
        'description': 'A stunning national park known for its waterfalls, giant sequoias, and granite cliffs.',
        'latitude': 37.8651,
        'longitude': -119.5383,
        'photo_url': 'https://images.unsplash.com/photo-1501594907352-04cda38ebc29',
        'embeddings': '0.1 0.2 0.3'  # Placeholder embedding
    }
    
    print("\nAdding test site...")
    insert_response = supabase.table('sites').insert(test_site).execute()
    print(f"Insert response: {insert_response.data}")
    
    # Verify the site was added
    verify_response = supabase.table('sites').select('*').execute()
    print(f"\nAll sites in database: {verify_response.data}")
    
except Exception as e:
    print(f"Error: {str(e)}") 