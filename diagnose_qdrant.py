from qdrant_client import QdrantClient

def diagnose():
    try:
        client = QdrantClient(path='qdrant_test')
        print(f"Client instance: {type(client)}")
        methods = sorted([m for m in dir(client) if not m.startswith('_')])
        print("Methods available:")
        for m in methods:
            print(f"  - {m}")
        
        # Check for specific search-related terms
        search_related = [m for m in methods if 'search' in m.lower() or 'query' in m.lower()]
        print("\nSearch related methods:")
        for m in search_related:
            print(f"  - {m}")
            
    except Exception as e:
        print(f"Error during diagnosis: {e}")

if __name__ == "__main__":
    diagnose()
