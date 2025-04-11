"""
Test Installation Script

This script verifies that all required dependencies are correctly installed.
"""

import sys
import importlib.util

def check_module(module_name):
    """Check if a module is installed"""
    spec = importlib.util.find_spec(module_name)
    if spec is None:
        print(f"❌ {module_name} is NOT installed")
        return False
    else:
        try:
            module = importlib.import_module(module_name)
            version = getattr(module, "__version__", "unknown version")
            print(f"✅ {module_name} is installed ({version})")
            return True
        except ImportError:
            print(f"❌ {module_name} is installed but cannot be imported")
            return False

def check_submodule(parent_module, submodule_name):
    """Check if a submodule is available"""
    try:
        parent = importlib.import_module(parent_module)
        submodule = getattr(parent, submodule_name, None)
        if submodule is None:
            # Try to import directly
            try:
                importlib.import_module(f"{parent_module}.{submodule_name}")
                print(f"✅ {parent_module}.{submodule_name} is available")
                return True
            except ImportError:
                print(f"❌ {parent_module}.{submodule_name} is NOT available")
                return False
        else:
            print(f"✅ {parent_module}.{submodule_name} is available")
            return True
    except ImportError:
        print(f"❌ {parent_module} cannot be imported to check for {submodule_name}")
        return False

def main():
    """Main function to check all dependencies"""
    print("Testing installation of required packages:")
    print("-----------------------------------------")
    
    # Core MCP dependencies
    mcp_installed = check_module("mcp")
    
    # Check specific MCP modules
    if mcp_installed:
        print("\nChecking MCP modules:")
        client_module = check_module("mcp.client")
        server_module = check_module("mcp.server")
        client_session = check_module("mcp.client.session")
        sse_client = check_module("mcp.client.sse")
        
        # Check critical functions and classes
        from_client_session = check_submodule("mcp.client.session", "ClientSession")
        from_sse = check_submodule("mcp.client.sse", "sse_client")
        from_server = check_submodule("mcp.server", "fastmcp")
        
        # Try importing specific functions
        try:
            from mcp.client.sse import sse_client
            print("✅ sse_client function is importable")
        except ImportError:
            print("❌ sse_client function cannot be imported")
    
    # RAG dependencies
    print("\nChecking RAG dependencies:")
    st_installed = check_module("sentence_transformers")
    chromadb_installed = check_module("chromadb")
    
    # Additional dependencies
    print("\nChecking additional dependencies:")
    faiss_installed = check_module("faiss")
    
    # Server dependencies
    uvicorn_installed = check_module("uvicorn")
    
    # Python version
    print(f"\nPython version: {sys.version}")
    
    # Summary
    all_installed = all([mcp_installed, st_installed, chromadb_installed, faiss_installed, uvicorn_installed])
    
    print("\nSUMMARY:")
    if all_installed:
        print("✅ All required packages are installed! You can proceed with running the demo.")
    else:
        print("❌ Some required packages are missing. Please run: pip install -r requirements.txt")
        print("\nSuggested command for MCP: pip install mcp>=1.0.0")

if __name__ == "__main__":
    main() 