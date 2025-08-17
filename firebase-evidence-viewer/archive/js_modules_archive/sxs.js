export function openSxS({ leftAsOf, rightSha256, focus }) {
  const overlay = document.querySelector('#sxsOverlay');
  if (!overlay) return;
  
  overlay.style.display = 'flex';
  overlay.classList.remove('hidden');
  
  // Populate headers
  const leftHeader = document.querySelector('.sxs-pane:first-child .pane-title');
  const rightHeader = document.querySelector('.sxs-pane:last-child .pane-title');
  
  if (leftHeader) {
    leftHeader.textContent = `Conformed (As-Of ${leftAsOf})`;
  }
  
  if (rightHeader) {
    rightHeader.textContent = `Document — ${rightSha256.slice(0, 8)}…`;
  }
  
  // Update left pane as-of date picker
  const leftAsOfInput = document.querySelector('.sxs-pane:first-child .as-of-date');
  if (leftAsOfInput) {
    leftAsOfInput.value = leftAsOf;
  }
  
  // TODO: render left conformed text for leftAsOf
  renderConformedContent(leftAsOf);
  
  // TODO: render right doc page and bbox highlight
  if (focus) {
    renderDocumentPage(rightSha256, focus.page, focus.bbox);
  }
  
  // Set focus state
  overlay.dataset.leftAsof = leftAsOf;
  overlay.dataset.rightSha256 = rightSha256;
  
  // Enable sync scroll if both panes are loaded
  enableSyncScroll();
}

export function closeSxS() {
  const overlay = document.querySelector('#sxsOverlay');
  if (overlay) {
    overlay.style.display = 'none';
    overlay.classList.add('hidden');
    
    // Clean up sync scroll
    disableSyncScroll();
  }
}

function renderConformedContent(asOfDate) {
  const leftPane = document.querySelector('.sxs-pane:first-child .document-canvas-container');
  if (!leftPane) return;
  
  // Mock conformed content - in production, fetch from API
  const content = generateConformedContent(asOfDate);
  leftPane.innerHTML = `
    <div class="document-page" style="width: 500px; min-height: 650px; background: white; padding: 30px;">
      ${content}
    </div>
  `;
}

function renderDocumentPage(sha256, page, bbox) {
  const rightPane = document.querySelector('.sxs-pane:last-child .document-canvas-container');
  if (!rightPane) return;
  
  // Mock document content - in production, load actual PDF page
  const content = generateDocumentContent(sha256, page);
  rightPane.innerHTML = `
    <div class="document-page" style="width: 500px; min-height: 650px; background: white; padding: 30px; position: relative;">
      ${content}
    </div>
  `;
  
  // Add highlight overlay if bbox provided
  if (bbox && bbox.length === 4) {
    setTimeout(() => addHighlightOverlay(rightPane, bbox), 100);
  }
}

function addHighlightOverlay(container, bbox) {
  const highlight = document.createElement('div');
  highlight.className = 'highlight-overlay flash';
  highlight.setAttribute('data-testid', 'highlight-span');
  highlight.style.position = 'absolute';
  highlight.style.left = (bbox[0] || 100) + 'px';
  highlight.style.top = (bbox[1] || 200) + 'px';
  highlight.style.width = ((bbox[2] || 300) - (bbox[0] || 100)) + 'px';
  highlight.style.height = ((bbox[3] || 220) - (bbox[1] || 200)) + 'px';
  highlight.style.background = 'rgba(59, 130, 246, 0.2)';
  highlight.style.border = '3px solid rgba(59, 130, 246, 0.8)';
  highlight.style.borderRadius = '4px';
  highlight.style.pointerEvents = 'none';
  highlight.style.zIndex = '10';
  highlight.style.boxShadow = '0 0 0 2px white, 0 0 10px rgba(59, 130, 246, 0.5)';
  
  const documentPage = container.querySelector('.document-page');
  if (documentPage) {
    documentPage.style.position = 'relative';
    documentPage.appendChild(highlight);
    
    // Remove flash class after animation
    setTimeout(() => {
      highlight.classList.remove('flash');
    }, 600);
  }
}

