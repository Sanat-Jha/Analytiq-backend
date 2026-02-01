/**
 * Click tracking module
 * Handles click events with conversion detection
 */

import { sendEvent } from './pageview.js';
import { sendSingleEvent } from '../api/sender.js';
import { Storage } from '../utils/storage.js';
import { Config } from '../core/config.js';
import { setClickCountRef } from './exit.js';

// Click counter state (shared with exit module via reference)
var clickState = { count: 0 };

/**
 * Get current click count
 * @returns {number} Total clicks in session
 */
export function getClickCount() {
  return clickState.count;
}

/**
 * Send conversion event to specialized endpoint
 * @param {string} eventType - Conversion type
 * @param {Object} data - Conversion data
 */
function sendConversionEvent(eventType, data) {
  var event = {
    site_id: Config.SITE_ID,
    ts: new Date().toISOString(),
    event_type: eventType,
    visitor_id: Storage.getVisitorId(),
    session_id: Storage.getSessionId(),
    ...data
  };

  sendSingleEvent('conversion', event);
}

/**
 * Initialize click tracking
 */
export function initClickTracking() {
  // Share click count with exit module
  setClickCountRef(clickState);

  document.addEventListener('click', function (e) {
    clickState.count++;

    var target = e.target;
    var tag = target.tagName.toLowerCase();
    var info = {
      tag: tag,
      clicks_count: clickState.count,
      page: window.location.pathname
    };

    if (target.href) info.href = target.href;
    if (target.id) info.id = target.id;
    if (target.className) info.class = target.className;
    if (target.textContent) info.text = target.textContent.substring(0, 100);

    // Detect potential conversion events
    var isConversionButton = target.textContent && (
      target.textContent.toLowerCase().includes('buy') ||
      target.textContent.toLowerCase().includes('purchase') ||
      target.textContent.toLowerCase().includes('checkout') ||
      target.textContent.toLowerCase().includes('add to cart') ||
      target.textContent.toLowerCase().includes('subscribe')
    );

    if (isConversionButton) {
      var conversionType = 'button_click';

      if (target.textContent.toLowerCase().includes('add to cart')) {
        conversionType = 'add_to_cart';
      } else if (target.textContent.toLowerCase().includes('checkout')) {
        conversionType = 'checkout_started';
      } else if (target.textContent.toLowerCase().includes('buy') ||
        target.textContent.toLowerCase().includes('purchase')) {
        conversionType = 'purchase_intent';
      }

      sendConversionEvent(conversionType, {
        button_text: target.textContent,
        button_id: target.id,
        button_class: target.className
      });
    }

    sendEvent('click', info);
  }, true);
}
