#!/usr/bin/env python3
"""
Test the Real Estate Database Schema
Verify all components are working correctly
"""
import asyncio
import asyncpg
import json
from datetime import date

DATABASE_URL = "postgresql://agent_user:agent_password@localhost:5432/agent_orchestration"

async def test_database():
    """Test all major database functionality"""
    
    print("🔍 Testing Real Estate Database Schema...")
    
    try:
        # Connect to database
        conn = await asyncpg.connect(DATABASE_URL)
        print("✅ Database connection successful")
        
        # Test 1: Basic document retrieval
        print("\n📄 Test 1: Document Retrieval")
        documents = await conn.fetch("""
            SELECT contract_name, contract_type, effective_date 
            FROM documents 
            ORDER BY effective_date 
            LIMIT 5
        """)
        
        for doc in documents:
            print(f"  • {doc['contract_name']} ({doc['contract_type']}) - {doc['effective_date']}")
        
        # Test 2: APN-based property search  
        print("\n🏠 Test 2: Property-Based Document Search")
        property_docs = await conn.fetch("""
            SELECT d.contract_name, d.contract_type, p.apn, p.legal_description
            FROM documents d
            JOIN document_parcels dp ON dp.document_id = d.document_id
            JOIN parcels p ON p.parcel_id = dp.parcel_id
            WHERE p.apn = '045-231-008'
            ORDER BY d.effective_date
        """)
        
        print(f"  Found {len(property_docs)} documents for APN 045-231-008:")
        for doc in property_docs:
            print(f"  • {doc['contract_name']} - {doc['contract_type']}")
        
        # Test 3: Obligations tracking
        print("\n📋 Test 3: Upcoming Obligations")
        obligations = await conn.fetch("""
            SELECT o.party_name, o.obligation_type, o.due_date, o.status, d.contract_name
            FROM obligations o
            JOIN documents d ON d.document_id = o.document_id  
            WHERE o.status IN ('open', 'in_progress')
            ORDER BY o.due_date
            LIMIT 5
        """)
        
        for obl in obligations:
            print(f"  • {obl['party_name']}: {obl['obligation_type']} (Due: {obl['due_date']}) - {obl['status']}")
        
        # Test 4: Financial summary
        print("\n💰 Test 4: Financial Analytics")
        financial_summary = await conn.fetch("""
            SELECT 
                d.contract_type,
                COUNT(*) as count,
                COALESCE(SUM(ft.total_contract_value), 0) as total_value
            FROM documents d
            LEFT JOIN financial_terms ft ON ft.document_id = d.document_id
            GROUP BY d.contract_type
            HAVING COUNT(*) > 0
            ORDER BY total_value DESC
        """)
        
        total_portfolio_value = 0
        for summary in financial_summary:
            value = float(summary['total_value']) if summary['total_value'] else 0
            total_portfolio_value += value
            print(f"  • {summary['contract_type']}: {summary['count']} docs, ${value:,.2f}")
        
        print(f"\n📊 Total Portfolio Value: ${total_portfolio_value:,.2f}")
        
        # Test 5: Test your predefined queries
        print("\n🔍 Test 5: Your Predefined Query Tests")
        
        # Test find-upcoming-obligations.sql equivalent
        upcoming = await conn.fetch("""
            SELECT o.*, d.contract_name, d.contract_type
            FROM obligations o  
            JOIN documents d USING (document_id)
            WHERE o.status IN ('open','in_progress')
                AND o.due_date <= CURRENT_DATE + INTERVAL '6 months'
            ORDER BY o.due_date
        """)
        print(f"  • Upcoming obligations (6 months): {len(upcoming)} items")
        
        # Test find-recordings-by-apn.sql equivalent (simplified)
        apn_docs = await conn.fetch("""
            SELECT d.contract_name, p.apn
            FROM documents d
            JOIN document_parcels dp ON dp.document_id = d.document_id  
            JOIN parcels p ON p.parcel_id = dp.parcel_id
            WHERE p.apn = '045-231-008'
        """)
        print(f"  • Documents for APN 045-231-008: {len(apn_docs)} documents")
        
        await conn.close()
        print("\n🎉 All database tests passed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Database test failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_database())