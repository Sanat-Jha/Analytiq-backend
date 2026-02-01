
# Enhanced aggregation logic for comprehensive analytics
import duckdb
import json
from app.db import con
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from urllib.parse import urlparse
import re

def normalize_path(path):
	"""Normalize URL path to avoid duplicate page counts"""
	if not path:
		return '/'
	# Remove trailing slash (except for root)
	path = path.rstrip('/') if path != '/' else path
	# Normalize to lowercase
	path = path.lower()
	# Ensure starts with /
	if not path.startswith('/'):
		path = '/' + path
	# Collapse Windows file paths to last two segments so file:///d:/foo/bar.html and
	# http://localhost/foo/bar.html both map to /foo/bar.html
	parts = [p for p in path.split('/') if p]
	if len(parts) >= 2 and parts[0].endswith(':'):
		path = '/' + '/'.join(parts[-2:])
	# Replace empty string with /
	return path or '/'
# Offline country lookup using bounding boxes (approximate coordinates)
# Format: country_name: (min_lat, max_lat, min_lng, max_lng)
COUNTRY_BOUNDING_BOXES = {
	'United States': (24.5, 49.5, -125.0, -66.5),
	'Canada': (41.7, 83.1, -141.0, -52.6),
	'Mexico': (14.5, 32.7, -118.4, -86.7),
	'Brazil': (-33.8, 5.3, -73.9, -34.8),
	'Argentina': (-55.1, -21.8, -73.6, -53.6),
	'United Kingdom': (49.9, 60.9, -8.6, 1.8),
	'France': (41.3, 51.1, -5.1, 9.6),
	'Germany': (47.3, 55.1, 5.9, 15.0),
	'Spain': (36.0, 43.8, -9.3, 4.3),
	'Italy': (36.6, 47.1, 6.6, 18.5),
	'Portugal': (36.9, 42.2, -9.5, -6.2),
	'Netherlands': (50.8, 53.5, 3.4, 7.2),
	'Belgium': (49.5, 51.5, 2.5, 6.4),
	'Switzerland': (45.8, 47.8, 5.9, 10.5),
	'Austria': (46.4, 49.0, 9.5, 17.2),
	'Poland': (49.0, 54.8, 14.1, 24.2),
	'Czech Republic': (48.5, 51.1, 12.1, 18.9),
	'Sweden': (55.3, 69.1, 11.1, 24.2),
	'Norway': (58.0, 71.2, 4.6, 31.1),
	'Finland': (59.8, 70.1, 20.6, 31.6),
	'Denmark': (54.6, 57.8, 8.1, 15.2),
	'Ireland': (51.4, 55.4, -10.5, -6.0),
	'Greece': (34.8, 41.7, 19.4, 29.6),
	'Romania': (43.6, 48.3, 20.3, 29.7),
	'Hungary': (45.7, 48.6, 16.1, 22.9),
	'Ukraine': (44.4, 52.4, 22.1, 40.2),
	'Russia': (41.2, 81.9, 19.6, 180.0),
	'China': (18.2, 53.6, 73.5, 135.0),
	'Japan': (24.0, 45.5, 122.9, 153.9),
	'South Korea': (33.1, 38.6, 124.6, 131.9),
	'India': (6.7, 35.5, 68.2, 97.4),
	'Indonesia': (-11.0, 6.1, 95.0, 141.0),
	'Thailand': (5.6, 20.5, 97.3, 105.6),
	'Vietnam': (8.4, 23.4, 102.1, 109.5),
	'Philippines': (4.6, 21.1, 116.9, 126.6),
	'Malaysia': (0.9, 7.4, 99.6, 119.3),
	'Singapore': (1.2, 1.5, 103.6, 104.0),
	'Australia': (-43.6, -10.7, 113.2, 153.6),
	'New Zealand': (-47.3, -34.4, 166.4, 178.6),
	'South Africa': (-34.8, -22.1, 16.5, 32.9),
	'Egypt': (22.0, 31.7, 24.7, 36.9),
	'Nigeria': (4.3, 13.9, 2.7, 14.7),
	'Kenya': (-4.7, 5.0, 33.9, 41.9),
	'Saudi Arabia': (16.4, 32.2, 34.5, 55.7),
	'UAE': (22.6, 26.1, 51.5, 56.4),
	'Israel': (29.5, 33.3, 34.3, 35.9),
	'Turkey': (36.0, 42.1, 26.0, 44.8),
	'Chile': (-55.9, -17.5, -75.6, -66.9),
	'Colombia': (-4.2, 12.5, -79.0, -66.9),
	'Peru': (-18.4, -0.0, -81.3, -68.7),
	'Pakistan': (23.7, 37.1, 60.9, 77.8),
	'Bangladesh': (20.7, 26.6, 88.0, 92.7),
}

def get_country_from_coordinates(lat, lng):
	"""
	Get country name from latitude/longitude using bounding box lookup.
	Returns 'Unknown' if coordinates don't match any known country.
	"""
	if lat is None or lng is None:
		return 'Unknown'
	
	try:
		lat = float(lat)
		lng = float(lng)
	except (ValueError, TypeError):
		return 'Unknown'
	
	# Check each country's bounding box
	for country, (min_lat, max_lat, min_lng, max_lng) in COUNTRY_BOUNDING_BOXES.items():
		if min_lat <= lat <= max_lat and min_lng <= lng <= max_lng:
			return country
	
	# If no bounding box match, try reverse geocoding as fallback (cached)
	return reverse_geocode_country(lat, lng)

# Simple cache for reverse geocoding results
_geocode_cache = {}

def reverse_geocode_country(lat, lng):
	"""
	Reverse geocode coordinates to country using geopy with caching.
	Falls back to 'Unknown' on error.
	"""
	# Round coordinates to reduce cache misses (1 decimal = ~11km precision)
	cache_key = (round(lat, 1), round(lng, 1))
	
	if cache_key in _geocode_cache:
		return _geocode_cache[cache_key]
	
	try:
		from geopy.geocoders import Nominatim
		geolocator = Nominatim(user_agent="analytiq-geo")
		location = geolocator.reverse(f"{lat}, {lng}", language='en', timeout=5)
		if location and location.raw and 'address' in location.raw:
			country = location.raw['address'].get('country', 'Unknown')
			_geocode_cache[cache_key] = country
			return country
	except Exception:
		pass
	
	_geocode_cache[cache_key] = 'Unknown'
	return 'Unknown'

def parse_user_agent(ua):
	"""Parse user agent to extract browser and OS"""
	browser = 'Unknown'
	os = 'Unknown'
	
	# Browser detection
	if 'Chrome' in ua and 'Edg' not in ua:
		browser = 'Chrome'
	elif 'Safari' in ua and 'Chrome' not in ua:
		browser = 'Safari'
	elif 'Firefox' in ua:
		browser = 'Firefox'
	elif 'Edg' in ua:
		browser = 'Edge'
	elif 'Opera' in ua or 'OPR' in ua:
		browser = 'Opera'
	
	# OS detection
	if 'Windows' in ua:
		os = 'Windows'
	elif 'Mac' in ua:
		os = 'macOS'
	elif 'Linux' in ua:
		os = 'Linux'
	elif 'Android' in ua:
		os = 'Android'
	elif 'iOS' in ua or 'iPhone' in ua or 'iPad' in ua:
		os = 'iOS'
	
	return browser, os

