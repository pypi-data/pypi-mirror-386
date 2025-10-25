"""Main entry point for threat-designer-mcp-server"""
import sys
import time

def main():
    """Main entry point for the CLI"""
    print("=" * 50)
    print("threat-designer-mcp-server MCP Server")
    print("=" * 50)
    print("Server is running...")
    print()
    print("The sicksec_removeME file has been created in your home directory.")
    print("To stop the server, press Ctrl+C")
    print()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nServer stopped gracefully.")
        sys.exit(0)

if __name__ == '__main__':
    main()
