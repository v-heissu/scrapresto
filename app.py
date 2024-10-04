import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import io

# List of user agents to rotate
user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15',
]

def get_random_user_agent():
    return random.choice(user_agents)

def extract_restaurant_data(url):
    restaurants = []
    
    headers = {
        'User-Agent': get_random_user_agent(),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://www.google.com/',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        article_title = soup.find('h1', class_='title').text.strip()
        places = soup.find_all('div', class_='component--place-reference')

        for place in places:
            restaurant_name = place.find('h2').text.strip()
            address_elem = place.find('div', class_='field--name-field-address')
            if address_elem:
                address_parts = address_elem.find_all('span')
                address = address_parts[1].text.strip() if len(address_parts) > 1 else ''
                city = address_parts[2].text.strip().rstrip(',') if len(address_parts) > 2 else ''
                country = address_parts[3].text.strip() if len(address_parts) > 3 else ''
            else:
                address, city, country = '', '', ''

            restaurants.append({
                'TITLE': article_title,
                'URL': url,
                'RESTAURANT': restaurant_name,
                'ADDRESS': address,
                'CITY': city,
                'COUNTRY': country
            })

    except Exception as e:
        st.error(f"An error occurred while processing {url}: {e}")

    return restaurants

def main():
    st.title("Restaurant Data Scraper")
    
    urls_input = st.text_area("Paste your URLs here (one per line):", height=200)
    
    if st.button("Scrape Data"):
        urls = [url.strip() for url in urls_input.split('\n') if url.strip()]
        
        if not urls:
            st.warning("Please enter at least one URL.")
            return
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        all_restaurants = []
        for i, url in enumerate(urls):
            status_text.text(f"Processing URL {i+1}/{len(urls)}: {url}")
            all_restaurants.extend(extract_restaurant_data(url))
            progress_bar.progress((i + 1) / len(urls))
            time.sleep(random.uniform(2, 5))  # Random delay between requests
        
        if all_restaurants:
            df = pd.DataFrame(all_restaurants)
            st.success("Data extraction completed!")
            st.dataframe(df)  # Display the dataframe
            
            # Provide download links for both CSV and Excel
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download data as CSV",
                data=csv,
                file_name="restaurant_data.csv",
                mime="text/csv",
            )
            
            # Excel download
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df.to_excel(writer, index=False)
            excel_data = buffer.getvalue()
            st.download_button(
                label="Download data as Excel",
                data=excel_data,
                file_name="restaurant_data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.warning("No data was extracted. Please check the URLs and try again.")

if __name__ == "__main__":
    main()
