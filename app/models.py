
# Pydantic schemas for API
from pydantic import BaseModel
from typing import Optional

class RawEvent(BaseModel):
	"""
	Analytics event schema. The payload can contain detailed metrics such as:
	- url, title, referrer, referrer_domain
	- user_agent, platform, device_type, screen, language
	- navigation_start, dom_content_loaded, load_event, first_contentful_paint, largest_contentful_paint, first_input_delay, server_response_time
	- utm_* params
	- geo: {lat, long}
	- and any other custom fields from the analytics client
	"""
	site_id: str
	ts: str  # ISO timestamp
	event_type: str
	payload: dict  # See docstring for expected keys
	visitor_id: str
	session_id: str

# Enhanced event schemas for detailed tracking
class ConversionEvent(BaseModel):
	"""Conversion tracking events like add_to_cart, checkout_started, purchase"""
	site_id: str
	ts: str
	event_type: str  # 'add_to_cart', 'checkout_started', 'purchase', 'product_view'
	visitor_id: str
	session_id: str
	product_id: Optional[str] = None
	product_name: Optional[str] = None
	category: Optional[str] = None
	price: Optional[float] = None
	quantity: Optional[int] = None
	currency: Optional[str] = None
	order_value: Optional[float] = None
	order_id: Optional[str] = None
	funnel_step: Optional[str] = None

class PerformanceEvent(BaseModel):
	"""Detailed performance metrics event"""
	site_id: str
	ts: str
	visitor_id: str
	session_id: str
	url: str
	# Core Web Vitals
	first_contentful_paint: Optional[float] = None
	largest_contentful_paint: Optional[float] = None
	cumulative_layout_shift: Optional[float] = None
	first_input_delay: Optional[float] = None
	# Network metrics
	connection_downlink: Optional[float] = None  # Mbps
	connection_rtt: Optional[float] = None  # ms
	connection_type: Optional[str] = None
	# Page load metrics
	dom_content_loaded: Optional[float] = None
	load_event_end: Optional[float] = None
	server_response_time: Optional[float] = None
	# Resource metrics
	total_resources: Optional[int] = None
	cached_resources: Optional[int] = None

class EngagementEvent(BaseModel):
	"""User engagement tracking"""
	site_id: str
	ts: str
	visitor_id: str
	session_id: str
	url: str
	# Engagement metrics
	scroll_depth_percent: Optional[float] = None
	time_on_page_sec: Optional[float] = None
	clicks_count: Optional[int] = None
	idle_time_sec: Optional[float] = None
	mouse_movements: Optional[int] = None
	keyboard_events: Optional[int] = None
	# Interactions
	form_started: Optional[bool] = None
	form_completed: Optional[bool] = None
	video_played: Optional[bool] = None
	video_watch_time_sec: Optional[float] = None

class SearchEvent(BaseModel):
	"""Site search tracking"""
	site_id: str
	ts: str
	visitor_id: str
	session_id: str
	search_term: str
	results_count: Optional[int] = None
	clicked_result: Optional[bool] = None
	result_position: Optional[int] = None

class CustomEvent(BaseModel):
	"""Custom business events"""
	site_id: str
	ts: str
	visitor_id: str
	session_id: str
	event_name: str  # 'newsletter_signup', 'rating_submitted', etc.
	event_category: Optional[str] = None
	event_value: Optional[float] = None
	custom_properties: Optional[dict] = None

from typing import List, Dict, Any

# Enhanced aggregated report models
class TrafficSource(BaseModel):
	source: str
	visitors: int
	percent: float

class UTMCampaign(BaseModel):
	campaign: str
	clicks: int
	conversions: int

class DeviceStat(BaseModel):
	type: str
	percent: float
	avg_screen_res: str

class OSStat(BaseModel):
	name: str
	percent: float

class BrowserStat(BaseModel):
	name: str
	percent: float

class PageLinkClick(BaseModel):
	href: str
	clicks: int

class PageReferrer(BaseModel):
	referrer: str
	views: int

class PageStat(BaseModel):
	page_title: str
	path: str
	avg_time_spent_sec: float
	avg_load_time_ms: float
	views: int
	unique_visitors: int
	bounce_rate_percent: float
	exit_rate_percent: float
	avg_scroll_depth_percent: float
	avg_clicks_per_visit: float
	links_clicked_most: List[PageLinkClick]
	top_referrers: List[PageReferrer]

