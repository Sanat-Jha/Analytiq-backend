/**
 * Site search tracking module
 * Detects and tracks site search queries
 */

import { sendSingleEvent } from '../api/sender.js';
import { Storage } from '../utils/storage.js';
import { Config } from '../core/config.js';

/**
 * Send search event to specialized endpoint
 * @param {string} searchTerm - Search query
 * @param {number} resultsCount - Number of results (optional)
 */
export function sendSearchEvent(searchTerm, resultsCount) {
  var event = {
    site_id: Config.SITE_ID,
    ts: new Date().toISOString(),
    visitor_id: Storage.getVisitorId(),
    session_id: Storage.getSessionId(),
    search_term: searchTerm,
    results_count: resultsCount || 0
  };

  sendSingleEvent('search', event);
}

/**
 * Detect site search from URL parameters
 */
export function detectSiteSearch() {
  var searchParams = new URLSearchParams(window.location.search);
  var searchTerms = searchParams.get('q') ||
    searchParams.get('search') ||
    searchParams.get('query');

  if (searchTerms) {
    sendSearchEvent(searchTerms);
  }
}
