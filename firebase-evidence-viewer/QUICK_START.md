# Quick Start Guide - 30 Minutes to Working Demo

## Overview
This guide gets you to a working Evidence Document Viewer in 30 minutes. Perfect for your work breaks or focused coding sessions.

## Prerequisites (5 minutes)
```bash
# Ensure you have these installed:
node --version  # v16 or higher
npm --version   # v8 or higher
firebase --version  # v11 or higher

# If missing, install:
npm install -g firebase-tools
```

## Speed Setup (10 minutes)

### 1. Create Firebase Project (3 min)
```bash
# Login and create project
firebase login
firebase projects:create your-evidence-viewer --display-name "Evidence Viewer"
```

### 2. Initialize React App (5 min)
```bash
cd firebase-evidence-viewer
npx create-react-app . --template typescript
npm install firebase pdfjs-dist @mui/material @emotion/react @emotion/styled react-dropzone
```

### 3. Firebase Config (2 min)
```bash
firebase init
# Select: Firestore, Hosting, Storage
# Choose existing project: your-evidence-viewer
# Accept defaults for everything
```

## Core Implementation (15 minutes)

### 1. Basic App Structure (5 min)
Copy the `App.js` from `COMPONENT_TEMPLATES.md` and create these files:
- `src/components/` (folder)
- `src/services/mockData.js` (copy from templates)
- `src/utils/` (folder)

### 2. PDF Viewer Component (7 min)
Create `src/components/PDFViewer.js` - copy from templates, focus on:
- PDF.js setup
- Canvas rendering
- Basic highlighting (can be simplified for demo)

### 3. Evidence Panel (3 min)
Create `src/components/EvidencePanel.js` - copy from templates, focus on:
- Display mock evidence
- Click handlers
- Confidence color coding

## Demo-Ready Features (Priority Order)

### Must Have (Core Demo)
1. **PDF Display** - Shows uploaded PDF 
2. **Evidence List** - Shows extracted fields with confidence
3. **Click Highlighting** - Click evidence → PDF highlights location
4. **Professional UI** - Material-UI components, clean layout

### Nice to Have (Time Permitting) 
5. **HIL Queue** - Shows low confidence items
6. **Page Navigation** - Next/previous buttons
7. **Zoom Controls** - Basic zoom in/out

### Skip for Demo
- Firebase persistence (use localStorage)
- File upload (hardcode sample PDF)
- Complex error handling
- Mobile responsiveness

## Simplified Implementation Strategy

### Mock Everything First
```javascript
// Instead of real PDF upload, use sample file:
const samplePDF = '/sample_contract.pdf'; // Put in public folder

// Instead of Firebase, use React state:
const [evidence, setEvidence] = useState(mockEvidence);

// Instead of complex highlighting, use simple overlay:
const highlightBox = { x: 100, y: 200, width: 150, height: 20 };
```

### Minimum Viable Components

#### App.js (Simplified)
```javascript
function App() {
  const [selectedEvidence, setSelectedEvidence] = useState(null);
  
  return (
    <Box sx={{ display: 'flex', height: '100vh' }}>
      <PDFViewer selectedEvidence={selectedEvidence} />
      <EvidencePanel onSelect={setSelectedEvidence} />
    </Box>
  );
}
```

#### PDFViewer.js (Core Only)
```javascript
const PDFViewer = ({ selectedEvidence }) => {
  // Load hardcoded sample PDF
  // Render with PDF.js
  // Show yellow highlight when selectedEvidence changes
  // Skip zoom, navigation for v1
};
```

#### EvidencePanel.js (Essential)
```javascript  
const EvidencePanel = ({ onSelect }) => {
  const evidenceList = Object.entries(mockEvidence);
  
  return (
    <List>
      {evidenceList.map(([key, data]) => (
        <ListItem onClick={() => onSelect(data)}>
          <ListItemText primary={data.value} secondary={`Page ${data.page}`} />
          <Chip label={data.confidence > 0.8 ? 'HIGH' : 'LOW'} />
        </ListItem>
      ))}
    </List>
  );
};
```

## Quick Test Scenarios

### 30-Second Demo Script
1. "This is our evidence document viewer"
2. **Click evidence item** → "See how it highlights the exact location in the PDF"
3. **Click different evidence** → "Every extracted field links directly to its source"
4. **Point to confidence levels** → "Low confidence items get flagged for human review"
5. "This creates complete audit trails for all extracted data"

### What This Proves
- ✅ Source linking works (core value prop)
- ✅ Evidence extraction system functional
- ✅ Professional UI suitable for real estate professionals  
- ✅ Human-in-the-loop workflow foundation
- ✅ Scales to complex documents

## Debugging Quick Fixes

### PDF Not Loading
```javascript
// Check PDF.js worker path:
pdfjsLib.GlobalWorkerOptions.workerSrc = 
  'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
```

### Highlights Not Showing
```javascript
// Simplify to fixed position first:
const highlightStyle = {
  position: 'absolute',
  left: '100px',
  top: '200px', 
  width: '150px',
  height: '20px',
  backgroundColor: 'rgba(255, 235, 59, 0.5)'
};
```

### UI Broken
```javascript
// Use basic HTML instead of Material-UI if needed:
<div style={{ display: 'flex' }}>
  <div style={{ flex: 1 }}>PDF Viewer</div>
  <div style={{ width: '300px' }}>Evidence Panel</div>
</div>
```

## Time Boxing

- **10 min**: Project setup + dependencies
- **10 min**: Basic PDF display working
- **5 min**: Evidence list showing
- **5 min**: Click highlighting functional

If you hit 30 minutes and it's not working, focus on the **evidence list** showing mock data with professional styling. That alone demonstrates the concept and you can add PDF integration in your next session.

The goal is a **working demonstration** of the core concept, not a perfect implementation. Ship it, test it, then iterate!