from flask import Flask, request, jsonify, send_file, render_template
import os
import subprocess
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = './'
OUTPUT_FILE = 'grouped_scraped_data.json'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Route: Home Page
@app.route('/')
def home():
    return render_template('index.html')

# Route: Upload CSV
@app.route('/upload', methods=['POST'])
def upload_csv():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'Invalid file format. Only CSV allowed.'}), 400

    # Save file securely
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'relevant_companies_last_search.csv')
    file.save(filepath)
    return jsonify({'message': 'CSV uploaded successfully'}), 200

# Route: Start Scraping
@app.route('/scrape', methods=['GET'])
def scrape():
    try:
        # Run the spider
        subprocess.run(['scrapy', 'crawl', 'company_spider'], check=True)

        # Check if the output file exists
        if not os.path.exists(OUTPUT_FILE):
            return jsonify({'error': 'Scraping failed, output file not found'}), 500

        return jsonify({'message': 'Scraping completed successfully'}), 200
    except subprocess.CalledProcessError as e:
        return jsonify({'error': f'Scraping process failed: {str(e)}'}), 500

# Route: Download JSON
@app.route('/download', methods=['GET'])
def download_json():
    if os.path.exists(OUTPUT_FILE):
        return send_file(OUTPUT_FILE, as_attachment=True)
    else:
        return jsonify({'error': 'File not found'}), 404

if __name__ == '__main__':
    app.run(debug=True)
