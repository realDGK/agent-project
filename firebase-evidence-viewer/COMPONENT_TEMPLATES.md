# Component Templates & Code Structure

## 1. App.js - Main Application Container

```javascript
import React, { useState } from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { Container, AppBar, Toolbar, Typography, Box } from '@mui/material';
import DocumentUpload from './components/DocumentUpload';
import MainViewer from './components/MainViewer';
import HILReviewQueue from './components/HILReviewQueue';
import './App.css';

const theme = createTheme({
  palette: {
    primary: { main: '#1976d2' },
    secondary: { main: '#dc004e' },
  },
});

function App() {
  const [currentDocument, setCurrentDocument] = useState(null);
  const [showReviewQueue, setShowReviewQueue] = useState(false);

  return (
    <ThemeProvider theme={theme}>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Evidence Document Viewer
          </Typography>
        </Toolbar>
      </AppBar>
      
      <Container maxWidth={false} sx={{ mt: 2, height: 'calc(100vh - 100px)' }}>
        {!currentDocument ? (
          <DocumentUpload onDocumentLoaded={setCurrentDocument} />
        ) : (
          <Box sx={{ display: 'flex', height: '100%', gap: 2 }}>
            <MainViewer 
              document={currentDocument} 
              onShowReviewQueue={() => setShowReviewQueue(true)}
            />
            {showReviewQueue && (
              <HILReviewQueue 
                document={currentDocument}
                onClose={() => setShowReviewQueue(false)}
              />
            )}
          </Box>
        )}
      </Container>
    </ThemeProvider>
  );
}

export default App;
```

## 2. DocumentUpload.js - PDF Upload Component

```javascript
import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Box, Typography, Paper, LinearProgress, Alert } from '@mui/material';
import { CloudUpload } from '@mui/icons-material';
import { uploadDocument } from '../services/firebase';
import { mockDocument } from '../services/mockData';

const DocumentUpload = ({ onDocumentLoaded }) => {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);

  const onDrop = useCallback(async (acceptedFiles) => {
    const file = acceptedFiles[0];
    if (!file) return;

    setUploading(true);
    setError(null);

    try {
      // For MVP: Use mock data instead of actual upload
      // const document = await uploadDocument(file);
      
      // Simulate upload delay
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // Use mock document with actual file for PDF display
      const document = {
        ...mockDocument,
        file: file,
        filename: file.name
      };
      
      onDocumentLoaded(document);
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  }, [onDocumentLoaded]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    maxFiles: 1
  });

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        height: '60vh'
      }}
    >
      <Paper
        {...getRootProps()}
        sx={{
          p: 6,
          textAlign: 'center',
          cursor: 'pointer',
          border: '2px dashed',
          borderColor: isDragActive ? 'primary.main' : 'grey.300',
          bgcolor: isDragActive ? 'primary.light' : 'background.paper',
          '&:hover': { bgcolor: 'grey.50' },
          minWidth: 400,
          minHeight: 200
        }}
      >
        <input {...getInputProps()} />
        <CloudUpload sx={{ fontSize: 60, color: 'grey.500', mb: 2 }} />
        
        {uploading ? (
          <>
            <Typography variant="h6" gutterBottom>
              Processing Document...
            </Typography>
            <LinearProgress sx={{ mt: 2 }} />
          </>
        ) : (
          <>
            <Typography variant="h6" gutterBottom>
              {isDragActive ? 'Drop PDF here' : 'Upload PDF Document'}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Drag and drop a PDF file here, or click to select
            </Typography>
          </>
        )}
      </Paper>

      {error && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {error}
        </Alert>
      )}
    </Box>
  );
};

export default DocumentUpload;
```

## 3. PDFViewer.js - PDF Display with Highlighting

```javascript
import React, { useEffect, useRef, useState } from 'react';
import { Box, Paper, IconButton, Typography, Slider } from '@mui/material';
import { ZoomIn, ZoomOut, NavigateBefore, NavigateNext } from '@mui/icons-material';
import * as pdfjsLib from 'pdfjs-dist';

// Configure PDF.js worker
pdfjsLib.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.js`;