def get_traffic_source(referrer, utm_params):
	"""Determine traffic source from referrer and UTM parameters"""
	if utm_params:
		return 'paid'
	
	if not referrer:
		return 'direct'
	
	try:
		ref_domain = urlparse(referrer).netloc.lower()
		
		if 'google.' in ref_domain or 'bing.' in ref_domain or 'yahoo.' in ref_domain:
			return 'organic'
		elif any(social in ref_domain for social in ['facebook', 'twitter', 'linkedin', 'instagram', 'tiktok', 'youtube']):
			return 'social'
		else:
			return 'referral'
	except:
		return 'direct'

def calculate_visitors_pageviews_trend(site_id, start_date, end_date):
	"""
	Calculate visitors and pageviews trend with dynamic time bucketing based on date range.
	
	Rules:
	- 1-3 days: 12-hour intervals
	- 4-10 days: daily buckets
	- 11-30 days: daily buckets
	- 31+ days: weekly buckets
	"""
	days_diff = (end_date - start_date).days + 1
	
	# Determine bucket strategy
	if days_diff <= 3:
		# 12-hour intervals
		bucket_hours = 12
		date_format = '%Y-%m-%d %I%p'  # e.g., "2025-12-30 12PM"
		
		# Generate all expected buckets
		current = datetime.combine(start_date, datetime.min.time())
		end_dt = datetime.combine(end_date, datetime.max.time())
		buckets = {}
		
		while current <= end_dt:
			bucket_key = current.strftime(date_format)
			buckets[bucket_key] = {'visitors': set(), 'pageviews': 0}
			current += timedelta(hours=bucket_hours)
		
		# Query data and bucket by 12-hour intervals
		raw_events = con.execute('''
			SELECT visitor_id, ts, event_type
			FROM raw_events
			WHERE site_id = ? AND DATE(ts) BETWEEN ? AND ?
		''', [site_id, str(start_date), str(end_date)]).fetchall()
		
		for event in raw_events:
			visitor_id, ts, event_type = event
			try:
				if isinstance(ts, str):
					if 'T' in ts:
						if ts.endswith('Z'):
							ts = ts[:-1] + '+00:00'
						event_dt = datetime.fromisoformat(ts)
					else:
						event_dt = datetime.fromisoformat(ts)
				else:
					event_dt = ts
				
				# Round down to 12-hour bucket
				hour = event_dt.hour
				bucket_hour = 0 if hour < 12 else 12
				bucket_dt = event_dt.replace(hour=bucket_hour, minute=0, second=0, microsecond=0)
				bucket_key = bucket_dt.strftime(date_format)
				
				if bucket_key in buckets:
					buckets[bucket_key]['visitors'].add(visitor_id)
					if event_type == 'pageview':
						buckets[bucket_key]['pageviews'] += 1
			except Exception:
				continue
		
		# Format output
		result = []
		for period in sorted(buckets.keys()):
			result.append({
				'period': period,
				'visitors': len(buckets[period]['visitors']),
				'pageviews': buckets[period]['pageviews']
			})
		
		return result
		
	elif days_diff <= 30:
		# Daily buckets
		date_format = '%Y-%m-%d'
		
		# Generate all expected buckets
		current = start_date
		buckets = {}
		
		while current <= end_date:
			bucket_key = current.strftime(date_format)
			buckets[bucket_key] = {'visitors': set(), 'pageviews': 0}
			current += timedelta(days=1)
		
		# Query data and bucket by day
		raw_events = con.execute('''
			SELECT visitor_id, ts, event_type
			FROM raw_events
			WHERE site_id = ? AND DATE(ts) BETWEEN ? AND ?
		''', [site_id, str(start_date), str(end_date)]).fetchall()
		
		for event in raw_events:
			visitor_id, ts, event_type = event
			try:
				if isinstance(ts, str):
					if 'T' in ts:
						if ts.endswith('Z'):
							ts = ts[:-1] + '+00:00'
						event_dt = datetime.fromisoformat(ts)
					else:
						event_dt = datetime.fromisoformat(ts)
				else:
					event_dt = ts
				
				bucket_key = event_dt.strftime(date_format)
				
				if bucket_key in buckets:
					buckets[bucket_key]['visitors'].add(visitor_id)
					if event_type == 'pageview':
						buckets[bucket_key]['pageviews'] += 1
			except Exception:
				continue
		
		# Format output
		result = []
		for period in sorted(buckets.keys()):
			result.append({
				'period': period,
				'visitors': len(buckets[period]['visitors']),
				'pageviews': buckets[period]['pageviews']
			})
		
		return result
		
	else:
		# Weekly buckets (31+ days)
		# Group by week starting Monday
		buckets = {}
		
		# Query data
		raw_events = con.execute('''
			SELECT visitor_id, ts, event_type
			FROM raw_events
			WHERE site_id = ? AND DATE(ts) BETWEEN ? AND ?
		''', [site_id, str(start_date), str(end_date)]).fetchall()
		
		for event in raw_events:
			visitor_id, ts, event_type = event
			try:
				if isinstance(ts, str):
					if 'T' in ts:
						if ts.endswith('Z'):
							ts = ts[:-1] + '+00:00'
						event_dt = datetime.fromisoformat(ts)
					else:
						event_dt = datetime.fromisoformat(ts)
				else:
					event_dt = ts
				
				# Get the Monday of the week
				days_since_monday = event_dt.weekday()
				week_start = event_dt - timedelta(days=days_since_monday)
				bucket_key = week_start.strftime('%Y-%m-%d')
				
				if bucket_key not in buckets:
					buckets[bucket_key] = {'visitors': set(), 'pageviews': 0}
				
				buckets[bucket_key]['visitors'].add(visitor_id)
				if event_type == 'pageview':
					buckets[bucket_key]['pageviews'] += 1
			except Exception:
				continue
		
		# Format output with "Week of" prefix
		result = []
		for period in sorted(buckets.keys()):
			result.append({
				'period': f"Week of {period}",
				'visitors': len(buckets[period]['visitors']),
				'pageviews': buckets[period]['pageviews']
			})
		
		return result

def create_page_data():
	"""Create a new page data structure"""
	return {
		'views': 0,
		'visitors': set(),
		'total_time': 0,
		'time_samples': [],
		'load_times': [],
		'scroll_depths': [],
		'clicks': [],
		'referrers': Counter(),
		'links_clicked': Counter()
	}

def create_pages_data():
	"""Create a new pages data structure for combining"""
	return {
		'views': 0,
		'unique_visitors': set(),
		# 'total_time': 0,
		'time_samples': [],
		'load_times': [],
		'scroll_depths': [],
		'clicks': []
	}

