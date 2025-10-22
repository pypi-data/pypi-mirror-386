# Windows Setup Guide for Semantic Model MCP Server

## 🚨 **Common Windows Issues & Solutions**

### **Issue: "pip is not recognized" or "python is not recognized"**

This is very common on Windows. Here are the solutions:

## 🔧 **Solution 1: Install Python Properly**

### **Step 1: Download and Install Python**
1. Go to: https://www.python.org/downloads/
2. Download the latest Python 3.11+ version
3. **CRITICAL**: During installation, check these boxes:
   - ✅ **"Add Python to PATH"** 
   - ✅ **"Install for all users"** (if you have admin rights)

### **Step 2: Verify Installation**
Open a **NEW** Command Prompt (cmd) and test:
```cmd
python --version
pip --version
```

## 🔧 **Solution 2: If Python is Installed but pip/python not recognized**

### **Option A: Use python -m pip**
```cmd
python -m pip install git+https://github.com/nahtheking/semantic-model-mcp.git
```

### **Option B: Use the py launcher**
```cmd
py -m pip install git+https://github.com/nahtheking/semantic-model-mcp.git
```

### **Option C: Add Python to PATH manually**
1. Find your Python installation:
   - Usually: `C:\Users\YourName\AppData\Local\Programs\Python\Python311\`
   - Or: `C:\Python311\`

2. Add to PATH:
   - Press `Win + R`, type `sysdm.cpl`, press Enter
   - Click "Environment Variables"
   - Under "System Variables", find "Path", click "Edit"
   - Click "New" and add:
     - `C:\Users\YourName\AppData\Local\Programs\Python\Python311\`
     - `C:\Users\YourName\AppData\Local\Programs\Python\Python311\Scripts\`

3. Restart Command Prompt and try again

## 🔧 **Solution 3: Use Full Path to Python**

If you know where Python is installed:
```cmd
# Example - replace with your actual Python path
C:\Users\YourName\AppData\Local\Programs\Python\Python311\python.exe -m pip install git+https://github.com/nahtheking/semantic-model-mcp.git
```

## 🔧 **Solution 4: Microsoft Store Python**

If you installed Python from Microsoft Store:
```cmd
# Try these commands
python3 -m pip install git+https://github.com/nahtheking/semantic-model-mcp.git
# OR
python.exe -m pip install git+https://github.com/nahtheking/semantic-model-mcp.git
```

## 🔧 **Solution 5: Use Anaconda/Miniconda** (Recommended for Enterprise)

1. Install Anaconda from: https://www.anaconda.com/download
2. Open "Anaconda Prompt" (not regular command prompt)
3. Run:
```cmd
pip install git+https://github.com/nahtheking/semantic-model-mcp.git
```

## 🎯 **Claude Desktop Configuration for Windows**

### **Step 1: Find Your Python Executable**

Try these commands to find Python:
```cmd
where python
where py
dir C:\Users\%USERNAME%\AppData\Local\Programs\Python\*\python.exe
```

### **Step 2: Configure Claude Desktop**

Use the **full path** to python.exe in your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "semantic_model_mcp_server": {
      "command": "C:\\Users\\YourName\\AppData\\Local\\Programs\\Python\\Python311\\python.exe",
      "args": ["-m", "semantic_model_mcp_server.server"]
    }
  }
}
```

**Common Windows Python paths:**
- `C:\Users\YourName\AppData\Local\Programs\Python\Python311\python.exe`
- `C:\Python311\python.exe`
- `C:\Users\YourName\AppData\Local\Microsoft\WindowsApps\python.exe` (Microsoft Store)

### **Step 3: Alternative with Virtual Environment**

If using a virtual environment:
```json
{
  "mcpServers": {
    "semantic_model_mcp_server": {
      "command": "C:\\path\\to\\your\\venv\\Scripts\\python.exe",
      "args": ["-m", "semantic_model_mcp_server.server"]
    }
  }
}
```

## 🚨 **Troubleshooting Windows-Specific Issues**

### **Issue: Access Denied Errors**
**Cause:** Windows security or antivirus blocking execution

**Solutions:**
1. Run Command Prompt as Administrator
2. Temporarily disable antivirus
3. Add Python to antivirus exclusions
4. Check Windows Defender SmartScreen settings

### **Issue: Execution Policy Restrictions**
**Cause:** PowerShell execution policy

**Solution:**
```powershell
# Run PowerShell as Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### **Issue: Corporate Network/Firewall**
**Cause:** Company firewall blocking pip installations

**Solutions:**
1. Use company's internal PyPI server
2. Download packages manually
3. Contact IT for firewall exceptions
4. Use `--trusted-host` with pip:
```cmd
python -m pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org git+https://github.com/nahtheking/semantic-model-mcp.git
```

### **Issue: Multiple Python Versions**
**Cause:** Multiple Python installations causing conflicts

**Solution:**
1. Use specific Python version:
```cmd
py -3.11 -m pip install git+https://github.com/nahtheking/semantic-model-mcp.git
```
2. Or uninstall old Python versions

## 🎯 **Complete Working Example for Windows**

### **1. Install Python (if needed)**
- Download from python.org
- Check "Add to PATH" during installation
- Restart computer

### **2. Install the package**
```cmd
python -m pip install git+https://github.com/nahtheking/semantic-model-mcp.git
```

### **3. Find Python path**
```cmd
where python
```
Copy the output (e.g., `C:\Users\John\AppData\Local\Programs\Python\Python311\python.exe`)

### **4. Configure Claude Desktop**
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

### **5. Test**
Restart Claude Desktop and try: `"List my Power BI workspaces"`

## 📞 **Still Having Issues?**

### **Quick Diagnostics**
Run these commands and share the output:
```cmd
echo %PATH%
python --version
pip --version
python -m pip list
```

### **Emergency Alternative: Use Online Installation**
If local installation fails, you can:
1. Use GitHub Codespaces
2. Use Google Colab
3. Use Azure Cloud Shell
4. Contact IT for Python installation support

---

**Windows Setup Complete!** ✅

*This guide covers 99% of Windows Python installation issues.*