const PDFViewer = ({ document, selectedEvidence, onPageLoad }) => {
  const canvasRef = useRef();
  const overlayRef = useRef();
  const [pdfDoc, setPdfDoc] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const [scale, setScale] = useState(1.2);
  const [pageData, setPageData] = useState({});

  // Load PDF document
  useEffect(() => {
    if (!document?.file) return;

    const loadPDF = async () => {
      const fileReader = new FileReader();
      fileReader.onload = async (e) => {
        const typedArray = new Uint8Array(e.target.result);
        const pdf = await pdfjsLib.getDocument(typedArray).promise;
        setPdfDoc(pdf);
        setTotalPages(pdf.numPages);
        setCurrentPage(1);
      };
      fileReader.readAsArrayBuffer(document.file);
    };

    loadPDF();
  }, [document]);

  // Render current page
  useEffect(() => {
    if (!pdfDoc || !canvasRef.current) return;

    const renderPage = async () => {
      const page = await pdfDoc.getPage(currentPage);
      const viewport = page.getViewport({ scale });
      
      const canvas = canvasRef.current;
      const context = canvas.getContext('2d');
      
      canvas.height = viewport.height;
      canvas.width = viewport.width;
      
      const renderContext = {
        canvasContext: context,
        viewport: viewport,
      };
      
      await page.render(renderContext).promise;
      
      // Store page data for coordinate mapping
      setPageData(prev => ({
        ...prev,
        [currentPage]: { viewport, page }
      }));
      
      onPageLoad?.(currentPage, viewport);
    };

    renderPage();
  }, [pdfDoc, currentPage, scale, onPageLoad]);

  // Highlight selected evidence
  useEffect(() => {
    if (!selectedEvidence || !overlayRef.current || !pageData[currentPage]) return;

    const overlay = overlayRef.current;
    const ctx = overlay.getContext('2d');
    const { viewport } = pageData[currentPage];
    
    // Clear previous highlights
    ctx.clearRect(0, 0, overlay.width, overlay.height);
    
    if (selectedEvidence.page === currentPage) {
      const [x1, y1, x2, y2] = selectedEvidence.bbox;
      
      // Transform coordinates to viewport
      const [vx1, vy1, vx2, vy2] = viewport.convertToViewportRectangle([x1, y1, x2, y2]);
      
      // Draw highlight rectangle
      ctx.fillStyle = 'rgba(255, 235, 59, 0.4)'; // Yellow highlight
      ctx.strokeStyle = 'rgba(255, 193, 7, 0.8)';
      ctx.lineWidth = 2;
      
      const rectHeight = vy1 - vy2; // PDF coordinates are flipped
      ctx.fillRect(vx1, vy2, vx2 - vx1, rectHeight);
      ctx.strokeRect(vx1, vy2, vx2 - vx1, rectHeight);
    }
  }, [selectedEvidence, currentPage, pageData]);

  // Navigate to specific page
  const goToPage = (pageNum) => {
    if (pageNum >= 1 && pageNum <= totalPages) {
      setCurrentPage(pageNum);
    }
  };

  // Navigate to evidence location
  useEffect(() => {
    if (selectedEvidence && selectedEvidence.page !== currentPage) {
      goToPage(selectedEvidence.page);
    }
  }, [selectedEvidence, currentPage]);

  return (
    <Paper sx={{ p: 2, height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* PDF Controls */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
        <IconButton onClick={() => goToPage(currentPage - 1)} disabled={currentPage <= 1}>
          <NavigateBefore />
        </IconButton>
        
        <Typography variant="body2">
          Page {currentPage} of {totalPages}
        </Typography>
        
        <IconButton onClick={() => goToPage(currentPage + 1)} disabled={currentPage >= totalPages}>
          <NavigateNext />
        </IconButton>
        
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, ml: 'auto' }}>
          <IconButton onClick={() => setScale(s => Math.max(0.5, s - 0.2))}>
            <ZoomOut />
          </IconButton>
          
          <Slider
            value={scale}
            onChange={(_, value) => setScale(value)}
            min={0.5}
            max={3}
            step={0.1}
            sx={{ width: 100 }}
          />
          
          <IconButton onClick={() => setScale(s => Math.min(3, s + 0.2))}>
            <ZoomIn />
          </IconButton>
        </Box>
      </Box>

      {/* PDF Canvas */}
      <Box sx={{ flex: 1, position: 'relative', overflow: 'auto', textAlign: 'center' }}>
        <canvas ref={canvasRef} style={{ display: 'block', margin: '0 auto' }} />
        <canvas
          ref={overlayRef}
          style={{
            position: 'absolute',
            top: 0,
            left: '50%',
            transform: 'translateX(-50%)',
            pointerEvents: 'none'
          }}
          width={canvasRef.current?.width || 0}
          height={canvasRef.current?.height || 0}
        />
      </Box>
    </Paper>
  );
};

export default PDFViewer;
```

## 4. EvidencePanel.js - Extracted Data Display

```javascript
import React from 'react';
import {
  Box, Paper, Typography, List, ListItem, ListItemButton,
  ListItemText, Chip, Badge
} from '@mui/material';
import { getConfidenceColor, formatEvidence } from '../utils/evidenceUtils';

