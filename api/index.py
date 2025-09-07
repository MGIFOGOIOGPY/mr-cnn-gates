from flask import Flask, request, jsonify
import requests
import time
import random
import re
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urlparse
from fake_useragent import UserAgent
from flask_cors import CORS
import concurrent.futures
import threading

app = Flask(__name__)
CORS(app)

# Payment gateway patterns
gateways = [
    'Stripe', 'PayPal', 'Braintree', 'tradesafe', 'Razorpay', 
    'Authorize.Net', '2Checkout', 'Mollie', 'Google Pay', 
    'Checkout.com', 'BlueSnap', 'Adyen', 'woocommerce'
]

# Global lock for thread-safe operations
analysis_lock = threading.Lock()

class DorkSearchTool:
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        ]
    
    def get_random_agent(self):
        return random.choice(self.user_agents)
    
    def check_protection(self, url):
        """Check if URL has protection like CAPTCHA"""
        try:
            headers = {'User-Agent': self.get_random_agent()}
            res = requests.get(url, headers=headers, timeout=8, allow_redirects=True)
            content = res.text.lower()
            return any(x in content for x in ['captcha', 'cloudflare', 'security check', 'firewall'])
        except:
            return False
    
    def search_google(self, query, pages=2):
        """Search using Google with improved parsing"""
        results = []
        for page in range(pages):
            try:
                start = page * 10
                url = f"https://www.google.com/search?q={quote_plus(query)}&start={start}"
                
                headers = {'User-Agent': self.get_random_agent()}
                response = requests.get(url, headers=headers, timeout=15)
                
                if response.status_code != 200:
                    continue
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find all links in search results
                for a in soup.find_all('a', href=True):
                    href = a['href']
                    if href.startswith('/url?q='):
                        link = href.split('/url?q=')[1].split('&')[0]
                        if urlparse(link).netloc and link not in results:
                            results.append(link)
                
                time.sleep(random.uniform(1, 2))
                
            except Exception as e:
                print(f"Google search error: {e}")
                continue
        
        return results
    
    def search_bing(self, query, pages=2):
        """Search using Bing"""
        results = []
        for page in range(1, pages + 1):
            try:
                url = f"https://www.bing.com/search?q={quote_plus(query)}&first={(page-1)*10+1}"
                
                headers = {'User-Agent': self.get_random_agent()}
                response = requests.get(url, headers=headers, timeout=15)
                
                if response.status_code != 200:
                    continue
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find organic results
                for li in soup.find_all('li', class_='b_algo'):
                    a = li.find('a')
                    if a and a.has_attr('href'):
                        href = a['href']
                        if href.startswith('http') and 'bing.com' not in href and href not in results:
                            results.append(href)
                
                time.sleep(random.uniform(1, 2))
                
            except Exception as e:
                print(f"Bing search error: {e}")
                continue
        
        return results
    
    def search_all_engines(self, query, pages=2):
        """Search using all available engines"""
        all_results = []
        
        print(f"Searching for: {query}")
        
        # Search both engines
        try:
            google_results = self.search_google(query, pages)
            all_results.extend(google_results)
            print(f"Google found {len(google_results)} results")
        except Exception as e:
            print(f"Google search failed: {e}")
        
        try:
            bing_results = self.search_bing(query, pages)
            all_results.extend(bing_results)
            print(f"Bing found {len(bing_results)} results")
        except Exception as e:
            print(f"Bing search failed: {e}")
        
        # Remove duplicates
        unique_results = list(set(all_results))
        print(f"Total unique results: {len(unique_results)}")
        return unique_results
    
    def filter_valid_results(self, results, max_results=15):
        """Filter results by checking protection and validity"""
        valid_results = []
        
        for url in results:
            if len(valid_results) >= max_results:
                break
                
            try:
                # Skip URLs that are clearly not stores
                if any(x in url for x in ['google.', 'bing.', 'youtube.', 'facebook.']):
                    continue
                    
                if not self.check_protection(url):
                    valid_results.append(url)
                    print(f"Found valid URL: {url}")
            except:
                continue
            
            time.sleep(0.3)
        
        return valid_results