def aggregate_daily(site_id):
	"""Comprehensive daily aggregation for all event types"""
	
	# Ensure all aggregation tables exist
	create_aggregation_tables()

	today = datetime.utcnow().date()

	# # Prevent double aggregation for the same day
	# already_aggregated = con.execute('''
	# 	SELECT 1 FROM aggregated_metrics_daily WHERE site_id = ? AND day = ?
	# ''', [site_id, str(today)]).fetchone()
	# if already_aggregated:
	# 	# Already aggregated for today, skip to prevent double-counting
	# 	return

	# Get all events for today
	raw_events = con.execute('''
		SELECT event_id, payload, visitor_id, session_id, event_type, ts
		FROM raw_events
		WHERE site_id = ? AND DATE(ts) = ?
	''', [site_id, str(today)]).fetchall()

	conversion_events = con.execute('''
		SELECT * FROM conversion_events
		WHERE site_id = ? AND DATE(ts) = ?
	''', [site_id, str(today)]).fetchall()

	performance_events = con.execute('''
		SELECT * FROM performance_events
		WHERE site_id = ? AND DATE(ts) = ?
	''', [site_id, str(today)]).fetchall()

	engagement_events = con.execute('''
		SELECT * FROM engagement_events
		WHERE site_id = ? AND DATE(ts) = ?
	''', [site_id, str(today)]).fetchall()

	search_events = con.execute('''
		SELECT * FROM search_events
		WHERE site_id = ? AND DATE(ts) = ?
	''', [site_id, str(today)]).fetchall()

	custom_events = con.execute('''
		SELECT * FROM custom_events
		WHERE site_id = ? AND DATE(ts) = ?
	''', [site_id, str(today)]).fetchall()

	if not raw_events:
		return
	
	# Process raw events
	pageviews = []
	visitors = set()
	sessions = defaultdict(list)
	traffic_sources = Counter()
	devices = Counter()
	browsers = Counter()
	operating_systems = Counter()
	pages = defaultdict(create_page_data)
	utm_campaigns = Counter()
	geo_data = []
	screen_resolutions = Counter()
	downlink_values = []
	rtt_values = []
	
	# Time-series tracking
	hourly_visitors = defaultdict(set)  # hour -> set of visitor_ids
	daily_timeline = []  # List of events with timestamps
	referrer_details = []  # Detailed referrer information
	user_journeys = defaultdict(list)  # visitor_id -> journey steps
	
	# Advanced metrics tracking
	entry_pages = Counter()  # First page visited in session
	exit_pages = Counter()   # Last page visited in session
	page_transitions = Counter()  # page A -> page B transitions
	click_heatmap = defaultdict(lambda: defaultdict(int))  # page -> coordinates -> clicks
	scroll_tracking = defaultdict(list)  # page -> scroll depths
	load_performance = defaultdict(list)  # page -> load times
	
	# Process each raw event
	for event in raw_events:
		event_id, payload_str, visitor_id, session_id, event_type, ts = event
		payload = json.loads(payload_str) if payload_str else {}
		
		visitors.add(visitor_id)
		sessions[session_id].append((event_type, payload, ts))
		
		# Parse timestamp for time-series tracking
		try:
			if isinstance(ts, str):
				if 'T' in ts:
					if ts.endswith('Z'):
						ts = ts[:-1] + '+00:00'
					event_time = datetime.fromisoformat(ts)
				else:
					event_time = datetime.fromisoformat(ts)
			else:
				event_time = ts
			
			# Track hourly visitors
			hour_key = event_time.strftime('%H:00')
			hourly_visitors[hour_key].add(visitor_id)
			
			# Add to timeline
			daily_timeline.append({
				'timestamp': event_time.isoformat(),
				'visitor_id': visitor_id,
				'session_id': session_id,
				'event_type': event_type,
				'hour': hour_key
			})
			
		except (ValueError, TypeError):
			event_time = datetime.utcnow()
			hour_key = event_time.strftime('%H:00')
			hourly_visitors[hour_key].add(visitor_id)
		
		if event_type == 'pageview':
			pageviews.append((visitor_id, session_id, payload, ts))
			
			# Track user journey
			url = payload.get('url', '')
			path = normalize_path(urlparse(url).path) if url else '/'
			user_journeys[visitor_id].append({
				'page': path,
				'timestamp': event_time.isoformat() if 'event_time' in locals() else str(ts),
				'session_id': session_id
			})
			
			# Traffic source analysis with detailed tracking
			referrer = payload.get('referrer', '')
			utm_params = {k: v for k, v in payload.items() if k.startswith('utm_')}
			source = get_traffic_source(referrer, utm_params)
			traffic_sources[source] += 1
			
			# Detailed referrer tracking
			if referrer:
				referrer_details.append({
					'referrer': referrer,
					'visitor_id': visitor_id,
					'timestamp': event_time.isoformat() if 'event_time' in locals() else str(ts),
					'landing_page': path
				})
			
			# Device analysis
			device_type = payload.get('device_type', 'desktop')  # Default to desktop
			devices[device_type] += 1
			
			# Browser/OS analysis
			user_agent = payload.get('user_agent', '')
			browser, os = parse_user_agent(user_agent)
			browsers[browser] += 1
			operating_systems[os] += 1
			
			# Page analysis with enhanced tracking
			title = payload.get('title', '')
			
			pages[path]['views'] += 1
			pages[path]['visitors'].add(visitor_id)
			
			# Track load performance (validate positive values only)
			if payload.get('load_event'):
				load_time = payload['load_event']
				if isinstance(load_time, (int, float)) and load_time > 0:
					pages[path]['load_times'].append(load_time)
					load_performance[path].append(load_time)
			
			# Track page as entry/exit point (will be refined later in session analysis)
			if len(user_journeys[visitor_id]) == 1:
				entry_pages[path] += 1
			
			# Screen resolution
			screen = payload.get('screen', '1920x1080')  # Default resolution
			if screen:
				screen_resolutions[screen] += 1
			# Network info
			downlink = payload.get('downlink_mbps')
			rtt = payload.get('rtt_ms')
			if downlink is not None:
				try:
					downlink_values.append(float(downlink))
				except Exception:
					pass
			if rtt is not None:
				try:
					rtt_values.append(float(rtt))
				except Exception:
					pass
			
			# UTM campaigns with better handling
			if utm_params:
				campaign = utm_params.get('utm_campaign', 'direct')
				source = utm_params.get('utm_source', 'unknown')
				medium = utm_params.get('utm_medium', 'unknown')
				campaign_key = f"{campaign}_{source}_{medium}"
				utm_campaigns[campaign_key] += 1
			else:
				# Track direct traffic as a campaign
				utm_campaigns['direct_traffic'] += 1
			
			# Geo data with improved country lookup using bounding boxes
			geo = payload.get('geo')
			lat = geo.get('lat') if geo else None
			long = geo.get('long') if geo else None
			country = geo.get('country') if geo else None
			city = geo.get('city', 'Unknown') if geo else 'Unknown'
			
			if lat is not None and long is not None:
				# If country is missing or unknown, use bounding box lookup
				if not country or country == 'Unknown':
					country = get_country_from_coordinates(lat, long)
				
				geo_data.append({
					'lat': lat,
					'long': long,
					'country': country,
					'city': city,
					'timestamp': event_time.isoformat() if 'event_time' in locals() else str(ts)
				})
			elif country and country != 'Unknown':
				# We have country but no coordinates - still useful for geo_distribution
				geo_data.append({
					'lat': 0,
					'long': 0,
					'country': country,
					'city': city,
					'timestamp': event_time.isoformat() if 'event_time' in locals() else str(ts)
				})
			# Skip entries with no useful geo data (no coordinates AND no country)
		
		# Track clicks and interactions
		elif event_type == 'click':
			page = payload.get('page', '/')
			x = payload.get('x', 0)
			y = payload.get('y', 0)
			click_heatmap[page][f"{x},{y}"] += 1
		
		# Track scroll events
		elif event_type == 'scroll':
			page = payload.get('page', '/')
			depth = payload.get('depth', 0)
			scroll_tracking[page].append(depth)
	
	# Process performance events
	performance_metrics = {
		'first_contentful_paint_avg_ms': 0.0,
		'largest_contentful_paint_avg_ms': 0.0,
		'cumulative_layout_shift_avg': 0.0,
		'first_input_delay_avg_ms': 0.0,
		'server_response_time_avg_ms': 0.0,
		'cdn_cache_hit_ratio_percent': 0.0
	}
	
	if performance_events:
		fcp_values = [e[6] for e in performance_events if e[6]]  # first_contentful_paint
		lcp_values = [e[7] for e in performance_events if e[7]]  # largest_contentful_paint
		cls_values = [e[8] for e in performance_events if e[8]]  # cumulative_layout_shift
		fid_values = [e[9] for e in performance_events if e[9]]  # first_input_delay
		srt_values = [e[15] for e in performance_events if e[15]]  # server_response_time
		
		if fcp_values:
			performance_metrics['first_contentful_paint_avg_ms'] = sum(fcp_values) / len(fcp_values)
		if lcp_values:
			performance_metrics['largest_contentful_paint_avg_ms'] = sum(lcp_values) / len(lcp_values)
		if cls_values:
			performance_metrics['cumulative_layout_shift_avg'] = sum(cls_values) / len(cls_values)
		if fid_values:
			performance_metrics['first_input_delay_avg_ms'] = sum(fid_values) / len(fid_values)
		if srt_values:
			performance_metrics['server_response_time_avg_ms'] = sum(srt_values) / len(srt_values)

		# Calculate cache hit ratio
		total_resources = sum([e[16] or 0 for e in performance_events])
		cached_resources = sum([e[17] or 0 for e in performance_events])
		if total_resources > 0:
			performance_metrics['cdn_cache_hit_ratio_percent'] = (cached_resources / total_resources) * 100
	
	# Process engagement events
	engagement_summary = {
		'avg_scroll_depth_percent': 0.0,
		'avg_clicks_per_session': 0.0,
		'avg_idle_time_sec': 0.0,
		'avg_form_interactions': 0.0,
		'avg_video_watch_time_sec': 0.0
	}
	
	if engagement_events:
		scroll_depths = [e[6] for e in engagement_events if e[6]]  # scroll_depth_percent
		clicks = [e[8] for e in engagement_events if e[8]]  # clicks_count
		idle_times = [e[9] for e in engagement_events if e[9]]  # idle_time_sec
		video_times = [e[15] for e in engagement_events if e[15]]  # video_watch_time_sec
		form_interactions = len([e for e in engagement_events if e[12] or e[13]])  # form_started or form_completed
		
		if scroll_depths:
			engagement_summary['avg_scroll_depth_percent'] = sum(scroll_depths) / len(scroll_depths)
		if clicks:
			engagement_summary['avg_clicks_per_session'] = sum(clicks) / len(sessions)
		if idle_times:
			engagement_summary['avg_idle_time_sec'] = sum(idle_times) / len(idle_times)
		if video_times:
			engagement_summary['avg_video_watch_time_sec'] = sum(video_times) / len(video_times)

		engagement_summary['avg_form_interactions'] = form_interactions / len(sessions) if sessions else 0

	# Merge specialized performance events into per-page aggregates
	for pe in performance_events:
		# pe indices: 0:event_id,1:site_id,2:ts,3:visitor_id,4:session_id,5:url,14:load_event_end,15:server_response_time
		try:
			url = pe[5] if len(pe) > 5 else None
			if url:
				path = normalize_path(urlparse(url).path)
				# prefer server_response_time, fallback to load_event_end (validate positive values)
				load_time = None
				if len(pe) > 15 and pe[15] is not None:
					if isinstance(pe[15], (int, float)) and pe[15] > 0:
						load_time = pe[15]
				elif len(pe) > 14 and pe[14] is not None:
					if isinstance(pe[14], (int, float)) and pe[14] > 0:
						load_time = pe[14]
				if load_time is not None:
					pages[path]['load_times'].append(load_time)
		except Exception:
			pass

	# Merge specialized engagement events into per-page aggregates
	for ee in engagement_events:
		# ee indices: 0:event_id,1:site_id,2:ts,3:visitor_id,4:session_id,5:url,6:scroll_depth_percent,7:time_on_page_sec,8:clicks_count
		try:
			url = ee[5] if len(ee) > 5 else None
			if url:
				path = normalize_path(urlparse(url).path)
				scroll = ee[6] if len(ee) > 6 else None
				time_on_page = ee[7] if len(ee) > 7 else None
				clicks_count = ee[8] if len(ee) > 8 else None
				if scroll is not None:
					pages[path]['scroll_depths'].append(scroll)
				if time_on_page is not None:
					try:
						# pages[path]['total_time'] += float(time_on_page)
						pages[path]['time_samples'].append(float(time_on_page))
					except Exception:
						pass
				if clicks_count is not None:
					try:
						pages[path]['clicks'].append(int(clicks_count))
					except Exception:
						pass
		except Exception:
			pass

	# Also merge raw-event collected scroll_tracking and load_performance into pages
	for path, depths in scroll_tracking.items():
		if depths:
			pages[path]['scroll_depths'].extend(depths)

	for path, times in load_performance.items():
		if times:
			pages[path]['load_times'].extend(times)
	
	# Process search events
	search_terms = Counter()
	for search_event in search_events:
		term = search_event[5]  # search_term column
		if term:
			search_terms[term] += 1
	
	# Process custom events
	events_summary = Counter()
	for custom_event in custom_events:
		event_name = custom_event[5]  # event_name column
		if event_name:
			events_summary[event_name] += 1
	
	# Calculate metrics
	total_visitors = len(visitors)
	unique_visitors = total_visitors
	total_pageviews = len(pageviews)
	
	# Calculate session metrics
	session_durations = []
	session_page_counts = []
	bounce_sessions = 0
	
	for session_id, session_events in sessions.items():
		page_events = [e for e in session_events if e[0] == 'pageview']
		session_page_counts.append(len(page_events))
		
		if len(page_events) == 1:
			bounce_sessions += 1
		
		# Calculate session duration from first to last event
		if len(session_events) > 1:
			times = []
			for e in session_events:
				# Handle different timestamp formats
				ts_str = str(e[2])
				try:
					if 'T' in ts_str:
						# ISO format
						if ts_str.endswith('Z'):
							ts_str = ts_str[:-1] + '+00:00'
						times.append(datetime.fromisoformat(ts_str))
					else:
						# Simple format - parse as is
						times.append(datetime.fromisoformat(ts_str))
				except (ValueError, TypeError):
					# Skip invalid timestamps
					continue
			
			if len(times) > 1:
				duration = (max(times) - min(times)).total_seconds()
				session_durations.append(duration)
	
	avg_session_duration = sum(session_durations) / len(session_durations) if session_durations else 0
	avg_pages_per_session = sum(session_page_counts) / len(session_page_counts) if session_page_counts else 0
	bounce_rate = (bounce_sessions / len(sessions)) * 100 if sessions else 0
	
	# Calculate per-page bounce and exit rates for the daily report
	page_bounce = {}
	page_exit = {}
	for path, data in pages.items():
		# Bounce: session with only one pageview and it's this page
		bounce_count = 0
		exit_count = 0
		for session in sessions.values():
			pageviews_in_session = [e for e in session if e[0] == 'pageview']
			if len(pageviews_in_session) == 1:
				url = pageviews_in_session[0][1].get('url')
				if url and normalize_path(urlparse(url).path) == path:
					bounce_count += 1
			# Exit: last pageview in session is this page
			if len(pageviews_in_session) > 0:
				last_url = pageviews_in_session[-1][1].get('url')
				if last_url and normalize_path(urlparse(last_url).path) == path:
					exit_count += 1
		page_bounce[path] = round(100 * bounce_count / data['views'], 1) if data['views'] > 0 else 0
		page_exit[path] = round(100 * exit_count / data['views'], 1) if data['views'] > 0 else 0

	# Prepare aggregated data
	aggregated_data = {
		'site_id': site_id,
		'day': str(today),
		'total_visitors': total_visitors,
		'unique_visitors': unique_visitors,
		'total_pageviews': total_pageviews,
		'avg_session_duration_sec': avg_session_duration,
		'avg_pages_per_session': avg_pages_per_session,
		'bounce_rate_percent': bounce_rate,
		'traffic_sources': dict(traffic_sources),
		'devices': dict(devices),
		'browsers': dict(browsers),
		'operating_systems': dict(operating_systems),
		'utm_campaigns': dict(utm_campaigns),
		'performance_metrics': performance_metrics,
		'engagement_summary': engagement_summary,
		'search_terms': dict(search_terms),
		'events_summary': dict(events_summary),
		'screen_resolutions': dict(screen_resolutions),
		'downlink_values': downlink_values,
		'rtt_values': rtt_values,
		'geo_data': geo_data[:100],  # Limit to last 100 for performance
		'hourly_visitors': {hour: len(visitors) for hour, visitors in hourly_visitors.items()},
		'daily_visitors_timeline': daily_timeline[:500],  # Limit for performance
		'referrer_details': referrer_details[:100],  # Latest 100 referrers
		'user_journey': {visitor_id: journey for visitor_id, journey in list(user_journeys.items())[:50]},  # Top 50 user journeys
		'advanced_metrics': {
			'click_heatmap': {page: dict(clicks) for page, clicks in click_heatmap.items()},
			'scroll_tracking': {page: depths for page, depths in scroll_tracking.items()},
			'load_performance': {page: times for page, times in load_performance.items()},
			'entry_pages': dict(entry_pages),
			'exit_pages': dict(exit_pages),
			'page_bounce': page_bounce,
			'page_exit': page_exit
		},
		'pages_data': {
			path: {
				'views': data['views'],
				'unique_visitors': len(data['visitors']),
				'avg_load_time_ms': sum(data['load_times']) / len(data['load_times']) if data['load_times'] else 0,
				# 'total_time': data['total_time'],
				'time_samples': data['time_samples'],
				'scroll_depths': data['scroll_depths'],
				'clicks': data['clicks'],
				'bounce_rate_percent': page_bounce.get(path, 0),
				'exit_rate_percent': page_exit.get(path, 0)
			} for path, data in pages.items()
		}
	}
	
	# Store in database
	store_daily_aggregation(aggregated_data)

