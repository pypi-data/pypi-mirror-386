# Team Installation Guide - Semantic Model MCP Server

This guide provides instructions for installing and using the Semantic Model MCP Server package within our company.

## 📦 Package Installation

### Option 1: Install from GitHub Package Registry (Recommended)

```bash
# Configure pip to use GitHub Package Registry
pip config set global.extra-index-url https://pypi.org/simple/

# Install the package
pip install semantic-model-mcp-server
```

### Option 2: Install from GitHub Repository (Development)

```bash
# Install directly from repository
pip install git+https://github.com/your-company/semantic-model-mcp-server.git

# Or install specific version/branch
pip install git+https://github.com/your-company/semantic-model-mcp-server.git@v0.3.0
```

### Option 3: Local Development Installation

```bash
# Clone the repository
git clone https://github.com/your-company/semantic-model-mcp-server.git
cd semantic-model-mcp-server

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install in development mode
pip install -e .
```

## 🔐 Authentication Setup

### Prerequisites
- Access to Microsoft Fabric/Power BI Premium workspaces
- Valid Azure AD credentials
- Appropriate permissions for semantic model access

### Environment Configuration

Create a `.env` file in your project directory:

```env
# Azure AD Configuration
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id

# Power BI Configuration  
POWERBI_TENANT=your-tenant.onmicrosoft.com

# Optional: Specific workspace access
DEFAULT_WORKSPACE=your-default-workspace-name
```

### Authentication Methods

1. **Interactive Authentication** (Recommended for development)
   - First run will prompt for login
   - Credentials cached securely

2. **Service Principal** (For automation/production)
   - Configure client ID and secret
   - Requires Azure AD app registration

## 🚀 Quick Start

### 1. Basic Usage Example

```python
from semantic_model_mcp_server import SemanticModelMCPServer

# Initialize the server
server = SemanticModelMCPServer()

# List available workspaces
workspaces = server.list_workspaces()
print(workspaces)

# Get model definition
model_def = server.get_model_definition("MyWorkspace", "MyDataset")
print(model_def)
```

### 2. VS Code Integration

1. Install the package in your Python environment
2. Configure VS Code with the MCP server settings
3. Use GitHub Copilot with the MCP server for semantic model interactions

#### VS Code Configuration

Create or update `.vscode/mcp.json`:

```json
{
    "servers": {
        "semantic_model_mcp_server": {
            "command": "python",
            "args": ["-m", "semantic_model_mcp_server.server"]
        }
    }
}
```

### 3. Command Line Usage

```bash
# Start the MCP server
semantic-model-mcp-server

# Or run as module
python -m semantic_model_mcp_server.server
```

## 🎯 Common Use Cases

### 1. Model Analysis and Best Practices

```python
# Analyze model for best practice violations
violations = server.analyze_model_bpa("MyWorkspace", "MyDataset")

# Generate comprehensive report
report = server.generate_bpa_report("MyWorkspace", "MyDataset", "detailed")

# Get performance-specific issues
perf_issues = server.get_bpa_violations_by_category("Performance")
```

### 2. DAX Query Execution

```python
# Execute DAX queries
result = server.execute_dax_query(
    workspace_name="MyWorkspace",
    dataset_name="MyDataset", 
    dax_query="EVALUATE TOPN(10, 'Sales', [SalesAmount])"
)
```

### 3. DirectLake Model Creation

```python
# Generate DirectLake model from Lakehouse
template = server.generate_directlake_tmsl_template(
    workspace_id="workspace-guid",
    lakehouse_name="MyLakehouse",
    table_names=["Sales", "Products", "Customers"],
    model_name="MyDirectLakeModel"
)

# Deploy the model
result = server.update_model_using_tmsl(
    workspace_name="MyWorkspace",
    dataset_name="MyDirectLakeModel",
    tmsl_definition=template
)
```

## 🛠️ Troubleshooting

### Common Issues

#### 1. Authentication Problems
```bash
# Clear token cache
python -c "from semantic_model_mcp_server.core.auth import clear_token_cache; clear_token_cache()"

# Re-authenticate
python -c "from semantic_model_mcp_server.core.auth import get_access_token; print(get_access_token())"
```

#### 2. Permission Errors
- Verify workspace access permissions
- Check Azure AD group membership
- Ensure Premium workspace licensing

#### 3. Connection Issues
- Verify network connectivity
- Check firewall settings
- Validate XMLA endpoint access

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

from semantic_model_mcp_server import SemanticModelMCPServer
server = SemanticModelMCPServer(debug=True)
```

## 📚 Documentation and Resources

### Internal Resources
- [Company Power BI Best Practices](./internal-powerbi-guide.md)
- [Semantic Model Standards](./model-standards.md)
- [Authentication Setup Guide](./auth-setup.md)

### External Resources
- [Microsoft Learn - Power BI](https://learn.microsoft.com/en-us/power-bi/)
- [DAX Documentation](https://learn.microsoft.com/en-us/dax/)
- [TMSL Reference](https://learn.microsoft.com/en-us/analysis-services/tmsl/)

## 🆘 Support

### Getting Help

1. **Check Documentation**: Review the README.md and examples/
2. **Search Issues**: Check GitHub issues for similar problems
3. **Team Chat**: Use our internal Teams channel #powerbi-support
4. **Create Issue**: Open a GitHub issue with detailed information

### Reporting Bugs

When reporting bugs, include:
- Package version: `pip show semantic-model-mcp-server`
- Python version: `python --version`
- Operating system
- Error messages and stack traces
- Steps to reproduce

### Feature Requests

Submit feature requests through:
- GitHub Issues with "enhancement" label
- Team feedback sessions
- Direct communication with maintainers

## 🔄 Updates and Versioning

### Checking for Updates

```bash
# Check current version
pip show semantic-model-mcp-server

# Check for available updates
pip list --outdated | findstr semantic-model-mcp-server
```

### Updating the Package

```bash
# Update to latest version
pip install --upgrade semantic-model-mcp-server

# Update to specific version
pip install semantic-model-mcp-server==0.3.1
```

### Version History

- **v0.3.0** - Initial internal release
  - Best Practice Analyzer
  - Power BI Desktop integration
  - Microsoft Learn integration
  - DirectLake support

## 🔒 Security Considerations

### Data Protection
- Never commit authentication tokens to version control
- Use environment variables for sensitive configuration
- Follow company data handling policies

### Access Control
- Package access limited to company GitHub organization
- Workspace access follows existing Power BI security model
- Regular security reviews and updates

### Compliance
- Follows company software approval process
- Regular security scanning via GitHub Actions
- Audit trail for all package usage

## 📞 Contact Information

### Package Maintainers
- **Primary**: [Your Name] - your.email@company.com
- **Secondary**: [Team Lead] - teamlead@company.com

### Team Channels
- **Teams**: #powerbi-mcp-server
- **Email**: powerbi-support@company.com
- **GitHub**: [Company GitHub Organization]/semantic-model-mcp-server

---

*Last Updated: October 2025*
*Version: 1.0*