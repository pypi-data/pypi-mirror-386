from enum import Enum
import json
from typing import Sequence

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
from pydantic import BaseModel


class BMITools(str, Enum):
    CALCULATE_BMI = "calculate_bmi"


class BMIResult(BaseModel):
    bmi: float
    category: str
    health_status: str


class BMIServer:
    def calculate_bmi(self, height: float, weight: float) -> BMIResult:
        """Calculate BMI and return health status assessment"""
        if height <= 0 or weight <= 0:
            raise ValueError("身高和体重必须为正数")
        
        # Calculate BMI
        bmi = weight / (height * height)
        
        # Determine health status
        if bmi < 18.5:
            category = "underweight"
            health_status = "体重过轻"
        elif bmi < 24:
            category = "normal"
            health_status = "体重正常"
        elif bmi < 28:
            category = "overweight"
            health_status = "超重"
        else:
            category = "obese"
            health_status = "肥胖"
        
        return BMIResult(
            bmi=round(bmi, 1),
            category=category,
            health_status=health_status
        )


async def serve() -> None:
    server = Server("mcp-bmi-calculator")
    bmi_server = BMIServer()

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """List available BMI tools."""
        return [
            Tool(
                name=BMITools.CALCULATE_BMI.value,
                description="计算身体质量指数（BMI）并返回健康状况评估",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "height": {
                            "type": "number",
                            "description": "身高（米），例如：1.75",
                        },
                        "weight": {
                            "type": "number",
                            "description": "体重（千克），例如：70",
                        }
                    },
                    "required": ["height", "weight"],
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        """Handle tool calls for BMI calculation."""
        try:
            match name:
                case BMITools.CALCULATE_BMI.value:
                    height = arguments.get("height")
                    weight = arguments.get("weight")
                    
                    if height is None or weight is None:
                        raise ValueError("Missing required arguments: height and weight")
                    
                    result = bmi_server.calculate_bmi(float(height), float(weight))
                    
                case _:
                    raise ValueError(f"Unknown tool: {name}")

            return [
                TextContent(type="text", text=json.dumps(result.model_dump(), indent=2, ensure_ascii=False))
            ]

        except Exception as e:
            raise ValueError(f"Error processing BMI calculation: {str(e)}")

    options = server.create_initialization_options()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, options)