class GeoStat(BaseModel):
	country: str
	percent: float

class VisitorGeo(BaseModel):
	lat: float
	long: float

class EngagementSummary(BaseModel):
	avg_scroll_depth_percent: float
	avg_clicks_per_session: float
	avg_idle_time_sec: float
	avg_form_interactions: float
	avg_video_watch_time_sec: float

class PerformanceMetrics(BaseModel):
	first_contentful_paint_avg_ms: float
	largest_contentful_paint_avg_ms: float
	cumulative_layout_shift_avg: float
	first_input_delay_avg_ms: float
	server_response_time_avg_ms: float
	cdn_cache_hit_ratio_percent: float

class ConversionFunnel(BaseModel):
	landing_page_visits: int
	product_page_views: int
	add_to_cart: int
	checkout_started: int
	purchases: int
	cart_abandonment_rate_percent: float

class SearchTerm(BaseModel):
	term: str
	count: int

class EventSummary(BaseModel):
	event: str
	count: int

class ScreenResolutionStat(BaseModel):
	resolution: str
	percent: float

class TechnologyStat(BaseModel):
	avg_downlink_mbps: float
	avg_rtt_ms: float
	common_screen_resolutions: List[ScreenResolutionStat]

class UserBehavior(BaseModel):
	avg_sessions_per_user: float
	avg_pages_per_session: float
	avg_session_duration_sec: float
	peak_visit_hour: str
	days_with_highest_traffic: List[str]

class CustomSegment(BaseModel):
	segment_name: str
	criteria: str
	visitors: int
	avg_order_value: Optional[float] = None
	recovered_percent: Optional[float] = None

class NewVsReturning(BaseModel):
	new_percent: float
	returning_percent: float

# Additional models for enhanced tracking
class SessionData(BaseModel):
	"""Session-level aggregated data"""
	session_id: str
	visitor_id: str
	site_id: str
	start_time: str
	end_time: Optional[str] = None
	page_count: int
	total_time_sec: float
	total_clicks: int
	total_scroll_depth: float
	is_bounce: bool
	conversion_events: List[str]
	entry_page: str
	exit_page: Optional[str] = None
	traffic_source: str
	utm_campaign: Optional[str] = None

class VisitorProfile(BaseModel):
	"""Visitor-level profile data"""
	visitor_id: str
	site_id: str
	first_seen: str
	last_seen: str
	total_sessions: int
	total_pageviews: int
	total_time_sec: float
	total_conversions: int
	total_order_value: float
	is_returning: bool
	device_type: str
	browser: str
	os: str
	country: Optional[str] = None
	acquisition_source: str

class AggregatedReport(BaseModel):
	website_name: str
	url: str
	report_generated_at: str
	date_range: str
	total_visitors: int
	unique_visitors: int
	total_pageviews: int
	total_pages: int
	avg_time_spent_on_site_sec: float
	avg_loading_time_ms: float
	bounce_rate_percent: float
	conversion_rate_percent: float
	new_vs_returning: NewVsReturning
	traffic_sources: List[TrafficSource]
	utm_campaigns: List[UTMCampaign]
	devices: List[DeviceStat]
	operating_systems: List[OSStat]
	browsers: List[BrowserStat]
	pages: List[PageStat]
	geo_distribution: List[GeoStat]
	last_24h_visitors_geo: List[VisitorGeo]
	engagement_summary: EngagementSummary
	performance_metrics: PerformanceMetrics
	conversion_funnel: ConversionFunnel
	search_terms: List[SearchTerm]
	events_summary: List[EventSummary]
	technology: TechnologyStat
	user_behavior: UserBehavior
	custom_segments: List[CustomSegment]


class User(BaseModel):
	id: str
	email: str
	created_at: Optional[str] = None

class AuthRequest(BaseModel):
	email: str
	password: str

class AuthResponse(BaseModel):
	access_token: str
	token_type: str = "bearer"

class Site(BaseModel):
	site_id: Optional[str] = None
	owner_user_id: Optional[str] = None
	name: str
	url: str
	site_key: Optional[str] = None
	last_updated: Optional[str] = None
	verified: Optional[bool] = False
