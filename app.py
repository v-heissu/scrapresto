import streamlit as st
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
import io

@st.cache_resource
def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    service = Service('/usr/bin/chromedriver')
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def fetch_and_extract(url, driver):
    restaurants = []
    try:
        driver.get(url)
        
        # Wait for the page to load
        time.sleep(5)
        
        # Wait for the article content to be present
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "places-zone"))
        )
        
        # Get the page source and parse it with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Find the div with class="places-zone"
        article_content = soup.find('div', class_='places-zone')
        
        if article_content:
            places = article_content.find_all('div', class_='component--place-reference')
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
                    'RESTAURANT': restaurant_name,
                    'ADDRESS': address,
                    'CITY': city,
                    'COUNTRY': country
                })
        else:
            st.warning(f"Article content not found for URL: {url}")
    
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
        
        driver = get_driver()
        all_restaurants = []
        
        try:
            for i, url in enumerate(urls):
                status_text.text(f"Processing URL {i+1}/{len(urls)}: {url}")
                restaurants = fetch_and_extract(url, driver)
                for restaurant in restaurants:
                    restaurant['URL'] = url
                all_restaurants.extend(restaurants)
                progress_bar.progress((i + 1) / len(urls))
                time.sleep(random.uniform(2, 5))  # Random delay between requests
        finally:
            driver.quit()
        
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
