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
import asyncio
import aiohttp
import backoff
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import urllib3
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc

# Disable insecure request warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Payment gateway patterns - expanded with verification patterns
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

# Gateway verification patterns (URLs, scripts, forms, etc.)
gateway_verification_patterns = {
    'Stripe': [
        r'js\.stripe\.com', r'stripe\.com/v3', r'stripe\.com/v2', 
        r'api\.stripe\.com', r'stripejs\.com', r'stripe-button',
        r'stripe-checkout', r'stripe-payment', r'stripe-form'
    ],
    'PayPal': [
        r'paypal\.com/sdk', r'paypal\.com/buttons', r'paypalobjects\.com',
        r'paypal\.com/checkout', r'paypal\.com/webapps', r'paypal-button',
        r'paypal-checkout', r'paypal-payment', r'paypal-form'
    ],
    'Braintree': [
        r'braintreegateway\.com', r'braintree-api\.com', r'braintree-checkout',
        r'braintree-payment', r'braintree-form', r'braintreejs\.com'
    ],
    'Razorpay': [
        r'razorpay\.com', r'checkout\.razorpay\.com', r'razorpay-checkout',
        r'razorpay-payment', r'razorpay-form', r'razorpayjs\.com'
    ],
    'Authorize.Net': [
        r'authorize\.net', r'secure\.authorize\.net', r'authorize-checkout',
        r'authorize-payment', r'authorize-form', r'authorizejs\.com'
    ],
    'Shopify': [
        r'shopify\.com', r'shopify-checkout', r'shopify-payment',
        r'shopify-form', r'shopifyjs\.com', r'shopify\.com/cdn'
    ],
    'WooCommerce': [
        r'woocommerce\.com', r'wc-', r'woocommerce-checkout',
        r'woocommerce-payment', r'woocommerce-form', r'woocommercejs\.com'
    ],
    'Square': [
        r'square\.com', r'square-up\.com', r'square-checkout',
        r'square-payment', r'square-form', r'squarejs\.com'
    ],
    'Amazon Pay': [
        r'amazonpay\.com', r'pay\.amazon\.com', r'amazon-checkout',
        r'amazon-payment', r'amazon-form', r'amazonpayjs\.com'
    ],
    'Google Pay': [
        r'google\.com/pay', r'google-pay', r'google-checkout',
        r'google-payment', r'google-form', r'googlepayjs\.com'
    ],
    'Apple Pay': [
        r'apple\.com/pay', r'apple-pay', r'apple-checkout',
        r'apple-payment', r'apple-form', r'applepayjs\.com'
    ],
    '2Checkout': [
        r'2checkout\.com', r'2co\.com', r'2checkout-checkout',
        r'2checkout-payment', r'2checkout-form', r'2checkoutjs\.com'
    ],
    'Adyen': [
        r'adyen\.com', r'adyen-checkout', r'adyen-payment',
        r'adyen-form', r'adyenjs\.com'
    ],
    'Klarna': [
        r'klarna\.com', r'klarna-checkout', r'klarna-payment',
        r'klarna-form', r'klarnajs\.com'
    ]
}

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
            'Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Brave Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15'
        ]
        
        # Create a session with retry strategy
        self.session = self.create_session()
        
        # Expanded list of search engines
        self.search_engines = [
            'google', 'bing', 'yahoo', 'duckduckgo', 
            'brave', 'yandex', 'baidu', 'aol', 'ask',
            'dogpile', 'startpage', 'qwant', 'ecosia',
            'gibiru', 'swisscows', 'mojeek', 'search_encrypt',
            'metager', 'yep', 'you', 'givewater'
        ]
        
        # Search engine configurations
        self.engine_configs = {
            'google': {
                'url': 'https://www.google.com/search?q={query}&start={start}&num=100',
                'pages_param': 'start',
                'increment': 10,
                'parser': self.parse_google
            },
            'bing': {
                'url': 'https://www.bing.com/search?q={query}&first={start}',
                'pages_param': 'first',
                'increment': 10,
                'parser': self.parse_bing
            },
            'yahoo': {
                'url': 'https://search.yahoo.com/search?p={query}&b={start}',
                'pages_param': 'b',
                'increment': 10,
                'parser': self.parse_yahoo
            },
            'duckduckgo': {
                'url': 'https://html.duckduckgo.com/html/?q={query}&s={start}',
                'pages_param': 's',
                'increment': 30,
                'parser': self.parse_duckduckgo
            },
            'brave': {
                'url': 'https://search.brave.com/search?q={query}&offset={start}',
                'pages_param': 'offset',
                'increment': 10,
                'parser': self.parse_brave
            },
            'yandex': {
                'url': 'https://yandex.com/search/?text={query}&p={page}',
                'pages_param': 'p',
                'increment': 1,
                'parser': self.parse_yandex
            },
            'baidu': {
                'url': 'https://www.baidu.com/s?wd={query}&pn={start}',
                'pages_param': 'pn',
                'increment': 10,
                'parser': self.parse_baidu
            },
            'aol': {
                'url': 'https://search.aol.com/aol/search?q={query}&page={page}',
                'pages_param': 'page',
                'increment': 1,
                'parser': self.parse_aol
            },
            'ask': {
                'url': 'https://www.ask.com/web?q={query}&page={page}',
                'pages_param': 'page',
                'increment': 1,
                'parser': self.parse_ask
            },
            'dogpile': {
                'url': 'https://www.dogpile.com/serp?q={query}&page={page}',
                'pages_param': 'page',
                'increment': 1,
                'parser': self.parse_dogpile
            },
            'startpage': {
                'url': 'https://www.startpage.com/sp/search?query={query}&page={page}',
                'pages_param': 'page',
                'increment': 1,
                'parser': self.parse_startpage
            },
            'qwant': {
                'url': 'https://www.qwant.com/?q={query}&page={page}',
                'pages_param': 'page',
                'increment': 1,
                'parser': self.parse_qwant
            },
            'ecosia': {
                'url': 'https://www.ecosia.org/search?q={query}&p={page}',
                'pages_param': 'p',
                'increment': 1,
                'parser': self.parse_ecosia
            },
            'gibiru': {
                'url': 'https://gibiru.com/results.html?q={query}&page={page}',
                'pages_param': 'page',
                'increment': 1,
                'parser': self.parse_gibiru
            },
            'swisscows': {
                'url': 'https://swisscows.com/web?query={query}&page={page}',
                'pages_param': 'page',
                'increment': 1,
                'parser': self.parse_swisscows
            },
            'mojeek': {
                'url': 'https://www.mojeek.com/search?q={query}&s={start}',
                'pages_param': 's',
                'increment': 10,
                'parser': self.parse_mojeek
            },
            'search_encrypt': {
                'url': 'https://www.searchencrypt.com/search?q={query}&page={page}',
                'pages_param': 'page',
                'increment': 1,
                'parser': self.parse_searchencrypt
            },
            'metager': {
                'url': 'https://metager.org/meta/meta.ger3?q={query}&page={page}',
                'pages_param': 'page',
                'increment': 1,
                'parser': self.parse_metager
            },
            'yep': {
                'url': 'https://yep.com/search?q={query}&page={page}',
                'pages_param': 'page',
                'increment': 1,
                'parser': self.parse_yep
            },
            'you': {
                'url': 'https://you.com/search?q={query}&page={page}',
                'pages_param': 'page',
                'increment': 1,
                'parser': self.parse_you
            },
            'givewater': {
                'url': 'https://search.givewater.com/serp?q={query}&page={page}',
                'pages_param': 'page',
                'increment': 1,
                'parser': self.parse_givewater
            }
        }
        
        # Initialize selenium driver options
        self.selenium_options = Options()
        self.selenium_options.add_argument('--headless')
        self.selenium_options.add_argument('--no-sandbox')
        self.selenium_options.add_argument('--disable-dev-shm-usage')
        self.selenium_options.add_argument('--disable-gpu')
        self.selenium_options.add_argument('--window-size=1920,1080')
        self.selenium_options.add_argument(f'--user-agent={self.get_random_agent()}')
        
        # Add additional options to avoid detection
        self.selenium_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.selenium_options.add_experimental_option('useAutomationExtension', False)
        self.selenium_options.add_argument('--disable-blink-features=AutomationControlled')
    
    def create_session(self):
        """Create a requests session with retry strategy"""
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=100, pool_maxsize=100)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session
    
    def get_random_agent(self):
        return random.choice(self.user_agents)
    
    def get_selenium_driver(self):
        """Get a Selenium WebDriver instance"""
        try:
            driver = uc.Chrome(options=self.selenium_options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            return driver
        except Exception as e:
            logger.error(f"Failed to create Selenium driver: {e}")
            # Fallback to regular Chrome
            try:
                driver = webdriver.Chrome(options=self.selenium_options)
                return driver
            except Exception as e2:
                logger.error(f"Failed to create Chrome driver: {e2}")
                return None
    
    @backoff.on_exception(backoff.expo, (requests.exceptions.RequestException,), max_tries=3)
    def check_protection(self, url):
        """Check if URL has protection like CAPTCHA"""
        try:
            headers = {'User-Agent': self.get_random_agent()}
            res = self.session.get(url, headers=headers, timeout=8, allow_redirects=True, verify=False)
            content = res.text.lower()
            protection_indicators = ['captcha', 'cloudflare', 'security check', 'firewall', 'ddos protection', 'access denied']
            return any(x in content for x in protection_indicators)
        except:
            return False
    
    def parse_google(self, soup):
        """Parse Google search results"""
        results = []
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
        return results
    
    def parse_bing(self, soup):
        """Parse Bing search results"""
        results = []
        for li in soup.find_all('li', class_='b_algo'):
            a = li.find('a')
            if a and a.has_attr('href'):
                href = a['href']
                if href.startswith('http') and 'bing.com' not in href:
                    if href not in results:
                        results.append(href)
        return results
    
    def parse_yahoo(self, soup):
        """Parse Yahoo search results"""
        results = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.startswith('http') and 'yahoo.com' not in href:
                if href not in results:
                    results.append(href)
        return results
    
    def parse_duckduckgo(self, soup):
        """Parse DuckDuckGo search results"""
        results = []
        for link in soup.find_all('a', class_='result__url'):
            href = link.get('href')
            if href and href.startswith('http'):
                if href not in results:
                    results.append(href)
        return results
    
    def parse_brave(self, soup):
        """Parse Brave search results"""
        results = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.startswith('http') and 'brave.com' not in href:
                if href not in results:
                    results.append(href)
        return results
    
    def parse_yandex(self, soup):
        """Parse Yandex search results"""
        results = []
        for a in soup.find_all('a', class_='link organic__url'):
            href = a.get('href')
            if href and href.startswith('http') and 'yandex' not in href:
                if href not in results:
                    results.append(href)
        return results
    
    def parse_baidu(self, soup):
        """Parse Baidu search results"""
        results = []
        for a in soup.find_all('a', href=True):
            href = a.get('href')
            if href and ('http://' in href or 'https://' in href) and 'baidu.com' not in href:
                if href not in results:
                    results.append(href)
        return results
    
    def parse_aol(self, soup):
        """Parse AOL search results"""
        results = []
        for a in soup.find_all('a', href=True):
            href = a.get('href')
            if href and href.startswith('http') and 'aol.com' not in href:
                if href not in results:
                    results.append(href)
        return results
    
    def parse_ask(self, soup):
        """Parse Ask.com search results"""
        results = []
        for a in soup.find_all('a', href=True):
            href = a.get('href')
            if href and href.startswith('http') and 'ask.com' not in href:
                if href not in results:
                    results.append(href)
        return results
    
    def parse_dogpile(self, soup):
        """Parse Dogpile search results"""
        results = []
        for a in soup.find_all('a', class_='result__url'):
            href = a.get('href')
            if href and href.startswith('http'):
                if href not in results:
                    results.append(href)
        return results
    
    def parse_startpage(self, soup):
        """Parse Startpage search results"""
        results = []
        for a in soup.find_all('a', class_='w-gl__result-url'):
            href = a.get('href')
            if href and href.startswith('http'):
                if href not in results:
                    results.append(href)
        return results
    
    def parse_qwant(self, soup):
        """Parse Qwant search results"""
        results = []
        for a in soup.find_all('a', class_='result__url'):
            href = a.get('href')
            if href and href.startswith('http'):
                if href not in results:
                    results.append(href)
        return results
    
    def parse_ecosia(self, soup):
        """Parse Ecosia search results"""
        results = []
        for a in soup.find_all('a', class_='result-url'):
            href = a.get('href')
            if href and href.startswith('http'):
                if href not in results:
                    results.append(href)
        return results
    
    def parse_gibiru(self, soup):
        """Parse Gibiru search results"""
        results = []
        for a in soup.find_all('a', class_='result_link'):
            href = a.get('href')
            if href and href.startswith('http'):
                if href not in results:
                    results.append(href)
        return results
    
    def parse_swisscows(self, soup):
        """Parse Swisscows search results"""
        results = []
        for a in soup.find_all('a', class_='link--result'):
            href = a.get('href')
            if href and href.startswith('http'):
                if href not in results:
                    results.append(href)
        return results
    
    def parse_mojeek(self, soup):
        """Parse Mojeek search results"""
        results = []
        for a in soup.find_all('a', class_='title'):
            href = a.get('href')
            if href and href.startswith('http'):
                if href not in results:
                    results.append(href)
        return results
    
    def parse_searchencrypt(self, soup):
        """Parse SearchEncrypt search results"""
        results = []
        for a in soup.find_all('a', class_='result-link'):
            href = a.get('href')
            if href and href.startswith('http'):
                if href not in results:
                    results.append(href)
        return results
    
    def parse_metager(self, soup):
        """Parse MetaGer search results"""
        results = []
        for a in soup.find_all('a', class_='result-link'):
            href = a.get('href')
            if href and href.startswith('http'):
                if href not in results:
                    results.append(href)
        return results
    
    def parse_yep(self, soup):
        """Parse Yep search results"""
        results = []
        for a in soup.find_all('a', class_='result-link'):
            href = a.get('href')
            if href and href.startswith('http'):
                if href not in results:
                    results.append(href)
        return results
    
    def parse_you(self, soup):
        """Parse You.com search results"""
        results = []
        for a in soup.find_all('a', class_='result-link'):
            href = a.get('href')
            if href and href.startswith('http'):
                if href not in results:
                    results.append(href)
        return results
    
    def parse_givewater(self, soup):
        """Parse GiveWater search results"""
        results = []
        for a in soup.find_all('a', class_='result-link'):
            href = a.get('href')
            if href and href.startswith('http'):
                if href not in results:
                    results.append(href)
        return results
    
    @backoff.on_exception(backoff.expo, (requests.exceptions.RequestException,), max_tries=2)
    def search_engine(self, engine, query, pages=3):
        """Generic search engine method"""
        results = []
        config = self.engine_configs.get(engine)
        
        if not config:
            return results
        
        for page in range(pages):
            try:
                # Build URL based on engine configuration
                if config['pages_param'] in ['start', 'first', 's', 'pn']:
                    start = page * config['increment']
                    url = config['url'].format(query=quote_plus(query), start=start)
                else:
                    page_num = page + 1
                    url = config['url'].format(query=quote_plus(query), page=page_num)
                
                headers = {'User-Agent': self.get_random_agent()}
                response = self.session.get(url, headers=headers, timeout=15, verify=False)
                
                if response.status_code != 200:
                    logger.warning(f"{engine} search returned status {response.status_code}")
                    continue
                
                soup = BeautifulSoup(response.text, 'html.parser')
                page_results = config['parser'](soup)
                results.extend(page_results)
                
                # Random delay between requests
                time.sleep(random.uniform(0.1, 0.5))
                
            except Exception as e:
                logger.error(f"{engine} search error: {e}")
                continue
        
        return results
    
    async def search_engine_async(self, engine, query, pages=3):
        """Async version of search engine method"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.search_engine, engine, query, pages)
    
    async def search_all_engines_async(self, query, pages=3, engines=None):
        """Search using multiple search engines asynchronously"""
        all_results = []
        
        logger.info(f"🔍 Searching for: {query}")
        
        if engines is None:
            engines = self.search_engines
        
        # Create async tasks for all engines
        tasks = []
        for engine in engines:
            if engine in self.engine_configs:
                tasks.append(self.search_engine_async(engine, query, pages))
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for i, result in enumerate(results):
            engine = engines[i]
            if isinstance(result, Exception):
                logger.error(f"❌ {engine} search failed: {result}")
            else:
                all_results.extend(result)
                logger.info(f"✅ {engine} found {len(result)} results")
        
        # Remove duplicates
        unique_results = list(set(all_results))
        logger.info(f"📊 Total unique results: {len(unique_results)}")
        return unique_results
    
    def search_all_engines(self, query, pages=3, engines=None):
        """Synchronous wrapper for async search"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            results = loop.run_until_complete(self.search_all_engines_async(query, pages, engines))
        finally:
            loop.close()
        return results
    
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
                logger.error(f"❌ Error checking {url}: {e}")
            return None
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            future_to_url = {executor.submit(check_url_protection, url): url for url in results}
            
            for future in concurrent.futures.as_completed(future_to_url):
                if len(valid_results) >= max_results:
                    break
                    
                result = future.result()
                if result:
                    valid_results.append(result)
                    logger.info(f"✅ Found valid URL: {result}")
        
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

def verify_gateway_presence(text, gateway):
    """Verify that a gateway is actually present on the page"""
    if not text:
        return False
    
    text_lower = text.lower()
    gateway_lower = gateway.lower()
    
    # Check for gateway name in text
    if gateway_lower in text_lower:
        return True
    
    # Check for verification patterns
    if gateway in gateway_verification_patterns:
        for pattern in gateway_verification_patterns[gateway]:
            if re.search(pattern, text, re.IGNORECASE):
                return True
    
    # Additional checks for common payment indicators
    payment_indicators = {
        'Credit Card': ['credit card', 'card number', 'expiry date', 'cvv', 'visa', 'mastercard', 'amex', 'american express'],
        'Debit Card': ['debit card', 'card number', 'expiry date', 'cvv'],
        'Visa': ['visa', 'card number', 'expiry date', 'cvv'],
        'MasterCard': ['mastercard', 'card number', 'expiry date', 'cvv'],
        'American Express': ['amex', 'american express', 'card number', 'expiry date', 'cvv'],
        'Payment Method': ['payment method', 'pay with', 'payment options'],
        'Payment Gateway': ['payment gateway', 'payment processor'],
        'Secure Payment': ['secure payment', 'ssl', 'encryption']
    }
    
    if gateway in payment_indicators:
        for indicator in payment_indicators[gateway]:
            if indicator in text_lower:
                return True
    
    return False

def find_gateways(text):
    """Find payment gateways mentioned in the text and verify they're real"""
    found = set()
    if not text:
        return found
    
    text_lower = text.lower()
    
    for gateway in gateways:
        if verify_gateway_presence(text, gateway):
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
        (r'square\.com', 'Square'),
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
        r'\d+\.\d{2}\s*(USD|EUR|GBP|CAD|AUD|JPY|CNY|INR|RUB|BRL|MXN)',  # 10.99 USD
        r'(USD|EUR|GBP|CAD|AUD|JPY|CNY|INR|RUB|BRL|MXN)\s*\d+\.\d{2}',  # USD 10.99
    ]
    
    prices = []
    for pattern in price_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        prices.extend(matches)
    
    return prices

