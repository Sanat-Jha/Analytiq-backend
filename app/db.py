import duckdb
import os
from dotenv import load_dotenv

load_dotenv()
DB_PATH = os.getenv("DUCKDB_PATH", "analytiq.db")
con = duckdb.connect(DB_PATH)

def init_db():
	con.execute("""
	CREATE TABLE IF NOT EXISTS users (
		id VARCHAR PRIMARY KEY,
		email VARCHAR UNIQUE NOT NULL,
		hashed_password VARCHAR NOT NULL,
		created_at TIMESTAMP DEFAULT current_timestamp
	);
	CREATE TABLE IF NOT EXISTS sites (
		site_id VARCHAR PRIMARY KEY,
		owner_user_id VARCHAR NOT NULL,
		name VARCHAR NOT NULL,
		url VARCHAR NOT NULL,
		site_key VARCHAR NOT NULL,
		last_updated TIMESTAMP DEFAULT current_timestamp,
		verified BOOLEAN DEFAULT FALSE
	);
	CREATE TABLE IF NOT EXISTS raw_events (
		event_id VARCHAR PRIMARY KEY,
		site_id VARCHAR NOT NULL,
		ts TIMESTAMP NOT NULL,
		event_type VARCHAR NOT NULL,
		payload JSON,
		visitor_id VARCHAR,
		session_id VARCHAR
	);
	CREATE TABLE IF NOT EXISTS conversion_events (
		event_id VARCHAR PRIMARY KEY,
		site_id VARCHAR NOT NULL,
		ts TIMESTAMP NOT NULL,
		event_type VARCHAR NOT NULL,
		visitor_id VARCHAR,
		session_id VARCHAR,
		product_id VARCHAR,
		product_name VARCHAR,
		category VARCHAR,
		price DECIMAL(10,2),
		quantity INTEGER,
		currency VARCHAR,
		order_value DECIMAL(10,2),
		order_id VARCHAR,
		funnel_step VARCHAR
	);
	CREATE TABLE IF NOT EXISTS performance_events (
		event_id VARCHAR PRIMARY KEY,
		site_id VARCHAR NOT NULL,
		ts TIMESTAMP NOT NULL,
		visitor_id VARCHAR,
		session_id VARCHAR,
		url VARCHAR,
		first_contentful_paint REAL,
		largest_contentful_paint REAL,
		cumulative_layout_shift REAL,
		first_input_delay REAL,
		connection_downlink REAL,
		connection_rtt REAL,
		connection_type VARCHAR,
		dom_content_loaded REAL,
		load_event_end REAL,
		server_response_time REAL,
		total_resources INTEGER,
		cached_resources INTEGER
	);
	CREATE TABLE IF NOT EXISTS engagement_events (
		event_id VARCHAR PRIMARY KEY,
		site_id VARCHAR NOT NULL,
		ts TIMESTAMP NOT NULL,
		visitor_id VARCHAR,
		session_id VARCHAR,
		url VARCHAR,
		scroll_depth_percent REAL,
		time_on_page_sec REAL,
		clicks_count INTEGER,
		idle_time_sec REAL,
		mouse_movements INTEGER,
		keyboard_events INTEGER,
		form_started BOOLEAN,
		form_completed BOOLEAN,
		video_played BOOLEAN,
		video_watch_time_sec REAL
	);
	CREATE TABLE IF NOT EXISTS search_events (
		event_id VARCHAR PRIMARY KEY,
		site_id VARCHAR NOT NULL,
		ts TIMESTAMP NOT NULL,
		visitor_id VARCHAR,
		session_id VARCHAR,
		search_term VARCHAR,
		results_count INTEGER,
		clicked_result BOOLEAN,
		result_position INTEGER
	);
	CREATE TABLE IF NOT EXISTS custom_events (
		event_id VARCHAR PRIMARY KEY,
		site_id VARCHAR NOT NULL,
		ts TIMESTAMP NOT NULL,
		visitor_id VARCHAR,
		session_id VARCHAR,
		event_name VARCHAR,
		event_category VARCHAR,
		event_value REAL,
		custom_properties JSON
	);
	CREATE TABLE IF NOT EXISTS visitor_profiles (
		visitor_id VARCHAR PRIMARY KEY,
		site_id VARCHAR NOT NULL,
		first_seen TIMESTAMP,
		last_seen TIMESTAMP,
		total_sessions INTEGER DEFAULT 0,
		total_pageviews INTEGER DEFAULT 0,
		total_time_sec REAL DEFAULT 0,
		total_conversions INTEGER DEFAULT 0,
		total_order_value DECIMAL(10,2) DEFAULT 0,
		is_returning BOOLEAN DEFAULT FALSE,
		device_type VARCHAR,
		browser VARCHAR,
		os VARCHAR,
		country VARCHAR,
		acquisition_source VARCHAR
	);
	CREATE TABLE IF NOT EXISTS session_data (
		session_id VARCHAR PRIMARY KEY,
		visitor_id VARCHAR NOT NULL,
		site_id VARCHAR NOT NULL,
		start_time TIMESTAMP,
		end_time TIMESTAMP,
		page_count INTEGER DEFAULT 0,
		total_time_sec REAL DEFAULT 0,
		total_clicks INTEGER DEFAULT 0,
		total_scroll_depth REAL DEFAULT 0,
		is_bounce BOOLEAN DEFAULT FALSE,
		conversion_events JSON,
		entry_page VARCHAR,
		exit_page VARCHAR,
		traffic_source VARCHAR,
		utm_campaign VARCHAR
	);
	""")

