

from fastapi import APIRouter, Depends, HTTPException, status
from app.models import Site
from app.auth_utils import verify_token
from app.db import create_site, get_sites_by_user, get_site_by_id
from fastapi.security import OAuth2PasswordBearer
from typing import Optional
import os
import re
import requests
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

def get_current_user(token: str = Depends(oauth2_scheme)):
	payload = verify_token(token)
	if not payload or "sub" not in payload:
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED, 
			detail="Invalid or expired token",
			headers={"WWW-Authenticate": "Bearer"}
		)
	return payload

@router.get("/sites", response_model=list[Site])
async def list_sites(current_user: dict = Depends(get_current_user)):
	user_id = current_user["sub"]
	sites = get_sites_by_user(user_id)
	return sites

from fastapi.responses import JSONResponse

@router.post("/sites")
async def add_site(site: Site, current_user: dict = Depends(get_current_user)):
	user_id = current_user["sub"]
	try:
		new_site = create_site(user_id, site)
		# Generate script snippet for embedding
		base_url = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
		script_snippet = f'''<script async src="{base_url}/stats-config.js?siteId={new_site.site_id}&siteKey={new_site.site_key}"></script>'''
		response = new_site.dict()
		response["snippet"] = script_snippet
		return JSONResponse(content=response)
	except ValueError as e:
		from fastapi import HTTPException
		raise HTTPException(status_code=400, detail=str(e))

@router.delete("/sites/{site_id}")
async def delete_site(site_id: str, current_user: dict = Depends(get_current_user)):
	"""Delete a site for the current user"""
	from app.db import con
	
	# Check site ownership
	site = get_site_by_id(site_id)
	if not site or site.owner_user_id != current_user["sub"]:
		raise HTTPException(status_code=404, detail="Site not found")
	
	try:
		# Delete site and all related data in a transaction-like manner
		# Order is important: delete child records first, then parent records
		con.execute("DELETE FROM dash_summary WHERE site_id = ?", [site_id])
		con.execute("DELETE FROM aggregated_metrics_daily WHERE site_id = ?", [site_id])
		con.execute("DELETE FROM session_data WHERE site_id = ?", [site_id])
		con.execute("DELETE FROM visitor_profiles WHERE site_id = ?", [site_id])
		con.execute("DELETE FROM custom_events WHERE site_id = ?", [site_id])
		con.execute("DELETE FROM search_events WHERE site_id = ?", [site_id])
		con.execute("DELETE FROM engagement_events WHERE site_id = ?", [site_id])
		con.execute("DELETE FROM performance_events WHERE site_id = ?", [site_id])
		con.execute("DELETE FROM conversion_events WHERE site_id = ?", [site_id])
		con.execute("DELETE FROM raw_events WHERE site_id = ?", [site_id])
		con.execute("DELETE FROM sites WHERE site_id = ?", [site_id])
		
		return {"status": "deleted", "message": f"Site {site_id} and all related data have been permanently deleted"}
	
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Failed to delete site: {str(e)}")


