/**
 * Configuration management for Analytiq analytics client
 * Handles API endpoints and site identification
 */

// Dynamically determine the backend URL from where the analytics script was loaded
function getBackendUrl() {
  // First check if explicitly set via window variable
  if (window.analytiqBackendUrl) {
    return window.analytiqBackendUrl;
  }

  // Try to detect from the script that loaded stats-config.js
  var scripts = document.querySelectorAll('script[src*="stats-config.js"]');
  if (scripts.length > 0) {
    var scriptSrc = scripts[scripts.length - 1].src;
    try {
      var url = new URL(scriptSrc);
      return url.origin; // Returns http://127.0.0.1:8000 or https://api.example.com
    } catch (e) {
      console.warn('[Analytiq] Could not parse script URL, using default');
    }
  }

  // Fallback to localhost for development
  return 'http://127.0.0.1:8000';
}

export var Config = {
  // Site identification (set by embedding script)
  SITE_ID: window.analytiqSiteId,
  SITE_KEY: window.analytiqSiteKey,

  // API endpoints - dynamically determined from script source
  BASE_URL: getBackendUrl(),

  // Unified ingest endpoint
  get INGEST_URL() {
    return this.BASE_URL + '/ingest/';
  },

  // Batching configuration
  BATCH_SIZE: 20,
  BATCH_INTERVAL: 5000, // 5 seconds

  // Engagement tracking intervals
  ENGAGEMENT_UPDATE_INTERVAL: 30000, // 30 seconds
  PERFORMANCE_UPDATE_INTERVAL: 10000, // 10 seconds
  IDLE_THRESHOLD: 30000, // 30 seconds
  ACTIVITY_THRESHOLD: 60000, // 1 minute
  RECENT_ACTIVITY_THRESHOLD: 120000 // 2 minutes
};
