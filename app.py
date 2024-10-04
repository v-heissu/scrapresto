import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# ... [previous code for user agents] ...

def get_proxies():
    url = 'https://free-proxy-list.net/'
    response = requests.get(url)
    parser = BeautifulSoup(response.text, 'html.parser')
    proxies = []
    for row in parser.find('tbody').find_all('tr'):
        if row.find_all('td')[4].text =='elite proxy':
            proxy = ':'.join([row.find_all('td')[0].text, row.find_all('td')[1].text])
            proxies.append(proxy)
    return proxies

def create_scraper_session(proxy):
    session = requests.Session()
    retry = Retry(total=5, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    session.proxies = {'http': proxy, 'https': proxy}
    return session

def extract_restaurant_data(url, session):
    # ... [rest of the function remains the same] ...

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
        
        proxies = get_proxies()
        all_restaurants = []
        for i, url in enumerate(urls):
            status_text.text(f"Processing URL {i+1}/{len(urls)}: {url}")
            proxy = random.choice(proxies)
            session = create_scraper_session(proxy)
            all_restaurants.extend(extract_restaurant_data(url, session))
            progress_bar.progress((i + 1) / len(urls))
            time.sleep(random.uniform(5, 10))
        
        if all_restaurants:
            df = pd.DataFrame(all_restaurants)
            st.success("Data extraction completed!")
            st.dataframe(df)
            
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
