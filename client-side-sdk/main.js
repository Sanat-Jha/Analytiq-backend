/**
 * Analytiq Analytics Client - Main Entry Point
 * 
 * Modular analytics tracking client that collects comprehensive
 * website usage data and sends it to the Analytiq backend.
 * 
 * Architecture:
 * - core/ - Configuration and constants
 * - utils/ - UUID generation, storage management
 * - collectors/ - Data collection modules (device, performance, network, etc.)
 * - tracking/ - Event tracking modules (pageviews, clicks, forms, etc.)
 * - api/ - API communication and batching logic
 */

import { trackInitialPageview, sendEvent } from './tracking/pageview.js';
import { initClickTracking, getClickCount } from './tracking/clicks.js';
import { initFormTracking } from './tracking/forms.js';
import { initVideoTracking } from './tracking/video.js';
import { detectSiteSearch, sendSearchEvent } from './tracking/search.js';
import { initEngagementTracking } from './tracking/engagement.js';
import { initExitTracking } from './tracking/exit.js';
import { initPerformanceMonitoring, sendPerformanceEvent } from './tracking/performance.js';
import { initEngagementMonitoring, sendEngagementUpdate, setClickCountGetter } from './tracking/monitor.js';
import { sendToSpecializedEndpoint, sendSingleEvent } from './api/sender.js';
import { Storage } from './utils/storage.js';
import { Config } from './core/config.js';

/**
 * Initialize all tracking modules
 */
(function () {
  console.log('[Analytiq] Initializing analytics client...');
  console.log('[Analytiq] Site ID:', window.analytiqSiteId);
  console.log('[Analytiq] Site Key:', window.analytiqSiteKey ? '***set***' : 'NOT SET');

  // Check if site credentials are set
  if (!window.analytiqSiteId || !window.analytiqSiteKey) {
    console.error('[Analytiq] ERROR: Site ID or Site Key not set! Add these to your page:');
    console.error('  window.analytiqSiteId = "your-site-id";');
    console.error('  window.analytiqSiteKey = "your-site-key";');
    return;
  }

  // 1. Track initial pageview
  console.log('[Analytiq] Tracking initial pageview...');
  trackInitialPageview();

  // 2. Initialize all tracking modules
  console.log('[Analytiq] Initializing event trackers...');
  initClickTracking();
  initFormTracking();
  initVideoTracking();
  initEngagementTracking();
  initExitTracking();

  // 3. Set up cross-module communication
  setClickCountGetter(getClickCount);

  // 4. Detect site search on page load
  detectSiteSearch();

  // 5. Start performance and engagement monitoring
  console.log('[Analytiq] Starting monitoring...');
  initPerformanceMonitoring();
  initEngagementMonitoring();

  // 6. Expose public API on window object
  console.log('[Analytiq] Exposing public API on window.analytiq');
  window.analytiq = {
    // Core tracking methods
    track: sendEvent,
    trackSearch: sendSearchEvent,
    trackPerformance: sendPerformanceEvent,
    trackEngagement: sendEngagementUpdate,

    // E-commerce tracking methods
    trackPurchase: function (orderData) {
      var event = {
        site_id: Config.SITE_ID,
        ts: new Date().toISOString(),
        event_type: 'purchase',
        visitor_id: Storage.getVisitorId(),
        session_id: Storage.getSessionId(),
        order_id: orderData.orderId,
        order_value: orderData.total,
        currency: orderData.currency || 'USD',
        product_count: orderData.items ? orderData.items.length : 1
      };
      sendSingleEvent('conversion', event);
    },

    trackAddToCart: function (productData) {
      var event = {
        site_id: Config.SITE_ID,
        ts: new Date().toISOString(),
        event_type: 'add_to_cart',
        visitor_id: Storage.getVisitorId(),
        session_id: Storage.getSessionId(),
        product_id: productData.id,
        product_name: productData.name,
        category: productData.category,
        price: productData.price,
        quantity: productData.quantity || 1,
        currency: productData.currency || 'USD'
      };
      sendToSpecializedEndpoint(Config.CONVERSION_URL, event);
    },

    trackProductView: function (productData) {
      var event = {
        site_id: Config.SITE_ID,
        ts: new Date().toISOString(),
        event_type: 'product_view',
        visitor_id: Storage.getVisitorId(),
        session_id: Storage.getSessionId(),
        product_id: productData.id,
        product_name: productData.name,
        category: productData.category,
        price: productData.price
      };
      sendToSpecializedEndpoint(Config.CONVERSION_URL, event);
    },

    // Custom event tracking
    trackCustom: function (eventName, data) {
      var event = {
        site_id: Config.SITE_ID,
        ts: new Date().toISOString(),
        visitor_id: Storage.getVisitorId(),
        session_id: Storage.getSessionId(),
        event_name: eventName,
        event_category: data.category || 'general',
        event_value: data.value || 0,
        custom_properties: data
      };
      sendSingleEvent('custom', event);
    },

    trackSignup: function (userData) {
      this.trackCustom('user_signup', {
        category: 'authentication',
        user_type: userData.type || 'regular',
        signup_method: userData.method || 'email'
      });
    },

    trackRating: function (rating, productId) {
      this.trackCustom('rating_submitted', {
        category: 'engagement',
        value: rating,
        product_id: productId
      });
    },

    // Manual triggers
    sendImmediatePerformance: function () {
      sendPerformanceEvent();
    },

    sendImmediateEngagement: function () {
      sendEngagementUpdate({
        manual_trigger: true
      });
    }
  };

  console.log('[Analytiq] ✅ Analytics client initialized successfully!');
})();
