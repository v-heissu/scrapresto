import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
import time
import random

# Setup Chrome options
def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(f"user-agent={get_random_user_agent()}")
    return webdriver.Chrome(options=chrome_options)

# List of user agents to rotate
user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15',
]

def get_random_user_agent():
    return random.choice(user_agents)

def extract_restaurant_data(url, driver):
    restaurants = []
    
    try:
        driver.get(url)
        time.sleep(5)  # Wait for page to load
        
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "places-zone"))
        )
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
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
    
    # Text area for URLs input
    urls_input = st.text_area("Paste your URLs here (one per line):", height=200)
    
    if st.button("Scrape Data"):
        urls = [url.strip() for url in urls_input.split('\n') if url.strip()]
        
        if not urls:
            st.warning("Please enter at least one URL.")
            return
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        driver = setup_driver()
        all_restaurants = []
        
        try:
            for i, url in enumerate(urls):
                status_text.text(f"Processing URL {i+1}/{len(urls)}: {url}")
                all_restaurants.extend(extract_restaurant_data(url, driver))
                progress_bar.progress((i + 1) / len(urls))
                time.sleep(random.uniform(3, 7))  # Random delay between requests
        finally:
            driver.quit()
        
        if all_restaurants:
            df = pd.DataFrame(all_restaurants)
            st.success("Data extraction completed!")
            st.dataframe(df)  # Display the dataframe
            
            # Provide download link
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download data as CSV",
                data=csv,
                file_name="restaurant_data.csv",
                mime="text/csv",
            )
        else:
            st.warning("No data was extracted. Please check the URLs and try again.")

if __name__ == "__main__":
    main()
