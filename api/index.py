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
    'Stripe', 'PayPal', 'Braintree', 'Razorpay', 'Authorize.Net',
    '2Checkout', 'Mollie', 'Google Pay', 'Checkout.com', 'BlueSnap',
    'Adyen', 'WooCommerce', 'Shopify', 'Square', 'Amazon Pay',
    'Skrill', 'WePay', 'PayU', 'Payoneer', 'TransferWise'
]

# Global lock for thread-safe operations
analysis_lock = threading.Lock()

class DorkSearchTool:
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (iPad; CPU OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36'
        ]
    
    def get_random_agent(self):
        return random.choice(self.user_agents)
    
    def check_protection(self, url):
        """Check if URL has protection like CAPTCHA"""
        try:
            headers = {'User-Agent': self.get_random_agent()}
            res = requests.get(url, headers=headers, timeout=8, allow_redirects=True)
            content = res.text.lower()
            protection_indicators = ['captcha', 'cloudflare', 'security check', 'firewall', 'ddos protection', 'access denied']
            return any(x in content for x in protection_indicators)
        except:
            return False
    
    def search_google(self, query, pages=3):
        """Search using Google with improved parsing"""
        results = []
        for page in range(pages):
            try:
                start = page * 10
                url = f"https://www.google.com/search?q={quote_plus(query)}&start={start}&num=100"
                
                headers = {'User-Agent': self.get_random_agent()}
                response = requests.get(url, headers=headers, timeout=20)
                
                if response.status_code != 200:
                    print(f"Google search returned status {response.status_code}")
                    continue
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find all search result links
                for a in soup.find_all('a', href=True):
                    href = a['href']
                    if href.startswith('/url?q='):
                        try:
                            link = href.split('/url?q=')[1].split('&')[0]
                            parsed_url = urlparse(link)
                            if parsed_url.netloc and 'google.com' not in parsed_url.netloc:
                                if link not in results:
                                    results.append(link)
                        except:
                            continue
                
                time.sleep(random.uniform(2, 4))
                
            except Exception as e:
                print(f"Google search error: {e}")
                continue
        
        return results
    
    def search_bing(self, query, pages=3):
        """Search using Bing"""
        results = []
        for page in range(1, pages + 1):
            try:
                url = f"https://www.bing.com/search?q={quote_plus(query)}&first={(page-1)*10+1}&count=50"
                
                headers = {'User-Agent': self.get_random_agent()}
                response = requests.get(url, headers=headers, timeout=20)
                
                if response.status_code != 200:
                    print(f"Bing search returned status {response.status_code}")
                    continue
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find organic results
                for li in soup.find_all('li', class_='b_algo'):
                    a = li.find('a')
                    if a and a.has_attr('href'):
                        href = a['href']
                        if href.startswith('http') and 'bing.com' not in href:
                            if href not in results:
                                results.append(href)
                
                time.sleep(random.uniform(2, 3))
                
            except Exception as e:
                print(f"Bing search error: {e}")
                continue
        
        return results
    
    def search_yahoo(self, query, pages=2):
        """Search using Yahoo"""
        results = []
        for page in range(1, pages + 1):
            try:
                url = f"https://search.yahoo.com/search?p={quote_plus(query)}&b={(page-1)*10+1}"
                
                headers = {'User-Agent': self.get_random_agent()}
                response = requests.get(url, headers=headers, timeout=20)
                
                if response.status_code != 200:
                    continue
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find search results
                for a in soup.find_all('a', href=True):
                    href = a['href']
                    if href.startswith('http') and 'yahoo.com' not in href:
                        if href not in results:
                            results.append(href)
                
                time.sleep(random.uniform(2, 3))
                
            except Exception as e:
                print(f"Yahoo search error: {e}")
                continue
        
        return results
    
    def search_duckduckgo(self, query, pages=2):
        """Search using DuckDuckGo"""
        results = []
        for page in range(1, pages + 1):
            try:
                url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}&s={(page-1)*30}"
                
                headers = {'User-Agent': self.get_random_agent()}
                response = requests.get(url, headers=headers, timeout=20)
                
                if response.status_code != 200:
                    continue
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find result links
                for link in soup.find_all('a', class_='result__url'):
                    href = link.get('href')
                    if href and href.startswith('http'):
                        if href not in results:
                            results.append(href)
                
                time.sleep(random.uniform(1, 2))
                
            except Exception as e:
                print(f"DuckDuckGo search error: {e}")
                continue
        
        return results
    
    def search_brave(self, query, pages=2):
        """Search using Brave"""
        results = []
        for page in range(1, pages + 1):
            try:
                url = f"https://search.brave.com/search?q={quote_plus(query)}&offset={(page-1)*10}"
                
                headers = {'User-Agent': self.get_random_agent()}
                response = requests.get(url, headers=headers, timeout=20)
                
                if response.status_code != 200:
                    continue
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find result links
                for a in soup.find_all('a', href=True):
                    href = a['href']
                    if href.startswith('http') and 'brave.com' not in href:
                        if href not in results:
                            results.append(href)
                
                time.sleep(random.uniform(1, 2))
                
            except Exception as e:
                print(f"Brave search error: {e}")
                continue
        
        return results
    
    def search_all_engines(self, query, pages=2):
        """Search using all available search engines"""
        all_results = []
        
        print(f"🔍 Searching for: {query}")
        
        # Search all engines in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(self.search_google, query, pages): "Google",
                executor.submit(self.search_bing, query, pages): "Bing",
                executor.submit(self.search_yahoo, query, pages): "Yahoo",
                executor.submit(self.search_duckduckgo, query, pages): "DuckDuckGo",
                executor.submit(self.search_brave, query, pages): "Brave"
            }
            
            for future in concurrent.futures.as_completed(futures):
                engine = futures[future]
                try:
                    results = future.result(timeout=30)
                    all_results.extend(results)
                    print(f"✅ {engine} found {len(results)} results")
                except Exception as e:
                    print(f"❌ {engine} search failed: {e}")
        
        # Remove duplicates
        unique_results = list(set(all_results))
        print(f"📊 Total unique results: {len(unique_results)}")
        return unique_results
    
    def filter_valid_results(self, results, max_results=50):
        """Filter results by checking protection and validity"""
        valid_results = []
        
        for url in results:
            if len(valid_results) >= max_results:
                break
                
            try:
                # Skip URLs that are clearly not stores
                if any(x in url.lower() for x in ['google.', 'bing.', 'youtube.', 'facebook.', 'twitter.', 'instagram.']):
                    continue
                    
                if not self.check_protection(url):
                    valid_results.append(url)
                    print(f"✅ Found valid URL: {url}")
            except Exception as e:
                print(f"❌ Error checking {url}: {e}")
                continue
            
            time.sleep(0.5)
        
        return valid_results

