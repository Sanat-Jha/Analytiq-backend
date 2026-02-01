
# Background tasks for analytics processing
from app.aggregator import aggregate_daily, update_dash_summary
from app.db import con
from datetime import datetime, timedelta

def run_aggregation(site_id: str):
	"""Run aggregation job for a specific site"""
	try:
		aggregate_daily(site_id)
		update_dash_summary(site_id)
		print(f"Aggregation completed for site: {site_id}")
	except Exception as e:
		print(f"Error running aggregation for site {site_id}: {e}")

def cleanup_old_events(days_to_keep: int = 90):
	"""Cleanup old raw events to maintain database performance"""
	try:
		cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
		
		# Clean up raw events older than cutoff date
		con.execute("DELETE FROM raw_events WHERE ts < ?", [cutoff_date])
		con.execute("DELETE FROM conversion_events WHERE ts < ?", [cutoff_date])
		con.execute("DELETE FROM performance_events WHERE ts < ?", [cutoff_date])
		con.execute("DELETE FROM engagement_events WHERE ts < ?", [cutoff_date])
		con.execute("DELETE FROM search_events WHERE ts < ?", [cutoff_date])
		con.execute("DELETE FROM custom_events WHERE ts < ?", [cutoff_date])
		
		print(f"Cleaned up events older than {cutoff_date}")
	except Exception as e:
		print(f"Error during cleanup: {e}")

def run_daily_aggregations():
	"""Run aggregation for all sites - can be called from a scheduler"""
	try:
		# Get all site IDs
		sites = con.execute("SELECT DISTINCT site_id FROM sites").fetchall()
		
		for site_row in sites:
			site_id = site_row[0]
			run_aggregation(site_id)
			
		print(f"Daily aggregations completed for {len(sites)} sites")
	except Exception as e:
		print(f"Error running daily aggregations: {e}")
