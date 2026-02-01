/**
 * Pageview tracking module
 * Handles initial page view events and comprehensive page data collection
 */

import { Storage } from '../utils/storage.js';
import { getDeviceInfo } from '../collectors/device.js';
import { getReferrerInfo } from '../collectors/referrer.js';
import { getAdvancedPerformanceMetrics } from '../collectors/performance.js';
import { getNetworkInfo } from '../collectors/network.js';
import { getUTMParams } from '../collectors/utm.js';
import { getGeoInfo } from '../collectors/geo.js';
import { addToBatch } from '../api/sender.js';
import { Config } from '../core/config.js';

/**
 * Send a generic event with comprehensive payload
 * @param {string} eventType - Type of event (pageview, click, etc.)
 * @param {Object} payload - Additional payload data
 * @param {Function} cb - Optional callback after sending
 */
export function sendEvent(eventType, payload, cb) {
  var visitorInfo = Storage.getOrSetVisitorId();
  var isNewVisitor = visitorInfo.isNewVisitor;
  var visitorId = visitorInfo.vid;
  var sessionId = Storage.getSessionId();
  
  // Always include page path for pageview and click events
  var pagePath = window.location.pathname;
  
  var basePayload = {
    url: window.location.href,
    page: pagePath,
    title: document.title,
    ...getReferrerInfo(),
    ...getDeviceInfo(),
    ...getAdvancedPerformanceMetrics(),
    ...getNetworkInfo(),
    ...getUTMParams(),
    visitor_id: visitorId,
    session_id: sessionId,
    is_new_visitor: isNewVisitor,
    is_returning_visitor: !isNewVisitor,
    ...payload
  };
  
  getGeoInfo(function(geo) {
    if (geo.lat && geo.long) {
      basePayload.geo = geo;
    }
    
    var event = {
      site_id: Config.SITE_ID,
      ts: new Date().toISOString(),
      event_type: eventType,
      payload: basePayload,
      visitor_id: visitorId,
      session_id: sessionId
    };
    
    addToBatch('raw_events', event);
    
    if (cb) cb();
  });
}

/**
 * Track initial pageview on load
 */
export function trackInitialPageview() {
  var visitorInfo = Storage.getOrSetVisitorId();
  var isFirstVisit = visitorInfo.isNewVisitor;

  // Delay to ensure performance timing is ready (loadEventEnd populated)
  var sendPageview = function () {
    sendEvent('pageview', {
      is_first_visit: isFirstVisit,
      is_returning: !isFirstVisit
    });
  };

  // Wait for window.onload + small delay so loadEventEnd is populated
  if (document.readyState === 'complete') {
    setTimeout(sendPageview, 100);
  } else {
    window.addEventListener('load', function () {
      setTimeout(sendPageview, 100);
    });
  }
}
