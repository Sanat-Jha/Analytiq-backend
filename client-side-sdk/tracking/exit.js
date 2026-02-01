/**
 * Exit tracking module
 * Tracks page exits, tab closes, and external link clicks
 */

import { sendEvent } from './pageview.js';
import { sendToSpecializedEndpoint } from '../api/sender.js';
import { flushBatch } from '../api/sender.js';
import { Storage } from '../utils/storage.js';
import { Config } from '../core/config.js';
import {
  getMaxScroll,
  getMouseMovements,
  getKeyboardEvents,
  getIdleTime
} from './engagement.js';

// Exit state
var sessionStart = Date.now();
var exitSent = false;
var clickCountRef = { count: 0 };

/**
 * Set click count reference (called from clicks module)
 * @param {Object} ref - Reference object with count property
 */
export function setClickCountRef(ref) {
  clickCountRef = ref;
}

/**
 * Send engagement event
 * @param {Object} data - Engagement data
 */
/*
 * Send engagement event
 * @param {Object} data - Engagement data
 */
function sendEngagementEvent(data) {
  var event = {
    site_id: Config.SITE_ID,
    ts: new Date().toISOString(),
    visitor_id: Storage.getVisitorId(),
    session_id: Storage.getSessionId(),
    url: window.location.href,
    ...data
  };

  // Use unified ingestion
  import('../api/sender.js').then(m => m.sendSingleEvent('engagement', event));
}

/**
 * Send exit event with comprehensive engagement data
 * @param {string} reason - Reason for exit
 * @param {Object} extra - Additional data
 */
export function sendExitEvent(reason, extra) {
  if (exitSent) return;
  exitSent = true;

  var timeSpent = (Date.now() - sessionStart) / 1000;
  var engagementData = {
    exit_reason: reason,
    time_spent_sec: timeSpent,
    scroll_depth_percent: getMaxScroll(),
    exit_url: window.location.href,
    clicks_count: clickCountRef.count,
    mouse_movements: getMouseMovements(),
    keyboard_events: getKeyboardEvents(),
    idle_time_sec: getIdleTime() / 1000,
    ...extra
  };

  sendEvent('exit', engagementData);
  sendEngagementEvent(engagementData);
  flushBatch(); // Ensure data is sent before leaving
}

/**
 * Initialize exit tracking
 */
export function initExitTracking() {
  // Page unload tracking
  window.addEventListener('beforeunload', function (e) {
    sendExitEvent('tab_close_or_reload');
  });

  // External link click tracking
  document.addEventListener('click', function (e) {
    var target = e.target.closest('a');
    if (target && target.href) {
      if (target.target === '_blank' || target.href.indexOf(window.location.host) === -1) {
        sendExitEvent('external_link_click', { link: target.href });
      } else if (target.href !== window.location.href) {
        sendExitEvent('internal_link_click', { link: target.href });
      }
    }
  }, true);

  // Tab visibility tracking
  document.addEventListener('visibilitychange', function () {
    if (document.visibilityState === 'hidden') {
      sendExitEvent('tab_hidden');
    }
  });
}

/**
 * Get session start time
 * @returns {number} Session start timestamp
 */
export function getSessionStart() {
  return sessionStart;
}
