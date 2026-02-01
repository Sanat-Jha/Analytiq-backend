/**
 * Performance monitoring module
 * Sends periodic performance updates
 */

import { sendSingleEvent } from '../api/sender.js';
import { getAdvancedPerformanceMetrics } from '../collectors/performance.js';
import { getNetworkInfo } from '../collectors/network.js';
import { Storage } from '../utils/storage.js';
import { Config } from '../core/config.js';
import { getLastActivity } from './engagement.js';

/**
 * Send performance event to specialized endpoint
 */
export function sendPerformanceEvent() {
  var perfData = getAdvancedPerformanceMetrics();
  var networkData = getNetworkInfo();

  var event = {
    site_id: Config.SITE_ID,
    ts: new Date().toISOString(),
    visitor_id: Storage.getVisitorId(),
    session_id: Storage.getSessionId(),
    url: window.location.href,
    ...perfData,
    ...networkData
  };

  sendSingleEvent('performance', event);
}

/**
 * Initialize performance monitoring with periodic updates
 */
export function initPerformanceMonitoring() {
  // Send initial performance metrics after page load
  if (window.addEventListener) {
    window.addEventListener('load', function () {
      setTimeout(sendPerformanceEvent, 1000); // Wait for metrics to be available
    });
  }

  // Send periodic performance updates (every 10 seconds if user is active)
  setInterval(function () {
    if (Date.now() - getLastActivity() < Config.RECENT_ACTIVITY_THRESHOLD) {
      sendPerformanceEvent();
    }
  }, Config.PERFORMANCE_UPDATE_INTERVAL);
}
