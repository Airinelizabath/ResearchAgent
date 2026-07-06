from tools import search_tool, read_page_tool

def test_flow():
    print("🧪 Running Search Tool Test...")
    query = "image similarity metrics"
    results = search_tool(query)
    
    if not results:
        print("❌ Search tool returned no results.")
        return
        
    if "error" in results[0]:
        print(f"❌ Search tool failed with error: {results[0]['error']}")
        return
        
    print(f"✅ Search tool succeeded. Found {len(results)} results:")
    for idx, r in enumerate(results):
        print(f"  [{idx+1}] {r['title']} - {r['url']}")
        
    # Test reading page
    target_url = results[0]["url"]
    print(f"\n🧪 Running Read Page Tool Test on: {target_url}...")
    content = read_page_tool(target_url)
    
    if content.startswith("Error"):
        print(f"❌ Read page tool failed: {content}")
    else:
        print(f"✅ Read page tool succeeded. Extracted {len(content)} characters.")
        print("\n--- Content Preview (first 300 chars) ---")
        print(content[:300])
        print("-----------------------------------------")

if __name__ == "__main__":
    test_flow()
