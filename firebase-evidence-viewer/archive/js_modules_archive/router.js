import { parseDeepLink } from './deeplink.js';
import { resolveDeepLink } from './api.js';
import { log } from './telemetry.js';
import { openSxS } from './sxs.js';

// Global state for router
let currentAsOfDate = '2020-10-01';
let fullViewOpen = false;
let currentTab = 'conformed';

function flash(el) {
  if (!el) return;
  el.classList.add('flash');
  setTimeout(() => el.classList.remove('flash'), 700);
}

function focusTabForDoc(sha256) {
  // Find the doc tab that matches sha256 and activate it
  const tabs = [...document.querySelectorAll('.tab')];
  let match = null;
  
  // Match by document name in the tab text
  if (sha256.includes('lease2019') || sha256.includes('abc123def456lease2019')) {
    match = tabs.find(t => t.textContent.includes('LEASE_2019'));
  } else if (sha256.includes('amend1') || sha256.includes('def789ghi012amend1')) {
    match = tabs.find(t => t.textContent.includes('AMEND_1'));
  }
  
  if (match) {
    // Update tab appearance manually to ensure it works
    document.querySelectorAll('.tab').forEach(tab => {
      tab.classList.remove('active');
    });
    match.classList.add('active');
    
    // Trigger the tab switch manually
    const tabId = match.dataset.tab;
    if (tabId) {
      currentTab = tabId;
      // Use global loadDocument function if available
      if (window.loadDocument) {
        window.loadDocument(tabId);
      }
    }
    
    return true;
  }
  
  console.warn('No tab found for SHA256:', sha256);
  return false;
}

function scrollToBbox(bbox) {
  // Your viewer should convert PDF user-space bbox → screen; here, just flash the overlay node
  setTimeout(() => {
    const overlay = document.querySelector('[data-testid="highlight-span"]');
    if (overlay) {
      flash(overlay);
      // Scroll to the overlay
      overlay.scrollIntoView({ behavior: 'smooth', block: 'center' });
    } else {
      // Create a temporary highlight if none exists
      createTempHighlight(bbox);
    }
  }, 200);
}

function createTempHighlight(bbox) {
  const documentContainer = document.querySelector('.document-page');
  if (!documentContainer) return;
  
  const highlight = document.createElement('div');
  highlight.className = 'highlight-overlay flash';
  highlight.setAttribute('data-testid', 'highlight-span');
  highlight.style.position = 'absolute';
  highlight.style.left = (bbox?.[0] || 100) + 'px';
  highlight.style.top = (bbox?.[1] || 200) + 'px';
  highlight.style.width = ((bbox?.[2] || 300) - (bbox?.[0] || 100)) + 'px';
  highlight.style.height = ((bbox?.[3] || 220) - (bbox?.[1] || 200)) + 'px';
  highlight.style.background = 'rgba(59, 130, 246, 0.2)';
  highlight.style.border = '3px solid rgba(59, 130, 246, 0.8)';
  highlight.style.borderRadius = '4px';
  highlight.style.pointerEvents = 'none';
  highlight.style.zIndex = '10';
  highlight.style.boxShadow = '0 0 0 2px white, 0 0 10px rgba(59, 130, 246, 0.5)';
  
  documentContainer.style.position = 'relative';
  documentContainer.appendChild(highlight);
  
  // Flash and then remove
  setTimeout(() => {
    highlight.classList.remove('flash');
  }, 600);
  
  // Auto-remove after 3 seconds
  setTimeout(() => {
    if (highlight.parentNode) {
      highlight.parentNode.removeChild(highlight);
    }
  }, 3000);
}

