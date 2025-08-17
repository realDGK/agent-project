export async function resolveDeepLink(url) {
  // If you don't have the backend yet, just return the parsed bits
  // Replace this with a POST /deep-link/resolve when your API is live.
  try {
    const response = await fetch('/deep-link/resolve', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ url })
    });
    
    if (response.ok) {
      return await response.json();
    } else {
      // Fallback for development
      console.warn('Deep link resolution failed, using fallback');
      return { ok: true, target: 'document' };
    }
  } catch (error) {
    console.warn('Deep link API not available, using fallback:', error);
    return { ok: true, target: 'document' };
  }
}

export async function getPagePreview(sha256, page) {
  // Replace with GET /documents/:sha256/pages/:p/preview
  // For now, return a placeholder or your local PNG route.
  try {
    const response = await fetch(`/documents/${sha256}/pages/${page}/preview`);
    if (response.ok) {
      return response.url;
    }
  } catch (error) {
    console.warn('Page preview API not available:', error);
  }
  
  // Fallback: return placeholder URL
  return `/documents/${sha256}/pages/${page}/preview`; // or blob URL when backend exists
}

export async function getConformedContent(asOfDate, dealId) {
  try {
    const params = new URLSearchParams({
      as_of: asOfDate,
      deal_id: dealId || 'default'
    });
    
    const response = await fetch(`/conformed?${params.toString()}`);
    if (response.ok) {
      return await response.json();
    }
  } catch (error) {
    console.warn('Conformed content API not available:', error);
  }
  
  // Fallback: return mock conformed content
  return {
    title: 'Conformed Agreement',
    content: `<h2>Conformed Content (As-Of ${asOfDate})</h2><p>Mock content for development</p>`
  };
}

export async function createHILTask(sha256, page, bbox, reason, field) {
  try {
    const response = await fetch('/hil/task', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        sha256,
        page,
        bbox,
        reason,
        field
      })
    });
    
    if (response.ok) {
      return await response.json();
    }
  } catch (error) {
    console.warn('HIL task creation failed:', error);
  }
  
  // Fallback
  return { task_id: 'mock_task_' + Date.now() };
}

export async function getAnswerData(answerId) {
  try {
    const response = await fetch(`/answers/${answerId}`);
    if (response.ok) {
      return await response.json();
    }
  } catch (error) {
    console.warn('Answer API not available:', error);
  }
  
  // Fallback: return mock answer data
  return {
    as_of: new Date().toISOString().split('T')[0],
    answer: 'Mock answer for development',
    breakdown: [],
    formula: 'mock_formula',
    tabs_to_open: [],
    schema_version: '1.0.0'
  };
}