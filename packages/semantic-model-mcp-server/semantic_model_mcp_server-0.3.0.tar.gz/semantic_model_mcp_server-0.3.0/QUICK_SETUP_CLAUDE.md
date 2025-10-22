# Quick Setup for Claude Desktop + Semantic Model MCP Server

## 🚀 **5-Minute Setup**

### **1. Install Package**

**Windows users (if pip not recognized):**
```cmd
python -m pip install git+https://github.com/nahtheking/semantic-model-mcp.git
```

**Alternative Windows methods:**
```cmd
# Try these if above doesn't work:
py -m pip install git+https://github.com/nahtheking/semantic-model-mcp.git
```

**Mac/Linux users:**
```bash
pip install git+https://github.com/nahtheking/semantic-model-mcp.git
```

### **2. Find Python Path**
```cmd
where python
```
*Copy this path - you'll need it!*

### **3. Configure Claude Desktop**

**Open Claude Desktop Settings → Add MCP Server:**

```json
{
  "mcpServers": {
    "semantic_model_mcp_server": {
      "command": "YOUR_PYTHON_PATH_HERE",
      "args": ["-m", "semantic_model_mcp_server.server"]
    }
  }
}
```

**Replace `YOUR_PYTHON_PATH_HERE` with your Python path from step 2**

### **4. Restart Claude Desktop**

### **5. Test**
Type in Claude: `"List my Power BI workspaces"`

## ✅ **Example Working Configurations**

### **Windows Example:**
```json
{
  "mcpServers": {
    "semantic_model_mcp_server": {
      "command": "C:\\Users\\John\\AppData\\Local\\Programs\\Python\\Python311\\python.exe",
      "args": ["-m", "semantic_model_mcp_server.server"]
    }
  }
}
```

### **macOS Example:**
```json
{
  "mcpServers": {
    "semantic_model_mcp_server": {
      "command": "/usr/local/bin/python3",
      "args": ["-m", "semantic_model_mcp_server.server"]
    }
  }
}
```

## 🎯 **Ready-to-Use Commands**

Once setup is complete, try these in Claude Desktop:

- `"Show me my Power BI workspaces"`
- `"Analyze my Sales model for best practices"`
- `"Run a DAX query to count rows in my fact table"`
- `"Get the top 10 products by sales amount"`
- `"Generate a BPA report for my Customer dataset"`

## 🆘 **Troubleshooting**

**❌ "Server not found"**
→ Double-check your Python path in the configuration

**❌ "Module not found"**  
→ Run: `pip list | grep semantic-model-mcp-server` to verify installation

**❌ "Authentication error"**
→ First command will prompt for Microsoft login - this is normal!

---

**Need help?** Check the full guide: `CLAUDE_DESKTOP_SETUP.md`