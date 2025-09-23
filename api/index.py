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
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Payment gateway patterns - expanded
gateways = [
    'Stripe', 'PayPal', 'Braintree', 'Razorpay', 'Authorize.Net',
    '2Checkout', 'Mollie', 'Google Pay', 'Checkout.com', 'BlueSnap',
    'Adyen', 'WooCommerce', 'Shopify', 'Square', 'Amazon Pay',
    'Skrill', 'WePay', 'PayU', 'Payoneer', 'TransferWise', 'SagePay',
    'WorldPay', 'Klarna', 'Afterpay', 'Affirm', 'iZettle', 'Paytm',
    'Alipay', 'WeChat Pay', 'Apple Pay', 'Samsung Pay', 'Visa Checkout',
    'Masterpass', 'Dwolla', 'PayTrace', 'Fortumo', 'Boleto', 'Pagar.me',
    'MercadoPago', 'WebMoney', 'Yandex.Money', 'Qiwi', 'GiroPay', 'Sofort',
    'Ideal', 'Bancontact', 'Multibanco', 'Przelewy24', 'Payeer', 'Perfect Money',
    'PaySafeCard', 'Epay', 'Neteller', 'Moneybookers', 'ClickandBuy', 'CashU',
    'OneCard', 'PayOp', 'Coinbase', 'BitPay', 'CoinPayments', 'Cryptopay'
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
        self.session = None
        self.search_engines = [
            'google', 'bing', 'yahoo', 'duckduckgo', 
            'brave', 'yandex', 'baidu', 'aol', 'ask',
            'dogpile', 'startpage', 'qwant', 'ecosia'
        ]
    
    def get_session(self):
        if not self.session:
            self.session = requests.Session()
        return self.session
    
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
    
    def search_google(self, query, pages=5):
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
                
                time.sleep(random.uniform(0.5, 1.5))
                
            except Exception as e:
                print(f"Google search error: {e}")
                continue
        
        return results
    
    def search_bing(self, query, pages=5):
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
                
                time.sleep(random.uniform(0.5, 1.5))
                
            except Exception as e:
                print(f"Bing search error: {e}")
                continue
        
        return results
    
    def search_yahoo(self, query, pages=4):
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
                
                time.sleep(random.uniform(0.5, 1.5))
                
            except Exception as e:
                print(f"Yahoo search error: {e}")
                continue
        
        return results
    
    def search_duckduckgo(self, query, pages=4):
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
                
                time.sleep(random.uniform(0.3, 1))
                
            except Exception as e:
                print(f"DuckDuckGo search error: {e}")
                continue
        
        return results
    
    def search_brave(self, query, pages=4):
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
                
                time.sleep(random.uniform(0.3, 1))
                
            except Exception as e:
                print(f"Brave search error: {e}")
                continue
        
        return results
    
    def search_yandex(self, query, pages=3):
        """Search using Yandex"""
        results = []
        for page in range(0, pages):
            try:
                url = f"https://yandex.com/search/?text={quote_plus(query)}&p={page}"
                
                headers = {'User-Agent': self.get_random_agent()}
                response = requests.get(url, headers=headers, timeout=20)
                
                if response.status_code != 200:
                    continue
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find result links
                for a in soup.find_all('a', class_='link organic__url'):
                    href = a.get('href')
                    if href and href.startswith('http') and 'yandex' not in href:
                        if href not in results:
                            results.append(href)
                
                time.sleep(random.uniform(0.3, 1))
                
            except Exception as e:
                print(f"Yandex search error: {e}")
                continue
        
        return results
    
    def search_baidu(self, query, pages=3):
        """Search using Baidu"""
        results = []
        for page in range(0, pages):
            try:
                url = f"https://www.baidu.com/s?wd={quote_plus(query)}&pn={page*10}"
                
                headers = {'User-Agent': self.get_random_agent()}
                response = requests.get(url, headers=headers, timeout=20)
                
                if response.status_code != 200:
                    continue
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find result links
                for a in soup.find_all('a', href=True):
                    href = a.get('href')
                    if href and ('http://' in href or 'https://' in href) and 'baidu.com' not in href:
                        if href not in results:
                            results.append(href)
                
                time.sleep(random.uniform(0.3, 1))
                
            except Exception as e:
                print(f"Baidu search error: {e}")
                continue
        
        return results
    
    def search_aol(self, query, pages=2):
        """Search using AOL"""
        results = []
        for page in range(0, pages):
            try:
                url = f"https://search.aol.com/aol/search?q={quote_plus(query)}&page={page+1}"
                
                headers = {'User-Agent': self.get_random_agent()}
                response = requests.get(url, headers=headers, timeout=20)
                
                if response.status_code != 200:
                    continue
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find result links
                for a in soup.find_all('a', href=True):
                    href = a.get('href')
                    if href and href.startswith('http') and 'aol.com' not in href:
                        if href not in results:
                            results.append(href)
                
                time.sleep(random.uniform(0.3, 1))
                
            except Exception as e:
                print(f"AOL search error: {e}")
                continue
        
        return results
    
    def search_ask(self, query, pages=2):
        """Search using Ask.com"""
        results = []
        for page in range(0, pages):
            try:
                url = f"https://www.ask.com/web?q={quote_plus(query)}&page={page+1}"
                
                headers = {'User-Agent': self.get_random_agent()}
                response = requests.get(url, headers=headers, timeout=20)
                
                if response.status_code != 200:
                    continue
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find result links
                for a in soup.find_all('a', href=True):
                    href = a.get('href')
                    if href and href.startswith('http') and 'ask.com' not in href:
                        if href not in results:
                            results.append(href)
                
                time.sleep(random.uniform(0.3, 1))
                
            except Exception as e:
                print(f"Ask search error: {e}")
                continue
        
        return results
    
    def search_all_engines(self, query, pages=3, engines=None):
        """Search using multiple search engines"""
        all_results = []
        
        print(f"🔍 Searching for: {query}")
        
        if engines is None:
            engines = self.search_engines
        
        # Map engine names to methods
        engine_methods = {
            'google': self.search_google,
            'bing': self.search_bing,
            'yahoo': self.search_yahoo,
            'duckduckgo': self.search_duckduckgo,
            'brave': self.search_brave,
            'yandex': self.search_yandex,
            'baidu': self.search_baidu,
            'aol': self.search_aol,
            'ask': self.search_ask
        }
        
        # Search selected engines in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(engines)) as executor:
            futures = {}
            
            for engine in engines:
                if engine in engine_methods:
                    futures[executor.submit(engine_methods[engine], query, pages)] = engine
            
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
        
        # Use threading for faster protection checking
        def check_url_protection(url):
            try:
                # Skip URLs that are clearly not stores
                if any(x in url.lower() for x in ['google.', 'bing.', 'youtube.', 'facebook.', 'twitter.', 'instagram.']):
                    return None
                    
                if not self.check_protection(url):
                    return url
            except Exception as e:
                print(f"❌ Error checking {url}: {e}")
            return None
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
            future_to_url = {executor.submit(check_url_protection, url): url for url in results}
            
            for future in concurrent.futures.as_completed(future_to_url):
                if len(valid_results) >= max_results:
                    break
                    
                result = future.result()
                if result:
                    valid_results.append(result)
                    print(f"✅ Found valid URL: {result}")
        
        return valid_results

def is_real_store(soup, text):
    """Check if the website appears to be a real e-commerce store"""
    store_indicators = [
        'cart', 'add to cart', 'product', 'shop', 'store', 
        'buy now', 'checkout', 'shopping', 'price', '$', '€', '£',
        'add to basket', 'shopping cart', 'add to bag', 'shop now',
        'buy online', 'purchase', 'order now', 'add to wishlist',
        'quantity', 'in stock', 'out of stock', 'add to cart button',
        'shipping', 'delivery', 'returns', 'payment', 'checkout',
        'items in cart', 'proceed to checkout', 'place order',
        'your cart', 'shopping bag', 'my cart', 'view cart',
        'continue shopping', 'product description', 'product details',
        'customer reviews', 'add to cart', 'buy now button'
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
        word in x.lower() for word in ['product', 'price', 'cart', 'buy', 'shop', 'item', 'stock', 'shipping']
    ))
    
    # Check for shopping cart icons
    cart_icons = soup.find_all('i', class_=lambda x: x and any(
        word in x.lower() for word in ['cart', 'shopping', 'bag', 'basket']
    ))
    
    return indicators_found >= 3 or len(ecommerce_elements) > 2 or len(product_elements) > 3 or len(cart_icons) > 0

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
            'stripe': ['stripe.com', 'stripe payment', 'stripe.js', 'stripe-api', 'stripecheckout'],
            'paypal': ['paypal.com', 'paypal checkout', 'paypal-button', 'paypalobjects.com'],
            'braintree': ['braintreepayments.com', 'braintreegateway.com', 'braintree-api'],
            'razorpay': ['razorpay.com', 'razorpaycheckout', 'razorpay.js'],
            'authorize.net': ['authorize.net', 'authorizenet.com', 'authorize-api'],
            'woocommerce': ['woocommerce.com', 'wc-', 'woocommerce-api', 'woocommerce_checkout'],
            'shopify': ['shopify.com', 'shopify-api', 'shopify-checkout', 'shopify.js'],
            'square': ['squareup.com', 'square-api', 'square-payments'],
            'adyen': ['adyen.com', 'adyen-api', 'adyen-payments'],
            '2checkout': ['2checkout.com', '2co.com', 'avangate.com'],
            'mollie': ['mollie.com', 'mollie-api', 'mollie-payments'],
            'klarna': ['klarna.com', 'klarna-api', 'klarna-payments'],
            'amazon pay': ['amazonpay.com', 'amazon-pay', 'amazonpayments'],
            'google pay': ['google-pay', 'googlepay.com', 'google-pay-api'],
            'apple pay': ['apple-pay', 'applepay.com', 'apple-pay-api'],
            'alipay': ['alipay.com', 'alipay-api', 'alipay-payment'],
            'wechat pay': ['wechat-pay', 'wechatpay.com', 'wechat-payment'],
            'bitpay': ['bitpay.com', 'bitpay-api', 'bitpay-payment'],
            'coinbase': ['coinbase.com', 'coinbase-commerce', 'coinbase-payment']
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
        ('pay with', 'Payment System'),
        ('card number', 'Credit Card'),
        ('expiry date', 'Credit Card'),
        ('cvv', 'Credit Card'),
        ('billing address', 'Billing Information'),
        ('payment gateway', 'Payment Gateway'),
        ('payment processor', 'Payment Processor'),
        ('secure payment', 'Secure Payment'),
        ('payment options', 'Payment Options'),
        ('payment information', 'Payment Information')
    ]
    
    for indicator, name in payment_indicators:
        if indicator in text_lower:
            found.add(name)
    
    # Regex patterns for payment gateways
    patterns = [
        (r'stripe\.com\/[vp]\d+', 'Stripe'),
        (r'js\.stripe\.com', 'Stripe'),
        (r'paypal\.com\/[a-z]+\/checkout', 'PayPal'),
        (r'www\.paypalobjects\.com', 'PayPal'),
        (r'braintreegateway\.com', 'Braintree'),
        (r'checkout\.razorpay\.com', 'Razorpay'),
        (r'api\.razorpay\.com', 'Razorpay'),
        (r'authorize\.net', 'Authorize.Net'),
        (r'2checkout\.com', '2Checkout'),
        (r'mollie\.com', 'Mollie'),
        (r'checkout\.shopify\.com', 'Shopify'),
        (r' Square\.com', 'Square'),
        (r'pay\.amazon\.com', 'Amazon Pay'),
        (r'skrill\.com', 'Skrill'),
        (r'wechatpay', 'WeChat Pay'),
        (r'alipay\.com', 'Alipay'),
        (r'bitpay\.com', 'BitPay'),
        (r'coinbase\.com\/commerce', 'Coinbase')
    ]
    
    for pattern, gateway in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            found.add(gateway)
    
    return found

