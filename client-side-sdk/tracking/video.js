/**
 * Video tracking module
 * Tracks video play, pause, and watch time events
 */

import { sendEvent } from './pageview.js';
import { sendSingleEvent } from '../api/sender.js';
import { Storage } from '../utils/storage.js';
import { Config } from '../core/config.js';

// Video watch time tracking
var videoWatchTime = {};

/**
 * Send engagement event
 * @param {Object} data - Engagement data
 */
function sendEngagementEvent(data) {
  var event = {
    site_id: Config.SITE_ID,
    ts: new Date().toISOString(),
    visitor_id: Storage.getVisitorId(),
    session_id: Storage.getSessionId(),
    url: window.location.href,
    ...data
  };

  sendSingleEvent('engagement', event);
}

/**
 * Initialize video tracking
 */
export function initVideoTracking() {
  // Video play tracking
  document.addEventListener('play', function (e) {
    if (e.target.tagName === 'VIDEO') {
      sendEvent('video_play', { video_src: e.target.currentSrc });
      sendEngagementEvent({
        video_played: true,
        video_src: e.target.currentSrc
      });
    }
  }, true);

  // Video time tracking
  document.addEventListener('timeupdate', function (e) {
    if (e.target.tagName === 'VIDEO') {
      var videoId = e.target.currentSrc || 'unknown';
      videoWatchTime[videoId] = e.target.currentTime;
    }
  }, true);

  // Video ended tracking
  document.addEventListener('ended', function (e) {
    if (e.target.tagName === 'VIDEO') {
      var videoId = e.target.currentSrc || 'unknown';
      var watchTime = videoWatchTime[videoId] || 0;

      sendEvent('video_ended', {
        video_src: e.target.currentSrc,
        duration: e.target.duration,
        watch_time: watchTime
      });

      sendEngagementEvent({
        video_watch_time_sec: watchTime
      });
    }
  }, true);
}
