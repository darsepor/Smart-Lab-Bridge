import os
import csv
import json
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor

class CompanySpider(CrawlSpider):
    name = 'company_spider'

    def __init__(self, company_limit=500, *args, **kwargs):
        super(CompanySpider, self).__init__(*args, **kwargs)

        self.company_limit = int(company_limit) if company_limit else None

        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        csv_path = os.path.join(project_root, 'processed_data_from_prh.fi', 'relevant_companies_broadly.csv')
        self.output_file = 'scraped_data_all_relevant_PRH_companies.json'

        # Load existing data if any
        if os.path.exists(self.output_file):
            with open(self.output_file, 'r', encoding='utf-8') as f:
                self.existing_data = json.load(f)
        else:
            self.existing_data = {}

        # Ensure the CSV file exists
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"CSV file not found at: {csv_path}")

        self.start_urls = []
        self.data_by_domain = {}
        new_companies_count = 0
        # Read the CSV and add only new domains
        with open(csv_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for i, row in enumerate(reader):
                if self.company_limit and new_companies_count >= self.company_limit:
                    break

                url = row['website.url']
                if not url.startswith('http'):
                    url = 'http://' + url
                domain = url.split("//")[-1].split("/")[0]
                # Normalize domain (to handle www. variants)
                domain = domain.replace('www.', '')

                # Check if domain already scraped
                if domain in self.existing_data:
                    # Already scraped -- skip
                    continue
                
                # If not in existing data, add to start_urls and data_by_domain
                self.start_urls.append(url)
                self.data_by_domain[domain] = {
                    'company_name': row['name'],
                    'url': url,
                    'mainBusinessLine': row['mainBusinessLine.descriptions'],
                    'pages': []
                }
                new_companies_count += 1

    rules = (
        Rule(
            LinkExtractor(allow=(), deny=(), unique=True),
            callback='parse_item',
            follow=True
        ),
    )

    def parse_item(self, response):
        domain = response.url.split("//")[-1].split("/")[0]
        domain = domain.replace('www.', '')

        if domain not in self.data_by_domain:
            return

        text_content = ' '.join(response.xpath('//body//text()').getall())
        text_content = ' '.join(text_content.split())
        self.data_by_domain[domain]['pages'].append({
            'page_url': response.url,
            'content': text_content
        })

    def closed(self, reason):
        # Merge existing_data with new scraped data
        for domain, info in self.data_by_domain.items():
            self.existing_data[domain] = info

        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(self.existing_data, f, ensure_ascii=False, indent=4)
        self.logger.info(f"Scraped data saved to {self.output_file}")
