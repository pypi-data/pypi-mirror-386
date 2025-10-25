# Katana MCP Server

Model Context Protocol (MCP) server for Katana Manufacturing ERP.

## Features

- **Inventory Management**: Check stock levels, find low stock items, search products
- **Environment-based Authentication**: Secure API key management
- **Built-in Resilience**: Automatic retries, rate limiting, and pagination
- **Type Safety**: Pydantic models for all requests and responses

## Installation

```bash
pip install katana-mcp-server
```

## Quick Start

### 1. Get Your Katana API Key

Obtain your API key from your Katana account settings.

### 2. Configure Environment

Create a `.env` file or set environment variable:

```bash
export KATANA_API_KEY=your-api-key-here
```

Or create `.env` file:

```
KATANA_API_KEY=your-api-key-here
KATANA_BASE_URL=https://api.katanamrp.com/v1  # Optional, uses default if not set
```

### 3. Use with Claude Desktop

Add to your Claude Desktop configuration (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "katana": {
      "command": "uvx",
      "args": ["katana-mcp-server"],
      "env": {
        "KATANA_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

Restart Claude Desktop, and you'll see Katana inventory tools available!

### 4. Run Standalone (Optional)

For testing or development:

```bash
export KATANA_API_KEY=your-api-key
katana-mcp-server
```

## Available Tools

### check_inventory

Check stock levels for a specific product SKU.

**Parameters**:
- `sku` (string, required): Product SKU to check

**Example Request**:
```json
{
  "sku": "WIDGET-001"
}
```

**Example Response**:
```json
{
  "sku": "WIDGET-001",
  "product_name": "Premium Widget",
  "available_stock": 150,
  "in_production": 50,
  "committed": 75
}
```

**Use Cases**:
- "What's the current stock level for SKU WIDGET-001?"
- "Check inventory for my best-selling product"
- "How much stock do we have available for order fulfillment?"

---

### list_low_stock_items

Find products below a specified stock threshold.

**Parameters**:
- `threshold` (integer, optional, default: 10): Stock level threshold
- `limit` (integer, optional, default: 50): Maximum items to return

**Example Request**:
```json
{
  "threshold": 5,
  "limit": 20
}
```

**Example Response**:
```json
{
  "items": [
    {
      "sku": "PART-123",
      "product_name": "Component A",
      "current_stock": 3,
      "threshold": 5
    },
    {
      "sku": "PART-456",
      "product_name": "Component B",
      "current_stock": 2,
      "threshold": 5
    }
  ],
  "total_count": 15
}
```

**Use Cases**:
- "Show me products with less than 10 units in stock"
- "What items need reordering?"
- "Find critical low stock items (below 5 units)"

---

### search_products

Search for products by name or SKU.

**Parameters**:
- `query` (string, required): Search term (matches name or SKU)
- `limit` (integer, optional, default: 20): Maximum results to return

**Example Request**:
```json
{
  "query": "widget",
  "limit": 10
}
```

**Example Response**:
```json
{
  "products": [
    {
      "id": 12345,
      "sku": "WIDGET-001",
      "name": "Premium Widget",
      "is_sellable": true,
      "stock_level": 150
    },
    {
      "id": 12346,
      "sku": "WIDGET-002",
      "name": "Economy Widget",
      "is_sellable": true,
      "stock_level": 200
    }
  ],
  "total_count": 2
}
```

**Use Cases**:
- "Find all products containing 'widget'"
- "Search for SKU PART-123"
- "What products do we have in the electronics category?"

## Configuration

### Environment Variables

- `KATANA_API_KEY` (required): Your Katana API key
- `KATANA_BASE_URL` (optional): API base URL (default: https://api.katanamrp.com/v1)

### Advanced Configuration

The server uses the [katana-openapi-client](https://pypi.org/project/katana-openapi-client/) library with:
- Automatic retries on rate limits (429) and server errors (5xx)
- Exponential backoff with jitter
- Transparent pagination for large result sets
- 30-second default timeout

## Troubleshooting

### "KATANA_API_KEY environment variable is required"

**Cause**: API key not set in environment.

**Solution**: Set the environment variable or add to `.env` file:
```bash
export KATANA_API_KEY=your-api-key-here
```

### "Authentication error: 401 Unauthorized"

**Cause**: Invalid or expired API key.

**Solution**: Verify your API key in Katana account settings and update the environment variable.

### Tools not showing up in Claude Desktop

**Cause**: Configuration error or server not starting.

**Solutions**:
1. Check Claude Desktop logs: `~/Library/Logs/Claude/mcp*.log`
2. Verify configuration file syntax (valid JSON)
3. Test server standalone: `katana-mcp-server` (should start without errors)
4. Restart Claude Desktop after configuration changes

### Rate limiting (429 errors)

**Cause**: Too many requests to Katana API.

**Solution**: The server automatically retries with exponential backoff. If you see persistent rate limiting, reduce request frequency.

## Development

### Install from Source

```bash
git clone https://github.com/dougborg/katana-openapi-client.git
cd katana-openapi-client/katana_mcp_server
uv sync
```

### Run Tests

```bash
# Unit tests only (no API key needed)
uv run pytest tests/ -m "not integration"

# All tests (requires KATANA_API_KEY)
export KATANA_API_KEY=your-key
uv run pytest tests/
```

### Local Development

```bash
# Run server in development mode
uv run python -m katana_mcp
```

## Version

Current version: **0.1.0-alpha1**

This is an alpha release with 3 inventory management tools. Future releases will add:
- Sales order management
- Purchase order management
- Manufacturing order management
- Custom resources and prompts

## Links

- **Documentation**: https://github.com/dougborg/katana-openapi-client
- **Issue Tracker**: https://github.com/dougborg/katana-openapi-client/issues
- **PyPI**: https://pypi.org/project/katana-mcp-server/
- **Katana API**: https://help.katanamrp.com/api/overview

## License

MIT License - see LICENSE file for details
