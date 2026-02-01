/**
 * Local storage management for visitor and session tracking
 */

import { uuidv4 } from './uuid.js';

export function getOrSetVisitorId() {
  var vid = localStorage.getItem('analytiq_vid');
  var isNewVisitor = false;
  
  if (!vid) {
    vid = uuidv4();
    localStorage.setItem('analytiq_vid', vid);
    isNewVisitor = true;
  }
  
  return { vid: vid, isNewVisitor: isNewVisitor };
}

export function getVisitorId() {
  return getOrSetVisitorId().vid;
}

export function getSessionId() {
  var sid = localStorage.getItem('analytiq_sid');
  
  if (!sid) {
    sid = uuidv4();
    localStorage.setItem('analytiq_sid', sid);
  }
  
  return sid;
}

export function clearSession() {
  localStorage.removeItem('analytiq_sid');
}

// Export as object for compatibility
export var Storage = {
  getOrSetVisitorId: getOrSetVisitorId,
  getVisitorId: getVisitorId,
  getSessionId: getSessionId,
  clearSession: clearSession
};
