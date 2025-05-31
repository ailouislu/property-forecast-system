import time
import requests
from bs4 import BeautifulSoup
from fetch_property_links import fetch_property_links
from properties import fetch_property_details
from config.redis_config import create_redis_client, check_property_in_redis, add_property_to_redis
from config.supabase_config import insert_property_and_history

# Main function to scrape properties

def fetch_suburbs(url, city):
    """
    Fetches the list of suburbs and their links from a given URL.
    """
    
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        suburb_links_container = soup.find('div', {'testid': 'suburbLinksContainer'})
        if suburb_links_container:
            suburb_links = suburb_links_container.find_all('a')
            # Reverse the order of links
            for link in suburb_links:
                suburb_name = link.get_text(strip=True)
                suburb_link = "https://propertyvalue.co.nz" + link.get('href')                
                print(f"Suburb: {suburb_name}, Link: {suburb_link}")
                
                # Fetch the page content for the suburb link
                suburb_response = requests.get(suburb_link)
                print(f"  Status code for {suburb_name}: {suburb_response.status_code}")
                if suburb_response.status_code == 200:
                    suburb_soup = BeautifulSoup(suburb_response.content, 'html.parser')
                    # Find the pagination element using role='group' and class_='btn-group'
                    pagination = suburb_soup.find('div', {'role': 'group', 'class': 'btn-group'})
                    if pagination:
                        # Find the label with "of" and the next label for the max page number
                        of_label = pagination.find('label', string='of')
                        if of_label and of_label.find_next_sibling('label'):
                            max_page = int(of_label.find_next_sibling('label').get_text(strip=True))
                            print(f"Suburb: {suburb_name}, Max Pages: {max_page}")
                        else:
                            print(f"  No page numbers found for {suburb_name}")
                    else:
                        print(f"  No pagination element found for {suburb_name}")
                        max_page = 1 # Default to 1 page if no pagination

                    scrape_properties(suburb_link, max_page, city, suburb_name)

def scrape_properties(main_url, max_pages, city, suburb):
    redis_client = create_redis_client()  # Instantiate the Redis client

    for page in range(1, max_pages + 1):
        # Fetch property links and titles for the current page
        property_links, titles = fetch_property_links(main_url, page)
        
        # Print and fetch details for each property on the current page
        for property_url, title in zip(property_links, titles):
            print(f"Fetching details for: {title}")
            
            # Check if the property address already exists in Redis
            if check_property_in_redis(redis_client, title):
                print(f"Property {title} already exists in Redis. Skipping...")
                continue

            # Fetch property details and history
            property_data, history_data = fetch_property_details(property_url, title, city, suburb)
            
            # Insert into Supabase
            insert_property_and_history(property_data, history_data)

            # Add the property to Redis to avoid duplicates
            add_property_to_redis(redis_client, title)
            
            # time.sleep(0.5)  # Adding a delay to avoid overloading the server

# Run the scraper
if __name__ == "__main__":
    city = "Upper Hutt City"
    fetch_suburbs("https://www.propertyvalue.co.nz/wellington/upper-hutt-city/45", city)