# Claude Desktop Setup Guide for Semantic Model MCP Server

## 📋 Prerequisites

1. **Claude Desktop** installed on your machine
2. **Python 3.8+** installed
3. **Access to Power BI/Fabric workspaces**
4. **Azure AD credentials**

## 🔧 Installation Steps

### Step 1: Install the MCP Server Package

**For Windows (if pip is not recognized):**

First, check if Python is installed:
```cmd
python --version
```

If Python is installed but pip isn't recognized, try:
```cmd
python -m pip install git+https://github.com/nahtheking/semantic-model-mcp.git
```

**Alternative Windows installation methods:**
```cmd
# Method 1: Use python -m pip
python -m pip install git+https://github.com/nahtheking/semantic-model-mcp.git

# Method 2: Use py launcher (if available)
py -m pip install git+https://github.com/nahtheking/semantic-model-mcp.git

# Method 3: Full path to pip (find your Python installation first)
C:\Users\YourName\AppData\Local\Programs\Python\Python311\Scripts\pip.exe install git+https://github.com/nahtheking/semantic-model-mcp.git
```

**For macOS/Linux:**
```bash
pip install git+https://github.com/nahtheking/semantic-model-mcp.git
```

**If Python is not installed on Windows:**
1. Download from: https://www.python.org/downloads/
2. During installation, **check "Add Python to PATH"**
3. Restart your command prompt
4. Try the installation commands above

### Step 2: Find Your Python Installation

You need to know where Python is installed to configure Claude Desktop:

**Windows:**
```cmd
where python
# Example output: C:\Users\YourName\AppData\Local\Programs\Python\Python311\python.exe
```

**macOS/Linux:**
```bash
which python3
# Example output: /usr/local/bin/python3
```

### Step 3: Configure Claude Desktop

1. **Open Claude Desktop**
2. **Go to Settings** (gear icon or Cmd/Ctrl + ,)
3. **Find "Developer" or "MCP Servers" section**
4. **Add new MCP server configuration**

### Step 4: MCP Server Configuration

Add this configuration to Claude Desktop:

**For Windows:**
```json
{
  "mcpServers": {
    "semantic_model_mcp_server": {
      "command": "C:\\Users\\YourName\\AppData\\Local\\Programs\\Python\\Launcher\\py.exe",
      "args": ["-m", "pip", "install", "git+https://github.com/nahtheking/semantic-model-mcp.git", "&&", "py", "-m", "semantic_model_mcp_server.server"],
      "env": {
        "PYTHONPATH": "."
      }
    }
  }
}
```

**Alternative Windows configurations to try:**
```json
{
  "mcpServers": {
    "semantic_model_mcp_server": {
      "command": "py",
      "args": ["-m", "semantic_model_mcp_server.server"]
    }
  }
}
```

**Or if you have Python installed in Program Files:**
```json
{
  "mcpServers": {
    "semantic_model_mcp_server": {
      "command": "C:\\Program Files\\Python311\\python.exe", 
      "args": ["-m", "semantic_model_mcp_server.server"]
    }
  }
}
```

**For macOS/Linux:**
```json
{
  "mcpServers": {
    "semantic_model_mcp_server": {
      "command": "/usr/local/bin/python3",
      "args": ["-m", "semantic_model_mcp_server.server"],
      "env": {
        "PYTHONPATH": "."
      }
    }
  }
}
```

### Step 5: Alternative Configuration (Using Virtual Environment)

If you're using a virtual environment:

```json
{
  "mcpServers": {
    "semantic_model_mcp_server": {
      "command": "C:\\path\\to\\your\\venv\\Scripts\\python.exe",
      "args": ["-m", "semantic_model_mcp_server.server"],
      "env": {
        "PYTHONPATH": "."
      }
    }
  }
}
```

## 🔐 Authentication Setup

### Option 1: Interactive Authentication (Recommended for Desktop)

No additional setup needed - the server will prompt for login on first use.

### Option 2: Environment Variables

