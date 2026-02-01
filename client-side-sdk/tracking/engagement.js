/**
 * User engagement tracking module
 * Tracks scroll depth, mouse movements, keyboard events, idle time
 */

import { Config } from '../core/config.js';

// Engagement state
var maxScroll = 0;
var mouseMovements = 0;
var keyboardEvents = 0;
var idleTime = 0;
var lastActivity = Date.now();

/**
 * Get max scroll depth
 * @returns {number} Maximum scroll percentage
 */
export function getMaxScroll() {
  return maxScroll;
}

/**
 * Get mouse movement count
 * @returns {number} Total mouse movements
 */
export function getMouseMovements() {
  return mouseMovements;
}

/**
 * Get keyboard event count
 * @returns {number} Total keyboard events
 */
export function getKeyboardEvents() {
  return keyboardEvents;
}

/**
 * Get idle time
 * @returns {number} Idle time in milliseconds
 */
export function getIdleTime() {
  return idleTime;
}

/**
 * Get last activity timestamp
 * @returns {number} Timestamp of last activity
 */
export function getLastActivity() {
  return lastActivity;
}

/**
 * Reset idle timer (called on any user activity)
 */
export function resetIdleTimer() {
  if (Date.now() - lastActivity > Config.IDLE_THRESHOLD) {
    idleTime += Date.now() - lastActivity;
  }
  lastActivity = Date.now();
}

/**
 * Initialize engagement tracking
 */
export function initEngagementTracking() {
  // Scroll tracking
  window.addEventListener('scroll', function() {
    resetIdleTimer();
    var scrollDepth = Math.round(
      (window.scrollY + window.innerHeight) / document.body.scrollHeight * 100
    );
    if (scrollDepth > maxScroll) {
      maxScroll = scrollDepth;
    }
  });
  
  // Mouse movement tracking
  document.addEventListener('mousemove', function() {
    resetIdleTimer();
    mouseMovements++;
  });
  
  // Keyboard event tracking
  document.addEventListener('keydown', function() {
    resetIdleTimer();
    keyboardEvents++;
  });
}