def extract_prices(text):
    """Extract prices from text using regex patterns"""
    price_patterns = [
        r'\$\d+\.\d{2}',  # $10.99
        r'\$\d+',         # $10
        r'\d+\.\d{2}\$',  # 10.99$
        r'\d+\s*USD',     # 10 USD
        r'\d+\s*EUR',     # 10 EUR
        r'\d+\s*GBP',     # 10 GBP
        r'USD\s*\d+\.\d{2}',  # USD 10.99
        r'EUR\s*\d+\.\d{2}',  # EUR 10.99
        r'GBP\s*\d+\.\d{2}',  # GBP 10.99
        r'price:\s*\$\d+',    # Price: $10
        r'cost:\s*\$\d+',     # Cost: $10
    ]
    
    prices = []
    for pattern in price_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        prices.extend(matches)
    
    return prices

def has_low_price_products(prices, max_price=10):
    """Check if the store has products with prices below max_price"""
    if not prices:
        return False
    
    for price_str in prices:
        try:
            # Extract numeric value from price string
            price_value = float(re.search(r'\d+\.?\d*', price_str.replace('$', '')).group())
            if price_value <= max_price:
                return True
        except:
            continue
    
    return False

def analyze_store(url, target_price=None, gateway_type=None, max_price=10):
    """Analyze a single store with price and gateway filtering - FOCUS ON LOW PRICES"""
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
        
        # Extract prices
        prices = extract_prices(text)
        
        # CRITICAL: Filter stores that have low price products (below max_price)
        if not has_low_price_products(prices, max_price):
            return None
        
        # Price filtering for specific target price
        if target_price:
            price_found = False
            for price_str in prices:
                try:
                    # Extract numeric value from price string
                    price_value = float(re.search(r'\d+\.?\d*', price_str.replace('$', '')).group())
                    if abs(price_value - target_price) <= 0.1:  # Allow small floating point differences
                        price_found = True
                        break
                except:
                    continue
            
            if not price_found:
                return None
        
        # Find payment gateways
        gateways_found = find_gateways(text)
        
        # Gateway type filtering
        if gateway_type and gateway_type.lower() not in [g.lower() for g in gateways_found]:
            return None
        
        # Check for various features
        captcha = 'captcha' in text.lower()
        cloudflare = 'cloudflare' in text.lower() or 'cf-ray' in response.headers
        vbv = bool(re.search(r'3d[\s\-]?secure|vbv', text, re.I))
        
        # Check for authentication
        is_auth = any(x in text.lower() for x in ['login', 'signin', 'register', 'account', 'my-account', 'sign up', 'password', 'username'])
        
        # Calculate average price for ranking
        numeric_prices = []
        for price_str in prices:
            try:
                price_value = float(re.search(r'\d+\.?\d*', price_str.replace('$', '')).group())
                numeric_prices.append(price_value)
            except:
                continue
        
        avg_price = sum(numeric_prices) / len(numeric_prices) if numeric_prices else 0
        
        return {
            'url': url,
            'real_store': True,
            'gateways': list(gateways_found),
            'gateways_count': len(gateways_found),
            'prices_found': prices[:10],  # Return first 10 prices
            'average_price': round(avg_price, 2),
            'low_price_products': has_low_price_products(prices, max_price),
            'cloudflare': cloudflare,
            'auth': is_auth,
            'captcha': captcha,
            'vbv': vbv,
            'price_analysis': {
                'total_prices_found': len(prices),
                'prices_below_10': len([p for p in numeric_prices if p <= 10]),
                'min_price': min(numeric_prices) if numeric_prices else 0,
                'max_price': max(numeric_prices) if numeric_prices else 0
            }
        }
        
    except Exception as e:
        print(f"❌ Error analyzing {url}: {e}")
        return None

