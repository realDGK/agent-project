// Telemetry logging for user interactions
let sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);

export function log(evt, payload = {}) {
  // console log now; swap with your analytics sink later
  const telemetryEvent = {
    event: evt,
    timestamp: new Date().toISOString(),
    session_id: sessionId,
    user_agent: navigator.userAgent,
    url: window.location.href,
    ...payload
  };
  
  console.debug('[telemetry]', evt, telemetryEvent);
  
  // In production, send to analytics service
  try {
    sendToAnalytics(telemetryEvent);
  } catch (error) {
    console.warn('Failed to send telemetry:', error);
  }
}

async function sendToAnalytics(event) {
  // Attempt to send to backend telemetry endpoint
  try {
    await fetch('/telemetry', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(event),
      keepalive: true // Ensure event is sent even if page is closing
    });
  } catch (error) {
    // Fallback: store in localStorage for later sync
    storeEventLocally(event);
  }
}

function storeEventLocally(event) {
  try {
    const stored = JSON.parse(localStorage.getItem('telemetry_queue') || '[]');
    stored.push(event);
    
    // Keep only last 100 events to prevent storage bloat
    if (stored.length > 100) {
      stored.splice(0, stored.length - 100);
    }
    
    localStorage.setItem('telemetry_queue', JSON.stringify(stored));
  } catch (error) {
    console.warn('Failed to store telemetry locally:', error);
  }
}

export function flushQueuedEvents() {
  try {
    const stored = JSON.parse(localStorage.getItem('telemetry_queue') || '[]');
    if (stored.length === 0) return;
    
    // Send all queued events
    stored.forEach(event => {
      fetch('/telemetry', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(event),
        keepalive: true
      }).catch(() => {}); // Ignore failures for queued events
    });
    
    // Clear the queue
    localStorage.removeItem('telemetry_queue');
  } catch (error) {
    console.warn('Failed to flush telemetry queue:', error);
  }
}

export function trackPageView() {
  log('page_view', {
    path: window.location.pathname,
    search: window.location.search,
    referrer: document.referrer
  });
}

export function trackError(error, context = {}) {
  log('error', {
    message: error.message,
    stack: error.stack,
    context
  });
}

// Auto-flush queued events when page loads
window.addEventListener('load', flushQueuedEvents);

// Track page views automatically
document.addEventListener('DOMContentLoaded', trackPageView);