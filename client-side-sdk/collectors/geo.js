
/**
 * Geolocation collector
 * Collects user location from browser geolocation API only (no third-party fallback)
 */

var GEO_CACHE_KEY = 'analytiq_geo';
var GEO_CACHE_TTL_MS = 60 * 60 * 1000; // 1 hour
var cachedGeo = null;
var pendingCallbacks = [];

function readCachedGeo() {
  try {
    var raw = localStorage.getItem(GEO_CACHE_KEY);
    if (!raw) return null;
    var parsed = JSON.parse(raw);
    if (!parsed || !parsed.ts || Date.now() - parsed.ts > GEO_CACHE_TTL_MS) return null;
    return parsed.geo;
  } catch (_) {
    return null;
  }
}

function saveCachedGeo(geo) {
  try {
    localStorage.setItem(GEO_CACHE_KEY, JSON.stringify({ ts: Date.now(), geo: geo }));
  } catch (_) {
    // Storage might be blocked; ignore
  }
}

function flushCallbacks(geo) {
  cachedGeo = geo;
  saveCachedGeo(geo);
  while (pendingCallbacks.length) {
    var cb = pendingCallbacks.shift();
    cb(geo);
  }
}

/**
 * Get geolocation information (latitude and longitude only)
 * Caches result to avoid repeated permission prompts during a session
 * @param {Function} cb - Callback function to receive geo data
 */
export function getGeoInfo(cb) {
  if (cachedGeo === null) cachedGeo = readCachedGeo();
  if (cachedGeo) {
    cb(cachedGeo);
    return;
  }

  pendingCallbacks.push(cb);
  if (pendingCallbacks.length > 1) return; // A request is already in flight

  var onGeoResolved = function (geo) {
    flushCallbacks(geo || { lat: 0, long: 0 });
  };

  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      function (pos) {
        onGeoResolved({
          lat: pos.coords.latitude,
          long: pos.coords.longitude
        });
      },
      function () {
        // User denied geolocation or error
        onGeoResolved({ lat: 0, long: 0 });
      },
      { timeout: 5000, enableHighAccuracy: false }
    );
  } else {
    // No geolocation support
    onGeoResolved({ lat: 0, long: 0 });
  }
}
