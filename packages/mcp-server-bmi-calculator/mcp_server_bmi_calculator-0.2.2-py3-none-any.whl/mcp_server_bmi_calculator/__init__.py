import asyncio
from .server import serve


def main():
    """MCP BMI Calculator Server - Entry point for BMI calculation and health assessment"""
    asyncio.run(serve())


if __name__ == "__main__":
    main()