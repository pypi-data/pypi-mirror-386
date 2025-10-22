###### **1. Service Introduction**

Provides Body Mass Index (BMI) calculation functionality to help users assess their health status.

###### **2. Key Features**

* BMI calculation
* Health status assessment

###### **3. Usage**

* Deploy the BMI Calculator service in the MCP service marketplace.

* Activate the BMI Calculator service in the MCP service marketplace.

###### (1) `calculate_bmi`

**Description**: Calculate Body Mass Index (BMI) and return health status assessment.

**Input Parameters**:\
**`height`**:\
Type: `float`\
Required: Yes\
Description: Height in meters, e.g., 1.75

**`weight`**:\
Type: `float`\
Required: Yes\
Description: Weight in kilograms, e.g., 70

**Return Value**:\
Type: `string`\
Description: A string containing the BMI value and health status assessment

**Health Status Assessment Criteria**:

* BMI < 18.5: Underweight
* 18.5 ≤ BMI < 24: Normal weight
* 24 ≤ BMI < 28: Overweight
* BMI ≥ 28: Obese

**Example**:

```text
height: 1.75
weight: 70
```

Result:
```text
BMI: 22.9
Health Status: Normal weight
```

###### **4. FAQ**

* Q: Is the BMI Calculator MCP service free to use?

* A: Yes, the BMI Calculator MCP service is open source and can be used freely under the MIT license.

* Q: What standard does the BMI calculation use?

* A: This service uses the internationally recognized BMI formula: BMI = weight(kg) / height²(m²). The health status assessment criteria are based on World Health Organization (WHO) recommendations.