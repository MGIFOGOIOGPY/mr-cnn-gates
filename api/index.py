from flask import Flask, request, jsonify
import requests
import time
import random
import re
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urlparse, urlunparse
from fake_useragent import UserAgent
from flask_cors import CORS
import concurrent.futures
import threading

app = Flask(__name__)
CORS(app)

# Payment gateway patterns
gateways = [
    r'Stripe', r'PayPal', r'Braintree', r'tradesafe', r'Razorpay', r'AWS', r'AVS',
    r'eway', r'Authorize\\.Net', r'2Checkout', r'Mollie', r'Google Pay', r'Checkout\\.com',
    r'BlueSnap', r'Adyen', r'woocommerce', r'authorize_net_cim_credit_card'
]

# Global lock for thread-safe operations
analysis_lock = threading.Lock()

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
    
    def search_google(self, query, pages=3):
        """Search using Google"""
        results = []
        for page in range(0, pages):
            try:
                start = page * 10
                url = f"https://www.google.com/search?q={quote_plus(query)}&start={start}"
                
                headers = {'User-Agent': self.get_random_agent()}
                response = requests.get(url, headers=headers, timeout=15)
                
                if response.status_code != 200:
                    print(f"Google search returned status {response.status_code}")
                    continue
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find all search result links
                for g in soup.find_all('div', class_='g'):
                    a = g.find('a')
                    if a and a.has_attr('href'):
                        href = a['href']
                        if href.startswith('/url?q='):
                            url = href.split('/url?q=')[1].split('&')[0]
                            if urlparse(url).netloc and url not in results:
                                results.append(url)
                
                time.sleep(random.uniform(2, 3))
                
            except Exception as e:
                print(f"Google search error: {e}")
                continue
        
        return results
    
    def search_bing(self, query, pages=3):
        """Search using Bing"""
        results = []
        for page in range(1, pages + 1):
            try:
                url = f"https://www.bing.com/search?q={quote_plus(query)}&first={(page-1)*10+1}"
                
                headers = {'User-Agent': self.get_random_agent()}
                response = requests.get(url, headers=headers, timeout=15)
                
                if response.status_code != 200:
                    print(f"Bing search returned status {response.status_code}")
                    continue
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find search result links
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if href.startswith('http') and 'bing.com' not in href and href not in results:
                        results.append(href)
                
                time.sleep(random.uniform(2, 3))
                
            except Exception as e:
                print(f"Bing search error: {e}")
                continue
        
        return results
    
    def search_duckduckgo(self, query, pages=3):
        """Search using DuckDuckGo"""
        results = []
        for page in range(1, pages + 1):
            try:
                url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}&s={(page-1)*30}"
                
                headers = {'User-Agent': self.get_random_agent()}
                response = requests.get(url, headers=headers, timeout=15)
                
                if response.status_code != 200:
                    print(f"DuckDuckGo search returned status {response.status_code}")
                    continue
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find result links
                for link in soup.find_all('a', class_='result__url'):
                    href = link.get('href')
                    if href and href.startswith('http') and href not in results:
                        results.append(href)
                
                time.sleep(random.uniform(1, 2))
                
            except Exception as e:
                print(f"DuckDuckGo search error: {e}")
                continue
        
        return results
    
    def search_all_engines(self, query, pages=3):
        """Search using all available engines"""
        all_results = []
        
        print(f"Searching for: {query}")
        
        # Use threading to search multiple engines concurrently
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_google = executor.submit(self.search_google, query, pages)
            future_bing = executor.submit(self.search_bing, query, pages)
            future_ddg = executor.submit(self.search_duckduckgo, query, pages)
            
            try:
                google_results = future_google.result(timeout=30)
                all_results.extend(google_results)
                print(f"Google found {len(google_results)} results")
            except Exception as e:
                print(f"Google search failed: {e}")
            
            try:
                bing_results = future_bing.result(timeout=30)
                all_results.extend(bing_results)
                print(f"Bing found {len(bing_results)} results")
            except Exception as e:
                print(f"Bing search failed: {e}")
            
            try:
                ddg_results = future_ddg.result(timeout=30)
                all_results.extend(ddg_results)
                print(f"DuckDuckGo found {len(ddg_results)} results")
            except Exception as e:
                print(f"DuckDuckGo search failed: {e}")
        
        # Remove duplicates
        unique_results = list(set(all_results))
        print(f"Total unique results: {len(unique_results)}")
        return unique_results
    
    def filter_valid_results(self, results, max_results=20):
        """Filter results by checking protection and validity"""
        valid_results = []
        
        for url in results:
            if len(valid_results) >= max_results:
                break
                
            if not self.check_protection(url):
                valid_results.append(url)
                print(f"Found valid URL: {url}")
            
            time.sleep(0.5)  # Be polite
        
        return valid_results

def is_real_store(soup):
    """Check if the website appears to be a real e-commerce store"""
    store_keywords = ['cart', 'add to cart', 'product', 'shop', 'store', 'buy now', 'checkout', 'shopping', 'price', '$']
    if soup:
        content = soup.get_text().lower()
        # Check for multiple indicators to reduce false positives
        indicators = sum(1 for word in store_keywords if word in content)
        return indicators >= 3  # At least 3 indicators
    return False