def create_aggregation_tables():
	"""Create tables for storing aggregated data"""
	# Create table only if it doesn't exist - DO NOT DROP to preserve multi-site data
	con.execute('''
	CREATE TABLE IF NOT EXISTS aggregated_metrics_daily (
		site_id VARCHAR,
		day DATE,
		total_visitors INTEGER,
		unique_visitors INTEGER,
		total_pageviews INTEGER,
		avg_session_duration_sec DOUBLE,
		avg_pages_per_session DOUBLE,
		bounce_rate_percent DOUBLE,
		traffic_sources JSON,
		devices JSON,
		browsers JSON,
		operating_systems JSON,
		utm_campaigns JSON,
		performance_metrics JSON,
		engagement_summary JSON,
		search_terms JSON,
		events_summary JSON,
		screen_resolutions JSON,
		geo_data JSON,
		pages_data JSON,
		hourly_visitors JSON,
		daily_visitors_timeline JSON,
		referrer_details JSON,
		user_journey JSON,
		advanced_metrics JSON,
		PRIMARY KEY (site_id, day)
	)
	''')

def store_daily_aggregation(data):
	"""Store daily aggregation data"""
	
	# Use INSERT OR REPLACE to avoid race condition between DELETE and INSERT
	# This ensures atomic update without a window where data is missing
	con.execute('''
		INSERT OR REPLACE INTO aggregated_metrics_daily 
		(site_id, day, total_visitors, unique_visitors, total_pageviews, 
		 avg_session_duration_sec, avg_pages_per_session, bounce_rate_percent, 
		 traffic_sources, devices, browsers, 
		 operating_systems, utm_campaigns, performance_metrics,
		 engagement_summary, search_terms, events_summary, screen_resolutions, geo_data, pages_data,
		 hourly_visitors, daily_visitors_timeline, referrer_details, user_journey, advanced_metrics)
		VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
	''', [
		data['site_id'], data['day'], data['total_visitors'], data['unique_visitors'],
		data['total_pageviews'], data['avg_session_duration_sec'], data['avg_pages_per_session'],
		data['bounce_rate_percent'],
		json.dumps(data['traffic_sources']), json.dumps(data['devices']),
		json.dumps(data['browsers']), json.dumps(data['operating_systems']),
		json.dumps(data['utm_campaigns']), json.dumps(data['performance_metrics']),
		json.dumps(data['engagement_summary']), json.dumps(data['search_terms']), 
		json.dumps(data['events_summary']), json.dumps(data['screen_resolutions']), 
		json.dumps(data['geo_data']), json.dumps(data['pages_data']), 
		json.dumps(data['hourly_visitors']), json.dumps(data['daily_visitors_timeline']), 
		json.dumps(data['referrer_details']), json.dumps(data['user_journey']), 
		json.dumps(data['advanced_metrics'])
	])

