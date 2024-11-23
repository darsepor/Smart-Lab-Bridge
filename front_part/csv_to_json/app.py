from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import csv
import os
import json
import time
from urllib.parse import urljoin, urlparse

app = Flask(__name__)
CORS(app)

# Path to the folder containing index.html
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def is_same_domain(base_url, target_url):
    """Check if the target_url belongs to the same domain as base_url."""
    return urlparse(base_url).netloc == urlparse(target_url).netloc

def scrape_page(url, retries=5, backoff_factor=0.5):
    """
    Scrape a single page with retry logic and exponential backoff.
    """
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=10)
            time.sleep(1)  # Sleep for 1 second between requests

            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            content = ' '.join(soup.body.get_text().split())
            raw_html = soup.prettify()  # Save raw HTML as well
            return {
                "page_url": url,
                "content": content,
                "raw_html": raw_html,
                "status": "success"
            }
        except requests.exceptions.RequestException as e:
            print(f"Error scraping {url}: {e}")
            if attempt < retries - 1:
                wait_time = backoff_factor * (2 ** attempt)
                print(f"Retrying in {wait_time:.2f} seconds...")
                time.sleep(wait_time)
            else:
                print(f"Failed to scrape {url} after {retries} attempts")
                return {"page_url": url, "content": None, "raw_html": None, "status": "failed"}

    return {"page_url": url, "content": None, "raw_html": None, "status": "failed"}


def scrape_website(base_url, max_pages=15):
    """
    Recursively scrape pages from the base URL up to a maximum number of pages.
    """
    visited = set()
    pages = []
    
    def recursive_scrape(url):
        if url in visited or len(pages) >= max_pages:
            return
        page_data = scrape_page(url)
        if page_data["status"] == "success":
            visited.add(url)
            pages.append(page_data)  # Append only if scraping succeeded
            soup = BeautifulSoup(page_data["raw_html"], 'html.parser')  # Use raw HTML here
            for link in soup.find_all('a', href=True):
                next_url = urljoin(base_url, link['href'])
                if is_same_domain(base_url, next_url) and next_url not in visited:
                    recursive_scrape(next_url)


    recursive_scrape(base_url)
    return pages

@app.route('/')
def serve_index():
    """Serve the index.html file when accessing the root route."""
    return send_from_directory(BASE_DIR, 'index.html')

@app.route('/scrape', methods=['GET'])
def scrape():
    csv_path = request.args.get('csv', 'relevant_companies_last_search.csv')
    
    if not os.path.exists(csv_path):
        return jsonify({"error": "CSV file not found"}), 404

    # Load company data from CSV
    data_by_name = {}
    try:
        with open(csv_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                name = row['name']
                url = row['website.url']
                if not url.startswith('http'):
                    url = f"http://{url}"
                
                data_by_name[name] = {
                    'url': url,
                    'mainBusinessLine': row['mainBusinessLine.descriptions'],
                    'pages': []
                }
    except Exception as e:
        return jsonify({"error": f"Error reading CSV: {e}"}), 500

    # Scrape each company's website
    for name, details in data_by_name.items():
        details['pages'] = scrape_website(details['url'], max_pages=10)

    # Save to JSON file
    output_file = 'grouped_scraped_data.json'
    try:
        with open(output_file, 'w', encoding='utf-8') as json_file:
            json.dump(data_by_name, json_file, ensure_ascii=False, indent=4)
    except Exception as e:
        return jsonify({"error": f"Error saving JSON file: {e}"}), 500

    return jsonify({"message": f"Scraped data saved to {output_file}"})

@app.route('/upload', methods=['POST'])
def upload_csv():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    try:
        file.save('relevant_companies_last_search.csv')
    except Exception as e:
        return jsonify({"error": f"Error saving uploaded file: {e}"}), 500
    return jsonify({"message": "File uploaded successfully"})

if __name__ == '__main__':
    app.run(debug=True)
