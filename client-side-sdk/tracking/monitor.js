/**
 * Engagement monitoring module
 * Sends periodic engagement updates
 */

import { sendSingleEvent } from '../api/sender.js';
import { Storage } from '../utils/storage.js';
import { Config } from '../core/config.js';
import {
  getMaxScroll,
  getMouseMovements,
  getKeyboardEvents,
  getIdleTime,
  getLastActivity
} from './engagement.js';
import { getSessionStart } from './exit.js';

// Store click count getter reference
var getClickCountFn = null;

/**
 * Set click count getter function
 * @param {Function} fn - Function that returns click count
 */
export function setClickCountGetter(fn) {
  getClickCountFn = fn;
}

/**
 * Send engagement event with current metrics
 * @param {Object} additionalData - Additional engagement data
 */
export function sendEngagementUpdate(additionalData = {}) {
  var event = {
    site_id: Config.SITE_ID,
    ts: new Date().toISOString(),
    visitor_id: Storage.getVisitorId(),
    session_id: Storage.getSessionId(),
    url: window.location.href,
    time_on_page_sec: (Date.now() - getSessionStart()) / 1000,
    scroll_depth_percent: getMaxScroll(),
    clicks_count: getClickCountFn ? getClickCountFn() : 0,
    mouse_movements: getMouseMovements(),
    keyboard_events: getKeyboardEvents(),
    idle_time_sec: getIdleTime() / 1000,
    ...additionalData
  };

  sendSingleEvent('engagement', event);
}

/**
 * Initialize engagement monitoring with periodic updates
 */
export function initEngagementMonitoring() {
  // Send periodic engagement updates (every 30 seconds if user is active)
  setInterval(function () {
    if (Date.now() - getLastActivity() < Config.ACTIVITY_THRESHOLD) {
      sendEngagementUpdate();
    }
  }, Config.ENGAGEMENT_UPDATE_INTERVAL);
}