def update_dash_summary(site_id):
	"""Update real-time dashboard summary"""
	con.execute('''
	CREATE TABLE IF NOT EXISTS dash_summary (
		site_id VARCHAR PRIMARY KEY,
		last_updated TIMESTAMP,
		current_total_visitors INTEGER,
		current_pageviews INTEGER,
		snapshot JSON
	)
	''')
	
	# Get current totals
	totals = con.execute('''
		SELECT COUNT(DISTINCT visitor_id), COUNT(*)
		FROM raw_events
		WHERE site_id = ? AND event_type = 'pageview'
	''', [site_id]).fetchone()
	
	total_visitors = totals[0] if totals else 0
	total_pageviews = totals[1] if totals else 0
	
	# Get recent activity (last hour) - using DuckDB syntax
	recent_activity = con.execute('''
		SELECT COUNT(DISTINCT visitor_id), COUNT(*)
		FROM raw_events
		WHERE site_id = ? AND ts > (current_timestamp - INTERVAL 1 HOUR)
	''', [site_id]).fetchone()
	
	recent_visitors = recent_activity[0] if recent_activity else 0
	recent_pageviews = recent_activity[1] if recent_activity else 0
	
	snapshot = {
		"total_visitors": total_visitors,
		"total_pageviews": total_pageviews,
		"recent_visitors": recent_visitors,
		"recent_pageviews": recent_pageviews,
		"last_updated": datetime.utcnow().isoformat()
	}
	
	# Use INSERT OR REPLACE to avoid race condition between DELETE and INSERT
	# This ensures atomic update without a window where data is missing
	con.execute('''
		INSERT OR REPLACE INTO dash_summary (site_id, last_updated, current_total_visitors, current_pageviews, snapshot)
		VALUES (?, current_timestamp, ?, ?, ?)
	''', [site_id, total_visitors, total_pageviews, json.dumps(snapshot)])

