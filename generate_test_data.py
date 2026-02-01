"""
Test Data Generator for Analytiq Ingest API
Generates and sends realistic sample analytics data for testing purposes.
"""

import requests
import random
import json
from datetime import datetime, timedelta
from typing import List, Dict
import uuid
import time

# Configuration
API_BASE_URL = "http://localhost:8000"  # Update with your API URL
INGEST_ENDPOINT = f"{API_BASE_URL}/ingest/"

# Sample data pools
PAGES = [
    "/", "/about", "/products", "/pricing", "/contact", "/blog",
    "/blog/seo-tips", "/blog/analytics-guide", "/products/premium",
    "/products/basic", "/checkout", "/cart", "/account", "/login", "/signup"
]

PAGE_TITLES = {
    "/": "Home - Analytiq",
    "/about": "About Us - Analytiq",
    "/products": "Products - Analytiq",
    "/pricing": "Pricing - Analytiq",
    "/contact": "Contact - Analytiq",
    "/blog": "Blog - Analytiq",
    "/blog/seo-tips": "SEO Tips for 2026 - Analytiq Blog",
    "/blog/analytics-guide": "Complete Analytics Guide - Analytiq Blog",
    "/products/premium": "Premium Plan - Analytiq",
    "/products/basic": "Basic Plan - Analytiq",
    "/checkout": "Checkout - Analytiq",
    "/cart": "Shopping Cart - Analytiq",
    "/account": "My Account - Analytiq",
    "/login": "Login - Analytiq",
    "/signup": "Sign Up - Analytiq"
}

REFERRERS = [
    "", "https://google.com/search", "https://facebook.com", "https://twitter.com",
    "https://linkedin.com", "https://news.ycombinator.com", "https://reddit.com",
    "https://medium.com", "direct", "https://bing.com/search"
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15"
]

DEVICES = [
    {"type": "desktop", "screen": "1920x1080", "platform": "Windows"},
    {"type": "desktop", "screen": "2560x1440", "platform": "MacOS"},
    {"type": "mobile", "screen": "390x844", "platform": "iOS"},
    {"type": "mobile", "screen": "412x915", "platform": "Android"},
    {"type": "tablet", "screen": "1024x1366", "platform": "iOS"},
    {"type": "desktop", "screen": "1366x768", "platform": "Linux"}
]

LANGUAGES = ["en-US", "en-GB", "es-ES", "fr-FR", "de-DE", "ja-JP", "zh-CN"]

UTM_CAMPAIGNS = [
    {"source": "google", "medium": "cpc", "campaign": "winter_sale_2026"},
    {"source": "facebook", "medium": "social", "campaign": "brand_awareness"},
    {"source": "email", "medium": "newsletter", "campaign": "weekly_digest"},
    {"source": "twitter", "medium": "social", "campaign": "product_launch"},
    {"source": "linkedin", "medium": "social", "campaign": "b2b_outreach"},
    None, None, None  # Most visits don't have UTM params
]

