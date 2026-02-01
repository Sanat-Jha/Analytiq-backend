/**
 * Performance metrics collector
 * Collects Core Web Vitals, page load timing, and resource metrics
 */

/**
 * Get advanced performance metrics including Core Web Vitals
 * @returns {Object} Performance data including FCP, LCP, CLS, FID, load times, resource counts
 */
export function getAdvancedPerformanceMetrics() {
  if (!window.performance || !performance.timing) return {};
  
  var t = performance.timing;
  var paint = (performance.getEntriesByType && performance.getEntriesByType('paint')) || [];
  var fcp = paint.find(e => e.name === 'first-contentful-paint');
  var lcp = (performance.getEntriesByType && performance.getEntriesByType('largest-contentful-paint')) 
    ? performance.getEntriesByType('largest-contentful-paint')[0] 
    : undefined;
  
  // Calculate Cumulative Layout Shift (CLS)
  var cls = 0;
  if (performance.getEntriesByType && performance.getEntriesByType('layout-shift')) {
    var shifts = performance.getEntriesByType('layout-shift');
    shifts.forEach(function(shift) {
      if (!shift.hadRecentInput) {
        cls += shift.value;
      }
    });
  }

  // Resource metrics
  var resources = performance.getEntriesByType ? performance.getEntriesByType('resource') : [];
  var cachedResources = resources.filter(function(r) {
    return r.transferSize === 0 && r.decodedBodySize > 0;
  }).length;

  // Only compute load_event if timing is actually ready (loadEventEnd > 0)
  var loadEvent = (t.loadEventEnd && t.loadEventEnd > 0 && t.navigationStart > 0)
    ? t.loadEventEnd - t.navigationStart
    : undefined;
  var domContentLoaded = (t.domContentLoadedEventEnd && t.domContentLoadedEventEnd > 0 && t.navigationStart > 0)
    ? t.domContentLoadedEventEnd - t.navigationStart
    : undefined;
  var serverResponse = (t.responseStart && t.requestStart && t.responseStart >= t.requestStart)
    ? t.responseStart - t.requestStart
    : undefined;

  return {
    navigation_start: t.navigationStart,
    dom_content_loaded: domContentLoaded,
    load_event: loadEvent,
    first_contentful_paint: fcp ? fcp.startTime : undefined,
    largest_contentful_paint: lcp ? lcp.startTime : undefined,
    cumulative_layout_shift: cls,
    first_input_delay: (performance.getEntriesByType && performance.getEntriesByType('first-input')) 
      ? (performance.getEntriesByType('first-input')[0]?.processingStart - performance.getEntriesByType('first-input')[0]?.startTime) 
      : undefined,
    server_response_time: serverResponse,
    total_resources: resources.length,
    cached_resources: cachedResources
  };
}