def analyze_store(url, target_price=None, gateway_type=None):
    """Analyze a single store with price and gateway filtering"""
    try:
        ua = UserAgent()
        headers = {'User-Agent': ua.random}
        response = requests.get(url, headers=headers, timeout=15, verify=False)
        
        if response.status_code != 200:
            return None
            
        soup = BeautifulSoup(response.content, 'html.parser')
        text = response.text
        
        # Check if it's a real store
        if not is_real_store(soup, text):
            return None
        
        # Extract prices
        prices = extract_prices(text)
        
        # Price filtering
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
        
        return {
            'url': url,
            'real_store': True,
            'gateways': list(gateways_found),
            'gateways_count': len(gateways_found),
            'prices_found': prices[:10],  # Return first 10 prices
            'cloudflare': cloudflare,
            'auth': is_auth,
            'captcha': captcha,
            'vbv': vbv
        }
        
    except Exception as e:
        logger.error(f"❌ Error analyzing {url}: {e}")
        return None

def send_telegram_message_sync(bot_token, chat_id, message):
    """Send message to Telegram bot synchronously"""
    try:
        import telegram
        bot = telegram.Bot(token=bot_token)
        bot.send_message(chat_id=chat_id, text=message, parse_mode='HTML')
        return True
    except Exception as e:
        logger.error(f"❌ Telegram error: {e}")
        return False