COUNTRIES = [
    # North America
    {"name": "United States", "city": "New York", "lat": 40.7128, "long": -74.0060, "tz_offset": -5},
    {"name": "United States", "city": "Los Angeles", "lat": 34.0522, "long": -118.2437, "tz_offset": -8},
    {"name": "United States", "city": "Chicago", "lat": 41.8781, "long": -87.6298, "tz_offset": -6},
    {"name": "United States", "city": "Houston", "lat": 29.7604, "long": -95.3698, "tz_offset": -6},
    {"name": "Canada", "city": "Toronto", "lat": 43.6532, "long": -79.3832, "tz_offset": -5},
    {"name": "Canada", "city": "Vancouver", "lat": 49.2827, "long": -123.1207, "tz_offset": -8},
    # Europe
    {"name": "United Kingdom", "city": "London", "lat": 51.5074, "long": -0.1278, "tz_offset": 0},
    {"name": "Germany", "city": "Berlin", "lat": 52.5200, "long": 13.4050, "tz_offset": 1},
    {"name": "France", "city": "Paris", "lat": 48.8566, "long": 2.3522, "tz_offset": 1},
    {"name": "Spain", "city": "Madrid", "lat": 40.4168, "long": -3.7038, "tz_offset": 1},
    {"name": "Netherlands", "city": "Amsterdam", "lat": 52.3676, "long": 4.9041, "tz_offset": 1},
    {"name": "Sweden", "city": "Stockholm", "lat": 59.3293, "long": 18.0686, "tz_offset": 1},
    # Asia-Pacific
    {"name": "Japan", "city": "Tokyo", "lat": 35.6762, "long": 139.6503, "tz_offset": 9},
    {"name": "Japan", "city": "Osaka", "lat": 34.6937, "long": 135.5023, "tz_offset": 9},
    {"name": "China", "city": "Shanghai", "lat": 31.2304, "long": 121.4737, "tz_offset": 8},
    {"name": "Singapore", "city": "Singapore", "lat": 1.3521, "long": 103.8198, "tz_offset": 8},
    {"name": "Australia", "city": "Sydney", "lat": -33.8688, "long": 151.2093, "tz_offset": 11},
    {"name": "Australia", "city": "Melbourne", "lat": -37.8136, "long": 144.9631, "tz_offset": 11},
    {"name": "India", "city": "Mumbai", "lat": 19.0760, "long": 72.8777, "tz_offset": 5.5},
    # Latin America
    {"name": "Brazil", "city": "São Paulo", "lat": -23.5505, "long": -46.6333, "tz_offset": -3},
    {"name": "Mexico", "city": "Mexico City", "lat": 19.4326, "long": -99.1332, "tz_offset": -6},
]

PRODUCTS = [
    {"id": "prod_001", "name": "Premium Plan", "category": "Subscription", "price": 49.99},
    {"id": "prod_002", "name": "Basic Plan", "category": "Subscription", "price": 19.99},
    {"id": "prod_003", "name": "Enterprise Plan", "category": "Subscription", "price": 199.99},
    {"id": "prod_004", "name": "Analytics Plugin", "category": "Add-on", "price": 9.99},
    {"id": "prod_005", "name": "Data Export Tool", "category": "Add-on", "price": 14.99}
]

SEARCH_TERMS = [
    "pricing", "features", "documentation", "api", "integration",
    "how to setup", "dashboard", "analytics", "reports", "export data"
]

# Hourly traffic distribution (weighted by hour of day)
# Represents realistic traffic patterns with peak hours during business day
HOURLY_WEIGHTS = {
    0: 0.5,    # Midnight - low
    1: 0.3,    # 1 AM - very low
    2: 0.2,    # 2 AM - very low
    3: 0.2,    # 3 AM - very low
    4: 0.2,    # 4 AM - very low
    5: 0.3,    # 5 AM - starting day in early regions
    6: 0.6,    # 6 AM - morning starts
    7: 1.0,    # 7 AM - morning peak begins
    8: 1.4,    # 8 AM - commute time
    9: 1.8,    # 9 AM - morning peak
    10: 2.0,   # 10 AM - peak work hours
    11: 2.0,   # 11 AM - peak work hours
    12: 1.8,   # Noon - slight dip (lunch)
    13: 1.9,   # 1 PM - afternoon starts
    14: 2.0,   # 2 PM - afternoon peak
    15: 2.0,   # 3 PM - afternoon peak
    16: 1.9,   # 4 PM - late afternoon
    17: 1.6,   # 5 PM - end of workday
    18: 1.2,   # 6 PM - evening starts
    19: 1.0,   # 7 PM - evening
    20: 0.9,   # 8 PM - evening continues
    21: 0.7,   # 9 PM - late evening
    22: 0.6,   # 10 PM - night
    23: 0.5    # 11 PM - late night
}


