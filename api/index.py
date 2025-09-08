from flask import Flask, request, jsonify
import requests
import time
import random
import re
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urlparse, urljoin
from fake_useragent import UserAgent
from flask_cors import CORS
import concurrent.futures
import threading
import json
from datetime import datetime
import logging
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        self.setup_session()
    
    def setup_session(self):
        """Setup requests session with retry strategy"""
        if not self.session:
            retry_strategy = Retry(
                total=3,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["GET"],
                backoff_factor=1
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            self.session = requests.Session()
            self.session.mount("https://", adapter)
            self.session.mount("http://", adapter)
    
    def get_random_agent(self):
        return random.choice(self.user_agents)
    
    def check_protection(self, url):
        """Check if URL has protection like CAPTCHA"""
        try:
            headers = {'User-Agent': self.get_random_agent()}
            res = self.session.get(url, headers=headers, timeout=8, allow_redirects=True)
            content = res.text.lower()
            protection_indicators = ['captcha', 'cloudflare', 'security check', 'firewall', 'ddos protection', 'access denied']
            return any(x in content for x in protection_indicators)
        except Exception as e:
            logger.error(f"Protection check error for {url}: {e}")
            return False
    
    def extract_search_results(self, soup, engine):
        """Extract search results based on search engine"""
        results = []
        
        if engine == "google":
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
        elif engine == "bing":
            for li in soup.find_all('li', class_='b_algo'):
                a = li.find('a')
                if a and a.has_attr('href'):
                    href = a['href']
                    if href.startswith('http') and 'bing.com' not in href:
                        if href not in results:
                            results.append(href)
        elif engine == "yahoo":
            for a in soup.find_all('a', href=True):
                href = a['href']
                if href.startswith('http') and 'yahoo.com' not in href:
                    if href not in results:
                        results.append(href)
        elif engine == "duckduckgo":
            for link in soup.find_all('a', class_='result__url'):
                href = link.get('href')
                if href and href.startswith('http'):
                    if href not in results:
                        results.append(href)
        elif engine == "brave":
            for a in soup.find_all('a', href=True):
                href = a['href']
                if href.startswith('http') and 'brave.com' not in href:
                    if href not in results:
                        results.append(href)
        elif engine == "yandex":
            for a in soup.find_all('a', class_='link organic__url'):
                href = a.get('href')
                if href and href.startswith('http') and 'yandex' not in href:
                    if href not in results:
                        results.append(href)
        elif engine == "baidu":
            for a in soup.find_all('a', href=True):
                href = a.get('href')
                if href and ('http://' in href or 'https://' in href) and 'baidu.com' not in href:
                    if href not in results:
                        results.append(href)
        
        return results
    
    def search_engine(self, engine, query, pages=3):
        """Generic search engine function"""
        results = []
        base_urls = {
            "google": "https://www.google.com/search?q={}&start={}&num=100",
            "bing": "https://www.bing.com/search?q={}&first={}&count=50",
            "yahoo": "https://search.yahoo.com/search?p={}&b={}",
            "duckduckgo": "https://html.duckduckgo.com/html/?q={}&s={}",
            "brave": "https://search.brave.com/search?q={}&offset={}",
            "yandex": "https://yandex.com/search/?text={}&p={}",
            "baidu": "https://www.baidu.com/s?wd={}&pn={}"
        }
        
        if engine not in base_urls:
            return results
        
        for page in range(pages):
            try:
                if engine == "google":
                    url = base_urls[engine].format(quote_plus(query), page * 10)
                elif engine == "bing":
                    url = base_urls[engine].format(quote_plus(query), (page-1)*10+1)
                elif engine == "yahoo":
                    url = base_urls[engine].format(quote_plus(query), (page-1)*10+1)
                elif engine == "duckduckgo":
                    url = base_urls[engine].format(quote_plus(query), (page-1)*30)
                elif engine == "brave":
                    url = base_urls[engine].format(quote_plus(query), (page-1)*10)
                elif engine == "yandex":
                    url = base_urls[engine].format(quote_plus(query), page)
                elif engine == "baidu":
                    url = base_urls[engine].format(quote_plus(query), page*10)
                
                headers = {'User-Agent': self.get_random_agent()}
                response = self.session.get(url, headers=headers, timeout=20)
                
                if response.status_code != 200:
                    logger.warning(f"{engine.capitalize()} search returned status {response.status_code}")
                    continue
                
                soup = BeautifulSoup(response.text, 'html.parser')
                page_results = self.extract_search_results(soup, engine)
                results.extend(page_results)
                
                logger.info(f"{engine.capitalize()} page {page+1} found {len(page_results)} results")
                time.sleep(random.uniform(1, 2))
                
            except Exception as e:
                logger.error(f"{engine.capitalize()} search error: {e}")
                continue
        
        return results
    
    def search_google(self, query, pages=3):
        """Search using Google with improved parsing"""
        return self.search_engine("google", query, pages)
    
    def search_bing(self, query, pages=3):
        """Search using Bing"""
        return self.search_engine("bing", query, pages)
    
    def search_yahoo(self, query, pages=2):
        """Search using Yahoo"""
        return self.search_engine("yahoo", query, pages)
    
    def search_duckduckgo(self, query, pages=2):
        """Search using DuckDuckGo"""
        return self.search_engine("duckduckgo", query, pages)
    
    def search_brave(self, query, pages=2):
        """Search using Brave"""
        return self.search_engine("brave", query, pages)
    
    def search_yandex(self, query, pages=2):
        """Search using Yandex"""
        return self.search_engine("yandex", query, pages)
    
    def search_baidu(self, query, pages=2):
        """Search using Baidu"""
        return self.search_engine("baidu", query, pages)
    
    def search_all_engines(self, query, pages=2):
        """Search using all available search engines"""
        all_results = []
        
        logger.info(f"Searching for: {query}")
        
        # Search all engines in parallel
        search_methods = [
            (self.search_google, "Google"),
            (self.search_bing, "Bing"),
            (self.search_yahoo, "Yahoo"),
            (self.search_duckduckgo, "DuckDuckGo"),
            (self.search_brave, "Brave"),
            (self.search_yandex, "Yandex"),
            (self.search_baidu, "Baidu")
        ]
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=7) as executor:
            futures = {
                executor.submit(method, query, pages): name for method, name in search_methods
            }
            
            for future in concurrent.futures.as_completed(futures):
                engine = futures[future]
                try:
                    results = future.result(timeout=30)
                    all_results.extend(results)
                    logger.info(f"{engine} found {len(results)} results")
                except Exception as e:
                    logger.error(f"{engine} search failed: {e}")
        
        # Remove duplicates
        unique_results = list(set(all_results))
        logger.info(f"Total unique results: {len(unique_results)}")
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
                logger.error(f"Error checking {url}: {e}")
            return None
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_url = {executor.submit(check_url_protection, url): url for url in results}
            
            for future in concurrent.futures.as_completed(future_to_url):
                if len(valid_results) >= max_results:
                    break
                    
                result = future.result()
                if result:
                    valid_results.append(result)
                    logger.info(f"Found valid URL: {result}")
        
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

