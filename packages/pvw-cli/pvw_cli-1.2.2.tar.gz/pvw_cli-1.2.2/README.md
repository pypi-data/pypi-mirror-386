# PURVIEW CLI v1.2.1 - Microsoft Purview Automation & Data Governance

> **LATEST UPDATE (October 2025):**
> - **� NEW: Bulk Term Import/Export** - Import multiple terms from CSV/JSON with dry-run support
> - **🗑️ NEW: Bulk Delete Scripts** - PowerShell and Python scripts for bulk term deletion
> - **📊 NEW: Multiple Output Formats** - `--output` flag supports table, json, and jsonc formats
> - **🔧 NEW: PowerShell Integration** - Plain JSON output works with `ConvertFrom-Json`
> - **🚀 Complete Data Product CRUD** - Full update and delete support with smart partial updates
> - **🏥 Health Monitoring API** - Automated governance health checks and recommendations
> - **🔄 Workflow Management** - Approval workflows and business process automation
> - **🚀 Complete Microsoft Purview Unified Catalog (UC)** - Full governance domains, glossary terms, data products, OKRs, and CDEs

---

## What is PVW CLI?

**PVW CLI v1.2.1** is a modern, full-featured command-line interface and Python library for Microsoft Purview. It enables automation and management of *all major Purview APIs* including:

- **Unified Catalog (UC) Management** - Complete governance domains, glossary terms, data products, OKRs, CDEs
- **Bulk Operations** - Import/export terms from CSV/JSON, bulk delete scripts with progress tracking
- **Scriptable Output** - Multiple output formats (table, json, jsonc) for PowerShell/bash automation
- Entity management (create, update, bulk, import/export)
- Glossary and term management
- Lineage operations
- Collection and account management
- Advanced search and discovery
- Data product management (legacy compatibility)
- Classification, label, and status management

The CLI is designed for data engineers, stewards, architects, and platform teams to automate, scale, and enhance their Microsoft Purview experience.

---

## Getting Started 

Follow this short flow to get PVW CLI installed and running quickly.

1. Install (from PyPI):

  ```bash
  pip install pvw-cli
  ```

  For the bleeding edge or development:

  ```bash
  pip install git+https://github.com/Keayoub/Purview_cli.git
  # or for editable development
  git clone https://github.com/Keayoub/Purview_cli.git
  cd Purview_cli
  pip install -r requirements.txt
  pip install -e .
  ```

2. Set required environment variables (examples for cmd, PowerShell, and pwsh)

  Windows cmd (example):

  ```cmd
  set PURVIEW_ACCOUNT_NAME=your-purview-account
  set PURVIEW_ACCOUNT_ID=your-purview-account-id-guid
  set PURVIEW_RESOURCE_GROUP=your-resource-group-name
  set AZURE_REGION=  # optional
  ```

  PowerShell (Windows PowerShell):

  ```powershell
  $env:PURVIEW_ACCOUNT_NAME = "your-purview-account"
  $env:PURVIEW_ACCOUNT_ID = "your-purview-account-id-guid"
  $env:PURVIEW_RESOURCE_GROUP = "your-resource-group-name"
  $env:AZURE_REGION = ""  # optional
  ```

  pwsh (PowerShell Core - cross-platform, recommended):

  ```pwsh
  $env:PURVIEW_ACCOUNT_NAME = 'your-purview-account'
  $env:PURVIEW_ACCOUNT_ID = 'your-purview-account-id-guid'
  $env:PURVIEW_RESOURCE_GROUP = 'your-resource-group-name'
  $env:AZURE_REGION = ''  # optional
  ```

3. Authenticate

  - Run `az login` (recommended), or
  - Provide Service Principal credentials via environment variables.

4. Try a few commands:

  ```bash
  # List governance domains
  pvw uc domain list

  # Search
  pvw search query --keywords="customer" --limit=5

  # Get help
  pvw --help
  pvw uc --help
  ```

For more advanced usage, see the documentation in `doc/` or the project docs: https://pvw-cli.readthedocs.io/

---

## Overview

**PVW CLI v1.2.1** is a modern command-line interface and Python library for Microsoft Purview, enabling:

- Advanced data catalog search and discovery
- Bulk import/export of entities, glossary terms, and lineage
- Real-time monitoring and analytics
- Automated governance and compliance
- Extensible plugin system

---

## Installation

You can install PVW CLI in two ways:

1. **From PyPI (recommended for most users):**

   ```bash
   pip install pvw-cli
   ```

2. **Directly from the GitHub repository (for latest/dev version):**

   ```bash
   pip install git+https://github.com/Keayoub/Purview_cli.git
   ```

Or for development (editable install):

```bash
git clone https://github.com/Keayoub/Purview_cli.git
cd Purview_cli
pip install -r requirements.txt
pip install -e .
```