def migrate_db():
	"""Run database migrations for schema changes"""
	try:
		# Check if last_updated column exists
		result = con.execute("SELECT last_updated FROM sites LIMIT 1").fetchone()
	except:
		# Column doesn't exist, add it
		print("Migrating database: Adding last_updated column to sites table...")
		con.execute("ALTER TABLE sites ADD COLUMN last_updated TIMESTAMP DEFAULT current_timestamp")
		# Update existing records with current timestamp
		con.execute("UPDATE sites SET last_updated = current_timestamp WHERE last_updated IS NULL")
		print("Migration completed successfully.")
	
	# Remove old columns if they exist
	try:
		con.execute("ALTER TABLE sites DROP COLUMN created_at")
		print("Removed old created_at column")
	except:
		pass  # Column doesn't exist or already removed
	
	try:
		con.execute("ALTER TABLE sites DROP COLUMN timezone")
		print("Removed old timezone column")
	except:
		pass  # Column doesn't exist or already removed
	
	# Add verified column if it doesn't exist
	try:
		con.execute("SELECT verified FROM sites LIMIT 1")
	except:
		print("Migrating database: Adding verified column to sites table...")
		con.execute("ALTER TABLE sites ADD COLUMN verified BOOLEAN DEFAULT FALSE")
		con.execute("UPDATE sites SET verified = FALSE WHERE verified IS NULL")
		print("Added verified column successfully.")

def update_site_timestamp(site_id: str):
	"""Update the last_updated timestamp for a site when new data is ingested"""
	con.execute("UPDATE sites SET last_updated = current_timestamp WHERE site_id = ?", [site_id])

def create_user(user_id, email, hashed_password):
	con.execute(
		"INSERT INTO users (id, email, hashed_password) VALUES (?, ?, ?)",
		[user_id, email, hashed_password]
	)

def get_user_by_email(email):
	res = con.execute("SELECT * FROM users WHERE email = ?", [email]).fetchone()
	if res:
		return {
			"id": res[0],
			"email": res[1],
			"hashed_password": res[2],
			"created_at": res[3],
		}
	return None


import json
def append_raw_event(site_id, ts, event_type, payload, visitor_id, session_id):
	import uuid
	event_id = str(uuid.uuid4())
	con.execute(
		"""
		INSERT INTO raw_events (event_id, site_id, ts, event_type, payload, visitor_id, session_id)
		VALUES (?, ?, ?, ?, ?, ?, ?)
		""",
		[event_id, site_id, ts, event_type, json.dumps(payload), visitor_id, session_id]
	)
	return event_id

def append_conversion_event(event):
	import uuid
	event_id = str(uuid.uuid4())
	con.execute(
		"""
		INSERT INTO conversion_events 
		(event_id, site_id, ts, event_type, visitor_id, session_id, product_id, product_name, 
		 category, price, quantity, currency, order_value, order_id, funnel_step)
		VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
		""",
		[event_id, event.site_id, event.ts, event.event_type, event.visitor_id, event.session_id,
		 event.product_id, event.product_name, event.category, event.price, event.quantity,
		 event.currency, event.order_value, event.order_id, event.funnel_step]
	)
	return event_id

def append_performance_event(event):
	import uuid
	event_id = str(uuid.uuid4())
	con.execute(
		"""
		INSERT INTO performance_events 
		(event_id, site_id, ts, visitor_id, session_id, url, first_contentful_paint, 
		 largest_contentful_paint, cumulative_layout_shift, first_input_delay, 
		 connection_downlink, connection_rtt, connection_type, dom_content_loaded, 
		 load_event_end, server_response_time, total_resources, cached_resources)
		VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
		""",
		[event_id, event.site_id, event.ts, event.visitor_id, event.session_id, event.url,
		 event.first_contentful_paint, event.largest_contentful_paint, event.cumulative_layout_shift,
		 event.first_input_delay, event.connection_downlink, event.connection_rtt, event.connection_type,
		 event.dom_content_loaded, event.load_event_end, event.server_response_time,
		 event.total_resources, event.cached_resources]
	)
	return event_id

