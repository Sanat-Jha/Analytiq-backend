/**
 * Referrer information collector
 * Analyzes traffic source from referrer and categorizes it
 */

import { getUTMParams } from './utm.js';

/**
 * Get referrer information and determine traffic source
 * @returns {Object} { referrer: string, referrer_domain: string, traffic_source: string }
 */
export function getReferrerInfo() {
  var ref = document.referrer;
  var source = 'direct';
  var refDomain = undefined;
  
  if (ref) {
    try {
      refDomain = (new URL(ref)).hostname;
      var currentDomain = window.location.hostname;
      
      if (refDomain !== currentDomain) {
        if (refDomain.includes('google.')) {
          source = 'organic';
        } else if (refDomain.includes('facebook.') || refDomain.includes('twitter.') || 
                   refDomain.includes('linkedin.') || refDomain.includes('instagram.')) {
          source = 'social';
        } else if (Object.keys(getUTMParams()).length > 0) {
          source = 'paid';
        } else {
          source = 'referral';
        }
      } else {
        source = 'internal';
      }
    } catch (e) {
      // Invalid referrer URL, treat as direct
      console.warn('Invalid referrer URL:', ref);
      refDomain = undefined;
    }
  }
  
  return {
    referrer: ref,
    referrer_domain: refDomain,
    traffic_source: source
  };
}
