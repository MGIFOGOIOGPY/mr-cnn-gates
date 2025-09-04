from flask import Flask, request, jsonify
import requests
import time
import random
import re
import sys
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urlparse, urlunparse
from fake_useragent import UserAgent
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Payment gateway patterns
gateways = [
    r'Stripe', r'PayPal', r'Braintree', r'tradesafe', r'Razorpay', r'AWS', r'AVS',
    r'eway', r'Authorize\\.Net', r'2Checkout', r'Mollie', r'Google Pay', r'Checkout\\.com',
    r'BlueSnap', r'Adyen', r'woocommerce', r'authorize_net_cim_credit_card'
]

class DorkSearchTool:
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36'
        ]
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': random.choice(self.user_agents)})
    
    def get_random_agent(self):
        return random.choice(self.user_agents)
    
    def check_protection(self, url):
        """Check if URL has protection like CAPTCHA"""
        try:
            headers = {'User-Agent': self.get_random_agent()}
            res = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
            content = res.text.lower()
            return any(x in content for x in ['captcha', 'cf-chl-bypass', 'cloudflare', 'security check'])
        except:
            return True
    
    def search_google(self, query, pages=5):
        """Search using Google (simulated)"""
        results = []
        for page in range(0, pages):
            try:
                # Simulate Google search with a search API provider
                start = page * 10
                url = f"https://www.google.com/search?q={quote_plus(query)}&start={start}"
                
                headers = {'User-Agent': self.get_random_agent()}
                response = requests.get(url, headers=headers, timeout=15)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if href.startswith('/url?q='):
                        url = href.split('/url?q=')[1].split('&')[0]
                        if urlparse(url).netloc and url not in results:
                            results.append(url)
                
                time.sleep(random.uniform(2, 5))  # Be polite with delays
                
            except Exception as e:
                print(f"Google search error: {e}")
                continue
        
        return results
    
    def search_bing(self, query, pages=5):
        """Search using Bing"""
        results = []
        for page in range(1, pages + 1):
            try:
                url = f"https://www.bing.com/search?q={quote_plus(query)}&first={(page-1)*10+1}"
                
                headers = {'User-Agent': self.get_random_agent()}
                response = requests.get(url, headers=headers, timeout=15)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                for link in soup.select('h2 a'):
                    href = link.get('href')
                    if href and href not in results:
                        results.append(href)
                
                time.sleep(random.uniform(2, 4))
                
            except Exception as e:
                print(f"Bing search error: {e}")
                continue
        
        return results
    
    def search_duckduckgo(self, query, pages=5):
        """Search using DuckDuckGo"""
        results = []
        for page in range(1, pages + 1):
            try:
                url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}&s={(page-1)*30}"
                
                headers = {'User-Agent': self.get_random_agent()}
                response = requests.get(url, headers=headers, timeout=15)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                for link in soup.select('.result__a'):
                    href = link.get('href')
                    if href and href.startswith('http') and href not in results:
                        results.append(href)
                
                time.sleep(random.uniform(1, 3))
                
            except Exception as e:
                print(f"DuckDuckGo search error: {e}")
                continue
        
        return results
    
    def search_all_engines(self, query, pages=5):
        """Search using all available engines"""
        all_results = []
        
        print("Searching Google...")
        google_results = self.search_google(query, pages)
        all_results.extend(google_results)
        
        print("Searching Bing...")
        bing_results = self.search_bing(query, pages)
        all_results.extend(bing_results)
        
        print("Searching DuckDuckGo...")
        ddg_results = self.search_duckduckgo(query, pages)
        all_results.extend(ddg_results)
        
        # Remove duplicates
        unique_results = list(set(all_results))
        return unique_results
    
    def filter_valid_results(self, results, max_results=50):
        """Filter results by checking protection and validity"""
        valid_results = []
        
        for url in results:
            if len(valid_results) >= max_results:
                break
                
            if not self.check_protection(url):
                valid_results.append(url)
                print(f"Found valid URL: {url}")
            
            time.sleep(1)  # Be polite
        
        return valid_results

def get_main_domain(url):
    """Extract the main domain from a URL"""
    parsed_url = urlparse(url)
    domain_parts = parsed_url.hostname.split('.')
    if len(domain_parts) > 2:
        domain = '.'.join(domain_parts[-3:])
    else:
        domain = '.'.join(domain_parts[-2:])
    home_page = parsed_url._replace(netloc=domain, path='/', query='', fragment='')
    return urlunparse(home_page)

