

from fastapi import APIRouter, Header, HTTPException, status
from app.models import RawEvent, ConversionEvent, PerformanceEvent, EngagementEvent, SearchEvent, CustomEvent
from app.db import append_raw_event, append_bulk_events, append_conversion_event, append_performance_event, append_engagement_event, append_search_event, append_custom_event, con, update_site_timestamp
from app.aggregator import aggregate_daily, update_dash_summary

router = APIRouter()

def validate_site(site_id: str, site_key: str):
	row = con.execute("SELECT 1 FROM sites WHERE site_id = ? AND site_key = ?", [site_id, site_key]).fetchone()
	if not row:
		raise HTTPException(status_code=401, detail="Invalid site_id or site_key")


# Unified ingest endpoint
from fastapi import Request

@router.post("/")
async def ingest_event(request: Request, x_site_id: str = Header(...), x_site_key: str = Header(...)):
	"""
	Accept any event type (raw, conversion, performance, engagement, search, custom, or batch).
	The payload must include a 'type' field (e.g. 'raw', 'conversion', etc.) or a 'batch' field for batch ingest.
	"""
	validate_site(x_site_id, x_site_key)
	data = await request.json()

	# Batch ingest
	if "batch" in data:
		batch = data["batch"]
		processed_count = 0
		# Accepts dict of event arrays: {raw_events: [...], conversion_events: [...], ...}
		for key, events in batch.items():
			if key == "raw_events":
				for event_data in events:
					event = RawEvent(**event_data)
					append_raw_event(event.site_id, event.ts, event.event_type, event.payload, event.visitor_id, event.session_id)
					processed_count += 1
			elif key == "conversion_events":
				for event_data in events:
					event = ConversionEvent(**event_data)
					append_conversion_event(event)
					processed_count += 1
			elif key == "performance_events":
				for event_data in events:
					event = PerformanceEvent(**event_data)
					append_performance_event(event)
					processed_count += 1
			elif key == "engagement_events":
				for event_data in events:
					event = EngagementEvent(**event_data)
					append_engagement_event(event)
					processed_count += 1
			elif key == "search_events":
				for event_data in events:
					event = SearchEvent(**event_data)
					append_search_event(event)
					processed_count += 1
			elif key == "custom_events":
				for event_data in events:
					event = CustomEvent(**event_data)
					append_custom_event(event)
					processed_count += 1
		if processed_count > 0:
			update_site_timestamp(x_site_id)
			aggregate_daily(x_site_id)
			update_dash_summary(x_site_id)
		return {"status": "ok", "processed_count": processed_count}

	# Single event ingest (efficient mapping)
	event_type = data.get("type")
	event_map = {
		"raw": (RawEvent, lambda e: append_raw_event(e.site_id, e.ts, e.event_type, e.payload, e.visitor_id, e.session_id)),
		"conversion": (ConversionEvent, append_conversion_event),
		"performance": (PerformanceEvent, append_performance_event),
		"engagement": (EngagementEvent, append_engagement_event),
		"search": (SearchEvent, append_search_event),
		"custom": (CustomEvent, append_custom_event)
	}
	if event_type in event_map:
		model_cls, append_func = event_map[event_type]
		event = model_cls(**data)
		append_func(event)
		update_site_timestamp(event.site_id)
		aggregate_daily(event.site_id)
		update_dash_summary(event.site_id)
		return {"status": "ok"}
	raise HTTPException(status_code=400, detail="Unknown or missing event type")