def send_telegram_message_sync(bot_token, chat_id, message):
    """Send message to Telegram bot synchronously"""
    try:
        import telegram
        bot = telegram.Bot(token=bot_token)
        bot.send_message(chat_id=chat_id, text=message, parse_mode='HTML')
        return True
    except Exception as e:
        print(f"❌ Telegram error: {e}")
        return False

@app.route('/analyze', methods=['GET'])
def analyze_single_store():
    """API endpoint to analyze a single e-commerce store"""
    url = request.args.get('url')
    target_price = request.args.get('target_price')
    gateway_type = request.args.get('gateway_type')
    max_price = float(request.args.get('max_price', 10))  # Default max price is 10
    
    if not url:
        return jsonify({
            'error': 'URL parameter is required',
            'api_by': '@R_O_P_D'
        }), 400
    
    if not url.startswith("http"):
        url = "https://" + url
    
    try:
        # Convert target_price to float if provided
        price_value = None
        if target_price:
            try:
                price_value = float(target_price)
            except ValueError:
                return jsonify({
                    'error': 'Invalid target_price format. Use numbers only (e.g., 1.99)',
                    'api_by': '@R_O_P_D'
                }), 400
        
        result = analyze_store(url, price_value, gateway_type, max_price)
        
        if not result:
            return jsonify({
                'error': 'This does not appear to be a valid e-commerce store or it doesn\'t have products with prices below ' + str(max_price),
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
    """API endpoint to find e-commerce stores and analyze them - FOCUS ON LOW PRICE STORES"""
    try:
        # Get query parameters
        pages = int(request.args.get('pages', 5))
        max_results = int(request.args.get('max_results', 50))
        gateways_count = int(request.args.get('gateways_count', 0))
        cloudflare_filter = request.args.get('cloudflare')
        auth_filter = request.args.get('auth')
        captcha_filter = request.args.get('captcha')
        vbv_filter = request.args.get('vbv')
        gateway_type = request.args.get('gateway_type')
        target_price = request.args.get('target_price')
        max_price = float(request.args.get('max_price', 10))  # Default max price is 10
        search_engines = request.args.get('search_engines')
        custom_query = request.args.get('custom_query')
        bot_token = request.args.get('bot_token')
        chat_id = request.args.get('chat_id')
        
        # Convert target_price to float if provided
        price_value = None
        if target_price:
            try:
                price_value = float(target_price)
            except ValueError:
                return jsonify({
                    'error': 'Invalid target_price format. Use numbers only (e.g., 1.99)',
                    'api_by': '@R_O_P_D'
                }), 400
        
        # Parse search engines
        engines_list = None
        if search_engines:
            engines_list = [engine.strip().lower() for engine in search_engines.split(',')]
        
        # CRITICAL: Focus on low price e-commerce search queries
        low_price_queries = [
            f'"$4" "add to cart"', f'"$10" "buy now"',
            f'"under $10" "online store"', f'"cheap" "products"',
            f'"low price" "shopping"', f'"affordable" "buy now"',
            f'"$5" "shop"', f'"$7" "store"', f'"$8" "ecommerce"',
            f'"budget" "online shop"', f'"discount" "add to cart"',
            f'"sale" "checkout"', f'"$6" "purchase"', f'"$9" "order"',
            f'"inexpensive" "shopping cart"', f'"$3" "payment"',
            f'"$2" "credit card"', f'"$1" "buy online"',
            f'"under $5" "digital products"', f'"$4.99" "shop now"',
            f'"$9.99" "free shipping"', f'"low cost" "add to basket"',
            f'"$0.99" "checkout"', f'"$1.99" "place order"',
            f'"$2.99" "payment method"', f'"$3.99" "secure checkout"',
            f'"$4.99" "shopping"', f'"$5.99" "online store"',
            f'"$6.99" "e-commerce"', f'"$7.99" "web store"',
            f'"$8.99" "buy"', f'"$9.99" "purchase online"'
        ]
        
        # Add custom query if provided
        if custom_query:
            low_price_queries.insert(0, custom_query)
        else:
            # Add price-specific queries based on target price
            if price_value:
                price_queries = [
                    f'"{price_value}" "add to cart"',
                    f'"{price_value}" "buy now"',
                    f'"{price_value}" "price"',
                    f'"{price_value}" "shop"',
                    f'"{price_value}" "product"'
                ]
                low_price_queries = price_queries + low_price_queries
        
        tool = DorkSearchTool()
        all_valid_results = []
        
        # Search with low price focused queries
        for query in low_price_queries:
            print(f"🔍 Searching for low price stores: {query}")
            results = tool.search_all_engines(query, pages, engines_list)
            valid_results = tool.filter_valid_results(results, max_results)
            all_valid_results.extend(valid_results)
            
            if len(all_valid_results) >= max_results * 3:  # Get more URLs for filtering
                break
        
        # Remove duplicates
        all_valid_results = list(set(all_valid_results))
        print(f"📊 Found {len(all_valid_results)} unique URLs to analyze for low price stores")
        
        # Analyze stores with threading - FOCUS ON LOW PRICES
        analyzed_stores = []
        
        def analyze_url(url):
            result = analyze_store(url, price_value, gateway_type, max_price)
            if result:
                # Apply additional filters
                if gateways_count > 0 and result['gateways_count'] < gateways_count:
                    return None
                if cloudflare_filter and result['cloudflare'] != (cloudflare_filter.lower() == 'true'):
                    return None
                if auth_filter and result['auth'] != (auth_filter.lower() == 'true'):
                    return None
                if captcha_filter and result['captcha'] != (captcha_filter.lower() == 'true'):
                    return None
                if vbv_filter and result['vbv'] != (vbv_filter.lower() == 'true'):
                    return None
                
                return result
            return None
        
        # Use threading for faster analysis
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            future_to_url = {executor.submit(analyze_url, url): url for url in all_valid_results[:max_results*3]}
            
            for future in concurrent.futures.as_completed(future_to_url):
                result = future.result()
                if result:
                    analyzed_stores.append(result)
                    if len(analyzed_stores) >= max_results:
                        break
        
        # Sort stores by average price (lowest first)
        analyzed_stores.sort(key=lambda x: x.get('average_price', 999))
        
        # Prepare response
        response_data = {
            'stores_found': len(analyzed_stores),
            'stores': analyzed_stores,
            'api_by': '@R_O_P_D',
            'message': f'Low price e-commerce store search completed (max price: ${max_price})',
            'search_parameters': {
                'pages': pages,
                'max_results': max_results,
                'target_price': target_price,
                'max_price': max_price,
                'gateway_type': gateway_type,
                'search_engines': engines_list or 'all'
            },
            'price_statistics': {
                'stores_with_prices_below_10': len([s for s in analyzed_stores if s.get('average_price', 0) <= 10]),
                'lowest_price_found': min([s.get('average_price', 999) for s in analyzed_stores]) if analyzed_stores else 0,
                'highest_price_found': max([s.get('average_price', 0) for s in analyzed_stores]) if analyzed_stores else 0
            },
            'timestamp': datetime.now().isoformat()
        }
        
        # Send to Telegram if token and chat_id provided
        if bot_token and chat_id:
            message = f"<b>🔍 LOW PRICE E-commerce Store Analysis Results</b>\n\n"
            message += f"<b>Stores Found:</b> {len(analyzed_stores)}\n"
            message += f"<b>Target Price:</b> {target_price or 'Any'}\n"
            message += f"<b>Max Price Filter:</b> ${max_price}\n"
            message += f"<b>Gateway Type:</b> {gateway_type or 'Any'}\n"
            message += f"<b>Timestamp:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            for i, store in enumerate(analyzed_stores[:5]):  # Send first 5 stores
                message += f"<b>Store {i+1}:</b> {store['url']}\n"
                message += f"<b>Gateways:</b> {', '.join(store['gateways'])}\n"
                message += f"<b>Avg Price:</b> ${store.get('average_price', 0)}\n"
                message += f"<b>Prices Found:</b> {', '.join(store.get('prices_found', [])[:3])}\n"
                message += f"<b>Cloudflare:</b> {'Yes' if store['cloudflare'] else 'No'}\n"
                message += f"<b>Auth:</b> {'Yes' if store['auth'] else 'No'}\n"
                message += f"<b>Captcha:</b> {'Yes' if store['captcha'] else 'No'}\n"
                message += f"<b>VBV:</b> {'Yes' if store['vbv'] else 'No'}\n\n"
            
            if len(analyzed_stores) > 5:
                message += f"<i>... and {len(analyzed_stores) - 5} more low price stores</i>\n\n"
            
            message += f"<b>API by:</b> @R_O_P_D"
            
            # Send message in a separate thread to avoid blocking
            threading.Thread(target=send_telegram_message_sync, args=(bot_token, chat_id, message)).start()
        
        return jsonify(response_data)
        
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
        'message': 'Low Price E-commerce Store Analysis API is running',
        'api_by': '@R_O_P_D',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/test', methods=['GET'])
def test_search():
    """Test endpoint to verify search is working"""
    try:
        tool = DorkSearchTool()
        results = tool.search_google('"$4" "add to cart"', 1)
        return jsonify({
            'results': results[:5],  # Return first 5 results
            'count': len(results),
            'status': 'success'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/engines', methods=['GET'])
def list_search_engines():
    """List all available search engines"""
    tool = DorkSearchTool()
    return jsonify({
        'available_engines': tool.search_engines,
        'api_by': '@R_O_P_D'
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
