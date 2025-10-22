# BMI Calculator MCP Server

A Model Context Protocol server for calculating BMI (Body Mass Index) and providing health status assessments.

## Features

- BMI calculation based on height and weight
- Health status assessment according to WHO standards
- Support for metric units (meters and kilograms)

## Installation

### Using uvx (recommended)

```bash
uvx mcp-server-bmi-calculator@latest
```

### Using pip

```bash
pip install mcp-server-bmi-calculator
```

## Usage

### With Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "bmi-calculator": {
      "command": "uvx",
      "args": ["mcp-server-bmi-calculator@latest"]
    }
  }
}
```

### With Cline

Add to your MCP settings:

```json
{
  "mcpServers": {
    "bmi-calculator": {
      "command": "uvx",
      "args": ["mcp-server-bmi-calculator@latest"]
    }
  }
}
```

## Available Tools

### calculate_bmi

Calculate Body Mass Index (BMI) and return health status assessment.

**Parameters:**
- `height` (number, required): Height in meters (e.g., 1.75)
- `weight` (number, required): Weight in kilograms (e.g., 70)

**Returns:**
- `bmi`: Calculated BMI value (rounded to 1 decimal place)
- `category`: Health category (underweight/normal/overweight/obese)
- `health_status`: Chinese description of health status

**Health Status Categories:**
- BMI < 18.5: Underweight (体重过轻)
- 18.5 ≤ BMI < 24: Normal weight (体重正常)
- 24 ≤ BMI < 28: Overweight (超重)
- BMI ≥ 28: Obese (肥胖)

**Example:**

Input:
```json
{
  "height": 1.75,
  "weight": 70
}
```

Output:
```json
{
  "bmi": 22.9,
  "category": "normal",
  "health_status": "体重正常"
}
```

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/mcp-server-bmi-calculator
cd mcp-server-bmi-calculator

# Install dependencies
pip install -e .
```

### Running locally

```bash
python -m mcp_server_bmi_calculator
```

### Building

```bash
python -m build
```

## License

MIT License - see LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.