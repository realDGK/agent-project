# Firebase Evidence Document Viewer

## Project Overview
A standalone web application for viewing PDF documents with clickable evidence linking and Human-in-the-Loop (HIL) review capabilities. This implements Steps 3 & 8 from the GPT-5 roadmap as an independent component.

## Core Features
1. **PDF Document Viewer** - Display PDFs with coordinate-based highlighting
2. **Evidence Panel** - Show extracted data with click-to-source functionality
3. **HIL Review Queue** - Handle low-confidence extractions with user input forms
4. **Confidence Visualization** - Color-coded highlights based on extraction confidence

## Tech Stack
- **Firebase Hosting** - Web app deployment
- **Firebase Firestore** - Document metadata and evidence storage
- **Firebase Storage** - PDF file storage with secure URLs
- **React** - Frontend framework
- **PDF.js** - PDF rendering and coordinate mapping
- **Material-UI** - Component library for professional UI

## Project Structure
```
firebase-evidence-viewer/
├── public/
│   ├── index.html
│   └── favicon.ico
├── src/
│   ├── components/
│   │   ├── PDFViewer.js
│   │   ├── EvidencePanel.js
│   │   ├── HILReviewQueue.js
│   │   └── DocumentUpload.js
│   ├── services/
│   │   ├── firebase.js
│   │   └── mockData.js
│   ├── utils/
│   │   └── pdfUtils.js
│   ├── App.js
│   └── index.js
├── firebase.json
├── firestore.rules
├── storage.rules
├── package.json
└── README.md
```

## Build Timeline
- **Phase 1 (Day 1)**: Project setup + basic PDF viewer
- **Phase 2 (Day 2)**: Evidence linking + highlighting system
- **Phase 3 (Day 3)**: HIL review forms + Firebase integration