def analyze_store(url):
    """Analyze a single store"""
    try:
        ua = UserAgent()
        headers = {'User-Agent': ua.random}
        
        # Create a session with retry logic
        session = requests.Session()
        retry_strategy = Retry(
            total=2,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
            backoff_factor=1
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        
        response = session.get(url, headers=headers, timeout=15)
        
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
        is_auth = any(x in text.lower() for x in ['login', 'signin', 'register', 'account', 'my-account', 'sign up', 'password', 'username'])
        
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
        logger.error(f"Error analyzing {url}: {e}")
        return None

def send_telegram_message_sync(bot_token, chat_id, message):
    """Send message to Telegram bot synchronously"""
    try:
        import telegram
        bot = telegram.Bot(token=bot_token)
        bot.send_message(chat_id=chat_id, text=message, parse_mode='HTML')
        return True
    except Exception as e:
        logger.error(f"Telegram error: {e}")
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
        result = analyze_store(url)
        
        if not result:
            return jsonify({
                'error': 'This does not appear to be a valid e-commerce store',
                'api_by': '@R_O_P_D'
            }), 404
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in analyze_single_store: {e}")
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
        cloudflare_filter = request.args.get('cloudflare')
        auth_filter = request.args.get('auth')
        captcha_filter = request.args.get('captcha')
        vbv_filter = request.args.get('vbv')
        gateway_type = request.args.get('gateway_type')
        bot_token = request.args.get('bot_token')
        chat_id = request.args.get('chat_id')
        
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
            '"food" "online delivery"',
            '"add to cart button" "checkout"',
            '"proceed to checkout" "shopping cart"',
            '"place order" "payment method"',
            '"credit card" "secure checkout"',
            '"buy now button" "add to basket"'
        ]
        
        tool = DorkSearchTool()
        all_valid_results = []
        
        # Search with multiple queries
        for query in ecommerce_queries:
            logger.info(f"Searching for: {query}")
            results = tool.search_all_engines(query, pages)
            valid_results = tool.filter_valid_results(results, max_results)
            all_valid_results.extend(valid_results)
            
            if len(all_valid_results) >= max_results * 2:  # Get more URLs for filtering
                break
        
        # Remove duplicates
        all_valid_results = list(set(all_valid_results))
        logger.info(f"Found {len(all_valid_results)} unique URLs to analyze")
        
        # Analyze stores with threading
        analyzed_stores = []
        
        def analyze_url(url):
            result = analyze_store(url)
            if result:
                # Apply filters
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
                if gateway_type and gateway_type not in [g.lower() for g in result['gateways']]:
                    return None
                
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
        
        # Prepare response
        response_data = {
            'stores_found': len(analyzed_stores),
            'stores': analyzed_stores,
            'api_by': '@R_O_P_D',
            'message': 'E-commerce store search completed successfully',
            'timestamp': datetime.now().isoformat()
        }
        
        # Send to Telegram if token and chat_id provided
        if bot_token and chat_id:
            message = f"<b>🔍 E-commerce Store Analysis Results</b>\n\n"
            message += f"<b>Stores Found:</b> {len(analyzed_stores)}\n"
            message += f"<b>Timestamp:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            for i, store in enumerate(analyzed_stores[:5]):  # Send first 5 stores
                message += f"<b>Store {i+1}:</b> {store['url']}\n"
                message += f"<b>Gateways:</b> {', '.join(store['gateways'])}\n"
                message += f"<b>Cloudflare:</b> {'Yes' if store['cloudflare'] else 'No'}\n"
                message += f"<b>Auth:</b> {'Yes' if store['auth'] else 'No'}\n"
                message += f"<b>Captcha:</b> {'Yes' if store['captcha'] else 'No'}\n"
                message += f"<b>VBV:</b> {'Yes' if store['vbv'] else 'No'}\n\n"
            
            if len(analyzed_stores) > 5:
                message += f"<i>... and {len(analyzed_stores) - 5} more stores</i>\n\n"
            
            message += f"<b>API by:</b> @R_O_P_D"
            
            # Send message in a separate thread to avoid blocking
            threading.Thread(target=send_telegram_message_sync, args=(bot_token, chat_id, message)).start()
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error in find_ecommerce_stores: {e}")
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
        'api_by': '@R_O_P_D',
        'timestamp': datetime.now().isoformat()
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
        logger.error(f"Error in test_search: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