def is_real_store(soup, text):
    """Check if the website appears to be a real e-commerce store"""
    store_indicators = [
        'cart', 'add to cart', 'product', 'shop', 'store', 
        'buy now', 'checkout', 'shopping', 'price', '$', '€', '£',
        'add to basket', 'shopping cart', 'add to bag', 'shop now',
        'buy online', 'purchase', 'order now', 'add to wishlist',
        'quantity', 'in stock', 'out of stock', 'add to cart button',
        'shipping', 'delivery', 'returns', 'payment', 'checkout'
    ]
    
    if not soup or not text:
        return False
    
    content = text.lower()
    
    # Check for multiple e-commerce indicators
    indicators_found = sum(1 for indicator in store_indicators if indicator in content)
    
    # Check for e-commerce HTML elements
    ecommerce_elements = soup.find_all(['form', 'button', 'input', 'select'], {
        'type': ['submit', 'button', 'number'],
        'value': lambda x: x and any(word in x.lower() for word in ['add', 'buy', 'cart', 'checkout', 'shop'])
    })
    
    # Check for product elements
    product_elements = soup.find_all(['div', 'span'], class_=lambda x: x and any(
        word in x.lower() for word in ['product', 'price', 'cart', 'buy', 'shop']
    ))
    
    return indicators_found >= 3 or len(ecommerce_elements) > 2 or len(product_elements) > 3

