# 🔥 LitAgent - The Lit User Agent Generator

LitAgent is a powerful, modern user agent generator that keeps your requests fresh and undetectable! Built for web scraping, it helps you manage user agents with ease and style.

---

## 🚀 Quick Start

```python
from webscout import LitAgent

# Create a LitAgent instance
agent = LitAgent()

# Get a random user agent
ua = agent.random()
print(ua)  # Mozilla/5.0 (Windows NT 11.0) AppleWebKit/537.36 ...
```

---

## 🎯 Features

### Browser-Specific Agents

```python
# Get agents for specific browsers
chrome_ua = agent.chrome()      # Latest Chrome agent
firefox_ua = agent.firefox()    # Latest Firefox agent
safari_ua = agent.safari()      # Latest Safari agent
edge_ua = agent.edge()          # Latest Edge agent
opera_ua = agent.opera()        # Latest Opera agent
```

### Device-Specific Agents

```python
# Get mobile or desktop agents
mobile_ua = agent.mobile()      # Mobile device agent
desktop_ua = agent.desktop()    # Desktop device agent

# New - Get agents for specific device types
tablet_ua = agent.tablet()      # Tablet device agent
tv_ua = agent.smart_tv()        # Smart TV agent
console_ua = agent.gaming()     # Gaming console agent

# Wearable device user agent support
wearable_ua = agent.wearable()  # Get a wearable device user agent
```

### OS-Specific Agents

```python
# New - Get agents for specific operating systems
windows_ua = agent.windows()    # Windows agent
mac_ua = agent.macos()          # macOS agent
linux_ua = agent.linux()        # Linux agent`
android_ua = agent.android()    # Android agent
ios_ua = agent.ios()            # iOS agent
```

### Custom Agent Generation

```python
# New - Generate custom user agents with specific attributes
custom_ua = agent.custom(
    browser="chrome",
    version="91.0",
    os="windows",
    os_version="10",
    device_type="desktop"
)
```

### Keep It Fresh

```python
# Refresh your agents pool anytime
agent.refresh()  # Generates new set of agents

# New - Schedule automatic refreshes
agent.auto_refresh(interval_minutes=30)  # Auto-refresh every 30 minutes
```

### IP Rotation

```python
# Rotate the IP address used in fingerprints
ip = agent.rotate_ip()
print(ip)  # 192.168.1.10 (example)
```

### Proxy Pool & Rotation

```python
agent.set_proxy_pool(["http://proxy1:8080", "http://proxy2:8080"])
proxy = agent.rotate_proxy()  # Get next proxy from pool
```

---

## 💫 Real-World Examples

### With Requests

```python
import requests
from webscout import LitAgent

agent = LitAgent()

def make_request(url):
    headers = {
        'User-Agent': agent.random(),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
    }
    return requests.get(url, headers=headers)

# Make requests with different agents
response1 = make_request('https://api.example.com')  # Random agent
response2 = make_request('https://mobile.example.com')  # Another random agent
```

### With aiohttp

```python
import aiohttp
import asyncio
from webscout import LitAgent

agent = LitAgent()

async def fetch(url):
    headers = {'User-Agent': agent.random()}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            return await response.text()

# Use it in your async code
async def main():
    urls = [
        'https://api1.example.com',
        'https://api2.example.com',
        'https://api3.example.com'
    ]
    tasks = [fetch(url) for url in urls]
    results = await asyncio.gather(*tasks)
    return results
```

### With Selenium

```python
from selenium import webdriver
from webscout import LitAgent

agent = LitAgent()

def create_driver():
    options = webdriver.ChromeOptions()
    options.add_argument(f'user-agent={agent.chrome()}')
    return webdriver.Chrome(options=options)

# Use it with Selenium
driver = create_driver()
driver.get('https://example.com')
```

---

## 🌟 Pro Tips

1. **Rotate Agents Regularly**  
   Refresh your agent pool periodically to avoid detection.

   ```python
   agent = LitAgent()
   for i in range(10):
       response = requests.get(url, headers={'User-Agent': agent.random()})
       if i % 3 == 0:
           agent.refresh()
   ```

2. **Device-Specific Scraping**  
   Use device-specific agents for different platforms.

   ```python
   # Mobile site scraping
   mobile_response = requests.get(
       'https://m.example.com',
       headers={'User-Agent': agent.mobile()}
   )
   # Desktop site scraping
   desktop_response = requests.get(
       'https://example.com',
       headers={'User-Agent': agent.desktop()}
   )
   ```

3. **Browser Consistency**  
   Stick to one browser type per session for realism.

   ```python
   chrome_agent = agent.chrome()
   headers = {
       'User-Agent': chrome_agent,
       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
   }
   # Use these headers for all requests in this session
   ```

4. **Browser Fingerprinting & IP Rotation**  
   Generate consistent browser fingerprints and rotate IPs.

   ```python
   fingerprint = agent.generate_fingerprint(browser="chrome")
   headers = {
       'User-Agent': fingerprint['user_agent'],
       'Accept-Language': fingerprint['accept_language'],
       'Accept': fingerprint['accept'],
       'Sec-Ch-Ua': fingerprint['sec_ch_ua'],
       'Sec-Ch-Ua-Platform': fingerprint['platform'],
       'X-Forwarded-For': fingerprint['x-forwarded-for']
   }
   ```

5. **Multi-threading Support**  
   Use thread-safe mode for concurrent requests.

   ```python
   import concurrent.futures
   from webscout import LitAgent
   import requests

   agent = LitAgent(thread_safe=True)

   def fetch_url(url):
       headers = {'User-Agent': agent.random()}
       return requests.get(url, headers=headers).text

   urls = ['https://example1.com', 'https://example2.com', 'https://example3.com']
   with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
       results = list(executor.map(fetch_url, urls))
   ```

---

## 🔧 Supported Browsers & Devices

- **Browsers**: Chrome, Firefox, Safari, Edge, Opera, Brave, Vivaldi
- **Operating Systems**: Windows, macOS, Linux, Android, iOS, Chrome OS
- **Devices**: Mobile phones, Tablets, Desktops, Game consoles, Smart TVs, Wearables

---

## 🎨 Why LitAgent?

- 🚀 Modern and up-to-date user agents
- 💪 Easy to use, hard to detect
- 🔄 Fresh agents on demand
- 📱 Device-specific agents
- 🌐 All major browsers supported
- ⚡ Lightweight and fast
- 🧩 Advanced fingerprinting protection
- 🔄 Seamless proxy integration
- 🧵 Thread-safe operation
- 🕰️ Automatic refresh scheduling

---

## 📊 Analytics and Reporting

Get statistics on your agent usage and export your data.

```python
# Get statistics on your agent usage
stats = agent.get_stats()
print(f"Agents generated: {stats.total_generated}")
print(f"Most used browser: {stats.top_browser}")
print(f"Detection avoidance rate: {stats.avoidance_rate}%")

# Export your usage data
agent.export_stats('agent_usage.json')
```

---

## 📋 Installation

```bash
pip install webscout
```

---

Made with 💖 by the HelpingAI team
