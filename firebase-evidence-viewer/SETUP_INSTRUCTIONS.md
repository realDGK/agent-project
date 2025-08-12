# Firebase Evidence Viewer - Setup Instructions

## Prerequisites
- Node.js (v16 or higher)
- Firebase CLI
- Google account for Firebase project

## Phase 1: Firebase Project Setup (15 minutes)

### 1. Install Firebase CLI
```bash
npm install -g firebase-tools
firebase login
```

### 2. Create Firebase Project
```bash
# Navigate to project directory
cd firebase-evidence-viewer

# Initialize Firebase project
firebase init

# Select services:
# ✅ Firestore: Configure security rules and indexes
# ✅ Hosting: Configure files for Firebase Hosting  
# ✅ Storage: Configure security rules for Cloud Storage

# Project setup:
# - Use existing project or create new one
# - Use default Firestore rules for now
# - Use 'build' as public directory
# - Configure as single-page app: Yes
# - Set up automatic builds: No
# - Use default Storage rules for now
```

### 3. Install Dependencies
```bash
# Core React dependencies
npm init react-app . --template typescript
npm install

# PDF and UI libraries
npm install pdfjs-dist
npm install @mui/material @emotion/react @emotion/styled
npm install @mui/icons-material

# Firebase SDK
npm install firebase

# Additional utilities
npm install react-dropzone
npm install uuid
```

## Phase 2: Core Component Development

### Component Architecture
```
App.js
├── DocumentUpload.js (handles PDF uploads)
├── MainViewer.js (container for viewer + evidence)
│   ├── PDFViewer.js (PDF rendering + highlights)
│   └── EvidencePanel.js (extracted data display)
└── HILReviewQueue.js (review tasks)
```

### Data Flow
1. **Upload**: PDF → Firebase Storage → Firestore metadata
2. **Display**: PDF rendered with PDF.js, evidence overlaid
3. **Interaction**: Click evidence → highlight PDF location
4. **Review**: Low confidence → HIL queue → user input → updated evidence

## Phase 3: Implementation Priority

### Day 1 Goals
- [ ] Firebase project configured
- [ ] Basic React app structure
- [ ] PDF upload to Firebase Storage
- [ ] PDF display with PDF.js
- [ ] Mock evidence data structure

### Day 2 Goals  
- [ ] Evidence panel component
- [ ] Click-to-highlight functionality
- [ ] Coordinate mapping system
- [ ] Confidence color coding

### Day 3 Goals
- [ ] HIL review queue component
- [ ] User input forms (transcribe/ignore/upload)
- [ ] Firebase data persistence
- [ ] Evidence update workflow

## Mock Data Strategy

Start with mock data to build UI independently:
```javascript
const mockDocument = {
  id: "doc_001",
  filename: "purchase_agreement.pdf",
  uploadedAt: new Date(),
  evidence: {
    purchase_amount: {
      value: "$350,000",
      page: 3,
      bbox: [150, 400, 250, 420],
      confidence: 0.95,
      snippet: "total purchase price of $350,000 shall be paid"
    },
    closing_date: {
      value: "December 31, 2024", 
      page: 2,
      bbox: [100, 300, 200, 315],
      confidence: 0.87,
      snippet: "closing shall occur on December 31, 2024"
    },
    buyer_name: {
      value: "John Smith",
      page: 1,
      bbox: [200, 150, 290, 170],
      confidence: 0.65, // Low confidence - should trigger HIL
      snippet: "Buyer: John Smith"
    }
  }
}
```

## Firebase Configuration Files

### Firestore Rules (`firestore.rules`)
```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Allow read/write to all documents (dev only)
    match /{document=**} {
      allow read, write: if true;
    }
  }
}
```

### Storage Rules (`storage.rules`)
```javascript
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    match /pdfs/{allPaths=**} {
      allow read, write: if true;
    }
  }
}
```

## Development Commands

```bash
# Start development server
npm start

# Build for production
npm run build

# Deploy to Firebase
firebase deploy

# Test Firebase functions locally
firebase emulators:start
```

## Environment Setup

### Create `.env` file:
```
REACT_APP_FIREBASE_API_KEY=your_api_key
REACT_APP_FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
REACT_APP_FIREBASE_PROJECT_ID=your_project_id
REACT_APP_FIREBASE_STORAGE_BUCKET=your_project.appspot.com
REACT_APP_FIREBASE_MESSAGING_SENDER_ID=your_sender_id
REACT_APP_FIREBASE_APP_ID=your_app_id
```

## Success Criteria

### Phase 1 Complete When:
- PDF uploads to Firebase Storage successfully
- PDF displays in browser with PDF.js
- Basic UI layout with Material-UI components

### Phase 2 Complete When:
- Evidence panel shows mock data
- Clicking evidence highlights PDF location
- Color coding works (green=high, yellow=medium, red=low confidence)

### Phase 3 Complete When:
- HIL review queue shows low-confidence items
- User can transcribe/ignore/upload for each item
- Evidence updates persist to Firestore
- System ready for real backend integration

## Next Steps After MVP
1. Connect to your agent-orchestrator API
2. Replace mock data with real extracted evidence
3. Add user authentication
4. Implement multi-document support
5. Add document comparison features