def is_real_store(soup, text):
    """Check if the website appears to be a real e-commerce store"""
    store_indicators = [
        'cart', 'add to cart', 'product', 'shop', 'store', 
        'buy now', 'checkout', 'shopping', 'price', '$', '€', '£',
        'add to basket', 'shopping cart', 'add to bag'
    ]
    
    if not soup:
        return False
    
    content = text.lower()
    
    # Check for multiple e-commerce indicators
    indicators_found = sum(1 for indicator in store_indicators if indicator in content)
    
    # Also check for common e-commerce HTML elements
    ecommerce_elements = soup.find_all(['form', 'button', 'input'], {
        'type': ['submit', 'button'],
        'value': lambda x: x and any(word in x.lower() for word in ['add', 'buy', 'cart', 'checkout'])
    })
    
    return indicators_found >= 2 or len(ecommerce_elements) > 0

def find_gateways(text):
    """Find payment gateways mentioned in the text"""
    found = set()
    text_lower = text.lower()
    
    for gateway in gateways:
        gateway_lower = gateway.lower()
        # Simple string search for better matching
        if gateway_lower in text_lower:
            found.add(gateway)
    
    # Additional checks for common payment indicators
    payment_indicators = [
        ('credit card', 'Credit Card'),
        ('debit card', 'Debit Card'),
        ('visa', 'Visa'),
        ('mastercard', 'MasterCard'),
        ('amex', 'American Express'),
        ('payment method', 'Payment Method'),
        ('checkout', 'Checkout')
    ]
    
    for indicator, name in payment_indicators:
        if indicator in text_lower:
            found.add(name)
    
    return found

def analyze_store(url):
    """Analyze a single store"""
    try:
        ua = UserAgent()
        headers = {'User-Agent': ua.random}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return None
            
        soup = BeautifulSoup(response.content, 'html.parser')
        text = response.text
        
        # Check if it's a real store
        if not is_real_store(soup, text):
            return None
        
        # Check for various features
        captcha = 'captcha' in text.lower()
        cloudflare = 'cloudflare' in text.lower() or 'cf-ray' in response.headers
        vbv = bool(re.search(r'3d[\s\-]?secure|vbv', text, re.I))
        
        # Find payment gateways
        gateways_found = find_gateways(text)
        
        # Check for authentication
        is_auth = any(x in text.lower() for x in ['login', 'signin', 'register', 'account', 'my-account'])
        
        return {
            'url': url,
            'real_store': True,
            'gateways': list(gateways_found),
            'gateways_count': len(gateways_found),
            'cloudflare': cloudflare,
            'auth': is_auth,
            'captcha': captcha,
            'vbv': vbv
        }
        
    except Exception as e:
        print(f"Error analyzing {url}: {e}")
        return None

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
        result = analyze_store(url)
        
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
        # Get query parameters
        pages = int(request.args.get('pages', 2))
        max_results = int(request.args.get('max_results', 10))
        gateways_count = int(request.args.get('gateways_count', 0))  # 0 means any
        
        # More effective e-commerce search queries
        ecommerce_queries = [
            '"add to cart" "buy now"',
            '"online store" "products"',
            '"shop now" "free shipping"',
            '"ecommerce" "checkout"',
            '"buy" "price" "shopping"',
            '"clothing store" "online shop"',
            '"electronics" "add to cart"'
        ]
        
        tool = DorkSearchTool()
        all_valid_results = []
        
        # Search with multiple queries
        for query in ecommerce_queries[:3]:  # Use first 3 queries
            print(f"Searching for: {query}")
            results = tool.search_all_engines(query, pages)
            valid_results = tool.filter_valid_results(results, max_results)
            all_valid_results.extend(valid_results)
            
            if len(all_valid_results) >= max_results:
                break
        
        # Remove duplicates
        all_valid_results = list(set(all_valid_results))
        print(f"Found {len(all_valid_results)} unique URLs to analyze")
        
        # Analyze stores
        analyzed_stores = []
        
        for url in all_valid_results[:max_results]:
            result = analyze_store(url)
            if result:
                # Check if meets gateway count requirement
                if gateways_count == 0 or result['gateways_count'] >= gateways_count:
                    analyzed_stores.append(result)
            
            # Be polite with delays
            time.sleep(0.5)
        
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

@app.route('/test', methods=['GET'])
def test_search():
    """Test endpoint to verify search is working"""
    try:
        tool = DorkSearchTool()
        results = tool.search_google('"add to cart" "buy now"', 1)
        return jsonify({
            'results': results,
            'count': len(results),
            'status': 'success'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
