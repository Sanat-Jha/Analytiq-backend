/**
 * UTM parameter collector
 * Extracts campaign tracking parameters from URL
 */

/**
 * Extract UTM parameters from current URL
 * @returns {Object} UTM parameters (utm_source, utm_medium, utm_campaign, etc.)
 */
export function getUTMParams() {
  var params = {};
  var search = window.location.search.substring(1).split('&');
  
  search.forEach(function(pair) {
    var kv = pair.split('=');
    if (kv.length === 2 && kv[0].startsWith('utm_')) {
      params[kv[0]] = decodeURIComponent(kv[1]);
    }
  });
  
  return params;
}