function generateConformedContent(asOfDate) {
  const isBeforeAmendment = asOfDate < '2019-06-01';
  const baseRent = isBeforeAmendment ? '$8,500.00' : '$10,000.00';
  const cam = isBeforeAmendment ? '$2,100.00' : '$4,231.17';
  const total = isBeforeAmendment ? '$12,691.00' : '$15,342.17';
  const status = isBeforeAmendment ? 'Original terms in effect' : 'As amended';
  
  return `
    <h3>Conformed Lease Agreement</h3>
    <p style="color: #64748b; margin-bottom: 20px;">As of: <strong>${asOfDate}</strong> | Status: ${status}</p>
    
    <div style="background: rgba(34, 197, 94, 0.2); padding: 12px; border-left: 4px solid #22c55e; margin-bottom: 20px;">
      <strong>Current Rent Terms:</strong><br>
      Base Rent: <strong>${baseRent}</strong>/month<br>
      CAM: <strong>${cam}</strong>/month<br>
      Total: <strong>${total}</strong>/month
    </div>
    
    <p style="font-size: 14px; color: #64748b;">
      ${!isBeforeAmendment ? '↳ Updated by Amendment 1, effective June 1, 2019' : '↳ Original lease terms in effect'}
    </p>
  `;
}

function generateDocumentContent(sha256, page) {
  // Mock content based on SHA256 and page
  if (sha256.includes('lease2019')) {
    return `
      <h3>Original Lease Agreement - Page ${page}</h3>
      <div style="background: rgba(255, 235, 59, 0.3); padding: 8px; border: 2px solid rgba(255, 193, 7, 0.8); margin: 20px 0;">
        <strong>Section 2.1(a) - Base Rent</strong><br>
        Tenant shall pay to Landlord as base rent the sum of <strong>$8,500.00</strong> per month.
      </div>
      <p>Additional lease terms and conditions...</p>
    `;
  } else if (sha256.includes('amend1')) {
    return `
      <h3>First Amendment to Lease - Page ${page}</h3>
      <div style="background: rgba(255, 235, 59, 0.3); padding: 8px; border: 2px solid rgba(255, 193, 7, 0.8); margin: 20px 0;">
        <strong>Amendment Section 1</strong><br>
        Base rent is hereby increased to <strong>$10,000.00</strong> per month.
      </div>
      <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
        <tr><th style="border: 1px solid #ddd; padding: 8px;">Item</th><th style="border: 1px solid #ddd; padding: 8px;">Amount</th></tr>
        <tr><td style="border: 1px solid #ddd; padding: 8px;">CAM Escalation</td><td style="border: 1px solid #ddd; padding: 8px; background: rgba(255, 235, 59, 0.3);">$1,442.17</td></tr>
      </table>
    `;
  }
  
  return `<h3>Document Content - Page ${page}</h3><p>Mock document content for SHA256: ${sha256.slice(0, 8)}...</p>`;
}

let syncScrollEnabled = false;

function enableSyncScroll() {
  if (syncScrollEnabled) return;
  
  const leftPane = document.querySelector('.sxs-pane:first-child .document-canvas-container');
  const rightPane = document.querySelector('.sxs-pane:last-child .document-canvas-container');
  
  if (!leftPane || !rightPane) return;
  
  function syncScroll(source, target) {
    if (source.dataset.syncing) return;
    target.dataset.syncing = 'true';
    
    const sourceScrollRatio = source.scrollTop / (source.scrollHeight - source.clientHeight);
    target.scrollTop = sourceScrollRatio * (target.scrollHeight - target.clientHeight);
    
    setTimeout(() => {
      delete target.dataset.syncing;
    }, 10);
  }
  
  leftPane.addEventListener('scroll', () => syncScroll(leftPane, rightPane));
  rightPane.addEventListener('scroll', () => syncScroll(rightPane, leftPane));
  
  syncScrollEnabled = true;
}

function disableSyncScroll() {
  syncScrollEnabled = false;
  // Remove event listeners by cloning and replacing elements
  const leftPane = document.querySelector('.sxs-pane:first-child .document-canvas-container');
  const rightPane = document.querySelector('.sxs-pane:last-child .document-canvas-container');
  
  if (leftPane) {
    const newLeftPane = leftPane.cloneNode(true);
    leftPane.parentNode.replaceChild(newLeftPane, leftPane);
  }
  
  if (rightPane) {
    const newRightPane = rightPane.cloneNode(true);
    rightPane.parentNode.replaceChild(newRightPane, rightPane);
  }
}