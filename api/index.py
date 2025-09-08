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
        """Setup requests session with retry logic"""
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def search_google(self, query, num_pages=3):
        """Search Google using dork queries"""
        results = []
        try:
            for page in range(num_pages):
                start = page * 10
                url = f"https://www.google.com/search?q={quote_plus(query)}&start={start}"
                
                headers = {
                    'User-Agent': random.choice(self.user_agents),
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                }
                
                response = self.session.get(url, headers=headers, timeout=30)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract search results
                for g in soup.find_all('div', class_='tF2Cxc'):
                    link = g.find('a')
                    if link and link.get('href'):
                        results.append(link['href'])
                
                time.sleep(random.uniform(2, 5))
                
        except Exception as e:
            logger.error(f"Google search error: {e}")
        
        return results

    def is_real_store(self, soup, text):
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
        
        text_lower = text.lower()
        score = 0
        
        for indicator in store_indicators:
            if indicator.lower() in text_lower:
                score += 1
        
        # Check for forms and buttons
        forms = soup.find_all('form')
        buttons = soup.find_all('button')
        inputs = soup.find_all('input')
        
        if any('cart' in str(form).lower() for form in forms):
            score += 2
        if any('buy' in str(button).lower() or 'add' in str(button).lower() for button in buttons):
            score += 2
        if any('quantity' in str(input_tag).lower() or 'price' in str(input_tag).lower() for input_tag in inputs):
            score += 2
        
        return score >= 5  # Minimum threshold to be considered a store

    def find_gateways(self, text):
        """Find payment gateways mentioned in the text"""
        found = set()
        if not text:
            return found
            
        text_lower = text.lower()
        for gateway in gateways:
            if gateway.lower() in text_lower:
                found.add(gateway)
        
        return found

    def analyze_store(self, url):
        """Analyze a single store"""
        try:
            ua = UserAgent()
            headers = {'User-Agent': ua.random}
            
            response = self.session.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            text = soup.get_text()
            
            # Check if it's a real store
            is_store = self.is_real_store(soup, text)
            
            # Find payment gateways
            found_gateways = self.find_gateways(text)
            
            # Additional analysis can be added here
            
            return {
                'url': url,
                'is_store': is_store,
                'gateways': list(found_gateways),
                'gateways_count': len(found_gateways),
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"Error analyzing {url}: {e}")
            return {
                'url': url,
                'is_store': False,
                'gateways': [],
                'gateways_count': 0,
                'status': 'error',
                'error': str(e)
            }

def safe_int(value, default=0):
    """Safely convert value to integer, return default if conversion fails"""
    try:
        return int(value) if value else default
    except (ValueError, TypeError):
        return default

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
        return jsonify({'error': 'URL parameter is required'}), 400
    
    try:
        tool = DorkSearchTool()
        result = tool.analyze_store(url)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in analyze_single_store: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/cvn', methods=['GET'])
def find_ecommerce_stores():
    """API endpoint to find e-commerce stores and analyze them"""
    try:
        # Get query parameters with safe conversion
        pages = safe_int(request.args.get('pages'), 3)
        max_results = safe_int(request.args.get('max_results'), 30)
        gateways_count = safe_int(request.args.get('gateways_count'), 0)
        
        cloudflare_filter = request.args.get('cloudflare')
        auth_filter = request.args.get('auth')
        captcha_filter = request.args.get('captcha')
        vbv_filter = request.args.get('vbv')
        gateway_type = request.args.get('gateway_type')
        bot_token = request.args.get('bot_token')
        chat_id = request.args.get('chat_id')
        
        # Your search and analysis logic here
        tool = DorkSearchTool()
        
        # Example search query
        query = '"add to cart" "buy now"'
        search_results = tool.search_google(query, pages)
        
        # Analyze results
        analyzed_stores = []
        for url in search_results[:max_results]:
            result = tool.analyze_store(url)
            if result['is_store'] and result['gateways_count'] >= gateways_count:
                analyzed_stores.append(result)
        
        return jsonify({
            'stores_found': len(analyzed_stores),
            'stores': analyzed_stores,
            'status': 'success'
        })
        
    except Exception as e:
        logger.error(f"Error in find_ecommerce_stores: {e}")
        return jsonify({'error': str(e)}), 500

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