def generate_comprehensive_report(site_id, start_date, end_date):
	"""Generate a comprehensive report like the sample JSON"""
	
	# Get site information
	site_info = con.execute('''
		SELECT name, url FROM sites WHERE site_id = ?
	''', [site_id]).fetchone()
	
	if not site_info:
		return None
	
	# Get aggregated data for the date range
	aggregated_data = con.execute('''
		SELECT * FROM aggregated_metrics_daily
		WHERE site_id = ? AND day BETWEEN ? AND ?
		ORDER BY day
	''', [site_id, str(start_date), str(end_date)]).fetchall()
	
	if not aggregated_data:
		return None
	
	# Build comprehensive report from aggregated data
	total_visitors = sum(row[2] for row in aggregated_data)  # total_visitors
	unique_visitors = sum(row[3] for row in aggregated_data)  # unique_visitors
	total_pageviews = sum(row[4] for row in aggregated_data)  # total_pageviews
	
	# Calculate averages
	num_days = len(aggregated_data)
	avg_session_duration = sum(row[5] for row in aggregated_data) / num_days if num_days > 0 else 0
	avg_pages_per_session = sum(row[6] for row in aggregated_data) / num_days if num_days > 0 else 0
	# Calculate bounce rate from total sessions and bounce sessions across all days
	total_sessions = 0
	total_bounce_sessions = 0

	for row in aggregated_data:
		day_visitors = row[2]  # total_visitors
		day_bounce_rate = row[7]  # bounce_rate_percent
		
		# Back-calculate the number of sessions and bounces for this day
		# Assuming sessions ≈ total_visitors (approximate, but better than averaging percentages)
		day_sessions = day_visitors
		day_bounces = int((day_bounce_rate / 100) * day_sessions)
		
		total_sessions += day_sessions
		total_bounce_sessions += day_bounces

	avg_bounce_rate = (total_bounce_sessions / total_sessions) * 100 if total_sessions > 0 else 0
	# avg_bounce_rate = sum(row[7] for row in aggregated_data) / num_days if num_days > 0 else 0
	
	# Combine JSON data from all days
	combined_traffic_sources = Counter()
	combined_devices = Counter()
	combined_browsers = Counter()
	combined_operating_systems = Counter()
	combined_utm_campaigns = Counter()
	combined_screen_resolutions = Counter()
	combined_search_terms = Counter()
	combined_events_summary = Counter()
	all_geo_data = []
	combined_pages_data = defaultdict(create_pages_data)
	
	# Time-series data aggregation
	all_hourly_visitors = defaultdict(list)
	all_daily_timelines = []
	all_referrer_details = []
	all_user_journeys = {}
	combined_advanced_metrics = {
		'click_heatmap': defaultdict(Counter),
		'scroll_tracking': defaultdict(list),
		'load_performance': defaultdict(list),
		'entry_pages': Counter(),
		'exit_pages': Counter()
	}
	
	# Aggregate performance and engagement metrics
	all_performance_metrics = []
	all_engagement_metrics = []
	
	for row in aggregated_data:
		# Parse JSON fields (updated indices after removing conversion fields)
		traffic_sources = json.loads(row[8]) if row[8] else {}
		devices = json.loads(row[9]) if row[9] else {}
		browsers = json.loads(row[10]) if row[10] else {}
		operating_systems = json.loads(row[11]) if row[11] else {}
		utm_campaigns = json.loads(row[12]) if row[12] else {}
		performance_metrics = json.loads(row[13]) if row[13] else {}
		engagement_summary = json.loads(row[14]) if row[14] else {}
		search_terms = json.loads(row[15]) if row[15] else {}
		events_summary = json.loads(row[16]) if row[16] else {}
		screen_resolutions = json.loads(row[17]) if row[17] else {}
		# Note: aggregated table stores geo_data at index 18 and pages_data at index 19
		# downlink_values and rtt_values are not persisted as separate columns in the table
		downlink_values = []
		rtt_values = []
		geo_data = json.loads(row[18]) if len(row) > 18 and row[18] else []
		pages_data = json.loads(row[19]) if len(row) > 19 and row[19] else {}
		
		# Parse new time-series fields if they exist
		base_fields = 20  # Number of base fields
		if len(row) > base_fields:
			hourly_visitors = json.loads(row[20]) if len(row) > 20 and row[20] else {}
			daily_timeline = json.loads(row[21]) if len(row) > 21 and row[21] else []
			referrer_details = json.loads(row[22]) if len(row) > 22 and row[22] else []
			user_journey = json.loads(row[23]) if len(row) > 23 and row[23] else {}
			advanced_metrics = json.loads(row[24]) if len(row) > 24 and row[24] else {}
			
			# Aggregate time-series data
			for hour, count in hourly_visitors.items():
				all_hourly_visitors[hour].append(count)
			
			all_daily_timelines.extend(daily_timeline)
			all_referrer_details.extend(referrer_details)
			all_user_journeys.update(user_journey)
			
			# Aggregate advanced metrics
			if 'click_heatmap' in advanced_metrics:
				for page, clicks in advanced_metrics['click_heatmap'].items():
					combined_advanced_metrics['click_heatmap'][page].update(clicks)
			
			if 'scroll_tracking' in advanced_metrics:
				for page, depths in advanced_metrics['scroll_tracking'].items():
					combined_advanced_metrics['scroll_tracking'][page].extend(depths)
			
			if 'load_performance' in advanced_metrics:
				for page, times in advanced_metrics['load_performance'].items():
					combined_advanced_metrics['load_performance'][page].extend(times)
			
			if 'entry_pages' in advanced_metrics:
				combined_advanced_metrics['entry_pages'].update(advanced_metrics['entry_pages'])
			
			if 'exit_pages' in advanced_metrics:
				combined_advanced_metrics['exit_pages'].update(advanced_metrics['exit_pages'])
		
		# Combine counters
		combined_traffic_sources.update(traffic_sources)
		combined_devices.update(devices)
		combined_browsers.update(browsers)
		combined_operating_systems.update(operating_systems)
		combined_utm_campaigns.update(utm_campaigns)
		combined_screen_resolutions.update(screen_resolutions)
		all_downlink_values = []
		all_rtt_values = []
		if downlink_values:
			all_downlink_values.extend([v for v in downlink_values if isinstance(v, (int, float))])
		if rtt_values:
			all_rtt_values.extend([v for v in rtt_values if isinstance(v, (int, float))])
		combined_search_terms.update(search_terms)
		combined_events_summary.update(events_summary)
		all_geo_data.extend(geo_data)
		
		# Combine pages data (normalize paths to avoid duplicates)
		for path, page_data in pages_data.items():
			normalized_path = normalize_path(path)
			if normalized_path not in combined_pages_data:
				combined_pages_data[normalized_path] = create_pages_data()
			# Views
			combined_pages_data[normalized_path]['views'] += page_data.get('views', 0)
			# Unique visitors: always use a set for correct merging
			visitors_data = page_data.get('unique_visitors', 0)
			if not isinstance(combined_pages_data[normalized_path]['unique_visitors'], set):
				combined_pages_data[normalized_path]['unique_visitors'] = set()
			if isinstance(visitors_data, (list, set)):
				combined_pages_data[normalized_path]['unique_visitors'].update(visitors_data)
			elif isinstance(visitors_data, int):
				# If it's a per-day count (int), treat as unique visitors for that day (approximate)
				# Add dummy values to set to avoid double-counting
				combined_pages_data[normalized_path]['unique_visitors'].update([f"dummy_{i}" for i in range(visitors_data)])
			# Total time spent
			# combined_pages_data[normalized_path]['total_time'] += page_data.get('total_time', 0)
			time_samples = page_data.get('time_samples', [])
			if isinstance(time_samples, list):
				combined_pages_data[normalized_path]['time_samples'].extend(time_samples)
			# Load times: accept either a list of load_times or a precomputed avg_load_time_ms
			if 'load_times' in page_data and isinstance(page_data.get('load_times'), list):
				combined_pages_data[normalized_path]['load_times'].extend(page_data.get('load_times', []))
			elif 'avg_load_time_ms' in page_data and page_data.get('avg_load_time_ms'):
				try:
					combined_pages_data[normalized_path]['load_times'].append(float(page_data.get('avg_load_time_ms')))
				except Exception:
					pass
			# Scroll depths
			scroll_depths = page_data.get('scroll_depths', [])
			if isinstance(scroll_depths, list):
				combined_pages_data[normalized_path]['scroll_depths'].extend(scroll_depths)
			# Clicks
			clicks = page_data.get('clicks', [])
			if isinstance(clicks, list):
				combined_pages_data[normalized_path]['clicks'].extend(clicks)
			# Bounce rate
			if 'bounce_rate_percent' in page_data and page_data['bounce_rate_percent'] is not None:
				if 'bounce_rate_percent' not in combined_pages_data[normalized_path] or combined_pages_data[normalized_path]['bounce_rate_percent'] is None:
					combined_pages_data[normalized_path]['bounce_rate_percent'] = page_data['bounce_rate_percent']
				else:
					combined_pages_data[normalized_path]['bounce_rate_percent'] = (
						combined_pages_data[normalized_path]['bounce_rate_percent'] + page_data['bounce_rate_percent']
					) / 2
			# Exit rate
			if 'exit_rate_percent' in page_data and page_data['exit_rate_percent'] is not None:
				if 'exit_rate_percent' not in combined_pages_data[normalized_path] or combined_pages_data[normalized_path]['exit_rate_percent'] is None:
					combined_pages_data[normalized_path]['exit_rate_percent'] = page_data['exit_rate_percent']
				else:
					combined_pages_data[normalized_path]['exit_rate_percent'] = (
						combined_pages_data[normalized_path]['exit_rate_percent'] + page_data['exit_rate_percent']
					) / 2
		
		# Collect metrics for averaging
		if performance_metrics:
			all_performance_metrics.append(performance_metrics)
		if engagement_summary:
			all_engagement_metrics.append(engagement_summary)
	
	# Calculate performance averages (skip None values to avoid TypeError)
	def _avg(key):
		vals = [m.get(key) for m in all_performance_metrics if m.get(key) is not None]
		return sum(vals) / len(vals) if vals else 0

	performance_metrics = {
		"first_contentful_paint_avg_ms": _avg('first_contentful_paint_avg_ms') if all_performance_metrics else 0,
		"largest_contentful_paint_avg_ms": _avg('largest_contentful_paint_avg_ms') if all_performance_metrics else 0,
		"cumulative_layout_shift_avg": _avg('cumulative_layout_shift_avg') if all_performance_metrics else 0,
		"first_input_delay_avg_ms": _avg('first_input_delay_avg_ms') if all_performance_metrics else 0,
		"server_response_time_avg_ms": _avg('server_response_time_avg_ms') if all_performance_metrics else 0,
		"cdn_cache_hit_ratio_percent": _avg('cdn_cache_hit_ratio_percent') if all_performance_metrics else 0
	}
	
	# Calculate engagement averages
	engagement_summary = {
		"avg_scroll_depth_percent": 0,
		"avg_clicks_per_session": 0,
		"avg_idle_time_sec": 0,
		"avg_form_interactions": 0,
		"avg_video_watch_time_sec": 0
	}
	
	if all_engagement_metrics:
		engagement_summary = {
			"avg_scroll_depth_percent": sum(m.get('avg_scroll_depth_percent', 0) for m in all_engagement_metrics) / len(all_engagement_metrics),
			"avg_clicks_per_session": sum(m.get('avg_clicks_per_session', 0) for m in all_engagement_metrics) / len(all_engagement_metrics),
			"avg_idle_time_sec": sum(m.get('avg_idle_time_sec', 0) for m in all_engagement_metrics) / len(all_engagement_metrics),
			"avg_form_interactions": sum(m.get('avg_form_interactions', 0) for m in all_engagement_metrics) / len(all_engagement_metrics),
			"avg_video_watch_time_sec": sum(m.get('avg_video_watch_time_sec', 0) for m in all_engagement_metrics) / len(all_engagement_metrics)
		}
	
	# Build the comprehensive report
	# Calculate new vs returning visitors from all ingested events in the date range
	new_visitor_count = 0
	returning_visitor_count = 0
	# Query all raw_events for this site and date range
	raw_events = con.execute('''
		SELECT payload FROM raw_events
		WHERE site_id = ? AND DATE(ts) BETWEEN ? AND ?
	''', [site_id, str(start_date), str(end_date)]).fetchall()
	seen_visitors = set()
	for (payload_str,) in raw_events:
		try:
			payload = json.loads(payload_str) if payload_str else {}
			visitor_id = payload.get('visitor_id')
			if not visitor_id or visitor_id in seen_visitors:
				continue
			seen_visitors.add(visitor_id)
			if payload.get('is_new_visitor'):
				new_visitor_count += 1
			elif payload.get('is_returning_visitor'):
				returning_visitor_count += 1
		except Exception:
			continue

	total_tracked = new_visitor_count + returning_visitor_count
	new_percent = round((new_visitor_count / total_tracked) * 100, 1) if total_tracked > 0 else 0.0
	returning_percent = round((returning_visitor_count / total_tracked) * 100, 1) if total_tracked > 0 else 0.0

	report = {
		"website_name": site_info[0],
		"url": site_info[1],
		"report_generated_at": datetime.utcnow().isoformat() + "Z",
		"date_range": f"{start_date} to {end_date}",
		"total_visitors": total_visitors,
		"unique_visitors": unique_visitors,
		"total_pageviews": total_pageviews,
		"avg_time_spent_on_site_sec": int(avg_session_duration),
		"bounce_rate_percent": round(avg_bounce_rate, 1),
		"traffic_sources": [
			{"source": k, "visitors": v, "percent": round((v/total_visitors)*100, 1) if total_visitors > 0 else 0}
			for k, v in combined_traffic_sources.most_common(5)
		],
		"devices": [
			{"type": k, "percent": round((v/total_pageviews)*100, 1) if total_pageviews > 0 else 0}
			for k, v in combined_devices.most_common(3)
		],
		"operating_systems": [
			{"name": k, "percent": round((v/total_pageviews)*100, 1) if total_pageviews > 0 else 0}
			for k, v in combined_operating_systems.most_common(5)
		],
		"browsers": [
			{"name": k, "percent": round((v/total_pageviews)*100, 1) if total_pageviews > 0 else 0}
			for k, v in combined_browsers.most_common(5)
		],
		"utm_campaigns": [
			{"campaign": k if k != 'direct_traffic' else 'Direct Traffic', "clicks": v, "conversions": 0}  # TODO: Calculate actual conversions
			for k, v in combined_utm_campaigns.most_common(10)
		] if combined_utm_campaigns else [
			{"campaign": "Direct Traffic", "clicks": total_visitors, "conversions": 0}
		],
		"last_24h_visitors_geo": all_geo_data[-100:],  # Last 100 geo points
		"engagement_summary": engagement_summary,
		"performance_metrics": performance_metrics,
		"search_terms": [
			{"term": k, "count": v}
			for k, v in combined_search_terms.most_common(10)
		],
		"events_summary": [
			{"event": k, "count": v}
			for k, v in combined_events_summary.most_common(10)
		],
		"technology": {
			"common_screen_resolutions": [
				{"resolution": k, "percent": round((v/total_visitors)*100, 1) if total_visitors > 0 else 0}
				for k, v in combined_screen_resolutions.most_common(5)
			]
		},
		"user_behavior": {
			"avg_sessions_per_user": round(total_pageviews / unique_visitors, 1) if unique_visitors > 0 else 0,
			"avg_pages_per_session": round(avg_pages_per_session, 1),
			"avg_session_duration_sec": int(avg_session_duration)
		},
			"pages": [
				{
					"page_title": path.split('/')[-1] or "Homepage",
					"path": path,
					"views": page_data['views'],
					"unique_visitors": (len(page_data['unique_visitors']) if isinstance(page_data['unique_visitors'], set) else page_data.get('unique_visitors', 0)),
					"avg_load_time_ms": int(sum(page_data.get('load_times', [])) / len(page_data.get('load_times', []))) if page_data.get('load_times') else 0,
					"avg_time_spent_sec": int(sum(page_data.get('time_samples', [])) / len(page_data.get('time_samples', []))) if page_data.get('time_samples') else 0,
					"avg_scroll_depth_percent": int(sum(page_data.get('scroll_depths', [])) / len(page_data.get('scroll_depths', []))) if page_data.get('scroll_depths') else 0,
					"bounce_rate_percent": page_data.get('bounce_rate_percent', None),
					"exit_rate_percent": page_data.get('exit_rate_percent', None)
				}
				for path, page_data in list(combined_pages_data.items())[:10]  # Top 10 pages
			],
		"total_pages": len(combined_pages_data),
		"avg_loading_time_ms": int(sum(m.get('server_response_time_avg_ms', 0) for m in all_performance_metrics) / len(all_performance_metrics)) if all_performance_metrics else 0,
		"new_vs_returning": {
			"new_percent": new_percent,
			"returning_percent": returning_percent
		},
		"geo_distribution": (
			# Calculate country-wise distribution from all_geo_data, filtering out Unknown
			lambda: (
				lambda known_geo: [
					{"country": country, "percent": round((count/len(known_geo))*100, 1)}
					for country, count in Counter(
						geo.get('country') for geo in known_geo
					).most_common()
				] if known_geo else [{"country": "Unknown", "percent": 100.0}]
			)([geo for geo in all_geo_data if geo.get('country') and geo.get('country') != 'Unknown'])
		)(),
		"time_series_data": {
			"visitors_pageviews_trend": calculate_visitors_pageviews_trend(site_id, start_date, end_date),
			"hourly_visitors": {
				hour: {
					"hour": hour,
					"average_visitors": round(sum(counts) / len(counts), 1) if counts else 0,
					"total_visitors": sum(counts)
				}
				for hour, counts in all_hourly_visitors.items()
			},
			"daily_timeline": all_daily_timelines[-100:],  # Last 100 events for timeline
			"visitor_journey_analysis": {
				"sample_journeys": dict(list(all_user_journeys.items())[:10]),  # Top 10 user journeys
				"common_entry_pages": [
					{"page": k, "visitors": v}
					for k, v in combined_advanced_metrics['entry_pages'].most_common(5)
				],
				"common_exit_pages": [
					{"page": k, "visitors": v}
					for k, v in combined_advanced_metrics['exit_pages'].most_common(5)
				]
			},
			"interaction_heatmap": {
				"click_data": {
					page: dict(clicks.most_common(10))
					for page, clicks in combined_advanced_metrics['click_heatmap'].items()
				},
				"scroll_analysis": {
					page: {
						"avg_scroll_depth": round(sum(depths) / len(depths), 1) if depths else 0,
						"max_scroll_depth": max(depths) if depths else 0
					}
					for page, depths in combined_advanced_metrics['scroll_tracking'].items()
				}
			},
			"performance_timeline": {
				page: {
					"avg_load_time_ms": round(sum(times) / len(times), 1) if times else 0,
					"fastest_load_ms": min(times) if times else 0,
					"slowest_load_ms": max(times) if times else 0
				}
				for page, times in combined_advanced_metrics['load_performance'].items()
			},
			"referrer_analysis": {
				"recent_referrers": all_referrer_details[-50:],  # Last 50 referrers
				"referrer_patterns": Counter([
					r.get('referrer', 'direct') 
					for r in all_referrer_details 
					if r.get('referrer')
				]).most_common(10)
			}
		},
		"technology": {
			"avg_downlink_mbps": round(sum(all_downlink_values) / len(all_downlink_values), 2) if all_downlink_values else 0.0,
			"avg_rtt_ms": round(sum(all_rtt_values) / len(all_rtt_values), 1) if all_rtt_values else 0,
			"common_screen_resolutions": [
				{"resolution": k, "percent": round((v/total_visitors)*100, 1) if total_visitors > 0 else 0}
				for k, v in combined_screen_resolutions.most_common(5)
			]
		},
		"custom_segments": []  # TODO: Implement custom segments based on user behavior
	}
	
	return report
