import time
from tools import search_tool, reset_search_state

def test_limits():
    print("🧪 Verification Test: Testing reformulations and limits...")
    reset_search_state()
    
    # 1. First search (initial query) should succeed (or raise standard search error, not limit error)
    print("1. Running first search query 'query1'...")
    t0 = time.time()
    try:
        search_tool("query1")
    except Exception as e:
        print(f"  Got exception (expected if search fails): {e}")
        
    # 2. Second search (reformulation 1) should include a 1.5s delay
    print("2. Running second search query 'query2'...")
    try:
        search_tool("query2")
    except Exception as e:
        print(f"  Got exception: {e}")
    t1 = time.time()
    elapsed = t1 - t0
    print(f"  Elapsed time for two searches: {elapsed:.2f} seconds.")
    if elapsed >= 1.4:
        print("  ✅ Consecutive search delay verified.")
    else:
        print("  ❌ Delay not detected.")
        
    # 3. Third search (reformulation 2)
    print("3. Running third search query 'query3'...")
    try:
        search_tool("query3")
    except Exception as e:
        print(f"  Got exception: {e}")
        
    # 4. Fourth search (reformulation 3) should be capped and raise a limit RuntimeError
    print("4. Running fourth search query 'query4' (should fail due to limit)...")
    try:
        search_tool("query4")
        print("  ❌ Error: Fourth search query did not raise limit error!")
    except RuntimeError as e:
        if "Query reformulation limit reached" in str(e):
            print(f"  ✅ Correctly raised limit error: {e}")
        else:
            print(f"  ❌ Raised unexpected RuntimeError: {e}")
    except Exception as e:
        print(f"  ❌ Raised unexpected exception: {type(e).__name__}: {e}")
        
    # 5. Resetting state should allow searching again
    print("5. Resetting search state and running query4 again...")
    reset_search_state()
    try:
        search_tool("query4")
        print("  ✅ Successfully searched after reset.")
    except Exception as e:
        print(f"  Got exception (non-limit): {e}")

if __name__ == "__main__":
    test_limits()