const EvidencePanel = ({ document, selectedEvidence, onEvidenceSelect, onShowReviewQueue }) => {
  if (!document?.evidence) return null;

  const evidenceEntries = Object.entries(document.evidence);
  const lowConfidenceCount = evidenceEntries.filter(([_, ev]) => ev.confidence < 0.7).length;

  return (
    <Paper sx={{ width: 400, height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Typography variant="h6" gutterBottom>
          Extracted Evidence
        </Typography>
        
        {lowConfidenceCount > 0 && (
          <Badge badgeContent={lowConfidenceCount} color="error">
            <Chip
              label="Review Required"
              color="warning"
              size="small"
              onClick={onShowReviewQueue}
              clickable
            />
          </Badge>
        )}
      </Box>

      {/* Evidence List */}
      <Box sx={{ flex: 1, overflow: 'auto' }}>
        <List>
          {evidenceEntries.map(([key, evidence]) => (
            <ListItem key={key} disablePadding>
              <ListItemButton
                selected={selectedEvidence?.key === key}
                onClick={() => onEvidenceSelect({ ...evidence, key })}
                sx={{
                  borderLeft: 4,
                  borderLeftColor: getConfidenceColor(evidence.confidence),
                  '&.Mui-selected': {
                    bgcolor: 'action.selected',
                  }
                }}
              >
                <ListItemText
                  primary={formatEvidence(key, evidence.value)}
                  secondary={
                    <Box>
                      <Typography variant="caption" display="block">
                        Page {evidence.page} • {Math.round(evidence.confidence * 100)}% confidence
                      </Typography>
                      <Typography variant="caption" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                        "{evidence.snippet}"
                      </Typography>
                    </Box>
                  }
                />
                
                <Chip
                  label={evidence.confidence > 0.8 ? 'HIGH' : evidence.confidence > 0.6 ? 'MED' : 'LOW'}
                  size="small"
                  sx={{
                    bgcolor: getConfidenceColor(evidence.confidence),
                    color: 'white',
                    fontWeight: 'bold'
                  }}
                />
              </ListItemButton>
            </ListItem>
          ))}
        </List>
      </Box>
    </Paper>
  );
};

export default EvidencePanel;
```

## 5. HILReviewQueue.js - Human Review Interface

```javascript
import React, { useState } from 'react';
import {
  Box, Paper, Typography, List, ListItem, TextField,
  Button, ButtonGroup, Chip, Alert, Divider
} from '@mui/material';
import { Save, Image, Cancel } from '@mui/icons-material';

const HILReviewQueue = ({ document, onClose, onEvidenceUpdate }) => {
  const [reviewValues, setReviewValues] = useState({});
  const [currentReview, setCurrentReview] = useState(null);

  if (!document?.evidence) return null;

  const lowConfidenceItems = Object.entries(document.evidence)
    .filter(([_, evidence]) => evidence.confidence < 0.7)
    .map(([key, evidence]) => ({ key, ...evidence }));

  const handleAction = (item, action, value = null) => {
    const updatedEvidence = {
      ...item,
      hilAction: action,
      hilValue: value,
      reviewedAt: new Date().toISOString(),
      confidence: action === 'transcribe' ? 1.0 : item.confidence
    };

    onEvidenceUpdate?.(item.key, updatedEvidence);
    
    // Remove from review queue (in real app, this would persist to DB)
    setCurrentReview(null);
  };

  return (
    <Paper sx={{ width: 400, height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Typography variant="h6" gutterBottom>
          Review Queue
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {lowConfidenceItems.length} items need attention
        </Typography>
        <Button size="small" onClick={onClose} sx={{ mt: 1 }}>
          Close
        </Button>
      </Box>

      {/* Review Items */}
      <Box sx={{ flex: 1, overflow: 'auto' }}>
        {lowConfidenceItems.length === 0 ? (
          <Alert severity="success" sx={{ m: 2 }}>
            All items reviewed! 🎉
          </Alert>
        ) : (
          <List>
            {lowConfidenceItems.map((item) => (
              <ListItem key={item.key} sx={{ display: 'block', p: 2 }}>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle1" gutterBottom>
                    {item.key.replace(/_/g, ' ').toUpperCase()}
                  </Typography>
                  
                  <Chip
                    label={`${Math.round(item.confidence * 100)}% confidence`}
                    color="warning"
                    size="small"
                    sx={{ mb: 1 }}
                  />
                  
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Page {item.page}: "{item.snippet}"
                  </Typography>
                  
                  <Typography variant="body1" sx={{ fontWeight: 'bold', mb: 2 }}>
                    Current Value: {item.value}
                  </Typography>
                </Box>

                {/* Review Actions */}
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  {/* Transcribe Option */}
                  <Box>
                    <Typography variant="caption" display="block" gutterBottom>
                      Correct the text:
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 1 }}>
                      <TextField
                        size="small"
                        fullWidth
                        defaultValue={item.value}
                        onChange={(e) => 
                          setReviewValues(prev => ({ ...prev, [item.key]: e.target.value }))
                        }
                      />
                      <Button
                        variant="contained"
                        size="small"
                        startIcon={<Save />}
                        onClick={() => handleAction(item, 'transcribe', reviewValues[item.key] || item.value)}
                      >
                        Save
                      </Button>
                    </Box>
                  </Box>

                  {/* Action Buttons */}
                  <ButtonGroup size="small" fullWidth>
                    <Button
                      startIcon={<Image />}
                      onClick={() => handleAction(item, 'keep_as_image')}
                    >
                      Keep as Image
                    </Button>
                    <Button
                      startIcon={<Cancel />}
                      onClick={() => handleAction(item, 'ignore')}
                    >
                      Ignore
                    </Button>
                  </ButtonGroup>
                </Box>
                
                <Divider sx={{ mt: 2 }} />
              </ListItem>
            ))}
          </List>
        )}
      </Box>
    </Paper>
  );
};

export default HILReviewQueue;
```

## 6. mockData.js - Sample Evidence Data

```javascript
export const mockDocument = {
  id: "doc_001",
  filename: "sample_purchase_agreement.pdf",
  uploadedAt: new Date("2024-01-15T10:30:00Z"),
  sha256: "abc123def456...",
  evidence: {
    purchase_amount: {
      value: "$350,000",
      page: 3,
      bbox: [150, 400, 250, 420],
      confidence: 0.95,
      snippet: "total purchase price of $350,000 shall be paid by Buyer",
      extractor: "gemini_vision",
      extractedAt: "2024-01-15T10:31:00Z"
    },
    closing_date: {
      value: "December 31, 2024",
      page: 2, 
      bbox: [100, 300, 220, 315],
      confidence: 0.87,
      snippet: "closing shall occur on or before December 31, 2024",
      extractor: "gemini_vision",
      extractedAt: "2024-01-15T10:31:00Z"
    },
    buyer_name: {
      value: "John Smith",
      page: 1,
      bbox: [200, 150, 290, 170], 
      confidence: 0.65, // Low confidence - will show in HIL queue
      snippet: "Buyer: John Smith (signature unclear)",
      extractor: "gemini_vision",
      extractedAt: "2024-01-15T10:31:00Z"
    },
    seller_name: {
      value: "Jane Doe Properties LLC",
      page: 1,
      bbox: [200, 180, 350, 200],
      confidence: 0.92,
      snippet: "Seller: Jane Doe Properties LLC",
      extractor: "gemini_vision", 
      extractedAt: "2024-01-15T10:31:00Z"
    },
    property_address: {
      value: "123 Main Street, Anytown, CA 90210",
      page: 1,
      bbox: [100, 250, 400, 280],
      confidence: 0.88,
      snippet: "Property located at 123 Main Street, Anytown, CA 90210",
      extractor: "gemini_vision",
      extractedAt: "2024-01-15T10:31:00Z" 
    },
    apn: {
      value: "123-456-789",
      page: 2,
      bbox: [300, 200, 380, 215],
      confidence: 0.62, // Low confidence - will show in HIL queue
      snippet: "APN: 123-456-789 (handwritten)",
      extractor: "gemini_vision",
      extractedAt: "2024-01-15T10:31:00Z"
    }
  }
};
```

## 7. Utility Functions

```javascript
// utils/evidenceUtils.js
export const getConfidenceColor = (confidence) => {
  if (confidence >= 0.8) return '#4caf50'; // Green
  if (confidence >= 0.6) return '#ff9800'; // Orange  
  return '#f44336'; // Red
};

export const formatEvidence = (key, value) => {
  const labels = {
    purchase_amount: 'Purchase Price',
    closing_date: 'Closing Date',
    buyer_name: 'Buyer',
    seller_name: 'Seller',
    property_address: 'Property Address',
    apn: 'Assessor Parcel Number'
  };
  
  return labels[key] || key.replace(/_/g, ' ').toUpperCase();
};

// utils/pdfUtils.js  
export const convertCoordinates = (bbox, viewport) => {
  // Convert PDF coordinates to viewport coordinates
  const [x1, y1, x2, y2] = bbox;
  return viewport.convertToViewportRectangle([x1, y1, x2, y2]);
};
```

This gives you a complete, working Firebase web app that demonstrates the core evidence viewer functionality. You can build it incrementally and it will integrate seamlessly with your backend when ready!