@router.post("/sites/{site_id}/verify")
async def verify_site(site_id: str, current_user: dict = Depends(get_current_user)):
	"""Verify that the tracking code is properly installed on the website"""
	from app.db import con
	
	# Check site ownership
	site = get_site_by_id(site_id)
	if not site or site.owner_user_id != current_user["sub"]:
		raise HTTPException(status_code=404, detail="Site not found")
	
	# Already verified
	if site.verified:
		return {
			"verified": True,
			"message": "Site is already verified",
			"site_id": site_id
		}
	
	try:
		# Fetch the website HTML
		url = site.url
		if not url.startswith(('http://', 'https://')):
			url = 'https://' + url
		
		response = requests.get(url, timeout=10, headers={
			'User-Agent': 'Analytiq-Verification-Bot/1.0'
		})
		response.raise_for_status()
		
		html_content = response.text
		
		# Check for tracking code patterns
		# Pattern 1: Direct script tag with stats-config.js
		backend_url = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
		pattern1 = rf'<script[^>]*src=["\']({re.escape(backend_url)})?/stats-config\.js\?siteId={re.escape(site.site_id)}&siteKey={re.escape(site.site_key)}["\'][^>]*>'
		
		# Pattern 2: Check for siteId and siteKey in window object or variables
		pattern2_id = rf'(window\.)?analytiqSiteId\s*=\s*["\']\s*{re.escape(site.site_id)}\s*["\']'
		pattern3_key = rf'(window\.)?analytiqSiteKey\s*=\s*["\']\s*{re.escape(site.site_key)}\s*["\']'
		
		# Pattern 3: Check for client-side-sdk.js (alternative loader)
		pattern4 = rf'<script[^>]*src=["\']({re.escape(backend_url)})?/client-side-sdk\.js["\'][^>]*>'
		
		# Check if any pattern matches
		has_script_tag = bool(re.search(pattern1, html_content, re.IGNORECASE))
		has_site_id = bool(re.search(pattern2_id, html_content, re.IGNORECASE))
		has_site_key = bool(re.search(pattern3_key, html_content, re.IGNORECASE))
		has_sdk_loader = bool(re.search(pattern4, html_content, re.IGNORECASE))
		
		# Verification succeeds if:
		# 1. Has the complete script tag with siteId and siteKey, OR
		# 2. Has both siteId and siteKey variables AND has the SDK loader
		is_verified = has_script_tag or (has_site_id and has_site_key and has_sdk_loader)
		
		if is_verified:
			# Update the database to mark site as verified
			con.execute("UPDATE sites SET verified = TRUE WHERE site_id = ?", [site_id])
			
			return {
				"verified": True,
				"message": "Tracking code successfully verified on your website",
				"site_id": site_id,
				"details": {
					"has_script_tag": has_script_tag,
					"has_site_id": has_site_id,
					"has_site_key": has_site_key,
					"has_sdk_loader": has_sdk_loader
				}
			}
		else:
			return {
				"verified": False,
				"message": "Tracking code not found on your website. Please ensure the snippet is correctly installed.",
				"site_id": site_id,
				"details": {
					"has_script_tag": has_script_tag,
					"has_site_id": has_site_id,
					"has_site_key": has_site_key,
					"has_sdk_loader": has_sdk_loader,
					"expected_site_id": site.site_id,
					"checked_url": url
				}
			}
		
	except requests.exceptions.Timeout:
		raise HTTPException(status_code=408, detail="Website request timed out. Please try again.")
	except requests.exceptions.ConnectionError:
		raise HTTPException(status_code=503, detail="Could not connect to the website. Please verify the URL is correct and accessible.")
	except requests.exceptions.HTTPError as e:
		raise HTTPException(status_code=502, detail=f"Website returned an error: {e.response.status_code}")
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")


@router.get("/sites/{site_id}/dashboard")
async def get_dashboard(site_id: str, current_user: dict = Depends(get_current_user)):
	"""Get comprehensive dashboard data for a site (last 7 days by default)"""
	from app.aggregator import generate_comprehensive_report
	from datetime import datetime, timedelta
	
	# Check site ownership
	site = get_site_by_id(site_id)
	if not site or site.owner_user_id != current_user["sub"]:
		raise HTTPException(status_code=404, detail="Site not found")
	
	# Get last 7 days of data for dashboard
	end_date = datetime.utcnow().date()
	start_date = end_date - timedelta(days=7)
	
	# Try to get comprehensive report
	report = generate_comprehensive_report(site_id, start_date, end_date)
	
	if report:
		return report
	else:
		# Fallback to basic data if no aggregated data exists
		from app.db import con
		summary = con.execute("SELECT * FROM dash_summary WHERE site_id = ?", [site_id]).fetchone()
		
		if summary:
			import json
			snapshot_data = json.loads(summary[4]) if summary[4] else {}
			return {
				"website_name": site.name,
				"url": site.url,
				"site_id": site_id,
				"last_updated": summary[1],
				"total_visitors": summary[2],
				"total_pageviews": summary[3],
				"snapshot": snapshot_data,
				"report_generated_at": datetime.utcnow().isoformat() + "Z",
				"date_range": f"{start_date} to {end_date}",
				"message": "Limited data available - comprehensive analytics will be available after data collection"
			}
		else:
			return {
				"website_name": site.name,
				"url": site.url,
				"site_id": site_id,
				"total_visitors": 0,
				"total_pageviews": 0,
				"report_generated_at": datetime.utcnow().isoformat() + "Z",
				"date_range": f"{start_date} to {end_date}",
				"message": "No data available yet - start collecting analytics data"
			}

@router.get("/sites/{site_id}/report")
async def get_comprehensive_report(
	site_id: str, 
	start_date: Optional[str] = None, 
	end_date: Optional[str] = None,
	current_user: dict = Depends(get_current_user)
):
	"""Get comprehensive analytics report for a site"""
	from app.aggregator import generate_comprehensive_report
	from datetime import datetime, timedelta
	
	# Check site ownership
	site = get_site_by_id(site_id)
	if not site or site.owner_user_id != current_user["sub"]:
		raise HTTPException(status_code=404, detail="Site not found")
	
	# Default to last 30 days if no date range provided
	if not start_date or not end_date:
		end_dt = datetime.utcnow().date()
		start_dt = end_dt - timedelta(days=30)
	else:
		try:
			start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
			end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
		except ValueError:
			raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
	
	report = generate_comprehensive_report(site_id, start_dt, end_dt)
	if not report:
		raise HTTPException(status_code=404, detail="No data available for the specified date range")
	print(report)
	return report
