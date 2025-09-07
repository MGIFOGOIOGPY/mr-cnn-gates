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
import asyncio
import aiohttp
import telegram
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Payment gateway patterns - موسع
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
    
    def get_session(self):
        if not self.session:
            self.session = requests.Session()
        return self.session
    
    def get_random_agent(self):
        return random.choice(self.user_agents)
    
    async def check_protection_async(self, url, session):
        """Check if URL has protection like CAPTCHA (async version)"""
        try:
            headers = {'User-Agent': self.get_random_agent()}
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as response:
                content = (await response.text()).lower()
                protection_indicators = ['captcha', 'cloudflare', 'security check', 'firewall', 'ddos protection', 'access denied']
                return any(x in content for x in protection_indicators)
        except:
            return False
    
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
    
    async def search_google_async(self, query, pages=3, session=None):
        """Search using Google with improved parsing (async version)"""
        results = []
        for page in range(pages):
            try:
                start = page * 10
                url = f"https://www.google.com/search?q={quote_plus(query)}&start={start}&num=100"
                
                headers = {'User-Agent': self.get_random_agent()}
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=20)) as response:
                    if response.status != 200:
                        print(f"Google search returned status {response.status}")
                        continue
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
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
                
                await asyncio.sleep(random.uniform(1, 2))
                
            except Exception as e:
                print(f"Google search error: {e}")
                continue
        
        return results
    
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
                
                time.sleep(random.uniform(1, 2))
                
            except Exception as e:
                print(f"Google search error: {e}")
                continue
        
        return results
    
    async def search_bing_async(self, query, pages=3, session=None):
        """Search using Bing (async version)"""
        results = []
        for page in range(1, pages + 1):
            try:
                url = f"https://www.bing.com/search?q={quote_plus(query)}&first={(page-1)*10+1}&count=50"
                
                headers = {'User-Agent': self.get_random_agent()}
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=20)) as response:
                    if response.status != 200:
                        print(f"Bing search returned status {response.status}")
                        continue
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Find organic results
                    for li in soup.find_all('li', class_='b_algo'):
                        a = li.find('a')
                        if a and a.has_attr('href'):
                            href = a['href']
                            if href.startswith('http') and 'bing.com' not in href:
                                if href not in results:
                                    results.append(href)
                
                await asyncio.sleep(random.uniform(1, 2))
                
            except Exception as e:
                print(f"Bing search error: {e}")
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
                
                time.sleep(random.uniform(1, 2))
                
            except Exception as e:
                print(f"Bing search error: {e}")
                continue
        
        return results
    
    async def search_yahoo_async(self, query, pages=2, session=None):
        """Search using Yahoo (async version)"""
        results = []
        for page in range(1, pages + 1):
            try:
                url = f"https://search.yahoo.com/search?p={quote_plus(query)}&b={(page-1)*10+1}"
                
                headers = {'User-Agent': self.get_random_agent()}
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=20)) as response:
                    if response.status != 200:
                        continue
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Find search results
                    for a in soup.find_all('a', href=True):
                        href = a['href']
                        if href.startswith('http') and 'yahoo.com' not in href:
                            if href not in results:
                                results.append(href)
                
                await asyncio.sleep(random.uniform(1, 2))
                
            except Exception as e:
                print(f"Yahoo search error: {e}")
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
                
                time.sleep(random.uniform(1, 2))
                
            except Exception as e:
                print(f"Yahoo search error: {e}")
                continue
        
        return results
    
    async def search_duckduckgo_async(self, query, pages=2, session=None):
        """Search using DuckDuckGo (async version)"""
        results = []
        for page in range(1, pages + 1):
            try:
                url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}&s={(page-1)*30}"
                
                headers = {'User-Agent': self.get_random_agent()}
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=20)) as response:
                    if response.status != 200:
                        continue
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Find result links
                    for link in soup.find_all('a', class_='result__url'):
                        href = link.get('href')
                        if href and href.startswith('http'):
                            if href not in results:
                                results.append(href)
                
                await asyncio.sleep(random.uniform(0.5, 1))
                
            except Exception as e:
                print(f"DuckDuckGo search error: {e}")
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
                
                time.sleep(random.uniform(0.5, 1))
                
            except Exception as e:
                print(f"DuckDuckGo search error: {e}")
                continue
        
        return results
    
    async def search_brave_async(self, query, pages=2, session=None):
        """Search using Brave (async version)"""
        results = []
        for page in range(1, pages + 1):
            try:
                url = f"https://search.brave.com/search?q={quote_plus(query)}&offset={(page-1)*10}"
                
                headers = {'User-Agent': self.get_random_agent()}
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=20)) as response:
                    if response.status != 200:
                        continue
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Find result links
                    for a in soup.find_all('a', href=True):
                        href = a['href']
                        if href.startswith('http') and 'brave.com' not in href:
                            if href not in results:
                                results.append(href)
                
                await asyncio.sleep(random.uniform(0.5, 1))
                
            except Exception as e:
                print(f"Brave search error: {e}")
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
                
                time.sleep(random.uniform(0.5, 1))
                
            except Exception as e:
                print(f"Brave search error: {e}")
                continue
        
        return results
    
    async def search_yandex_async(self, query, pages=2, session=None):
        """Search using Yandex (async version)"""
        results = []
        for page in range(0, pages):
            try:
                url = f"https://yandex.com/search/?text={quote_plus(query)}&p={page}"
                
                headers = {'User-Agent': self.get_random_agent()}
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=20)) as response:
                    if response.status != 200:
                        continue
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Find result links
                    for a in soup.find_all('a', class_='link organic__url'):
                        href = a.get('href')
                        if href and href.startswith('http') and 'yandex' not in href:
                            if href not in results:
                                results.append(href)
                
                await asyncio.sleep(random.uniform(0.5, 1))
                
            except Exception as e:
                print(f"Yandex search error: {e}")
                continue
        
        return results
    
    def search_yandex(self, query, pages=2):
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
                
                time.sleep(random.uniform(0.5, 1))
                
            except Exception as e:
                print(f"Yandex search error: {e}")
                continue
        
        return results
    
    async def search_baidu_async(self, query, pages=2, session=None):
        """Search using Baidu (async version)"""
        results = []
        for page in range(0, pages):
            try:
                url = f"https://www.baidu.com/s?wd={quote_plus(query)}&pn={page*10}"
                
                headers = {'User-Agent': self.get_random_agent()}
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=20)) as response:
                    if response.status != 200:
                        continue
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Find result links
                    for a in soup.find_all('a', href=True):
                        href = a.get('href')
                        if href and ('http://' in href or 'https://' in href) and 'baidu.com' not in href:
                            if href not in results:
                                results.append(href)
                
                await asyncio.sleep(random.uniform(0.5, 1))
                
            except Exception as e:
                print(f"Baidu search error: {e}")
                continue
        
        return results
    
    def search_baidu(self, query, pages=2):
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
                
                time.sleep(random.uniform(0.5, 1))
                
            except Exception as e:
                print(f"Baidu search error: {e}")
                continue
        
        return results
    
    async def search_all_engines_async(self, query, pages=2):
        """Search using all available search engines (async version)"""
        all_results = []
        
        print(f"🔍 Searching for: {query}")
        
        async with aiohttp.ClientSession() as session:
            tasks = [
                self.search_google_async(query, pages, session),
                self.search_bing_async(query, pages, session),
                self.search_yahoo_async(query, pages, session),
                self.search_duckduckgo_async(query, pages, session),
                self.search_brave_async(query, pages, session),
                self.search_yandex_async(query, pages, session),
                self.search_baidu_async(query, pages, session)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(results):
                engine_names = ["Google", "Bing", "Yahoo", "DuckDuckGo", "Brave", "Yandex", "Baidu"]
                if isinstance(result, Exception):
                    print(f"❌ {engine_names[i]} search failed: {result}")
                else:
                    all_results.extend(result)
                    print(f"✅ {engine_names[i]} found {len(result)} results")
        
        # Remove duplicates
        unique_results = list(set(all_results))
        print(f"📊 Total unique results: {len(unique_results)}")
        return unique_results
    
    def search_all_engines(self, query, pages=2):
        """Search using all available search engines"""
        all_results = []
        
        print(f"🔍 Searching for: {query}")
        
        # Search all engines in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=7) as executor:
            futures = {
                executor.submit(self.search_google, query, pages): "Google",
                executor.submit(self.search_bing, query, pages): "Bing",
                executor.submit(self.search_yahoo, query, pages): "Yahoo",
                executor.submit(self.search_duckduckgo, query, pages): "DuckDuckGo",
                executor.submit(self.search_brave, query, pages): "Brave",
                executor.submit(self.search_yandex, query, pages): "Yandex",
                executor.submit(self.search_baidu, query, pages): "Baidu"
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
    
    async def filter_valid_results_async(self, results, max_results=50):
        """Filter results by checking protection and validity (async version)"""
        valid_results = []
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for url in results:
                if len(valid_results) >= max_results:
                    break
                
                # Skip URLs that are clearly not stores
                if any(x in url.lower() for x in ['google.', 'bing.', 'youtube.', 'facebook.', 'twitter.', 'instagram.']):
                    continue
                
                tasks.append(self.check_protection_async(url, session))
            
            protection_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, has_protection in enumerate(protection_results):
                if not has_protection and i < len(results):
                    valid_results.append(results[i])
                    print(f"✅ Found valid URL: {results[i]}")
        
        return valid_results
    
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
            
            time.sleep(0.1)  # Reduced sleep time for faster processing
        
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

async def analyze_store_async(url, session):
    """Analyze a single store (async version)"""
    try:
        ua = UserAgent()
        headers = {'User-Agent': ua.random}
        
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as response:
            if response.status != 200:
                return None
                
            html = await response.text()
            soup = BeautifulSoup(html, 'html.parser')
            text = html
            
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
        print(f"❌ Error analyzing {url}: {e}")
        return None

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
        print(f"❌ Error analyzing {url}: {e}")
        return None

async def send_telegram_message(bot_token, chat_id, message):
    """Send message to Telegram bot"""
    try:
        bot = telegram.Bot(token=bot_token)
        await bot.send_message(chat_id=chat_id, text=message, parse_mode='HTML')
        return True
    except Exception as e:
        print(f"❌ Telegram error: {e}")
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
            print(f"🔍 Searching for: {query}")
            # Use async for faster searching
            results = asyncio.run(tool.search_all_engines_async(query, pages))
            valid_results = asyncio.run(tool.filter_valid_results_async(results, max_results))
            all_valid_results.extend(valid_results)
            
            if len(all_valid_results) >= max_results * 2:  # Get more URLs for filtering
                break
        
        # Remove duplicates
        all_valid_results = list(set(all_valid_results))
        print(f"📊 Found {len(all_valid_results)} unique URLs to analyze")
        
        # Analyze stores with async
        analyzed_stores = []
        
        async def analyze_urls(urls):
            async with aiohttp.ClientSession() as session:
                tasks = [analyze_store_async(url, session) for url in urls]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in results:
                    if result and isinstance(result, dict):
                        # Apply filters
                        if gateways_count > 0 and result['gateways_count'] < gateways_count:
                            continue
                        if cloudflare_filter and result['cloudflare'] != (cloudflare_filter.lower() == 'true'):
                            continue
                        if auth_filter and result['auth'] != (auth_filter.lower() == 'true'):
                            continue
                        if captcha_filter and result['captcha'] != (captcha_filter.lower() == 'true'):
                            continue
                        if vbv_filter and result['vbv'] != (vbv_filter.lower() == 'true'):
                            continue
                        if gateway_type and gateway_type not in [g.lower() for g in result['gateways']]:
                            continue
                        
                        analyzed_stores.append(result)
                        if len(analyzed_stores) >= max_results:
                            break
            
            return analyzed_stores
        
        # Run async analysis
        analyzed_stores = asyncio.run(analyze_urls(all_valid_results[:max_results*2]))
        
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
            
            # Send message asynchronously
            asyncio.run(send_telegram_message(bot_token, chat_id, message))
        
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
        results = asyncio.run(tool.search_google_async('"add to cart" "buy now"', 1))
        return jsonify({
            'results': results[:5],  # Return first 5 results
            'count': len(results),
            'status': 'success'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
