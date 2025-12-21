
try:
    from cyborgdb import Client
    print(f"Methods: {[m for m in dir(Client) if not m.startswith('_')]}")
except ImportError:
    print("CyborgDB not installed")
except Exception as e:
    print(f"Error: {e}")