def find_gateways(text):
    """Find payment gateways mentioned in the text"""
    found = set()
    text_lower = text.lower()
    
    for g in gateways:
        pattern = re.compile(r'\b' + re.escape(g.lower().replace('\\.', '.')) + r'\b', re.IGNORECASE)
        if pattern.search(text_lower):
            found.add(g.replace('\\.', '.').replace('\\', ''))
    
    # Additional checks for common payment indicators
    payment_indicators = [
        ('credit card', 'Credit Card'),
        ('debit card', 'Debit Card'),
        ('visa', 'Visa'),
        ('mastercard', 'MasterCard'),
        ('american express', 'American Express'),
        ('payment method', 'Payment Method')
    ]
    
    for indicator, name in payment_indicators:
        if indicator in text_lower:
            found.add(name)
    
    return found

def analyze_store(url, ua):
    """Analyze a single store"""
    try:
        headers = {'User-Agent': ua.random}
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            return None
            
        soup = BeautifulSoup(response.content, 'html.parser')
        text = response.text
        
        # Check if it's a real store
        if not is_real_store(soup):
            return None
        
        # Check for various features
        captcha = 'captcha' in text.lower()
        cloudflare = 'cloudflare' in text.lower() or 'cf-ray' in response.headers
        vbv = bool(re.search(r'3D[\s\-]?Secure|VBV|threeD[\s\-]?SecureInfo', text, re.I))
        
        # Check for authentication pages
        auth_paths = ['/my-account', '/login', '/signin', '/register', '/signup']
        is_auth = any(check_path_exists(url, path, ua) for path in auth_paths)
        
        # Find payment gateways
        gateways_found = find_gateways(text)
        
        # Check checkout pages for additional gateway info
        checkout_pages = ['/checkout', '/payment', '/pay', '/cart']
        for path in checkout_pages:
            try:
                checkout_url = url.rstrip('/') + path
                res2 = requests.get(checkout_url, headers={'User-Agent': ua.random}, timeout=8)
                gateways_found.update(find_gateways(res2.text))
                if re.search(r'3D[\s\-]?Secure|VBV', res2.text, re.I):
                    vbv = True
            except:
                continue
        
        return {
            'url': url,
            'real_store': True,
            'gateways': list(gateways_found) if gateways_found else [],
            'gateways_count': len(gateways_found),
            'cloudflare': cloudflare,
            'auth': is_auth,
            'captcha': captcha,
            'vbv': vbv
        }
        
    except Exception as e:
        print(f"Error analyzing {url}: {e}")
        return None

def check_path_exists(base_url, path, user_agent):
    """Check if a specific path exists on the website"""
    full_url = base_url.rstrip('/') + path
    try:
        res = requests.get(full_url, headers={'User-Agent': user_agent.random}, timeout=8)
        return res.status_code == 200
    except:
        return False

@app.route('/analyze', methods=['GET'])
def analyze_single_store():
    """API endpoint to analyze a single e-commerce store"""
    url = request.args.get('url')
    
    if not url:
        return jsonify({
            'error': 'URL parameter is required',
            'api_by': '@R_O_P_D'
        }), 400
    
    if not url.startswith("http"):
        url = "https://" + url
    
    try:
        ua = UserAgent()
        result = analyze_store(url, ua)
        
        if not result:
            return jsonify({
                'error': 'This does not appear to be a valid e-commerce store',
                'api_by': '@R_O_P_D'
            }), 404
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'error': f'Unexpected error: {str(e)}',
            'api_by': '@R_O_P_D'
        }), 500

@app.route('/cvn', methods=['GET'])
def find_ecommerce_stores():
    """API endpoint to find e-commerce stores and analyze them"""
    try:
        # Get query parameters with reasonable defaults
        pages = int(request.args.get('pages', 3))
        max_results = int(request.args.get('max_results', 20))
        gateways_count = int(request.args.get('gateways_count', 1))
        
        # Limit parameters to prevent abuse
        pages = min(pages, 5)
        max_results = min(max_results, 50)
        
        # Create search queries for e-commerce stores
        ecommerce_queries = [
            'site:shop.com "add to cart"',
            'site:store.com "buy now"',
            '"online shop" "products"',
            '"ecommerce store" "checkout"',
            '"clothing store" "shop now"',
            '"electronics store" "add to cart"'
        ]
        
        tool = DorkSearchTool()
        all_valid_results = []
        
        # Search for each query
        for query in ecommerce_queries[:2]:  # Limit to 2 queries for performance
            print(f"Searching for: {query}")
            results = tool.search_all_engines(query, pages)
            valid_results = tool.filter_valid_results(results, max_results)
            all_valid_results.extend(valid_results)
            
            if len(all_valid_results) >= max_results:
                break
        
        # Remove duplicates
        all_valid_results = list(set(all_valid_results))
        
        # Analyze stores with threading for better performance
        analyzed_stores = []
        ua = UserAgent()
        
        # Use ThreadPoolExecutor to analyze stores concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_url = {executor.submit(analyze_store, url, ua): url for url in all_valid_results[:max_results]}
            
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    result = future.result()
                    if result and len(result['gateways']) >= gateways_count:
                        with analysis_lock:
                            analyzed_stores.append(result)
                except Exception as e:
                    print(f"Error processing {url}: {e}")
        
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
        'message': 'E-commerce Store Analysis API is running',
        'api_by': '@R_O_P_D'
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