export function wireChips() {
  document.querySelectorAll('[data-testid="evidence-chip"]').forEach(chip => {
    chip.addEventListener('click', async (e) => {
      const href = chip.getAttribute('href');
      if (!href) return;
      
      // v2.1.0: Allow Ctrl/Cmd+Click to open new tab (browser default)
      if (e.metaKey || e.ctrlKey) {
        // Don't preventDefault - let browser handle new tab
        log('chip_clicked', { 
          sha256: chip.dataset.sha256,
          page: parseInt(chip.dataset.page),
          field: chip.dataset.field,
          asof: chip.dataset.asof || currentAsOfDate,
          with_shift: false,
          new_tab: true
        });
        return;
      }
      
      // Prevent navigation for all other clicks
      e.preventDefault();
      
      const parsed = parseDeepLink(href);
      if (!parsed) {
        console.error('Failed to parse deep link:', href);
        return;
      }
      
      try {
        await resolveDeepLink(href);
      } catch (error) {
        console.warn('Deep link resolution failed:', error);
      }
      
      if (e.shiftKey) {
        // v2.1.0: Shift+Click → SxS (Conformed@As-Of left, source doc right)
        openSxS({ 
          leftAsOf: parsed.asof || currentAsOfDate, 
          rightSha256: parsed.sha256, 
          focus: { page: parsed.page, bbox: parsed.bbox } 
        });
        log('sxs_opened', { 
          left_type: 'conformed',
          left_as_of: parsed.asof || currentAsOfDate,
          right_type: 'document',
          sha256: parsed.sha256,
          page: parsed.page,
          field: parsed.field
        });
        return;
      }
      
      // v2.1.0: Default click → route inside Source Reading Pane, flash bbox/cell
      routeSourcePaneTo(href);
      
      log('chip_clicked', { 
        sha256: parsed.sha256, 
        page: parsed.page, 
        field: parsed.field, 
        asof: parsed.asof || currentAsOfDate, 
        with_shift: false,
        new_tab: false
      });
    });
  });
}

// v2.1.0: New function for in-pane routing
function routeSourcePaneTo(href) {
  const parsed = parseDeepLink(href);
  if (!parsed) return;
  
  // Focus the correct tab in Source Reading Pane (this loads the document)
  const tabFocused = focusTabForDoc(parsed.sha256);
  if (tabFocused) {
    // Scroll to bbox/cell and flash highlight after content loads
    setTimeout(() => {
      scrollToBbox(parsed.bbox);
    }, 300); // Give time for content to load and render
  }
}

export function wireAsOf() {
  const asof = document.querySelector('[data-testid="asof-date"]');
  if (!asof) return;
  
  asof.addEventListener('change', () => {
    const oldValue = asof.dataset.previousValue || asof.defaultValue;
    const newValue = asof.value;
    
    // Update conformed tab label
    const conformedTab = document.querySelector('[data-testid="tab-conformed"]');
    if (conformedTab) {
      conformedTab.textContent = `Conformed (As-Of ${newValue})`;
      conformedTab.setAttribute('data-asof', newValue);
    }
    
    // Update timeline chips
    document.querySelectorAll('[data-testid="timeline-chip"]').forEach(chip => {
      chip.classList.toggle('active', chip.dataset.date === newValue);
    });
    
    // Auto-switch to conformed tab
    if (conformedTab) {
      conformedTab.click();
    }
    
    // TODO: re-render conformed text for this date
    log('asof_changed', { from: oldValue, to: newValue });
    
    // Store current value for next change
    asof.dataset.previousValue = newValue;
  });
  
  // Store initial value
  asof.dataset.previousValue = asof.value;
}

export function wirePrevNext() {
  const prev = document.querySelector('[data-testid="prev-evidence"]');
  const next = document.querySelector('[data-testid="next-evidence"]');
  let currentEvidenceIndex = 0;
  
  function getEvidenceChips() {
    return [...document.querySelectorAll('[data-testid="evidence-chip"]')];
  }
  
  function go(dir) {
    const chips = getEvidenceChips();
    if (chips.length === 0) return;
    
    currentEvidenceIndex += dir;
    
    // Wrap around
    if (currentEvidenceIndex < 0) {
      currentEvidenceIndex = chips.length - 1;
    } else if (currentEvidenceIndex >= chips.length) {
      currentEvidenceIndex = 0;
    }
    
    const targetChip = chips[currentEvidenceIndex];
    if (targetChip) {
      // Highlight the selected chip
      chips.forEach(c => c.classList.remove('selected'));
      targetChip.classList.add('selected');
      
      // Trigger click to focus the evidence
      targetChip.click();
      
      // Scroll the chip into view in the chat
      targetChip.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      
      log('evidence_navigation', { 
        direction: dir > 0 ? 'next' : 'prev',
        index: currentEvidenceIndex,
        total: chips.length
      });
    }
  }
  
  prev?.addEventListener('click', () => go(-1));
  next?.addEventListener('click', () => go(1));
  
  // Keyboard shortcuts
  document.addEventListener('keydown', (e) => {
    // Only handle shortcuts when not in input fields
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
    
    if (e.key === '[') {
      e.preventDefault();
      go(-1);
    } else if (e.key === ']') {
      e.preventDefault();
      go(1);
    }
  });
}