---

## Requirements

- Python 3.8+
- Azure CLI (`az login`) or Service Principal credentials
- Microsoft Purview account

---

## Getting Started

1. **Install**

   ```bash
   pip install pvw-cli
   ```

2. **Set Required Environment Variables**

   ```bash
   # Required for Purview API access
   set PURVIEW_ACCOUNT_NAME=your-purview-account
   set PURVIEW_ACCOUNT_ID=your-purview-account-id-guid
   set PURVIEW_RESOURCE_GROUP=your-resource-group-name
   
   # Optional
   set AZURE_REGION=  # (optional, e.g. 'china', 'usgov')
   ```

3. **Authenticate**

   - Azure CLI: `az login`

   - Or set Service Principal credentials as environment variables

4. **Run a Command**

   ```bash
   pvw search query --keywords="customer" --limit=5
   ```

5. **See All Commands**

   ```bash
   pvw --help
   ```

---

## Authentication

PVW CLI supports multiple authentication methods for connecting to Microsoft Purview, powered by Azure Identity's `DefaultAzureCredential`. This allows you to use the CLI securely in local development, CI/CD, and production environments.

### 1. Azure CLI Authentication (Recommended for Interactive Use)

- Run `az login` to authenticate interactively with your Azure account.
- The CLI will automatically use your Azure CLI credentials.

### 2. Service Principal Authentication (Recommended for Automation/CI/CD)

Set the following environment variables before running any PVW CLI command:

- `AZURE_CLIENT_ID` (your Azure AD app registration/client ID)
- `AZURE_TENANT_ID` (your Azure AD tenant ID)
- `AZURE_CLIENT_SECRET` (your client secret)

**Example (Windows):**

```cmd
set AZURE_CLIENT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
set AZURE_TENANT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
set AZURE_CLIENT_SECRET=your-client-secret
```

**Example (Linux/macOS):**

```bash
export AZURE_CLIENT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
export AZURE_TENANT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
export AZURE_CLIENT_SECRET=your-client-secret
```

### 3. Managed Identity (for Azure VMs, App Services, etc.)

If running in Azure with a managed identity, no extra configuration is needed. The CLI will use the managed identity automatically.

### 4. Visual Studio/VS Code Authentication

If you are signed in to Azure in Visual Studio or VS Code, `DefaultAzureCredential` can use those credentials as a fallback.

---

**Note:**
- The CLI will try all supported authentication methods in order. The first one that works will be used.
- For most automation and CI/CD scenarios, service principal authentication is recommended.
- For local development, Azure CLI authentication is easiest.

