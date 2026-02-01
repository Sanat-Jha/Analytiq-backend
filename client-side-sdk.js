// Analytiq Client-Side SDK - Modular Structure
// Loads ES6 modules from client-side-sdk/ directory
// Note: Must be served via HTTP/HTTPS (not file://) for modules to work

(function() {
  'use strict';

  // Find the script tag that loaded this file (stats-config.js)
  var scripts = document.querySelectorAll('script[src*="stats-config.js"]');
  var currentScript = scripts[scripts.length - 1];
  
  if (!currentScript || !currentScript.src) {
    console.error('Could not find stats-config.js script tag');
    return;
  }
  
  // Get the full URL where stats-config.js is actually being served from
  var scriptSrc = currentScript.src;
  console.log('[Analytiq] Loaded from:', scriptSrc);
  
  // Extract the base URL (e.g., http://127.0.0.1:8000)
  var baseUrl;
  try {
    // Remove the filename to get base URL
    var lastSlash = scriptSrc.lastIndexOf('/');
    baseUrl = scriptSrc.substring(0, lastSlash);
  } catch (e) {
    console.error('Failed to parse analytics client URL:', scriptSrc, e);
    return;
  }
  
  // Build path to main.js (same server that served client-side-sdk.js)
  var mainJsPath = baseUrl + '/client-side-sdk/main.js';
  console.log('[Analytiq] Loading modules from:', mainJsPath);

  // Load main.js as an ES6 module
  var script = document.createElement('script');
  script.type = 'module';
  script.src = mainJsPath;
  script.onerror = function() {
    console.error('Failed to load Analytiq client SDK from:', mainJsPath);
    console.error('Make sure the backend server is running and /client-side-sdk is mounted correctly.');
  };
  document.head.appendChild(script);

})();