@app.route('/analyze', methods=['GET'])
def analyze_single_store():
    """API endpoint to analyze a single e-commerce store"""
    url = request.args.get('url')
    target_price = request.args.get('target_price')
    gateway_type = request.args.get('gateway_type')
    
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
        
        result = analyze_store(url, price_value, gateway_type)
        
        if not result:
            return jsonify({
                'error': 'This does not appear to be a valid e-commerce store or it doesn\'t match your filters',
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
        pages = int(request.args.get('pages', 5))
        max_results = int(request.args.get('max_results', 50))
        gateways_count = int(request.args.get('gateways_count', 0))
        cloudflare_filter = request.args.get('cloudflare')
        auth_filter = request.args.get('auth')
        captcha_filter = request.args.get('captcha')
        vbv_filter = request.args.get('vbv')
        gateway_type = request.args.get('gateway_type')
        target_price = request.args.get('target_price')
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
        
        # Add custom query if provided
        if custom_query:
            ecommerce_queries.insert(0, custom_query)
        
        # Add price-specific queries if target_price is provided
        if price_value:
            price_queries = [
                f'"{price_value}" "add to cart"',
                f'"{price_value}" "buy now"',
                f'"{price_value}" "price"',
                f'"{price_value}" "shop"',
                f'"{price_value}" "product"'
            ]
            ecommerce_queries = price_queries + ecommerce_queries
        
        tool = DorkSearchTool()
        all_valid_results = []
        
        # Search with multiple queries
        for query in ecommerce_queries:
            logger.info(f"🔍 Searching for: {query}")
            results = tool.search_all_engines(query, pages, engines_list)
            valid_results = tool.filter_valid_results(results, max_results)
            all_valid_results.extend(valid_results)
            
            if len(all_valid_results) >= max_results * 3:  # Get more URLs for filtering
                break
        
        # Remove duplicates
        all_valid_results = list(set(all_valid_results))
        logger.info(f"📊 Found {len(all_valid_results)} unique URLs to analyze")
        
        # Analyze stores with threading
        analyzed_stores = []
        
        def analyze_url(url):
            result = analyze_store(url, price_value, gateway_type)
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
        
        # Prepare response
        response_data = {
            'stores_found': len(analyzed_stores),
            'stores': analyzed_stores,
            'api_by': '@R_O_P_D',
            'message': 'E-commerce store search completed successfully',
            'search_parameters': {
                'pages': pages,
                'max_results': max_results,
                'target_price': target_price,
                'gateway_type': gateway_type,
                'search_engines': engines_list or 'all'
            },
            'timestamp': datetime.now().isoformat()
        }
        
        # Send to Telegram if token and chat_id provided
        if bot_token and chat_id:
            message = f"<b>🔍 E-commerce Store Analysis Results</b>\n\n"
            message += f"<b>Stores Found:</b> {len(analyzed_stores)}\n"
            message += f"<b>Target Price:</b> {target_price or 'Any'}\n"
            message += f"<b>Gateway Type:</b> {gateway_type or 'Any'}\n"
            message += f"<b>Timestamp:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            for i, store in enumerate(analyzed_stores[:5]):  # Send first 5 stores
                message += f"<b>Store {i+1}:</b> {store['url']}\n"
                message += f"<b>Gateways:</b> {', '.join(store['gateways'])}\n"
                message += f"<b>Prices:</b> {', '.join(store.get('prices_found', [])[:3])}\n"
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
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
