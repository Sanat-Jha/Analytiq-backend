/**
 * Send event to a specialized endpoint (not used in current batching logic)
 * @param {string} endpoint - The endpoint URL
 * @param {Object} eventData - The event data to send
 */
export function sendToSpecializedEndpoint(endpoint, eventData) {
  fetch(endpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-site-id': Config.SITE_ID,
      'x-site-key': Config.SITE_KEY
    },
    body: JSON.stringify(eventData)
  }).catch(function(error) {
    console.warn('Failed to send event to specialized endpoint:', error);
  });
}
/**
 * API sender with batching support
 * Handles sending events to backend with intelligent batching and specialized endpoints
 */

import { Config } from '../core/config.js';

// Unified batching state
var eventBatch = {
  raw_events: [],
  conversion_events: [],
  performance_events: [],
  engagement_events: [],
  search_events: [],
  custom_events: []
};
var batchTimeout = null;

/**
 * Add event to batch queue (all events go to /ingest)
 * @param {string} eventType - Type of event (raw_events, conversion_events, etc.)
 * @param {Object} eventData - Event data to queue
 */
export function addToBatch(eventType, eventData) {
  if (!eventBatch[eventType]) return;
  eventBatch[eventType].push(eventData);
  checkBatchSize();
}

function checkBatchSize() {
  var totalEvents = Object.values(eventBatch).reduce(function(sum, arr) { 
    return sum + arr.length; 
  }, 0);
  if (totalEvents >= Config.BATCH_SIZE) {
    flushBatch();
  } else if (!batchTimeout) {
    batchTimeout = setTimeout(flushBatch, Config.BATCH_INTERVAL);
  }
}

/**
 * Flush the batch queue and send all queued events to /ingest
 */
export function flushBatch() {
  if (batchTimeout) {
    clearTimeout(batchTimeout);
    batchTimeout = null;
  }
  var hasEvents = Object.values(eventBatch).some(arr => arr.length > 0);
  if (!hasEvents) return;
  // Send batch to backend
  fetch(Config.INGEST_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-site-id': Config.SITE_ID,
      'x-site-key': Config.SITE_KEY
    },
    body: JSON.stringify({ batch: eventBatch })
  }).catch(function(error) {
    console.error('Failed to send batch events:', error);
    // Could implement retry logic here
  });
  // Reset batch
  eventBatch = {
    raw_events: [],
    conversion_events: [],
    performance_events: [],
    engagement_events: [],
    search_events: [],
    custom_events: []
  };
}

/**
 * Send a single event immediately to /ingest
 * @param {string} eventType - Type of event (raw, conversion, etc.)
 * @param {Object} eventData - Event data to send
 */
export function sendSingleEvent(eventType, eventData) {
  // Add a 'type' field for backend discrimination
  var payload = Object.assign({}, eventData, { type: eventType });
  fetch(Config.INGEST_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-site-id': Config.SITE_ID,
      'x-site-key': Config.SITE_KEY
    },
    body: JSON.stringify(payload)
  }).catch(function(error) {
    console.warn('Failed to send event to /ingest:', error);
    // Fallback to batch
    addToBatch(eventType + '_events', eventData);
  });
}
