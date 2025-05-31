# supabase_config.py
from datetime import datetime
import os
from dotenv import load_dotenv
from supabase import create_client, Client

# 连接到 Supabase
load_dotenv()  # 默认加载根目录的 .env 文件

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Create a Supabase client
def create_supabase_client() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("Supabase URL and API key must be provided")
    return create_client(SUPABASE_URL, SUPABASE_KEY)

# Insert property details into the properties table
def insert_property(supabase_client, property_data):
    try:
        # Remove the 'id' from property_data if it exists, so it can be auto-generated
        property_data.pop('id', None)
        
        # Clean up the last_sold_price before inserting
        if 'last_sold_price' in property_data and property_data['last_sold_price']:
            property_data['last_sold_price'] = clean_price(property_data['last_sold_price'])
        
        # Clean up the capital_value, land_value, and improvement_value as well
        if 'capital_value' in property_data and property_data['capital_value']:
            property_data['capital_value'] = clean_price(property_data['capital_value'])
        if 'land_value' in property_data and property_data['land_value']:
            property_data['land_value'] = clean_price(property_data['land_value'])
        if 'improvement_value' in property_data and property_data['improvement_value']:
            property_data['improvement_value'] = clean_price(property_data['improvement_value'])

        # Insert the property data (without 'id')
        response = supabase_client.table('properties').insert(property_data).execute()

        # Check for errors in the response
        if response.error:
            print(f"Failed to insert property: {response.error}")  # Print the error message
            return None
        
        # If successful, return the ID of the inserted property
        print(f"Property inserted: {property_data['address']}")
        return response.data[0]['id']  # Return the property ID

    except Exception as e:
        print(f"Error inserting property: {str(e)}")
        return None

def clean_price(price_str):
    if price_str is None:
        return None
    if isinstance(price_str, (int, float)):
        return price_str
    try:
        return float(price_str.replace('$', '').replace(',', '').strip())
    except ValueError:
        return None

def clean_property_data(property_data):
    price_fields = ['last_sold_price', 'capital_value', 'land_value', 'improvement_value']
    for field in price_fields:
        if field in property_data:
            property_data[field] = clean_price(property_data[field])
    return property_data

def parse_date(date_str):
    if not date_str:
        return None
    date_formats = ['%d %b %Y', '%Y', '%b %Y', '%d/%m/%Y', '%Y-%m-%d']
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    print(f"Warning: Unable to parse date '{date_str}'")
    return None

def format_date_for_json(date_obj):
    if date_obj is None:
        return None
    return date_obj.isoformat()  # Converts date to ISO 8601 string format

def insert_property_and_history(property_data, history_data):
    try:
        supabase = create_supabase_client()
        
        # Clean property data
        cleaned_property_data = clean_property_data(property_data)
        
        # Insert property data
        response = supabase.table('properties').insert(cleaned_property_data).execute()
        
        if response.data:
            property_id = response.data[0]['id']
            print(f"Property inserted successfully. ID: {property_id}")
            
            # Insert history data if available
            if history_data and isinstance(history_data, list):
                for event in history_data:
                    history_entry = {
                        'property_id': property_id,
                        'event_description': event.get('event_description', ''),
                        'event_date': format_date_for_json(parse_date(event.get('event_date'))),  # Convert to string format
                        'interval_since_last_event': event.get('event_interval', '')
                    }
                    if history_entry['event_date'] is not None:
                        history_response = supabase.table('property_history').insert(history_entry).execute()
                        if not history_response.data:
                            print(f"Failed to insert history entry: {event}")
                    else:
                        print(f"Skipped inserting history entry due to invalid date: {event}")
                print("Property history insertion completed.")
            else:
                print("No history data to insert.")
        else:
            print("Failed to insert property data.")
    except Exception as e:
        print(f"Error in insert_property_and_history: {str(e)}")
        print(f"Property data: {property_data}")
        if history_data:
            print(f"History data: {history_data}")

def insert_real_estate(address, status):
    try:
        supabase = create_supabase_client()
        data = {
            "address": address,
            "status": status
        }
        response = supabase.table('real_estate').insert(data).execute()
        if response.data:
            print(f"Inserted {address} into Supabase successfully.")
        else:
            print(f"Failed to insert {address} into Supabase.")
    except Exception as e:
        print(f"Error inserting {address} into Supabase: {str(e)}")
