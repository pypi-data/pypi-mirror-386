"""BMI Calculator MCP Server

A Model Context Protocol server for calculating BMI (Body Mass Index).
"""

__version__ = "0.1.11"

from .bmi_mcp_server import server_main


def main(transport, port=9982):
    """MCP BMI Calculator Server - BMI calculation functionality for MCP"""
    server_main(transport, port)


if __name__ == "__main__":
    main("stdio")
