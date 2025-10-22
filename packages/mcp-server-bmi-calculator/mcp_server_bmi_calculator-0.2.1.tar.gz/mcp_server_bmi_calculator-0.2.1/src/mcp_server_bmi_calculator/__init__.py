from .server import serve


def main():
    """MCP BMI Calculator Server - BMI calculation functionality for MCP"""
    import asyncio
    
    asyncio.run(serve())


if __name__ == "__main__":
    main()