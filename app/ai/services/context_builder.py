"""
context_builder.py - Builds comprehensive analytics context for AI from database
"""
from app.db import con

def build_site_context(website_id: str, days: int = 7) -> str:
    """
    Fetches comprehensive analytics data for a site and returns human-readable context.
    This gives AI access to all user data: visitors, sessions, performance, engagement, devices, etc.
    """
    context_parts = []
    
    # 1. Basic site stats
    try:
        stats = con.execute(f"""
            SELECT 
                count(*) as total_events,
                count(distinct session_id) as total_sessions,
                count(distinct visitor_id) as total_visitors
            FROM raw_events 
            WHERE site_id = ? 
            AND ts > current_timestamp - INTERVAL '{days}' DAY
        """, [website_id]).fetchone()
        
        context_parts.append(f"OVERVIEW (Last {days} days):")
        context_parts.append(f"- Total Events: {stats[0]}")
        context_parts.append(f"- Total Sessions: {stats[1]}")
        context_parts.append(f"- Total Visitors: {stats[2]}")
    except Exception as e:
        context_parts.append(f"Basic stats unavailable: {e}")
    
    # 2. Device/Screen Types
    try:
        device_rows = con.execute("""
            SELECT device_type, count(*) as cnt 
            FROM visitor_profiles 
            WHERE site_id = ? AND device_type IS NOT NULL 
            GROUP BY device_type 
            ORDER BY cnt DESC
        """, [website_id]).fetchall()
        
        if device_rows:
            context_parts.append(f"\nDEVICE/SCREEN TYPES:")
            for row in device_rows:
                context_parts.append(f"- {row[0]}: {row[1]} visitors")
    except Exception:
        pass
    
    # Screen resolution breakdown from raw events
    try:
        screen_rows = con.execute("""
            SELECT 
                json_extract_string(payload, '$.screen') as screen_res,
                count(distinct visitor_id) as visitors
            FROM raw_events 
            WHERE site_id = ? 
            AND json_extract_string(payload, '$.screen') IS NOT NULL
            AND ts > current_timestamp - INTERVAL '7' DAY
            GROUP BY screen_res
            ORDER BY visitors DESC
            LIMIT 10
        """, [website_id]).fetchall()
        
        if screen_rows:
            context_parts.append(f"\nSCREEN RESOLUTIONS:")
            for row in screen_rows:
                context_parts.append(f"- {row[0]}: {row[1]} visitors")
    except Exception:
        pass
    
    # Platform breakdown (desktop/mobile/tablet detailed)
    try:
        platform_rows = con.execute("""
            SELECT 
                json_extract_string(payload, '$.platform') as platform,
                count(distinct visitor_id) as visitors
            FROM raw_events 
            WHERE site_id = ? 
            AND json_extract_string(payload, '$.platform') IS NOT NULL
            AND ts > current_timestamp - INTERVAL '7' DAY
            GROUP BY platform
            ORDER BY visitors DESC
        """, [website_id]).fetchall()
        
        if platform_rows:
            context_parts.append(f"\nPLATFORM DISTRIBUTION:")
            for row in platform_rows:
                context_parts.append(f"- {row[0]}: {row[1]} visitors")
    except Exception:
        pass
    
    # 3. Browsers
    try:
        browser_rows = con.execute("""
            SELECT browser, count(*) as cnt 
            FROM visitor_profiles 
            WHERE site_id = ? AND browser IS NOT NULL 
            GROUP BY browser 
            ORDER BY cnt DESC 
            LIMIT 10
        """, [website_id]).fetchall()
        
        if browser_rows:
            context_parts.append(f"\nBROWSERS:")
            for row in browser_rows:
                context_parts.append(f"- {row[0]}: {row[1]} visitors")
    except Exception:
        pass
    
    # 4. Operating Systems
    try:
        os_rows = con.execute("""
            SELECT os, count(*) as cnt 
            FROM visitor_profiles 
            WHERE site_id = ? AND os IS NOT NULL 
            GROUP BY os 
            ORDER BY cnt DESC 
            LIMIT 10
        """, [website_id]).fetchall()
        
        if os_rows:
            context_parts.append(f"\nOPERATING SYSTEMS:")
            for row in os_rows:
                context_parts.append(f"- {row[0]}: {row[1]} visitors")
    except Exception:
        pass
    
    # 5. Traffic Sources / Acquisition
    try:
        source_rows = con.execute("""
            SELECT acquisition_source, count(*) as cnt 
            FROM visitor_profiles 
            WHERE site_id = ? AND acquisition_source IS NOT NULL 
            GROUP BY acquisition_source 
            ORDER BY cnt DESC 
            LIMIT 10
        """, [website_id]).fetchall()
        
        if source_rows:
            context_parts.append(f"\nTRAFFIC SOURCES:")
            for row in source_rows:
                context_parts.append(f"- {row[0]}: {row[1]} visitors")
    except Exception:
        pass
    
    # 6. Top Pages
    try:
        page_rows = con.execute("""
            SELECT url, count(*) as cnt 
            FROM (
                SELECT url FROM performance_events WHERE site_id = ?
                UNION ALL
                SELECT url FROM engagement_events WHERE site_id = ?
            )
            WHERE url IS NOT NULL
            GROUP BY url
            ORDER BY cnt DESC
            LIMIT 10
        """, [website_id, website_id]).fetchall()
        
        if page_rows:
            context_parts.append(f"\nTOP PAGES:")
            for row in page_rows:
                context_parts.append(f"- {row[0]}: {row[1]} events")
    except Exception:
        pass
    
    # 7. UTM Campaigns and detailed UTM parameters
    try:
        utm_rows = con.execute("""
            SELECT utm_campaign, count(*) as cnt 
            FROM session_data 
            WHERE site_id = ? AND utm_campaign IS NOT NULL 
            GROUP BY utm_campaign 
            ORDER BY cnt DESC 
            LIMIT 10
        """, [website_id]).fetchall()
        
        if utm_rows:
            context_parts.append(f"\nCAMPAIGNS (UTM):")
            for row in utm_rows:
                context_parts.append(f"- {row[0]}: {row[1]} sessions")
    except Exception:
        pass
    
    # UTM Source breakdown
    try:
        utm_source_rows = con.execute("""
            SELECT 
                json_extract_string(payload, '$.utm_source') as utm_source,
                json_extract_string(payload, '$.utm_medium') as utm_medium,
                count(distinct session_id) as sessions
            FROM raw_events 
            WHERE site_id = ? 
            AND json_extract_string(payload, '$.utm_source') IS NOT NULL
            AND ts > current_timestamp - INTERVAL '7' DAY
            GROUP BY utm_source, utm_medium
            ORDER BY sessions DESC
            LIMIT 10
        """, [website_id]).fetchall()
        
        if utm_source_rows:
            context_parts.append(f"\nTRAFFIC SOURCE BREAKDOWN (UTM):")
            for row in utm_source_rows:
                source = row[0] or "unknown"
                medium = row[1] or "unknown"
                context_parts.append(f"- {source} / {medium}: {row[2]} sessions")
    except Exception:
        pass
    
    # Referrer domains
    try:
        referrer_rows = con.execute("""
            SELECT 
                json_extract_string(payload, '$.referrer_domain') as referrer_domain,
                count(distinct visitor_id) as visitors
            FROM raw_events 
            WHERE site_id = ? 
            AND json_extract_string(payload, '$.referrer_domain') IS NOT NULL
            AND json_extract_string(payload, '$.referrer_domain') != 'direct'
            AND ts > current_timestamp - INTERVAL '7' DAY
            GROUP BY referrer_domain
            ORDER BY visitors DESC
            LIMIT 10
        """, [website_id]).fetchall()
        
        if referrer_rows:
            context_parts.append(f"\nTOP REFERRER DOMAINS:")
            for row in referrer_rows:
                context_parts.append(f"- {row[0]}: {row[1]} visitors")
    except Exception:
        pass
    
    # Network connection types
    try:
        network_rows = con.execute("""
            SELECT 
                connection_type,
                count(*) as cnt,
                avg(connection_downlink) as avg_downlink,
                avg(connection_rtt) as avg_rtt
            FROM performance_events 
            WHERE site_id = ? 
            AND connection_type IS NOT NULL
            AND ts > current_timestamp - INTERVAL '7' DAY
            GROUP BY connection_type
            ORDER BY cnt DESC
        """, [website_id]).fetchall()
        
        if network_rows:
            context_parts.append(f"\nNETWORK CONNECTION TYPES:")
            for row in network_rows:
                downlink_str = f", avg {row[2]:.2f} Mbps" if row[2] else ""
                rtt_str = f", {row[3]:.0f}ms RTT" if row[3] else ""
                context_parts.append(f"- {row[0]}: {row[1]} events{downlink_str}{rtt_str}")
    except Exception:
        pass
    
    # Page titles (top viewed pages with titles)
    try:
        title_rows = con.execute("""
            SELECT 
                json_extract_string(payload, '$.title') as page_title,
                json_extract_string(payload, '$.url') as page_url,
                count(*) as views
            FROM raw_events 
            WHERE site_id = ? 
            AND json_extract_string(payload, '$.title') IS NOT NULL
            AND ts > current_timestamp - INTERVAL '7' DAY
            GROUP BY page_title, page_url
            ORDER BY views DESC
            LIMIT 10
        """, [website_id]).fetchall()
        
        if title_rows:
            context_parts.append(f"\nTOP PAGES (with titles):")
            for row in title_rows:
                context_parts.append(f"- '{row[0]}' ({row[1]}): {row[2]} views")
    except Exception:
        pass
    
    # 8. Performance Metrics (averages)
    try:
        perf = con.execute(f"""
            SELECT 
                avg(first_contentful_paint) as avg_fcp,
                avg(largest_contentful_paint) as avg_lcp,
                avg(cumulative_layout_shift) as avg_cls,
                avg(first_input_delay) as avg_fid,
                avg(dom_content_loaded) as avg_dcl,
                avg(load_event_end) as avg_load
            FROM performance_events 
            WHERE site_id = ? 
            AND ts > current_timestamp - INTERVAL '{days}' DAY
        """, [website_id]).fetchone()
        
        if perf and any(perf):
            context_parts.append(f"\nPERFORMANCE METRICS (Avg, Last {days} days):")
            if perf[0]: context_parts.append(f"- First Contentful Paint: {perf[0]:.2f}ms")
            if perf[1]: context_parts.append(f"- Largest Contentful Paint: {perf[1]:.2f}ms")
            if perf[2]: context_parts.append(f"- Cumulative Layout Shift: {perf[2]:.4f}")
            if perf[3]: context_parts.append(f"- First Input Delay: {perf[3]:.2f}ms")
            if perf[4]: context_parts.append(f"- DOM Content Loaded: {perf[4]:.2f}ms")
            if perf[5]: context_parts.append(f"- Load Event End: {perf[5]:.2f}ms")
    except Exception:
        pass
    
    # 9. Engagement Metrics (averages)
    try:
        eng = con.execute(f"""
            SELECT 
                avg(scroll_depth_percent) as avg_scroll,
                avg(time_on_page_sec) as avg_time,
                avg(clicks_count) as avg_clicks
            FROM engagement_events 
            WHERE site_id = ? 
            AND ts > current_timestamp - INTERVAL '{days}' DAY
        """, [website_id]).fetchone()
        
        if eng and any(eng):
            context_parts.append(f"\nENGAGEMENT METRICS (Avg, Last {days} days):")
            if eng[0]: context_parts.append(f"- Scroll Depth: {eng[0]:.1f}%")
            if eng[1]: context_parts.append(f"- Time on Page: {eng[1]:.1f} seconds")
            if eng[2]: context_parts.append(f"- Clicks per Page: {eng[2]:.1f}")
    except Exception:
        pass
    
    # 10. Geographic Distribution (Countries and Cities)
    try:
        # Country-level distribution
        country_rows = con.execute("""
            SELECT country, count(*) as cnt 
            FROM visitor_profiles 
            WHERE site_id = ? AND country IS NOT NULL 
            GROUP BY country 
            ORDER BY cnt DESC 
            LIMIT 15
        """, [website_id]).fetchall()
        
        if country_rows:
            context_parts.append(f"\nGEOGRAPHIC DISTRIBUTION BY COUNTRY:")
            for row in country_rows:
                context_parts.append(f"- {row[0]}: {row[1]} visitors")
    except Exception:
        pass
    
    # City-level distribution from raw events payload
    try:
        city_rows = con.execute("""
            SELECT 
                json_extract_string(payload, '$.city') as city,
                json_extract_string(payload, '$.country') as country,
                count(distinct visitor_id) as visitors
            FROM raw_events 
            WHERE site_id = ? 
            AND json_extract_string(payload, '$.city') IS NOT NULL
            AND ts > current_timestamp - INTERVAL '7' DAY
            GROUP BY city, country
            ORDER BY visitors DESC 
            LIMIT 15
        """, [website_id]).fetchall()
        
        if city_rows:
            context_parts.append(f"\nGEOGRAPHIC DISTRIBUTION BY CITY:")
            for row in city_rows:
                city = row[0] or "Unknown"
                country = row[1] or "Unknown"
                context_parts.append(f"- {city}, {country}: {row[2]} visitors")
    except Exception:
        pass
    
    # Coordinate data for detailed location analysis
    try:
        coord_rows = con.execute("""
            SELECT 
                json_extract_string(payload, '$.country') as country,
                json_extract_string(payload, '$.city') as city,
                avg(CAST(json_extract_string(payload, '$.geo.lat') AS DOUBLE)) as avg_lat,
                avg(CAST(json_extract_string(payload, '$.geo.long') AS DOUBLE)) as avg_lng,
                count(distinct visitor_id) as visitors
            FROM raw_events 
            WHERE site_id = ? 
            AND json_extract_string(payload, '$.geo.lat') IS NOT NULL
            AND ts > current_timestamp - INTERVAL '7' DAY
            GROUP BY country, city
            ORDER BY visitors DESC
            LIMIT 10
        """, [website_id]).fetchall()
        
        if coord_rows:
            context_parts.append(f"\nDETAILED LOCATION DATA (with coordinates):")
            for row in coord_rows:
                country = row[0] or "Unknown"
                city = row[1] or "Unknown"
                context_parts.append(f"- {city}, {country}: {row[4]} visitors (avg coordinates: {row[2]:.4f}, {row[3]:.4f})")
    except Exception:
        pass
    
    # Language distribution
    try:
        lang_rows = con.execute("""
            SELECT 
                json_extract_string(payload, '$.language') as language,
                count(distinct visitor_id) as visitors
            FROM raw_events 
            WHERE site_id = ? 
            AND json_extract_string(payload, '$.language') IS NOT NULL
            AND ts > current_timestamp - INTERVAL '7' DAY
            GROUP BY language
            ORDER BY visitors DESC
            LIMIT 10
        """, [website_id]).fetchall()
        
        if lang_rows:
            context_parts.append(f"\nLANGUAGE DISTRIBUTION:")
            for row in lang_rows:
                context_parts.append(f"- {row[0]}: {row[1]} visitors")
    except Exception:
        pass
    
    # Timezone distribution
    try:
        tz_rows = con.execute("""
            SELECT 
                json_extract_string(payload, '$.tz_offset') as tz_offset,
                count(distinct visitor_id) as visitors
            FROM raw_events 
            WHERE site_id = ? 
            AND json_extract_string(payload, '$.tz_offset') IS NOT NULL
            AND ts > current_timestamp - INTERVAL '7' DAY
            GROUP BY tz_offset
            ORDER BY visitors DESC
            LIMIT 10
        """, [website_id]).fetchall()
        
        if tz_rows:
            context_parts.append(f"\nTIMEZONE DISTRIBUTION:")
            for row in tz_rows:
                tz_offset = row[0]
                context_parts.append(f"- UTC{tz_offset if tz_offset.startswith('-') or tz_offset.startswith('+') else '+' + str(tz_offset)}: {row[1]} visitors")
    except Exception:
        pass
    
    # 11. Conversion Events Summary
    try:
        conv = con.execute(f"""
            SELECT 
                event_type,
                count(*) as cnt,
                sum(order_value) as total_value
            FROM conversion_events 
            WHERE site_id = ? 
            AND ts > current_timestamp - INTERVAL '{days}' DAY
            GROUP BY event_type
            ORDER BY cnt DESC
        """, [website_id]).fetchall()
        
        if conv:
            context_parts.append(f"\nCONVERSIONS (Last {days} days):")
            for row in conv:
                val_str = f", Total Value: ${row[2]:.2f}" if row[2] else ""
                context_parts.append(f"- {row[0]}: {row[1]} events{val_str}")
    except Exception:
        pass
    
    # 12. Search Events Summary
    try:
        searches = con.execute(f"""
            SELECT 
                search_term,
                count(*) as cnt
            FROM search_events 
            WHERE site_id = ? 
            AND ts > current_timestamp - INTERVAL '{days}' DAY
            GROUP BY search_term
            ORDER BY cnt DESC
            LIMIT 10
        """, [website_id]).fetchall()
        
        if searches:
            context_parts.append(f"\nTOP SEARCH TERMS:")
            for row in searches:
                context_parts.append(f"- '{row[0]}': {row[1]} searches")
    except Exception:
        pass
    
    # 13. New vs Returning Visitors
    try:
        returning = con.execute("""
            SELECT 
                sum(CASE WHEN is_returning = true THEN 1 ELSE 0 END) as returning,
                sum(CASE WHEN is_returning = false THEN 1 ELSE 0 END) as new
            FROM visitor_profiles 
            WHERE site_id = ?
        """, [website_id]).fetchone()
        
        if returning and any(returning):
            context_parts.append(f"\nVISITOR TYPE:")
            context_parts.append(f"- Returning Visitors: {returning[0] or 0}")
            context_parts.append(f"- New Visitors: {returning[1] or 0}")
    except Exception:
        pass
    
    # 14. Session Bounce Rate
    try:
        bounce = con.execute(f"""
            SELECT 
                sum(CASE WHEN is_bounce = true THEN 1 ELSE 0 END) as bounces,
                count(*) as total_sessions
            FROM session_data 
            WHERE site_id = ?
            AND start_time > current_timestamp - INTERVAL '{days}' DAY
        """, [website_id]).fetchone()
        
        if bounce and bounce[1] > 0:
            bounce_rate = (bounce[0] / bounce[1]) * 100 if bounce[0] else 0
            context_parts.append(f"\nBOUNCE RATE:")
            context_parts.append(f"- {bounce_rate:.1f}% ({bounce[0]} bounces out of {bounce[1]} sessions)")
    except Exception:
        pass
    
    # 15. Recent Event Types Sample
    try:
        events = con.execute("""
            SELECT event_type, count(*) as cnt 
            FROM raw_events 
            WHERE site_id = ? 
            AND ts > current_timestamp - INTERVAL '1' DAY
            GROUP BY event_type 
            ORDER BY cnt DESC
        """, [website_id]).fetchall()
        
        if events:
            context_parts.append(f"\nRECENT EVENT TYPES (Last 24h):")
            for row in events:
                context_parts.append(f"- {row[0]}: {row[1]} events")
    except Exception:
        pass
    
    if not context_parts:
        return "No analytics data available for this website."
    
    return "\n".join(context_parts)
