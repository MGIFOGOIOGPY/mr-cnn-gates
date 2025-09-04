from flask import Flask, request, jsonify
import requests
import re
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from urllib.parse import urlparse, urlunparse
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Payment gateway patterns
gateways = [
    r'Stripe', r'PayPal', r'Braintree', r'tradesafe', r'Razorpay', r'AWS', r'AVS',
    r'eway', r'Authorize\\.Net', r'2Checkout', r'Mollie', r'Google Pay', r'Checkout\\.com',
    r'BlueSnap', r'Adyen', r'woocommerce', r'authorize_net_cim_credit_card'
]

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
    store_keywords = ['cart', 'add to cart', 'product', 'shop', 'store', 'buy now']
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

@app.route('/analyze', methods=['GET'])
def analyze_store():
    """API endpoint to analyze an e-commerce store"""
    url = request.args.get('url')
    
    if not url:
        return jsonify({
            'error': 'URL parameter is required',
            'api_by': '@R_O_P_D'
        }), 400
    
    if not url.startswith("http"):
        return jsonify({
            'error': 'Invalid URL. Please provide a URL starting with http or https',
            'api_by': '@R_O_P_D'
        }), 400
    
    try:
        ua = UserAgent()
        headers = {'User-Agent': ua.random}
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.content, 'html.parser')
        text = response.text
        
        # Check for various features
        captcha = 'captcha' in text.lower()
        cloudflare = 'cloudflare' in text.lower()
        vbv = bool(re.search(r'3D[\s\-]?Secure|VBV|threeD[\s\-]?SecureInfo', text, re.I))
        
        # Check for authentication pages
        is_auth = check_path_exists(url, '/my-account', ua)
        
        # Check if it's a real store
        store = is_real_store(soup)
        
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

        # Prepare response
        result = {
            'url': url,
            'real_store': store,
            'gateways': list(gateways_found) if gateways_found else [],
            'cloudflare': cloudflare,
            'auth': is_auth,
            'captcha': captcha,
            'vbv': vbv,
            'api_by': '@R_O_P_D',
            'message': 'Analysis completed successfully'
        }
        
        return jsonify(result)
        
    except requests.exceptions.Timeout:
        return jsonify({
            'error': 'Request timeout. The website took too long to respond.',
            'api_by': '@R_O_P_D'
        }), 408
    except requests.exceptions.RequestException as e:
        return jsonify({
            'error': f'Network error: {str(e)}',
            'api_by': '@R_O_P_D'
        }), 502
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
