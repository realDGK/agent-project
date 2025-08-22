#!/usr/bin/env python3
"""
MCP Database Connection Smoke Test
Tests connectivity to all 4 databases (PostgreSQL, Neo4j, Qdrant, Redis)
"""

import os
import sys
import time
from typing import Dict, Tuple
from dotenv import load_dotenv

def test_postgres() -> Tuple[bool, str]:
    """Test PostgreSQL connection"""
    try:
        import psycopg2
        
        conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            port=int(os.getenv('POSTGRES_PORT', 5432)),
            database=os.getenv('POSTGRES_DB', 'contracts'),
            user=os.getenv('POSTGRES_USER', 'app'),
            password=os.getenv('POSTGRES_PASSWORD', 'changeme')
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        
        return True, f"PostgreSQL connected: {version.split(',')[0]}"
    except ImportError:
        return False, "psycopg2 not installed (pip install psycopg2-binary)"
    except Exception as e:
        return False, f"PostgreSQL connection failed: {str(e)}"

def test_neo4j() -> Tuple[bool, str]:
    """Test Neo4j connection"""
    try:
        from neo4j import GraphDatabase
        
        uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
        user = os.getenv('NEO4J_USER', 'neo4j')
        password = os.getenv('NEO4J_PASSWORD', 'changeme')
        
        driver = GraphDatabase.driver(uri, auth=(user, password))
        
        with driver.session() as session:
            result = session.run("RETURN 1 as test")
            value = result.single()['test']
            if value != 1:
                raise Exception("Test query failed")
        
        driver.close()
        return True, f"Neo4j connected to {uri}"
    except ImportError:
        return False, "neo4j not installed (pip install neo4j)"
    except Exception as e:
        return False, f"Neo4j connection failed: {str(e)}"

def test_qdrant() -> Tuple[bool, str]:
    """Test Qdrant connection"""
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.http.exceptions import UnexpectedResponse
        
        host = os.getenv('QDRANT_URL', 'http://localhost:6333').replace('http://', '').replace('https://', '')
        if ':' in host:
            host, port = host.split(':')
            port = int(port)
        else:
            port = 6333
        
        client = QdrantClient(host=host, port=port)
        
        # Test connection by getting collections
        collections = client.get_collections()
        collection_count = len(collections.collections) if collections else 0
        
        return True, f"Qdrant connected: {collection_count} collections found"
    except ImportError:
        return False, "qdrant-client not installed (pip install qdrant-client)"
    except Exception as e:
        return False, f"Qdrant connection failed: {str(e)}"

def test_redis() -> Tuple[bool, str]:
    """Test Redis connection"""
    try:
        import redis
        
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        
        # Parse Redis URL
        if redis_url.startswith('redis://'):
            redis_url = redis_url[8:]
        
        if '@' in redis_url:
            auth, host_port = redis_url.split('@')
            password = auth.split(':')[1] if ':' in auth else None
        else:
            host_port = redis_url
            password = os.getenv('REDIS_PASSWORD', None)
        
        if '/' in host_port:
            host_port, db = host_port.split('/')
            db = int(db)
        else:
            db = 0
        
        if ':' in host_port:
            host, port = host_port.split(':')
            port = int(port)
        else:
            host = host_port
            port = 6379
        
        r = redis.Redis(host=host, port=port, db=db, password=password, decode_responses=True)
        
        # Test connection
        r.ping()
        info = r.info('server')
        version = info.get('redis_version', 'unknown')
        
        return True, f"Redis connected: version {version}"
    except ImportError:
        return False, "redis not installed (pip install redis)"
    except Exception as e:
        return False, f"Redis connection failed: {str(e)}"

def run_smoke_test():
    """Run all database connection tests"""
    print("=" * 60)
    print("MCP Database Connection Smoke Test")
    print("=" * 60)
    
    # Load environment variables
    env_files = ['.env', '.env.mcp']
    for env_file in env_files:
        if os.path.exists(env_file):
            load_dotenv(env_file)
            print(f"Loaded environment from: {env_file}")
    
    print()
    
    # Define tests
    tests = {
        'PostgreSQL': test_postgres,
        'Neo4j': test_neo4j,
        'Qdrant': test_qdrant,
        'Redis': test_redis
    }
    
    results = {}
    all_passed = True
    
    # Run each test
    for name, test_func in tests.items():
        print(f"Testing {name}...", end=" ")
        sys.stdout.flush()
        
        start_time = time.time()
        success, message = test_func()
        elapsed = time.time() - start_time
        
        results[name] = {
            'success': success,
            'message': message,
            'time': elapsed
        }
        
        if success:
            print(f"✅ ({elapsed:.2f}s)")
        else:
            print(f"❌ ({elapsed:.2f}s)")
            all_passed = False
    
    # Print summary
    print("\n" + "=" * 60)
    print("Test Results:")
    print("=" * 60)
    
    for name, result in results.items():
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        print(f"{name:12} {status:8} - {result['message']}")
    
    print("\n" + "=" * 60)
    
    if all_passed:
        print("✅ All database connections successful!")
        return 0
    else:
        print("❌ Some database connections failed. Please check your configuration.")
        print("\nTroubleshooting:")
        print("1. Ensure all databases are running: ./deploy-multi-db.sh status")
        print("2. Check your .env.mcp file has correct credentials")
        print("3. Verify network connectivity to database containers")
        return 1

if __name__ == "__main__":
    sys.exit(run_smoke_test())