class TestDataGenerator:
    def __init__(self, site_id: str, site_key: str, base_url: str = "https://example.com"):
        self.site_id = site_id
        self.site_key = site_key
        self.base_url = base_url
        self.visitors = []
        self.sessions = []
        
    def generate_visitor_id(self) -> str:
        """Generate a unique visitor ID"""
        return f"visitor_{uuid.uuid4().hex[:16]}"
    
    def generate_session_id(self) -> str:
        """Generate a unique session ID"""
        return f"session_{uuid.uuid4().hex[:16]}"
    
    def random_timestamp(self, days_ago: int = 7) -> str:
        """Generate a random timestamp within the last N days, weighted by hourly traffic patterns"""
        now = datetime.now()
        random_days = random.randint(0, days_ago)
        
        # Select hour weighted by traffic distribution
        hours = list(HOURLY_WEIGHTS.keys())
        weights = list(HOURLY_WEIGHTS.values())
        selected_hour = random.choices(hours, weights=weights, k=1)[0]
        
        # Add some randomness to minutes and seconds
        random_minute = random.randint(0, 59)
        random_second = random.randint(0, 59)
        
        random_date = now - timedelta(
            days=random_days,
            hours=selected_hour,
            minutes=random_minute,
            seconds=random_second
        )
        
        # Adjust for timezone variations (simulate visitors across regions)
        tz_adjustment = random.uniform(-12, 12)  # Hours of timezone offset
        random_date = random_date + timedelta(hours=tz_adjustment)
        
        return random_date.isoformat()
    
    def generate_raw_event(self, visitor_id: str, session_id: str, timestamp: str) -> Dict:
        """Generate a raw pageview event"""
        page = random.choice(PAGES)
        device = random.choice(DEVICES)
        utm = random.choice(UTM_CAMPAIGNS)
        country = random.choice(COUNTRIES)
        
        payload = {
            "url": f"{self.base_url}{page}",
            "title": PAGE_TITLES.get(page, "Page - Analytiq"),
            "referrer": random.choice(REFERRERS),
            "user_agent": random.choice(USER_AGENTS),
            "platform": device["platform"],
            "device_type": device["type"],
            "screen": device["screen"],
            "language": random.choice(LANGUAGES),
            "navigation_start": random.randint(50, 200),
            "dom_content_loaded": random.randint(300, 1500),
            "load_event": random.randint(800, 3000),
            "first_contentful_paint": random.randint(400, 2000),
            "largest_contentful_paint": random.randint(1000, 4000),
            "first_input_delay": random.randint(10, 300),
            "server_response_time": random.randint(50, 500),
        }
        
        if utm:
            payload["utm_source"] = utm["source"]
            payload["utm_medium"] = utm["medium"]
            payload["utm_campaign"] = utm["campaign"]
        
        if random.random() < 0.7:  # 70% have geo data
            payload["geo"] = {
                "lat": country["lat"],
                "long": country["long"],
                "city": country.get("city", ""),
                "country": country["name"]
            }
        
        return {
            "type": "raw",
            "site_id": self.site_id,
            "ts": timestamp,
            "event_type": "pageview",
            "payload": payload,
            "visitor_id": visitor_id,
            "session_id": session_id
        }
    
    def generate_performance_event(self, visitor_id: str, session_id: str, timestamp: str) -> Dict:
        """Generate a performance metrics event"""
        page = random.choice(PAGES)
        
        return {
            "type": "performance",
            "site_id": self.site_id,
            "ts": timestamp,
            "visitor_id": visitor_id,
            "session_id": session_id,
            "url": f"{self.base_url}{page}",
            "first_contentful_paint": random.uniform(400, 2500),
            "largest_contentful_paint": random.uniform(1000, 5000),
            "cumulative_layout_shift": random.uniform(0, 0.3),
            "first_input_delay": random.uniform(10, 350),
            "connection_downlink": random.uniform(1.5, 100),
            "connection_rtt": random.uniform(20, 200),
            "connection_type": random.choice(["4g", "wifi", "ethernet", "5g"]),
            "dom_content_loaded": random.uniform(300, 2000),
            "load_event_end": random.uniform(800, 4000),
            "server_response_time": random.uniform(50, 600),
            "total_resources": random.randint(10, 80),
            "cached_resources": random.randint(5, 60)
        }
    
    def generate_engagement_event(self, visitor_id: str, session_id: str, timestamp: str) -> Dict:
        """Generate an engagement tracking event"""
        page = random.choice(PAGES)
        
        return {
            "type": "engagement",
            "site_id": self.site_id,
            "ts": timestamp,
            "visitor_id": visitor_id,
            "session_id": session_id,
            "url": f"{self.base_url}{page}",
            "scroll_depth_percent": random.uniform(10, 100),
            "time_on_page_sec": random.uniform(5, 600),
            "clicks_count": random.randint(0, 20),
            "idle_time_sec": random.uniform(0, 120),
            "mouse_movements": random.randint(50, 500),
            "keyboard_events": random.randint(0, 100),
            "form_started": random.choice([True, False]),
            "form_completed": random.choice([True, False]),
            "video_played": random.choice([True, False, False, False]),  # 25% play video
            "video_watch_time_sec": random.uniform(0, 300) if random.random() < 0.25 else 0
        }
    
    def generate_conversion_event(self, visitor_id: str, session_id: str, timestamp: str) -> Dict:
        """Generate a conversion event"""
        event_types = ["product_view", "add_to_cart", "checkout_started", "purchase"]
        event_type = random.choice(event_types)
        product = random.choice(PRODUCTS)
        
        event = {
            "type": "conversion",
            "site_id": self.site_id,
            "ts": timestamp,
            "event_type": event_type,
            "visitor_id": visitor_id,
            "session_id": session_id,
            "product_id": product["id"],
            "product_name": product["name"],
            "category": product["category"],
            "price": product["price"],
            "quantity": random.randint(1, 3),
            "currency": "USD"
        }
        
        if event_type == "purchase":
            event["order_value"] = product["price"] * event["quantity"]
            event["order_id"] = f"order_{uuid.uuid4().hex[:12]}"
        
        return event
    
    def generate_search_event(self, visitor_id: str, session_id: str, timestamp: str) -> Dict:
        """Generate a search event"""
        term = random.choice(SEARCH_TERMS)
        
        return {
            "type": "search",
            "site_id": self.site_id,
            "ts": timestamp,
            "visitor_id": visitor_id,
            "session_id": session_id,
            "search_term": term,
            "results_count": random.randint(0, 50),
            "clicked_result": random.choice([True, False]),
            "result_position": random.randint(1, 10) if random.random() < 0.6 else None
        }
    
    def generate_custom_event(self, visitor_id: str, session_id: str, timestamp: str) -> Dict:
        """Generate a custom business event"""
        custom_events = [
            {"name": "newsletter_signup", "category": "engagement", "value": 5.0},
            {"name": "rating_submitted", "category": "feedback", "value": 1.0},
            {"name": "download_whitepaper", "category": "lead_gen", "value": 10.0},
            {"name": "social_share", "category": "viral", "value": 2.0},
            {"name": "chat_initiated", "category": "support", "value": 3.0}
        ]
        
        event_data = random.choice(custom_events)
        
        return {
            "type": "custom",
            "site_id": self.site_id,
            "ts": timestamp,
            "visitor_id": visitor_id,
            "session_id": session_id,
            "event_name": event_data["name"],
            "event_category": event_data["category"],
            "event_value": event_data["value"],
            "custom_properties": {
                "source": random.choice(["organic", "paid", "referral"]),
                "device": random.choice(["mobile", "desktop", "tablet"])
            }
        }
    
    def generate_user_session(self, days_ago: int = 7) -> List[Dict]:
        """Generate a realistic user session with multiple events, respecting hourly patterns"""
        visitor_id = self.generate_visitor_id()
        session_id = self.generate_session_id()
        
        # Session start time with weighted hourly distribution
        session_start = datetime.now() - timedelta(days=random.randint(0, days_ago))
        
        # Select hour weighted by traffic distribution
        hours = list(HOURLY_WEIGHTS.keys())
        weights = list(HOURLY_WEIGHTS.values())
        selected_hour = random.choices(hours, weights=weights, k=1)[0]
        
        session_start = session_start.replace(
            hour=selected_hour,
            minute=random.randint(0, 59),
            second=random.randint(0, 59),
            microsecond=0
        )
        
        events = []
        num_pages = random.randint(1, 8)  # 1-8 pages per session
        
        for i in range(num_pages):
            # Each page view happens 5-300 seconds after the previous one
            event_time = session_start + timedelta(seconds=random.randint(5, 300) * i)
            timestamp = event_time.isoformat()
            
            # Always generate raw pageview
            events.append(self.generate_raw_event(visitor_id, session_id, timestamp))
            
            # 80% chance of performance event
            if random.random() < 0.8:
                events.append(self.generate_performance_event(visitor_id, session_id, timestamp))
            
            # 60% chance of engagement event
            if random.random() < 0.6:
                events.append(self.generate_engagement_event(visitor_id, session_id, timestamp))
            
            # 20% chance of conversion event
            if random.random() < 0.2:
                events.append(self.generate_conversion_event(visitor_id, session_id, timestamp))
            
            # 10% chance of search event
            if random.random() < 0.1:
                events.append(self.generate_search_event(visitor_id, session_id, timestamp))
            
            # 15% chance of custom event
            if random.random() < 0.15:
                events.append(self.generate_custom_event(visitor_id, session_id, timestamp))
        
        return events
    
    def send_event(self, event: Dict) -> bool:
        """Send a single event to the API"""
        headers = {
            "X-Site-Id": self.site_id,
            "X-Site-Key": self.site_key,
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(INGEST_ENDPOINT, json=event, headers=headers)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Error sending event: {e}")
            return False
    
    def send_batch(self, events: List[Dict]) -> bool:
        """Send multiple events in a batch"""
        # Group events by type
        batch = {
            "raw_events": [],
            "conversion_events": [],
            "performance_events": [],
            "engagement_events": [],
            "search_events": [],
            "custom_events": []
        }
        
        for event in events:
            event_type = event.pop("type")
            if event_type == "raw":
                batch["raw_events"].append(event)
            elif event_type == "conversion":
                batch["conversion_events"].append(event)
            elif event_type == "performance":
                batch["performance_events"].append(event)
            elif event_type == "engagement":
                batch["engagement_events"].append(event)
            elif event_type == "search":
                batch["search_events"].append(event)
            elif event_type == "custom":
                batch["custom_events"].append(event)
        
        # Remove empty arrays
        batch = {k: v for k, v in batch.items() if v}
        
        headers = {
            "X-Site-Id": self.site_id,
            "X-Site-Key": self.site_key,
            "Content-Type": "application/json"
        }
        
        payload = {"batch": batch}
        
        try:
            response = requests.post(INGEST_ENDPOINT, json=payload, headers=headers)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Error sending batch: {e}")
            return False
    
    def generate_and_send(self, num_sessions: int = 100, days_ago: int = 7, batch_size: int = 50):
        """Generate and send test data"""
        print(f"Generating {num_sessions} user sessions spanning {days_ago} days...")
        print(f"Using batch size of {batch_size} events")
        
        all_events = []
        
        for i in range(num_sessions):
            session_events = self.generate_user_session(days_ago)
            all_events.extend(session_events)
            
            if (i + 1) % 10 == 0:
                print(f"Generated {i + 1}/{num_sessions} sessions ({len(all_events)} events so far)")
        
        print(f"\nTotal events generated: {len(all_events)}")
        print(f"Sending in batches of {batch_size}...")
        
        # Send in batches
        successful = 0
        failed = 0
        
        for i in range(0, len(all_events), batch_size):
            batch = all_events[i:i + batch_size]
            if self.send_batch(batch):
                successful += len(batch)
                print(f"Sent batch {i // batch_size + 1} ({len(batch)} events) ✓")
            else:
                failed += len(batch)
                print(f"Failed to send batch {i // batch_size + 1} ✗")
            
            # Small delay to avoid overwhelming the server
            time.sleep(0.1)
        
        print(f"\n{'='*60}")
        print(f"Data generation complete!")
        print(f"Total events sent: {successful}")
        print(f"Failed events: {failed}")
        print(f"{'='*60}")


def main():
    """Main function to run the test data generator"""
    print("=" * 60)
    print("Analytiq Test Data Generator")
    print("=" * 60)
    print()
    
    # Get site credentials
    site_id = input("Enter Site ID: ").strip()
    site_key = input("Enter Site Key: ").strip()
    
    # Get test parameters
    try:
        num_sessions = int(input("Number of user sessions to generate (default 100): ").strip() or "100")
        days_ago = int(input("Spread data over how many days (default 7): ").strip() or "7")
        batch_size = int(input("Batch size for sending (default 50): ").strip() or "50")
    except ValueError:
        print("Invalid input, using defaults")
        num_sessions = 100
        days_ago = 7
        batch_size = 50
    
    print()
    
    # Create generator and run
    generator = TestDataGenerator(site_id, site_key)
    generator.generate_and_send(num_sessions, days_ago, batch_size)


if __name__ == "__main__":
    main()