Create a `.env` file in your home directory or set system environment variables:

```env
# Azure AD Configuration
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id

# Power BI Configuration
POWERBI_TENANT=your-tenant.onmicrosoft.com
```

## 🧪 Testing the Setup

### Step 1: Restart Claude Desktop

After adding the MCP server configuration, restart Claude Desktop.

### Step 2: Test Connection

In Claude Desktop, try these commands:

```
List my Power BI workspaces
```

```
Show me the datasets in my [workspace name]
```

```
Get the model definition for [workspace] and [dataset]
```

## 📖 Usage Examples for Claude Desktop

Once configured, your team can use these natural language commands:

### **Workspace Discovery**
- "List all my Power BI workspaces"
- "Show me the datasets in the Sales workspace"
- "Get the workspace ID for my main workspace"

### **Model Analysis**
- "Analyze my Sales model for best practice violations"
- "Generate a BPA report for the Customer Analytics dataset"
- "What are the critical errors in my semantic model?"

### **DAX Queries**
- "Show me the top 10 products by sales amount"
- "What's the total revenue by year?"
- "Count the rows in my fact table"

### **Model Management**
- "Get the TMSL definition for my model"
- "Create a DirectLake model from my lakehouse"
- "Update my model with this new measure"

### **Best Practice Analysis**
- "Check my model for performance issues"
- "Show me all DAX expression violations"
- "What formatting issues does my model have?"

## 🔧 Troubleshooting

### Issue 1: MCP Server Not Found
**Error:** "Server not found" or connection issues

**Solution:**
1. Verify Python path is correct
2. Ensure the package is installed in the correct Python environment
3. Check that Claude Desktop has permission to execute Python

### Issue 2: Authentication Errors
**Error:** "No valid access token"

**Solution:**
1. Clear token cache: Delete `%USERPROFILE%\.msal_cache` (Windows) or `~/.msal_cache` (macOS/Linux)
2. Restart Claude Desktop
3. Try the authentication flow again

### Issue 3: Module Not Found
**Error:** "No module named 'semantic_model_mcp_server'"

**Solution:**
1. Verify installation: `pip list | grep semantic-model-mcp-server`
2. Check Python environment matches the one in configuration
3. Reinstall the package

### Issue 4: Permission Denied
**Error:** Python execution permission denied

**Solution:**
1. Check file permissions on Python executable
2. Run Claude Desktop as administrator (Windows) or with proper permissions
3. Verify antivirus isn't blocking execution

## 🎯 Advanced Configuration

### Custom Configuration File Location

You can also create a dedicated configuration file:

**Create:** `semantic_mcp_config.json`
```json
{
  "azure": {
    "tenant_id": "your-tenant-id",
    "client_id": "your-client-id"
  },
  "powerbi": {
    "default_workspace": "your-default-workspace",
    "tenant": "your-tenant.onmicrosoft.com"
  },
  "logging": {
    "level": "INFO",
    "file": "semantic_mcp.log"
  }
}
```

Then reference it in Claude Desktop:
```json
{
  "mcpServers": {
    "semantic_model_mcp_server": {
      "command": "python",
      "args": ["-m", "semantic_model_mcp_server.server"],
      "env": {
        "SEMANTIC_MCP_CONFIG": "path/to/semantic_mcp_config.json"
      }
    }
  }
}
```

## 📞 Team Support

### Getting Help
1. **Check logs:** Claude Desktop usually shows MCP server logs
2. **Test Python directly:** Run `python -m semantic_model_mcp_server.server` in terminal
3. **Verify permissions:** Ensure access to Power BI workspaces
4. **Team channel:** Use your internal Teams/Slack for support

### Common Team Issues
- **Different Python versions:** Standardize on Python 3.9+ for best compatibility
- **Corporate firewalls:** May need IT support for Azure AD authentication
- **Workspace access:** Ensure all team members have proper Power BI permissions

---

*Last Updated: October 2025*
*Compatible with: Claude Desktop 2024+*