/**
 * Network information collector
 * Collects connection speed, latency, and connection type
 */

/**
 * Get network connection information
 * @returns {Object} Network data including downlink, RTT, connection type, save data mode
 */
export function getNetworkInfo() {
  var conn = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
  
  if (conn) {
    return {
      connection_downlink: conn.downlink,
      connection_rtt: conn.rtt,
      connection_type: conn.effectiveType,
      connection_save_data: conn.saveData
    };
  }
  
  return {};
}
