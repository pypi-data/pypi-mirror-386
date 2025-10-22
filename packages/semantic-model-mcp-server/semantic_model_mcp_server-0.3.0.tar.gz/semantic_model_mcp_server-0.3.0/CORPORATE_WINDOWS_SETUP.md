# Corporate Windows Setup Guide - Access Denied Issues

## 🚨 **Your Specific Issue**

Based on your error logs, you have:
- **Python 3.14** installed at: `C:\Users\HoangLeDucAnh\AppData\Local\Programs\Python\Python314\python.exe`
- **Corporate security restrictions** blocking direct executable access
- **WindowsApps Python stub** interfering with normal Python execution

## 🔧 **Step-by-Step Solution**

### Step 1: Install the MCP Server Package

Since normal `pip` commands are blocked, try these alternatives:

**Option A: Using Python module execution (Most likely to work)**
```cmd
C:\Users\HoangLeDucAnh\AppData\Local\Programs\Python\Python314\python.exe -m pip install git+https://github.com/nahtheking/semantic-model-mcp.git
```

**Option B: If Option A fails, try with user flag**
```cmd
C:\Users\HoangLeDucAnh\AppData\Local\Programs\Python\Python314\python.exe -m pip install --user git+https://github.com/nahtheking/semantic-model-mcp.git
```

**Option C: If still blocked, download and install manually**
1. Download the package manually from: https://github.com/nahtheking/semantic-model-mcp/archive/main.zip
2. Extract to a folder (e.g., `C:\temp\semantic-model-mcp-main`)
3. Install locally:
```cmd
C:\Users\HoangLeDucAnh\AppData\Local\Programs\Python\Python314\python.exe -m pip install C:\temp\semantic-model-mcp-main
```

### Step 2: Claude Desktop Configuration

Use this **exact configuration** in Claude Desktop settings:

```json
{
  "mcpServers": {
    "semantic_model_mcp_server": {
      "command": "C:\\Users\\HoangLeDucAnh\\AppData\\Local\\Programs\\Python\\Python314\\python.exe",
      "args": ["-m", "semantic_model_mcp_server.server"],
      "env": {
        "PYTHONPATH": "."
      }
    }
  }
}
```

### Step 3: Test the Installation

Before configuring Claude Desktop, test that the installation worked:

```cmd
C:\Users\HoangLeDucAnh\AppData\Local\Programs\Python\Python314\python.exe -m semantic_model_mcp_server.server --help
```

### Step 4: Corporate Environment Workarounds

If you still get "Access Denied" errors:

**Option 1: Request IT Support**
- Ask your IT team to whitelist the Python executable
- Request permission to run Python scripts from your user directory

**Option 2: Use PowerShell Execution Policy**
Try running PowerShell as Administrator and execute:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Option 3: Alternative Python Distribution**
If corporate restrictions are too strict, ask IT to install:
- **Python from Microsoft Store** (sometimes has different permissions)
- **Anaconda/Miniconda** (may have different security context)

## 🎯 **Quick Test Commands**

Before configuring Claude Desktop, verify each step works:

1. **Test Python Access:**
```cmd
C:\Users\HoangLeDucAnh\AppData\Local\Programs\Python\Python314\python.exe --version
```

2. **Test Pip Access:**
```cmd
C:\Users\HoangLeDucAnh\AppData\Local\Programs\Python\Python314\python.exe -m pip --version
```

3. **Test Package Installation:**
```cmd
C:\Users\HoangLeDucAnh\AppData\Local\Programs\Python\Python314\python.exe -m pip list | findstr semantic
```

4. **Test Module Import:**
```cmd
C:\Users\HoangLeDucAnh\AppData\Local\Programs\Python\Python314\python.exe -c "import semantic_model_mcp_server; print('Success!')"
```

## 🔐 **Corporate IT Request Template**

If you need to contact IT support, use this template:

---

**Subject:** Python Script Execution Permission Request

**Body:**
I need permission to execute Python scripts for business analysis tools. Specifically:

- **Executable:** `C:\Users\HoangLeDucAnh\AppData\Local\Programs\Python\Python314\python.exe`
- **Purpose:** Microsoft Fabric and Power BI data analysis automation
- **Business Need:** Automated semantic model analysis and best practice validation
- **Security Note:** Scripts run in user context only, no system-level access required

Current error: "Access is denied" when trying to execute Python scripts.

---

## 🚨 **Troubleshooting Your Specific Error**

Your original Claude Desktop error:
```
Python was not found; run without arguments to install from the Microsoft Store
```

**Root Cause:** Claude Desktop was using the WindowsApps Python stub instead of your real Python installation.

**Solution:** Use the full path to your actual Python executable in the Claude Desktop configuration.

## 📋 **Next Steps**

1. **Try the installation commands above**
2. **Update Claude Desktop configuration with the exact path**
3. **Test the configuration**
4. **If still blocked, contact IT with the template above**

## 🔄 **Alternative: Team Distribution**

If corporate restrictions prevent direct installation:

1. **Package the server** as a standalone executable using PyInstaller
2. **Create a shared network location** with the pre-built package
3. **Use Windows scheduled tasks** to run the server if direct execution is blocked

Let me know which approach works for your environment!

---

*Created specifically for HoangLeDucAnh's corporate Windows environment*
*Date: October 21, 2025*