export function wireTimelineChips() {
  document.querySelectorAll('[data-testid="timeline-chip"]').forEach(chip => {
    chip.addEventListener('click', () => {
      const date = chip.dataset.date;
      if (!date) return;
      
      // Update the as-of date input
      const asofInput = document.querySelector('[data-testid="asof-date"]');
      if (asofInput) {
        asofInput.value = date;
        asofInput.dispatchEvent(new Event('change'));
      }
      
      log('timeline_chip_clicked', {
        date: date,
        label: chip.textContent.trim()
      });
    });
  });
}

export function wireTabSwitching() {
  document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
      const tabId = tab.dataset.tab;
      if (!tabId) return;
      
      // Update tab appearance
      document.querySelectorAll('.tab').forEach(t => {
        t.classList.toggle('active', t === tab);
      });
      
      log('tab_switched', {
        tab_id: tabId,
        tab_type: tab.hasAttribute('data-testid') ? tab.getAttribute('data-testid') : 'unknown'
      });
      
      // Load document content (delegated to existing functions)
      if (window.loadDocument) {
        window.loadDocument(tabId);
      }
    });
  });
}

// v2.1.0: Full View functionality
export function getActiveTabMeta() {
  const activeTab = document.querySelector('.tab.active');
  if (!activeTab) return null;
  
  const tabType = activeTab.classList.contains('conformed') ? 'conformed' : 'document';
  const result = { tabType };
  
  if (tabType === 'conformed') {
    result.asOf = currentAsOfDate;
  } else {
    result.sha256 = activeTab.dataset.sha256 || 'unknown';
  }
  
  return result;
}

export function openFullView(tabMeta) {
  if (!tabMeta) tabMeta = getActiveTabMeta();
  if (!tabMeta) return;
  
  fullViewOpen = true;
  
  // Create or show full view overlay
  let overlay = document.getElementById('fullViewOverlay');
  if (!overlay) {
    overlay = createFullViewOverlay();
  }
  
  overlay.style.display = 'flex';
  overlay.classList.remove('hidden');
  
  // Set aria-pressed on expand button
  const expandBtn = document.querySelector('[data-testid="fullview-toggle"]');
  if (expandBtn) {
    expandBtn.setAttribute('aria-pressed', 'true');
  }
  
  // Populate content based on tab type
  if (tabMeta.tabType === 'conformed') {
    populateFullViewConformed(overlay, tabMeta.asOf);
  } else {
    populateFullViewDocument(overlay, tabMeta.sha256);
  }
  
  // Focus trap
  trapFocus(overlay);
  
  log('fullview_opened', {
    tab: tabMeta.tabType,
    as_of: tabMeta.asOf,
    sha256: tabMeta.sha256
  });
}

export function closeFullView() {
  const overlay = document.getElementById('fullViewOverlay');
  if (!overlay) return;
  
  fullViewOpen = false;
  overlay.style.display = 'none';
  overlay.classList.add('hidden');
  
  // Reset aria-pressed
  const expandBtn = document.querySelector('[data-testid="fullview-toggle"]');
  if (expandBtn) {
    expandBtn.setAttribute('aria-pressed', 'false');
  }
  
  // Restore focus
  restoreFocus();
  
  log('fullview_closed', {
    tab: getActiveTabMeta()?.tabType
  });
}

