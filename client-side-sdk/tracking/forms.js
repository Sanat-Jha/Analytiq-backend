/**
 * Form tracking module
 * Tracks form submissions, interactions, and conversions
 */

import { sendEvent } from './pageview.js';
import { sendSingleEvent } from '../api/sender.js';
import { Storage } from '../utils/storage.js';
import { Config } from '../core/config.js';

/**
 * Send conversion event
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

  sendSingleEvent('engagement', event);
}

/**
 * Initialize form tracking
 */
export function initFormTracking() {
  // Form submission tracking
  document.addEventListener('submit', function (e) {
    var form = e.target;
    var formData = new FormData(form);
    var hasEmail = false;
    var hasPayment = false;

    // Check form content to categorize
    for (var pair of formData.entries()) {
      var name = pair[0].toLowerCase();
      if (name.includes('email')) hasEmail = true;
      if (name.includes('card') || name.includes('payment') || name.includes('billing')) {
        hasPayment = true;
      }
    }

    var conversionType = 'form_submit';
    if (hasEmail && !hasPayment) {
      conversionType = 'newsletter_signup';
    } else if (hasPayment) {
      conversionType = 'checkout_started';
    }

    sendConversionEvent(conversionType, {
      form_id: form.id,
      form_class: form.className,
      form_action: form.action,
      has_email: hasEmail,
      has_payment: hasPayment
    });

    sendEvent('form_submit', {
      form_id: form.id,
      form_class: form.className,
      form_action: form.action,
      form_type: conversionType
    });
  }, true);

  // Form interaction tracking (when user starts filling)
  document.addEventListener('focus', function (e) {
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
      sendEngagementEvent({
        form_started: true,
        form_field: e.target.name || e.target.id
      });
    }
  }, true);
}