def find_gateways(text):
    """Find payment gateways mentioned in the text"""
    found = set()
    if not text:
        return found
    
    text_lower = text.lower()
    
    for gateway in gateways:
        gateway_lower = gateway.lower()
        # Check for gateway name in text
        if gateway_lower in text_lower:
            found.add(gateway)
        
        # Also check for common variations
        variations = {
            'stripe': ['stripe.com', 'stripe payment'],
            'paypal': ['paypal.com', 'paypal checkout'],
            'braintree': ['braintreepayments.com'],
            'razorpay': ['razorpay.com'],
            'authorize.net': ['authorize.net'],
            'woocommerce': ['woocommerce.com', 'wc-']
        }
        
        if gateway_lower in variations:
            for variation in variations[gateway_lower]:
                if variation in text_lower:
                    found.add(gateway)
    
    # Additional checks for common payment indicators
    payment_indicators = [
        ('credit card', 'Credit Card'),
        ('debit card', 'Debit Card'),
        ('visa', 'Visa'),
        ('mastercard', 'MasterCard'),
        ('amex', 'American Express'),
        ('american express', 'American Express'),
        ('discover', 'Discover'),
        ('payment method', 'Payment Method'),
        ('checkout', 'Checkout'),
        ('pay with', 'Payment System')
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
        response = requests.get(url, headers=headers, timeout=15)
        
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
        is_auth = any(x in text.lower() for x in ['login', 'signin', 'register', 'account', 'my-account', 'sign up'])
        
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
        print(f"❌ Error analyzing {url}: {e}")
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
        pages = int(request.args.get('pages', 3))
        max_results = int(request.args.get('max_results', 30))
        gateways_count = int(request.args.get('gateways_count', 0))
        
        # Comprehensive e-commerce search queries
        ecommerce_queries = [
            '"add to cart" "buy now"',
            '"online store" "products"',
            '"shop now" "free shipping"',
            '"ecommerce" "checkout"',
            '"buy" "price" "shopping"',
            '"clothing store" "online shop"',
            '"electronics" "add to cart"',
            '"digital products" "buy now"',
            '"jewelry" "online store"',
            '"home decor" "shop online"',
            '"beauty products" "buy"',
            '"sports equipment" "online store"',
            '"books" "online bookstore"',
            '"toys" "shop online"',
            '"food" "online delivery"'
        ]
        
        tool = DorkSearchTool()
        all_valid_results = []
        
        # Search with multiple queries
        for query in ecommerce_queries:
            print(f"🔍 Searching for: {query}")
            results = tool.search_all_engines(query, pages)
            valid_results = tool.filter_valid_results(results, max_results)
            all_valid_results.extend(valid_results)
            
            if len(all_valid_results) >= max_results * 2:  # Get more URLs for filtering
                break
        
        # Remove duplicates
        all_valid_results = list(set(all_valid_results))
        print(f"📊 Found {len(all_valid_results)} unique URLs to analyze")
        
        # Analyze stores with threading
        analyzed_stores = []
        
        def analyze_url(url):
            result = analyze_store(url)
            if result and (gateways_count == 0 or result['gateways_count'] >= gateways_count):
                return result
            return None
        
        # Use threading for faster analysis
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_url = {executor.submit(analyze_url, url): url for url in all_valid_results[:max_results*2]}
            
            for future in concurrent.futures.as_completed(future_to_url):
                result = future.result()
                if result:
                    analyzed_stores.append(result)
                    if len(analyzed_stores) >= max_results:
                        break
        
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
            'results': results[:5],  # Return first 5 results
            'count': len(results),
            'status': 'success'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