function createFullViewOverlay() {
  const overlay = document.createElement('div');
  overlay.id = 'fullViewOverlay';
  overlay.className = 'fullview-overlay hidden';
  overlay.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.8);
    z-index: 2000;
    display: none;
    align-items: center;
    justify-content: center;
  `;
  
  overlay.innerHTML = `
    <div class="fullview-container" style="
      width: 95%;
      height: 95%;
      background: white;
      border-radius: 8px;
      display: flex;
      flex-direction: column;
      position: relative;
    ">
      <div class="fullview-header" style="
        padding: 16px 20px;
        border-bottom: 1px solid #e2e8f0;
        display: flex;
        justify-content: between;
        align-items: center;
      ">
        <h2 class="fullview-title">Full View</h2>
        <button class="fullview-close-btn" data-testid="fullview-close" style="
          background: none;
          border: none;
          font-size: 24px;
          cursor: pointer;
          color: #64748b;
          margin-left: auto;
        ">&times;</button>
      </div>
      <div class="fullview-content" style="
        flex: 1;
        overflow: auto;
        padding: 20px;
      "></div>
    </div>
  `;
  
  // Add close button handler
  overlay.querySelector('[data-testid="fullview-close"]').addEventListener('click', closeFullView);
  
  // Close on overlay click
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) closeFullView();
  });
  
  document.body.appendChild(overlay);
  return overlay;
}

function populateFullViewConformed(overlay, asOf) {
  const title = overlay.querySelector('.fullview-title');
  const content = overlay.querySelector('.fullview-content');
  
  title.textContent = `Full Conformed View (As-Of ${asOf})`;
  
  // Add As-Of picker to header if not present
  let asOfPicker = overlay.querySelector('.fullview-asof-picker');
  if (!asOfPicker) {
    asOfPicker = document.createElement('input');
    asOfPicker.type = 'date';
    asOfPicker.className = 'fullview-asof-picker';
    asOfPicker.value = asOf;
    asOfPicker.style.cssText = 'margin-left: 20px; padding: 4px 8px; border: 1px solid #d1d5db; border-radius: 4px;';
    title.parentNode.insertBefore(asOfPicker, title.nextSibling);
    
    asOfPicker.addEventListener('change', () => {
      currentAsOfDate = asOfPicker.value;
      populateFullViewConformed(overlay, asOfPicker.value);
    });
  }
  
  // Generate full-screen conformed content
  content.innerHTML = generateFullConformedContent(asOf);
}

function populateFullViewDocument(overlay, sha256) {
  const title = overlay.querySelector('.fullview-title');
  const content = overlay.querySelector('.fullview-content');
  
  title.textContent = `Full Document View - ${sha256.slice(0, 8)}...`;
  
  // Remove As-Of picker if present
  const asOfPicker = overlay.querySelector('.fullview-asof-picker');
  if (asOfPicker) {
    asOfPicker.remove();
  }
  
  // Generate full-screen document content
  content.innerHTML = generateFullDocumentContent(sha256);
}

function generateFullConformedContent(asOf) {
  const isBeforeAmendment = asOf < '2019-06-01';
  const baseRent = isBeforeAmendment ? '$8,500.00' : '$10,000.00';
  const cam = isBeforeAmendment ? '$2,100.00' : '$4,231.17';
  const total = isBeforeAmendment ? '$12,691.00' : '$15,342.17';
  
  return `
    <div style="max-width: 800px; margin: 0 auto; font-family: serif; line-height: 1.6;">
      <h1 style="text-align: center; margin-bottom: 30px;">CONFORMED LEASE AGREEMENT</h1>
      <p style="text-align: center; color: #64748b; margin-bottom: 40px;">
        As of: <strong>${asOf}</strong> | 
        Status: ${isBeforeAmendment ? 'Original terms in effect' : 'As amended'}
      </p>
      
      <div style="background: rgba(34, 197, 94, 0.1); padding: 20px; border-left: 4px solid #22c55e; margin-bottom: 30px;">
        <h3>Current Rent Terms</h3>
        <table style="width: 100%; margin-top: 15px;">
          <tr><td><strong>Base Rent:</strong></td><td style="text-align: right;"><strong>${baseRent}</strong>/month</td></tr>
          <tr><td><strong>CAM:</strong></td><td style="text-align: right;"><strong>${cam}</strong>/month</td></tr>
          <tr><td><strong>Property Taxes:</strong></td><td style="text-align: right;"><strong>$1,111.00</strong>/month</td></tr>
          <tr style="border-top: 2px solid #22c55e; font-weight: bold;"><td>TOTAL:</td><td style="text-align: right;">${total}/month</td></tr>
        </table>
      </div>
      
      <div style="margin-bottom: 30px;">
        <h3>Amendment History</h3>
        <ul>
          <li><strong>Original Lease:</strong> January 1, 2019 - Base rent $8,500, CAM $2,100</li>
          ${!isBeforeAmendment ? '<li><strong>Amendment 1:</strong> June 1, 2019 - Base rent increased to $10,000, CAM to $4,231.17</li>' : '<li style="color: #94a3b8;">Amendment 1: June 1, 2019 - <em>(not yet effective as of this date)</em></li>'}
        </ul>
      </div>
      
      <div style="background: #f8fafc; padding: 20px; border-radius: 8px;">
        <h3>Key Terms & Conditions</h3>
        <p>This conformed view represents the contract as it exists on the specified As-Of date, incorporating all amendments and modifications that were effective as of that time.</p>
      </div>
    </div>
  `;
}

function generateFullDocumentContent(sha256) {
  return `
    <div style="max-width: 800px; margin: 0 auto;">
      <h1>Document: ${sha256.slice(0, 8)}...</h1>
      <div style="background: #f8fafc; padding: 20px; border-radius: 8px; margin: 20px 0;">
        <p><strong>Full document viewer would be rendered here</strong></p>
        <p>In production, this would show:</p>
        <ul>
          <li>Full PDF.js viewer with all pages</li>
          <li>Page thumbnails sidebar (optional)</li>
          <li>Zoom, search, and navigation controls</li>
          <li>Preserved highlight from evidence chip</li>
        </ul>
      </div>
    </div>
  `;
}

let lastFocusedElement = null;

function trapFocus(container) {
  lastFocusedElement = document.activeElement;
  
  const focusableElements = container.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  );
  
  if (focusableElements.length === 0) return;
  
  const firstElement = focusableElements[0];
  const lastElement = focusableElements[focusableElements.length - 1];
  
  firstElement.focus();
  
  container.addEventListener('keydown', (e) => {
    if (e.key === 'Tab') {
      if (e.shiftKey) {
        if (document.activeElement === firstElement) {
          e.preventDefault();
          lastElement.focus();
        }
      } else {
        if (document.activeElement === lastElement) {
          e.preventDefault();
          firstElement.focus();
        }
      }
    }
  });
}

function restoreFocus() {
  if (lastFocusedElement) {
    lastFocusedElement.focus();
    lastFocusedElement = null;
  }
}

// Initialize URL routing for deep links
export function initializeRouting() {
  // Handle initial page load with deep link
  const currentUrl = window.location.href;
  const deepLinkMatch = currentUrl.match(/\/doc\/[^?]+\?/);
  
  if (deepLinkMatch) {
    const parsed = parseDeepLink(currentUrl);
    if (parsed) {
      // Auto-focus the evidence on page load
      setTimeout(() => {
        focusTabForDoc(parsed.sha256);
        scrollToBbox(parsed.bbox);
        
        // Check for full view parameter
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('view') === 'full') {
          openFullView();
        }
        
        log('deep_link_loaded', {
          sha256: parsed.sha256,
          page: parsed.page,
          field: parsed.field,
          asof: parsed.asof,
          full_view: urlParams.get('view') === 'full'
        });
      }, 500);
    }
  }
  
  // Handle browser back/forward navigation
  window.addEventListener('popstate', (event) => {
    if (event.state && event.state.deepLink) {
      const parsed = parseDeepLink(event.state.deepLink);
      if (parsed) {
        focusTabForDoc(parsed.sha256);
        scrollToBbox(parsed.bbox);
      }
    }
  });
}