def append_engagement_event(event):
	import uuid
	event_id = str(uuid.uuid4())
	con.execute(
		"""
		INSERT INTO engagement_events 
		(event_id, site_id, ts, visitor_id, session_id, url, scroll_depth_percent, 
		 time_on_page_sec, clicks_count, idle_time_sec, mouse_movements, keyboard_events,
		 form_started, form_completed, video_played, video_watch_time_sec)
		VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
		""",
		[event_id, event.site_id, event.ts, event.visitor_id, event.session_id, event.url,
		 event.scroll_depth_percent, event.time_on_page_sec, event.clicks_count, event.idle_time_sec,
		 event.mouse_movements, event.keyboard_events, event.form_started, event.form_completed,
		 event.video_played, event.video_watch_time_sec]
	)
	return event_id

def append_search_event(event):
	import uuid
	event_id = str(uuid.uuid4())
	con.execute(
		"""
		INSERT INTO search_events 
		(event_id, site_id, ts, visitor_id, session_id, search_term, results_count, clicked_result, result_position)
		VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
		""",
		[event_id, event.site_id, event.ts, event.visitor_id, event.session_id,
		 event.search_term, event.results_count, event.clicked_result, event.result_position]
	)
	return event_id

def append_custom_event(event):
	import uuid
	event_id = str(uuid.uuid4())
	con.execute(
		"""
		INSERT INTO custom_events 
		(event_id, site_id, ts, visitor_id, session_id, event_name, event_category, event_value, custom_properties)
		VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
		""",
		[event_id, event.site_id, event.ts, event.visitor_id, event.session_id,
		 event.event_name, event.event_category, event.event_value, 
		 json.dumps(event.custom_properties) if event.custom_properties else None]
	)
	return event_id

def append_bulk_events(events):
	for e in events:
		append_raw_event(
			e.site_id, e.ts, e.event_type, e.payload, e.visitor_id, e.session_id
		)


import uuid
import secrets
from app.models import Site

def create_site(owner_user_id, site: Site):
	# Check if the user already has a site with the same URL
	existing = con.execute(
		"SELECT 1 FROM sites WHERE owner_user_id = ? AND url = ?",
		[owner_user_id, site.url]
	).fetchone()
	if existing:
		raise ValueError("Site with this URL already exists for this user.")

	site_id = str(uuid.uuid4())
	site_key = secrets.token_urlsafe(16)
	con.execute(
		"""
		INSERT INTO sites (site_id, owner_user_id, name, url, site_key)
		VALUES (?, ?, ?, ?, ?)
		""",
		[site_id, owner_user_id, site.name, site.url, site_key]
	)
	# Fetch the full site record including last_updated
	r = con.execute("SELECT site_id, owner_user_id, name, url, site_key, strftime('%Y-%m-%d %H:%M:%S', last_updated) as last_updated, verified FROM sites WHERE site_id = ?", [site_id]).fetchone()
	if r:
		return Site(site_id=r[0], owner_user_id=r[1], name=r[2], url=r[3], site_key=r[4], last_updated=r[5], verified=r[6])
	else:
		# Fallback: return without last_updated if something went wrong
		return Site(site_id=site_id, owner_user_id=owner_user_id, name=site.name, url=site.url, site_key=site_key)

def get_sites_by_user(owner_user_id):
	rows = con.execute("SELECT site_id, owner_user_id, name, url, site_key, strftime('%Y-%m-%d %H:%M:%S', last_updated) as last_updated, verified FROM sites WHERE owner_user_id = ?", [owner_user_id]).fetchall()
	return [Site(site_id=r[0], owner_user_id=r[1], name=r[2], url=r[3], site_key=r[4], last_updated=r[5], verified=r[6]) for r in rows]

def get_site_by_id(site_id):
	r = con.execute("SELECT site_id, owner_user_id, name, url, site_key, strftime('%Y-%m-%d %H:%M:%S', last_updated) as last_updated, verified FROM sites WHERE site_id = ?", [site_id]).fetchone()
	if r:
		return Site(site_id=r[0], owner_user_id=r[1], name=r[2], url=r[3], site_key=r[4], last_updated=r[5], verified=r[6])
	return None
