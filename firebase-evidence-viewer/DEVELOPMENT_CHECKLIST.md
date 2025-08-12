# Development Checklist & Testing Guide

## Phase 1: Project Foundation ✅

### Firebase Setup
- [ ] Firebase CLI installed and logged in
- [ ] New Firebase project created
- [ ] Firestore, Hosting, and Storage enabled
- [ ] React app initialized with TypeScript
- [ ] All dependencies installed (see SETUP_INSTRUCTIONS.md)
- [ ] Firebase config added to .env file
- [ ] First deployment successful (`firebase deploy`)

### Basic Structure  
- [ ] Component folder structure created
- [ ] Mock data file created with sample evidence
- [ ] Basic routing between upload and viewer working
- [ ] Material-UI theme applied consistently

**Test**: Upload component shows, can drop files, shows loading state

## Phase 2: Core PDF Functionality ✅

### PDF Display
- [ ] PDF.js properly configured with worker
- [ ] PDF files load and render correctly
- [ ] Page navigation (next/previous) works
- [ ] Zoom controls functional (slider + buttons)
- [ ] PDF scales properly at different zoom levels
- [ ] Canvas resizing works correctly

### Coordinate System
- [ ] PDF coordinate mapping implemented
- [ ] Viewport transformations working
- [ ] Test coordinates align with actual PDF locations
- [ ] Different PDF sizes handled correctly

**Test**: Load sample PDF, navigate pages, zoom in/out, verify coordinates

## Phase 3: Evidence Integration ✅

### Evidence Panel
- [ ] Mock evidence data displays correctly
- [ ] Evidence items show confidence color coding
- [ ] Click on evidence item highlights PDF location
- [ ] Selected evidence state management works
- [ ] Confidence levels display (HIGH/MED/LOW chips)
- [ ] Evidence formatting looks professional

### Highlighting System
- [ ] Bounding box highlighting works accurately
- [ ] Highlight follows evidence selection
- [ ] Page changes when clicking evidence on different page
- [ ] Multiple highlights don't interfere with each other
- [ ] Highlight colors are visible and professional

**Test**: Click evidence items, verify PDF highlights appear in correct locations

## Phase 4: Human-in-the-Loop ✅

### Review Queue
- [ ] Low confidence items (<0.7) show in HIL queue
- [ ] Review counter badge displays correctly
- [ ] HIL queue opens/closes properly
- [ ] Review items show context (page, snippet, confidence)

### Review Actions
- [ ] Transcribe form accepts text input
- [ ] "Keep as Image" button works
- [ ] "Ignore" button works  
- [ ] Actions update evidence confidence to 1.0
- [ ] Completed reviews remove from queue
- [ ] Success message shows when queue empty

### State Management
- [ ] Evidence updates persist during session
- [ ] Reviewed items don't reappear in queue
- [ ] Form values saved correctly
- [ ] Component re-renders after updates

**Test**: Review all low-confidence items, verify they update correctly

## Phase 5: Firebase Integration ✅

### Firestore Operations
- [ ] Document metadata saves to Firestore
- [ ] Evidence data persists correctly  
- [ ] Updates sync in real-time
- [ ] Error handling for failed operations
- [ ] Loading states during Firebase operations

### Storage Operations  
- [ ] PDF files upload to Firebase Storage
- [ ] Secure download URLs generated
- [ ] File size limits enforced
- [ ] Error handling for upload failures

### Security Rules
- [ ] Firestore rules allow read/write (dev mode)
- [ ] Storage rules allow PDF upload/download
- [ ] Rules tested with Firebase emulator

**Test**: Upload PDF, verify Firestore document created, check Storage for file

## Production Readiness ✅

### Performance
- [ ] Large PDFs (>10MB) load without crashing
- [ ] Page rendering optimized (lazy loading)
- [ ] Memory usage reasonable during long sessions
- [ ] UI responsive during PDF operations

### Error Handling
- [ ] Invalid PDF files handled gracefully
- [ ] Network failures show user-friendly messages
- [ ] Missing evidence data doesn't break UI
- [ ] Firebase errors logged and handled

### User Experience
- [ ] Loading states show during operations
- [ ] Success/error messages are clear
- [ ] UI remains responsive during heavy operations
- [ ] Mobile responsiveness (basic)

### Code Quality
- [ ] Components are properly organized
- [ ] State management is clean and predictable
- [ ] No console errors in production build
- [ ] TypeScript types properly defined
- [ ] Code follows React best practices

## Testing Scenarios

### Test Case 1: Complete Workflow
1. Load app → should show upload component
2. Drop PDF file → should show processing, then viewer
3. Click evidence item → should highlight PDF location
4. Open review queue → should show low confidence items
5. Complete a review → should update evidence and remove from queue
6. Navigate pages → highlights should follow evidence locations

### Test Case 2: Error Handling  
1. Upload invalid file → should show error message
2. Upload very large PDF → should handle gracefully
3. Disconnect internet → should show offline message
4. Invalid evidence data → should show fallback UI

### Test Case 3: Performance
1. Upload 50+ page PDF → should load without hanging
2. Rapid page navigation → should be smooth
3. Multiple zoom changes → should not lag
4. Long session use → memory should not leak

## Integration Testing

### Mock Data Validation
- [ ] All mock evidence has required fields (value, page, bbox, confidence, snippet)
- [ ] Bounding boxes align with actual PDF content
- [ ] Confidence levels create appropriate HIL queue
- [ ] Evidence types cover common real estate fields

### API Readiness
- [ ] Component props match expected backend API structure
- [ ] Evidence format matches GPT-5 roadmap requirements
- [ ] Firebase data structure ready for backend integration
- [ ] Component interfaces ready for real authentication

## Deployment Checklist

### Firebase Hosting
- [ ] Production build creates clean build/ folder
- [ ] Firebase hosting configured correctly
- [ ] Custom domain (optional) configured
- [ ] SSL certificate active
- [ ] App loads correctly from hosting URL

### Environment Configuration
- [ ] Production Firebase config added
- [ ] API keys secured appropriately
- [ ] Build scripts working correctly
- [ ] Environment variables properly set

## Success Metrics

### MVP Complete When:
1. **Can upload PDF and see evidence** - Core functionality working
2. **Clicking evidence highlights PDF** - Source linking functional
3. **HIL queue processes reviews** - Human feedback loop working  
4. **Evidence updates persist** - Data management working
5. **Professional UI/UX** - Ready for stakeholder demo

### Demo Ready When:
1. Can show complete workflow in under 2 minutes
2. No visible bugs during normal operation
3. UI looks professional and trustworthy
4. Performance acceptable on typical hardware
5. Error handling graceful for common failures

This checklist ensures your Firebase Evidence Viewer is production-ready and demonstrates the core value proposition of your larger system!