def check_path_exists(base_url, path, user_agent):
    """Check if a specific path exists on the website"""
    full_url = base_url.rstrip('/') + path
    try:
        res = requests.get(full_url, headers={'User-Agent': user_agent.random}, timeout=10)
        return res.status_code == 200
    except:
        return False

def is_real_store(soup):
    """Check if the website appears to be a real e-commerce store"""
    store_keywords = ['cart', 'add to cart', 'product', 'shop', 'store', 'buy now', 'checkout', 'shopping']
    if soup:
        content = soup.get_text().lower()
        return any(word in content for word in store_keywords)
    return False

def find_gateways(text):
    """Find payment gateways mentioned in the text"""
    found = set()
    for g in gateways:
        if re.search(r'\b' + re.escape(g) + r'\b', text, re.IGNORECASE):
            found.add(g.replace('\\.', '.'))
    return found

@app.route('/cvn', methods=['GET'])
def find_ecommerce_stores():
    """API endpoint to find e-commerce stores and analyze them"""
    try:
        # Get query parameters
        pages = int(request.args.get('pages', 5))
        max_results = int(request.args.get('max_results', 50))
        gateways_count = int(request.args.get('gateways_count', 1))
        
        # Create search queries for e-commerce stores
        ecommerce_queries = [
            '"shop" "products" "buy now"',
            '"online store" "add to cart"',
            '"ecommerce" "shop" "products"',
            '"buy" "products" "online"',
            '"clothing store" "shop now"',
            '"electronics store" "buy now"',
            '"digital cards" "buy now"',
            '"online shop" "products"'
        ]
        
        tool = DorkSearchTool()
        all_valid_results = []
        
        # Search for each query
        for query in ecommerce_queries:
            print(f"Searching for: {query}")
            results = tool.search_all_engines(query, pages)
            valid_results = tool.filter_valid_results(results, max_results)
            all_valid_results.extend(valid_results)
            
            if len(all_valid_results) >= max_results:
                break
        
        # Remove duplicates
        all_valid_results = list(set(all_valid_results))
        
        # Analyze each store
        analyzed_stores = []
        ua = UserAgent()
        
        for url in all_valid_results[:max_results]:
            try:
                headers = {'User-Agent': ua.random}
                response = requests.get(url, headers=headers, timeout=15)
                soup = BeautifulSoup(response.content, 'html.parser')
                text = response.text
                
                # Check if it's a real store
                if not is_real_store(soup):
                    continue
                
                # Check for various features
                captcha = 'captcha' in text.lower()
                cloudflare = 'cloudflare' in text.lower()
                vbv = bool(re.search(r'3D[\s\-]?Secure|VBV|threeD[\s\-]?SecureInfo', text, re.I))
                
                # Check for authentication pages
                is_auth = check_path_exists(url, '/my-account', ua)
                
                # Find payment gateways
                gateways_found = find_gateways(text)
                
                # Check checkout pages for additional gateway info
                checkout_pages = ['/checkout', '/payment', '/pay']
                for path in checkout_pages:
                    try:
                        checkout_url = url.rstrip('/') + path
                        res2 = requests.get(checkout_url, headers={'User-Agent': ua.random}, timeout=10)
                        gateways_found.update(find_gateways(res2.text))
                        if re.search(r'3D[\s\-]?Secure|VBV', res2.text, re.I):
                            vbv = True
                    except:
                        continue
                
                # Filter by minimum gateways count
                if len(gateways_found) >= gateways_count:
                    analyzed_stores.append({
                        'url': url,
                        'real_store': True,
                        'gateways': list(gateways_found) if gateways_found else [],
                        'gateways_count': len(gateways_found),
                        'cloudflare': cloudflare,
                        'auth': is_auth,
                        'captcha': captcha,
                        'vbv': vbv
                    })
                
                time.sleep(1)  # Be polite with requests
                
            except Exception as e:
                print(f"Error analyzing {url}: {e}")
                continue
        
        return jsonify({
            'stores_found': len(analyzed_stores),
            'stores': analyzed_stores,
            'api_by': '@R_O_P_D',
            'message': 'E-commerce store search completed successfully'
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Unexpected error: {str(e)}',
            'api_by': '@R_O_P_D'
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'OK',
        'message': 'E-commerce Store Search API is running',
        'api_by': '@R_O_P_D'
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
