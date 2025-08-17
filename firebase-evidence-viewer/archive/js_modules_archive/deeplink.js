// Parse /doc/{sha256}?page=12&bbox=100,520,420,560&field=base_rent&asof=2020-10-01&exp=...&sig=...
export function parseDeepLink(url) {
  const m = url.match(/\/doc\/([^?]+)\?(.*)$/);
  if (!m) return null;
  const sha256 = decodeURIComponent(m[1]);
  const params = new URLSearchParams(m[2]);
  const page = parseInt(params.get('page') || '1', 10);
  const bbox = (params.get('bbox') || '').split(',').map(n => parseInt(n,10));
  return {
    sha256,
    page,
    bbox: bbox.length === 4 ? bbox : null,
    field: params.get('field') || null,
    asof: params.get('asof') || null,
    exp: params.get('exp') || null,
    sig: params.get('sig') || null
  };
}

export function generateDeepLink(sha256, page, bbox, field, asof) {
  const exp = Math.floor(Date.now() / 1000) + 600; // 10 minutes from now
  const sig = 'mock_signature'; // In production, generate HMAC
  
  const params = new URLSearchParams({
    page: page.toString(),
    field: field || '',
    asof: asof || new Date().toISOString().split('T')[0]
  });
  
  if (bbox && bbox.length === 4) {
    params.set('bbox', bbox.join(','));
  }
  
  params.set('exp', exp.toString());
  params.set('sig', sig);
  
  return `/doc/${sha256}?${params.toString()}`;
}

export function validateDeepLink(parsed) {
  if (!parsed) return false;
  if (!parsed.sha256) return false;
  if (!parsed.page || parsed.page < 1) return false;
  if (parsed.exp && parseInt(parsed.exp) < Date.now() / 1000) return false;
  return true;
}