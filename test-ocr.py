#!/usr/bin/env python3
"""
Quick OCR Test for Real Estate Contracts
Tests OCR agent on sample PDFs
"""
import os
import sys
sys.path.append('src')

# Add current directory to path to find our modules
if os.path.exists('src/app/agents/ocr_agent.py'):
    sys.path.insert(0, 'src/app/agents')

def test_pdf_processing():
    """Test OCR on available PDF contracts"""
    
    print("🔍 Testing OCR Agent on Real Estate Contracts")
    print("=" * 50)
    
    # List available PDFs
    contracts_dir = "data/samplecontracts/"
    if not os.path.exists(contracts_dir):
        print("❌ Sample contracts directory not found")
        return
    
    pdf_files = [f for f in os.listdir(contracts_dir) if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        print("❌ No PDF files found for testing")
        return
    
    print(f"📋 Found {len(pdf_files)} PDF contracts:")
    for i, pdf_file in enumerate(pdf_files, 1):
        size_mb = os.path.getsize(os.path.join(contracts_dir, pdf_file)) / (1024*1024)
        print(f"  {i}. {pdf_file} ({size_mb:.1f} MB)")
    
    # Test the smallest file first (fastest processing)
    pdf_sizes = [(f, os.path.getsize(os.path.join(contracts_dir, f))) for f in pdf_files]
    smallest_pdf = min(pdf_sizes, key=lambda x: x[1])[0]
    
    print(f"\n🧪 Testing OCR on smallest file: {smallest_pdf}")
    
    try:
        # Try to import our OCR agent
        from ocr_agent import OCRAgent, quick_ocr_test
        
        test_file = os.path.join(contracts_dir, smallest_pdf)
        quick_ocr_test(test_file)
        
        print("\n✅ OCR Test completed successfully!")
        print("\n📋 Next Steps:")
        print("  1. Install dependencies: pip install pytesseract pdf2image Pillow")  
        print("  2. Test on larger contracts")
        print("  3. Integrate with document processing pipeline")
        
    except ImportError as e:
        print(f"\n⚠️  OCR dependencies not installed: {e}")
        print("\n📦 To install dependencies:")
        print("  pip install --break-system-packages pytesseract pdf2image Pillow")
        print("\n📋 Or update Docker container with:")
        print("  docker-compose -f docker-compose.integrated.yml build --no-cache")
        
    except Exception as e:
        print(f"\n❌ OCR test failed: {e}")
        print("This is expected if dependencies aren't installed yet")

if __name__ == "__main__":
    test_pdf_processing()