For more details, see the [Azure Identity documentation](https://learn.microsoft.com/en-us/python/api/overview/azure/identity-readme?view=azure-python).

---

## Output Formats & Scripting Integration

PVW CLI supports multiple output formats to fit different use cases - from human-readable tables to machine-parseable JSON.

### Output Format Options

All `list` commands now support the `--output` parameter with three formats:

1. **`table`** (default) - Rich formatted table with colors for human viewing
2. **`json`** - Plain JSON for scripting with PowerShell, bash, jq, etc.
3. **`jsonc`** - Colored JSON with syntax highlighting for viewing

### PowerShell Integration

The `--output json` format produces plain JSON that works perfectly with PowerShell's `ConvertFrom-Json`:

```powershell
# Get all terms as PowerShell objects
$domainId = "59ae27b5-40bc-4c90-abfe-fe1a0638fe3a"
$terms = py -m purviewcli uc term list --domain-id $domainId --output json | ConvertFrom-Json

# Access properties
Write-Host "Found $($terms.Count) terms"
foreach ($term in $terms) {
    Write-Host "  • $($term.name) - $($term.status)"
}

# Filter and export
$draftTerms = $terms | Where-Object { $_.status -eq "Draft" }
$draftTerms | Export-Csv -Path "draft_terms.csv" -NoTypeInformation

# Group by status
$terms | Group-Object status | Format-Table Count, Name
```

### Bash/Linux Integration

Use `jq` for JSON processing in bash:

```bash
# Get domain ID
DOMAIN_ID="59ae27b5-40bc-4c90-abfe-fe1a0638fe3a"

# Get term names only
pvw uc term list --domain-id $DOMAIN_ID --output json | jq -r '.[] | .name'

# Count terms
pvw uc term list --domain-id $DOMAIN_ID --output json | jq 'length'

# Filter by status
pvw uc term list --domain-id $DOMAIN_ID --output json | jq '.[] | select(.status == "Draft")'

# Group by status
pvw uc term list --domain-id $DOMAIN_ID --output json | jq 'group_by(.status) | map({status: .[0].status, count: length})'

# Save to file
pvw uc term list --domain-id $DOMAIN_ID --output json > terms.json
```

### Examples by Command

```bash
# Domains
pvw uc domain list --output json | jq '.[] | .name'

# Terms  
pvw uc term list --domain-id "abc-123" --output json
pvw uc term list --domain-id "abc-123" --output table   # Default
pvw uc term list --domain-id "abc-123" --output jsonc   # Colored for viewing

# Data Products
pvw uc dataproduct list --domain-id "abc-123" --output json
```

### Migration from Old --json Flag

**Old (deprecated):**
```bash
pvw uc term list --domain-id "abc-123" --json
```

**New (recommended):**
```bash
pvw uc term list --domain-id "abc-123" --output json    # Plain JSON for scripting
pvw uc term list --domain-id "abc-123" --output jsonc   # Colored JSON (old behavior)
```

---

## Required Purview Configuration

Before using PVW CLI, you need to set three essential environment variables. Here's how to find them:

### 🔍 **How to Find Your Purview Values**

#### **1. PURVIEW_ACCOUNT_NAME**
- This is your Purview account name as it appears in Azure Portal
- Example: `kaydemopurview`

#### **2. PURVIEW_ACCOUNT_ID** 
- This is the GUID that identifies your Purview account for Unified Catalog APIs
- **✅ Important: For most Purview deployments, this is your Azure Tenant ID**

- **Method 1 - Get your Tenant ID (recommended):**
  
  **Bash/Command Prompt:**
  ```bash
  az account show --query tenantId -o tsv
  ```
  
  **PowerShell:**
  ```powershell
  az account show --query tenantId -o tsv
  # Or store directly in environment variable:
  $env:PURVIEW_ACCOUNT_ID = az account show --query tenantId -o tsv
  ```

- **Method 2 - Azure CLI (extract from Atlas endpoint):**
  ```bash
  az purview account show --name YOUR_ACCOUNT_NAME --resource-group YOUR_RG --query endpoints.catalog -o tsv
  ```
  Extract the GUID from the URL (before `-api.purview-service.microsoft.com`)

- **Method 3 - Azure Portal:**
  1. Go to your Purview account in Azure Portal
  2. Navigate to Properties → Atlas endpoint URL
  3. Extract GUID from: `https://GUID-api.purview-service.microsoft.com/catalog`

#### **3. PURVIEW_RESOURCE_GROUP**
- The Azure resource group containing your Purview account
- Example: `fabric-artifacts`

### 📋 **Setting the Variables**

**Windows Command Prompt:**
```cmd
set PURVIEW_ACCOUNT_NAME=your-purview-account
set PURVIEW_ACCOUNT_ID=your-purview-account-id
set PURVIEW_RESOURCE_GROUP=your-resource-group
```

**Windows PowerShell:**
```powershell
$env:PURVIEW_ACCOUNT_NAME="your-purview-account"
$env:PURVIEW_ACCOUNT_ID="your-purview-account-id" 
$env:PURVIEW_RESOURCE_GROUP="your-resource-group"
```

**Linux/macOS:**
```bash
export PURVIEW_ACCOUNT_NAME=your-purview-account
export PURVIEW_ACCOUNT_ID=your-purview-account-id
export PURVIEW_RESOURCE_GROUP=your-resource-group
```

**Permanent (Windows Command Prompt):**
```cmd
setx PURVIEW_ACCOUNT_NAME "your-purview-account"
setx PURVIEW_ACCOUNT_ID "your-purview-account-id"
setx PURVIEW_RESOURCE_GROUP "your-resource-group"
```

**Permanent (Windows PowerShell):**
```powershell
[Environment]::SetEnvironmentVariable("PURVIEW_ACCOUNT_NAME", "your-purview-account", "User")
[Environment]::SetEnvironmentVariable("PURVIEW_ACCOUNT_ID", "your-purview-account-id", "User")
[Environment]::SetEnvironmentVariable("PURVIEW_RESOURCE_GROUP", "your-resource-group", "User")
```

### 🔧 **Debug Environment Issues**

If you experience issues with environment variables between different terminals, use these debug commands:

**Command Prompt/Bash:**
```bash
# Run this to check your current environment
python -c "
import os
print('PURVIEW_ACCOUNT_NAME:', os.getenv('PURVIEW_ACCOUNT_NAME'))
print('PURVIEW_ACCOUNT_ID:', os.getenv('PURVIEW_ACCOUNT_ID'))
print('PURVIEW_RESOURCE_GROUP:', os.getenv('PURVIEW_RESOURCE_GROUP'))
"
```

**PowerShell:**
```powershell
# Check environment variables in PowerShell
python -c "
import os
print('PURVIEW_ACCOUNT_NAME:', os.getenv('PURVIEW_ACCOUNT_NAME'))
print('PURVIEW_ACCOUNT_ID:', os.getenv('PURVIEW_ACCOUNT_ID'))
print('PURVIEW_RESOURCE_GROUP:', os.getenv('PURVIEW_RESOURCE_GROUP'))
"

# Or use PowerShell native commands
Write-Host "PURVIEW_ACCOUNT_NAME: $env:PURVIEW_ACCOUNT_NAME"
Write-Host "PURVIEW_ACCOUNT_ID: $env:PURVIEW_ACCOUNT_ID" 
Write-Host "PURVIEW_RESOURCE_GROUP: $env:PURVIEW_RESOURCE_GROUP"
```

---

## Search Command (Discovery Query API)

The PVW CLI provides advanced search using the latest Microsoft Purview Discovery Query API:

- Search for assets, tables, files, and more with flexible filters
- Use autocomplete and suggestion endpoints
- Perform faceted, time-based, and entity-type-specific queries

### CLI Usage Examples

#### 🎯 **Multiple Output Formats**

```bash
# 1. Table Format (Default) - Quick overview
pvw search query --keywords="customer" --limit=5
# → Clean table with Name, Type, Collection, Classifications, Qualified Name

# 2. Detailed Format - Human-readable with all metadata  
pvw search query --keywords="customer" --limit=5 --detailed
# → Rich panels showing full details, timestamps, search scores

# 3. JSON Format - Complete technical details with syntax highlighting (WELL-FORMATTED)
pvw search query --keywords="customer" --limit=5 --json
# → Full JSON response with indentation, line numbers and color coding

# 4. Table with IDs - For entity operations
pvw search query --keywords="customer" --limit=5 --show-ids
# → Table format + entity GUIDs for copy/paste into update commands
```

#### 🔍 **Search Operations**

```bash
# Basic search for assets with keyword 'customer'
pvw search query --keywords="customer" --limit=5

# Advanced search with classification filter
pvw search query --keywords="sales" --classification="PII" --objectType="Tables" --limit=10

# Pagination through large result sets
pvw search query --keywords="SQL" --offset=10 --limit=5

# Autocomplete suggestions for partial keyword
pvw search autocomplete --keywords="ord" --limit=3

# Get search suggestions (fuzzy matching)
pvw search suggest --keywords="prod" --limit=2

**⚠️ IMPORTANT - Command Line Quoting:**
```cmd
# ✅ CORRECT - Use quotes around keywords
pvw search query --keywords="customer" --limit=5

# ✅ CORRECT - For wildcard searches, use quotes
pvw search query --keywords="*" --limit=5

# ❌ WRONG - Don't use unquoted * (shell expands to file names)
pvw search query --keywords=* --limit=5
# This causes: "Error: Got unexpected extra arguments (dist doc ...)"
```

```bash
# Faceted search with aggregation
pvw search query --keywords="finance" --facetFields="objectType,classification" --limit=5

# Browse entities by type and path
pvw search browse --entityType="Tables" --path="/root/finance" --limit=2

# Time-based search for assets created after a date
pvw search query --keywords="audit" --createdAfter="2024-01-01" --limit=1

# Entity type specific search
pvw search query --keywords="finance" --entityTypes="Files,Tables" --limit=2
```

#### 💡 **Usage Scenarios**

- **Daily browsing**: Use default table format for quick scans
- **Understanding assets**: Use `--detailed` for rich information panels  
- **Technical work**: Use `--json` for complete API data access
- **Entity operations**: Use `--show-ids` to get GUIDs for updates

### Python Usage Example

```python
from purviewcli.client._search import Search

search = Search()
args = {"--keywords": "customer", "--limit": 5}
search.searchQuery(args)
print(search.payload)  # Shows the constructed search payload
```

### Test Examples

See `tests/test_search_examples.py` for ready-to-run pytest examples covering all search scenarios:

- Basic query
- Advanced filter
- Autocomplete
- Suggest
- Faceted search
- Browse
- Time-based search
- Entity type search

---

## Unified Catalog Management (NEW)

PVW CLI now includes comprehensive **Microsoft Purview Unified Catalog (UC)** support with the new `uc` command group. This provides complete management of modern data governance features including governance domains, glossary terms, data products, objectives (OKRs), and critical data elements.

**🎯 Feature Parity**: Full compatibility with [UnifiedCatalogPy](https://github.com/olafwrieden/unifiedcatalogpy) functionality.

See [`doc/commands/unified-catalog.md`](doc/commands/unified-catalog.md) for complete documentation and examples.

### Quick UC Examples

#### 🏛️ **Governance Domains Management**

```bash
# List all governance domains
pvw uc domain list

# Create a new governance domain
pvw uc domain create --name "Finance" --description "Financial data governance domain"

# Get domain details
pvw uc domain get --domain-id "abc-123-def-456"

# Update domain information
pvw uc domain update --domain-id "abc-123" --description "Updated financial governance"
```

#### 📖 **Glossary Terms in UC**

```bash
# List all terms in a domain
pvw uc term list --domain-id "abc-123"
pvw uc term list --domain-id "abc-123" --output json    # Plain JSON for scripting
pvw uc term list --domain-id "abc-123" --output jsonc   # Colored JSON for viewing

# Create a single glossary term
pvw uc term create --name "Customer" --domain-id "abc-123" --description "A person or entity that purchases products"

# Get term details
pvw uc term show --term-id "term-456"

# Update term
pvw uc term update --term-id "term-456" --description "Updated description"

# Delete term
pvw uc term delete --term-id "term-456" --confirm
```

**📦 Bulk Import (NEW)**

Import multiple terms from CSV or JSON files with validation and progress tracking:

```bash
# CSV Import - Preview with dry-run
pvw uc term import-csv --csv-file "samples/csv/uc_terms_bulk_example.csv" --domain-id "abc-123" --dry-run

# CSV Import - Actual import
pvw uc term import-csv --csv-file "samples/csv/uc_terms_bulk_example.csv" --domain-id "abc-123"

# JSON Import - Preview with dry-run
pvw uc term import-json --json-file "samples/json/term/uc_terms_bulk_example.json" --dry-run

# JSON Import - Actual import (domain_id from JSON or override with flag)
pvw uc term import-json --json-file "samples/json/term/uc_terms_bulk_example.json"
pvw uc term import-json --json-file "samples/json/term/uc_terms_bulk_example.json" --domain-id "abc-123"
```

**Bulk Import Features:**
- ✅ Import from CSV or JSON files
- ✅ Dry-run mode to preview before importing
- ✅ Support for multiple owners (Entra ID Object IDs), acronyms, and resources
- ✅ Progress tracking with Rich console output
- ✅ Detailed error messages and summary reports
- ✅ Sequential POST requests (no native bulk endpoint available)

**CSV Format Example:**
```csv
name,description,status,acronym,owner_id,resource_name,resource_url
Customer Acquisition Cost,Cost to acquire new customer,Draft,CAC,<guid>,Metrics Guide,https://docs.example.com
Monthly Recurring Revenue,Predictable monthly revenue,Draft,MRR,<guid>,Finance Dashboard,https://finance.example.com
```

**JSON Format Example:**
```json
{
  "terms": [
    {
      "name": "Data Lake",
      "description": "Centralized repository for structured/unstructured data",
      "domain_id": "your-domain-id-here",
      "status": "Draft",
      "acronyms": ["DL"],
      "owner_ids": ["<entra-id-object-id-guid>"],
      "resources": [{"name": "Architecture Guide", "url": "https://example.com"}]
    }
  ]
}
```

**Important Notes:**
- ⚠️ **Owner IDs must be Entra ID Object IDs (GUIDs)**, not email addresses
- ⚠️ **Terms cannot be "Published" in unpublished domains** - use "Draft" status
- ✅ Sample files available: `samples/csv/uc_terms_bulk_example.csv`, `samples/json/term/uc_terms_bulk_example.json`
- 📖 Complete documentation: [`doc/commands/unified-catalog/term-bulk-import.md`](doc/commands/unified-catalog/term-bulk-import.md)

**🗑️ Bulk Delete (NEW)**

Delete all terms in a domain using PowerShell or Python scripts:

```powershell
# PowerShell - Delete all terms with confirmation
.\scripts\delete-all-uc-terms.ps1 -DomainId "abc-123"

# PowerShell - Delete without confirmation
.\scripts\delete-all-uc-terms.ps1 -DomainId "abc-123" -Force
```

```bash
# Python - Delete all terms with confirmation
python scripts/delete_all_uc_terms_v2.py --domain-id "abc-123"

# Python - Delete without confirmation
python scripts/delete_all_uc_terms_v2.py --domain-id "abc-123" --force
```

**Bulk Delete Features:**
- ✅ Interactive confirmation prompts (type "DELETE" to confirm)
- ✅ Beautiful progress display with colors
- ✅ Success/failure tracking per term
- ✅ Detailed summary reports
- ✅ Rate limiting (200ms delay between deletes)
- ✅ Graceful error handling and Ctrl+C support

#### 📦 **Data Products Management**

```bash
# List all data products in a domain
pvw uc dataproduct list --domain-id "abc-123"

# Create a comprehensive data product
pvw uc dataproduct create \
  --name "Customer Analytics Dashboard" \
  --domain-id "abc-123" \
  --description "360-degree customer analytics with behavioral insights" \
  --type Analytical \
  --status Draft

# Get detailed data product information
pvw uc dataproduct show --product-id "prod-789"

# Update data product (partial updates supported - only specify fields to change)
pvw uc dataproduct update \
  --product-id "prod-789" \
  --status Published \
  --description "Updated comprehensive customer analytics" \
  --endorsed

# Update multiple fields at once
pvw uc dataproduct update \
  --product-id "prod-789" \
  --status Published \
  --update-frequency Monthly \
  --endorsed

# Delete a data product (with confirmation)
pvw uc dataproduct delete --product-id "prod-789"

# Delete without confirmation prompt
pvw uc dataproduct delete --product-id "prod-789" --yes
```

#### 🎯 **Objectives & Key Results (OKRs)**

```bash
# List objectives for a domain
pvw uc objective list --domain-id "abc-123"

# Create measurable objectives
pvw uc objective create \
  --definition "Improve data quality score by 25% within Q4" \
  --domain-id "abc-123" \
  --target-value "95" \
  --measurement-unit "percentage"

# Track objective progress
pvw uc objective update \
  --objective-id "obj-456" \
  --domain-id "abc-123" \
  --current-value "87" \
  --status "in-progress"
```

#### 🔑 **Critical Data Elements (CDEs)**

```bash
# List critical data elements
pvw uc cde list --domain-id "abc-123"

# Define critical data elements with governance rules
pvw uc cde create \
  --name "Social Security Number" \
  --data-type "String" \
  --domain-id "abc-123" \
  --classification "PII" \
  --retention-period "7-years"

# Associate CDEs with data assets
pvw uc cde link \
  --cde-id "cde-789" \
  --domain-id "abc-123" \
  --asset-id "ea3412c3-7387-4bc1-9923-11f6f6f60000"
```

#### 🏥 **Health Monitoring (NEW)**

Monitor governance health and get automated recommendations to improve your data governance posture.

```bash
# List all health findings and recommendations
pvw uc health query

# Filter by severity
pvw uc health query --severity High
pvw uc health query --severity Medium

# Filter by status
pvw uc health query --status NotStarted
pvw uc health query --status InProgress

# Get detailed information about a specific health action
pvw uc health show --action-id "5ea3fc78-6a77-4098-8779-ed81de6f87c9"

# Update health action status
pvw uc health update \
  --action-id "5ea3fc78-6a77-4098-8779-ed81de6f87c9" \
  --status InProgress \
  --reason "Working on assigning glossary terms to data products"

# Get health summary statistics
pvw uc health summary

# Output health findings in JSON format
pvw uc health query --json
```

**Health Finding Types:**
- Missing glossary terms on data products (High)
- Data products without OKRs (Medium)
- Missing data quality scores (Medium)
- Classification gaps on data assets (Medium)
- Description quality issues (Medium)
- Business domains without critical data entities (Medium)

#### 🔄 **Workflow Management (NEW)**

Manage approval workflows and business process automation in Purview.

```bash
# List all workflows
pvw workflow list

# Get workflow details
pvw workflow get --workflow-id "workflow-123"

# Create a new workflow (requires JSON definition)
pvw workflow create --workflow-id "approval-flow-1" --payload-file workflow-definition.json

# Execute a workflow
pvw workflow execute --workflow-id "workflow-123"

# List workflow executions
pvw workflow executions --workflow-id "workflow-123"

# View specific execution details
pvw workflow execution-details --workflow-id "workflow-123" --execution-id "exec-456"

# Update workflow configuration
pvw workflow update --workflow-id "workflow-123" --payload-file updated-workflow.json

# Delete a workflow
pvw workflow delete --workflow-id "workflow-123"

# Output workflows in JSON format
pvw workflow list --json
```

**Workflow Use Cases:**
- Data access request approvals
- Glossary term certification workflows
- Data product publishing approvals
- Classification review processes

#### 🔄 **Integrated Workflow Example**

```bash
# 1. Discover assets to govern
pvw search query --keywords="customer" --detailed

# 2. Create governance domain for discovered assets
pvw uc domain create --name "Customer Data" --description "Customer information governance"

# 3. Define governance terms
pvw uc term create --name "Customer PII" --domain-id "new-domain-id" --definition "Personal customer information"

# 4. Create data product from discovered assets
pvw uc dataproduct create --name "Customer Master Data" --domain-id "new-domain-id"

# 5. Set governance objectives
pvw uc objective create --definition "Ensure 100% PII classification compliance" --domain-id "new-domain-id"
```

---

## Entity Management & Updates

PVW CLI provides comprehensive entity management capabilities for updating Purview assets like descriptions, classifications, and custom attributes.

### 🔄 **Entity Update Examples**

#### **Update Asset Descriptions**

```bash
# Update table description using GUID
pvw entity update-attribute \
  --guid "ece43ce5-ac45-4e50-a4d0-365a64299efc" \
  --attribute "description" \
  --value "Updated customer data warehouse table with enhanced analytics"

# Update dataset description using qualified name
pvw entity update-attribute \
  --qualifiedName "https://app.powerbi.com/groups/abc-123/datasets/def-456" \
  --attribute "description" \
  --value "Power BI dataset for customer analytics dashboard"
```

#### **Bulk Entity Operations**

```bash
# Read entity details before updating
pvw entity read-by-attribute \
  --guid "ea3412c3-7387-4bc1-9923-11f6f6f60000" \
  --attribute "description,classifications,customAttributes"

# Update multiple attributes at once
pvw entity update-bulk \
  --input-file entities_to_update.json \
  --output-file update_results.json
```

#### **Column-Level Updates**

```bash
# Update specific column descriptions in a table
pvw entity update-attribute \
  --guid "column-guid-123" \
  --attribute "description" \
  --value "Customer unique identifier - Primary Key"

# Add classifications to sensitive columns
pvw entity add-classification \
  --guid "column-guid-456" \
  --classification "MICROSOFT.PERSONAL.EMAIL"
```

### 🔍 **Discovery to Update Workflow**

```bash
# 1. Find assets that need updates
pvw search query --keywords="customer table" --show-ids --limit=10

# 2. Get detailed information about a specific asset
pvw entity read-by-attribute --guid "FOUND_GUID" --attribute "description,classifications"

# 3. Update the asset description
pvw entity update-attribute \
  --guid "FOUND_GUID" \
  --attribute "description" \
  --value "Updated description based on business requirements"

# 4. Verify the update
pvw search query --keywords="FOUND_GUID" --detailed
```

---

## Data Product Management (Legacy)

PVW CLI also includes the original `data-product` command group for backward compatibility with traditional data product lifecycle management.

See [`doc/commands/data-product.md`](doc/commands/data-product.md) for full documentation and examples.

### Example Commands

```bash
# Create a data product
pvw data-product create --qualified-name="product.test.1" --name="Test Product" --description="A test data product"

# Add classification and label
pvw data-product add-classification --qualified-name="product.test.1" --classification="PII"
pvw data-product add-label --qualified-name="product.test.1" --label="gold"

# Link glossary term
pvw data-product link-glossary --qualified-name="product.test.1" --term="Customer"

# Set status and show lineage
pvw data-product set-status --qualified-name="product.test.1" --status="active"
pvw data-product show-lineage --qualified-name="product.test.1"
```

---

## Core Features

- **Unified Catalog (UC)**: Complete modern data governance (NEW)
  ```bash
  # Manage governance domains, terms, data products, OKRs, CDEs
  pvw uc domain list
  pvw uc term create --name "Customer" --domain-id "abc-123"
  pvw uc objective create --definition "Improve quality" --domain-id "abc-123"
  ```
- **Discovery Query/Search**: Flexible, advanced search for all catalog assets
- **Entity Management**: Bulk import/export, update, and validation
- **Glossary Management**: Import/export terms, assign terms in bulk
  ```bash
  # List all terms in a glossary
  pvw glossary list-terms --glossary-guid "your-glossary-guid"
  
  # Create and manage glossary terms
  pvw glossary create-term --payload-file term.json
  ```
- **Lineage Operations**: Lineage discovery, CSV-based bulk lineage
- **Monitoring & Analytics**: Real-time dashboards, metrics, and reporting
- **Plugin System**: Extensible with custom plugins

---

## API Coverage and Support

PVW CLI provides comprehensive automation for all major Microsoft Purview APIs, including the new **Unified Catalog APIs** for modern data governance.

### Supported API Groups

- **Unified Catalog**: Complete governance domains, glossary terms, data products, OKRs, CDEs management ✅
  - **Health Monitoring**: Automated governance health checks and recommendations ✅ NEW
  - **Workflows**: Approval workflows and business process automation ✅ NEW
- **Data Map**: Full entity and lineage management ✅
- **Discovery**: Advanced search, browse, and query capabilities ✅
- **Collections**: Collection and account management ✅
- **Management**: Administrative operations ✅
- **Scan**: Data source scanning and configuration ✅

### API Version Support

- **Unified Catalog**: Latest UC API endpoints (September 2025)
- Data Map: **2024-03-01-preview** (default) or **2023-09-01** (stable)
- Collections: **2019-11-01-preview**
- Account: **2019-11-01-preview**
- Management: **2021-07-01**
- Scan: **2018-12-01-preview**

For the latest API documentation and updates, see:
- [Microsoft Purview REST API reference](https://learn.microsoft.com/en-us/rest/api/purview/)
- [Atlas 2.2 API documentation](https://learn.microsoft.com/en-us/purview/data-gov-api-atlas-2-2)
- [Azure Updates](https://azure.microsoft.com/updates/) for new releases

If you need a feature that is not yet implemented, please open an issue or check for updates in future releases.

---

## Sample Files & Scripts

PVW CLI includes comprehensive sample files and scripts for bulk operations:

### Bulk Import Samples

- **CSV Samples:** `samples/csv/uc_terms_bulk_example.csv` (8 sample terms)
- **JSON Samples:** 
  - `samples/json/term/uc_terms_bulk_example.json` (8 data management terms)
  - `samples/json/term/uc_terms_sample.json` (8 business terms)

### Bulk Delete Scripts

- **PowerShell:** `scripts/delete-all-uc-terms.ps1` - Full-featured with confirmation prompts
- **Python:** `scripts/delete_all_uc_terms_v2.py` - Rich progress bars and error handling

### Test Scripts

- **PowerShell:** `scripts/test-json-output.ps1` - Validates JSON output parsing

### Jupyter Notebooks

- `samples/notebooks (plus)/unified_catalog_terms_examples.ipynb` - Complete examples including:
  - Examples 10-16: Bulk import demonstrations
  - Code generation for CSV/JSON files
  - Dry-run and actual import examples
  - Term verification workflows

---

## Documentation

### Core Documentation

- **Main Documentation:** [`doc/README.md`](doc/README.md)
- **Unified Catalog:** [`doc/commands/unified-catalog.md`](doc/commands/unified-catalog.md)
- **Bulk Import Guide:** [`doc/commands/unified-catalog/term-bulk-import.md`](doc/commands/unified-catalog/term-bulk-import.md)
- **Data Products:** [`doc/commands/data-product.md`](doc/commands/data-product.md)

### Quick Reference

- **API Coverage:** All major Purview APIs including Unified Catalog, Data Map, Discovery, Collections
- **Authentication:** Azure CLI, Service Principal, Managed Identity support
- **Output Formats:** Table (default), JSON (plain), JSONC (colored)
- **Bulk Operations:** Import/export terms from CSV/JSON, bulk delete scripts

---

## Recent Updates (October 2025)

### ✅ Bulk Term Import/Export
- Import multiple terms from CSV or JSON files
- Dry-run mode for validation before import
- Support for owners (Entra ID GUIDs), acronyms, resources
- Progress tracking and detailed error reporting
- 100% success rate in testing (8/8 terms)

### ✅ PowerShell & Scripting Integration
- New `--output` parameter with table/json/jsonc formats
- Plain JSON works with PowerShell's `ConvertFrom-Json`
- Compatible with jq, Python json module, and other tools
- Migration from deprecated `--json` flag

### ✅ Bulk Delete Scripts
- PowerShell script with interactive confirmation ("DELETE" to confirm)
- Python script with Rich progress bars
- Beautiful UI with colored output
- Success/failure tracking per term
- Rate limiting (200ms delay)

### ✅ Critical Fixes
- **Owner ID Format:** Must use Entra ID Object IDs (GUIDs), not email addresses
- **Domain Status:** Terms cannot be "Published" in unpublished domains - use "Draft"
- **Error Validation:** Enhanced error handling shows actual API responses

---

## Key Features Summary

### 🚀 **Unified Catalog (UC) - Complete Management**
- Governance domains, glossary terms, data products
- Objectives & Key Results (OKRs), Critical Data Elements (CDEs)
- Health monitoring and workflow automation
- Full CRUD operations with smart partial updates

### 📦 **Bulk Operations**
- CSV/JSON import with dry-run validation
- PowerShell and Python bulk delete scripts
- Progress tracking and error handling
- Sample files and templates included

### 📊 **Multiple Output Formats**
- Table format for human viewing (default)
- Plain JSON for PowerShell/bash scripting
- Colored JSON for visual inspection

### 🔧 **Automation & Integration**
- Azure CLI, Service Principal, Managed Identity auth
- Works in local development, CI/CD, and production
- Compatible with PowerShell, bash, Python, jq

### 📚 **Comprehensive Documentation**
- Complete API coverage documentation
- Jupyter notebook examples
- Troubleshooting guides
- Sample files and templates

---

## Contributing & Support

- **Documentation:** [Full Documentation](https://github.com/Keayoub/Purview_cli/blob/main/doc/README.md)
- **Issue Tracker:** [GitHub Issues](https://github.com/Keayoub/Purview_cli/issues)
- **Email Support:** [keayoub@msn.com](mailto:keayoub@msn.com)
- **Repository:** [GitHub - Keayoub/Purview_cli](https://github.com/Keayoub/Purview_cli)

---

## License

See [LICENSE](LICENSE) file for details.

---

**PVW CLI v1.2.1 empowers data engineers, stewards, and architects to automate, scale, and enhance their Microsoft Purview experience with powerful command-line and programmatic capabilities.**

**Latest Features:** Bulk term import/export, PowerShell integration, multiple output formats, and comprehensive bulk delete scripts with beautiful progress tracking.
