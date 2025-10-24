# Micantis API Wrapper

A lightweight Python wrapper for interacting with the Micantis API plus some helpful utilities.  
Built for ease of use, fast prototyping, and clean integration into data workflows.

---

## 🚀 Features

- Authenticate and connect to the Micantis API service
- Download and parse csvs and binary data into pandas DataFrames
- Filter, search, and retrieve metadata
- Utility functions to simplify common API tasks

---

## ⚠️ Important

This package is designed for authenticated Micantis customers only.  
If you are not a Micantis customer, the API wrapper and utilities in this package will not work for you.

For more information on accessing the Micantis API, please contact us at info@micantis.io.

---

## 📦 Installation

```pip install micantis ```

---

## 💻 Examples

### Import functions

``` python
import pandas as pd
from micantis import MicantisAPI
```

### Initialize API

``` python
# Option 1 - login with username and password
service_url = 'your service url'
username = 'your username'
password = 'your password'

api = MicantisAPI(service_url=service_url, username=username, password=password)
```

``` python
# Option 2 - login in with Microsoft Entra ID
SERVICE = 'your service url'
CLIENT_ID = 'your client id'
AUTHORITY = 'https://login.microsoftonline.com/organizations'
SCOPES = ['your scopes']

api = MicantisAPI(service_url=SERVICE, client_id=CLIENT_ID, authority=AUTHORITY, scopes=SCOPES)
```
### Authenticate API
``` api.authenticate() ```

### Download Data Table Summary

#### Optional parameters
- `search`: Search string (same syntax as the Micantis WebApp)
- `barcode`: Search for a specific barcode
- `limit`: Number of results to return (default: 500)
- `min_date`: Only return results after this date
- `max_date`: Only return results before this date
- `show_ignored`: Include soft-deleted files (default: `True`)

```python
table = api.get_data_table(search=search, barcode=barcode, min_date=min_date, max_date=max_date, limit = 10, show_ignored=show_ignored)
table
```

### Download Binary Files

``` python
# Download single file

file_id = 'File ID obtained from data table, id column'
df = api.download_binary_file(id)

```

``` python
# Download many files using list of files from the table

file_id_list = table['id'].to_list()
data = []

for id in file_id_list:
    df = api.download_csv_file(id)
    data.append(df)

all_data = pd.concat(data)
```

### Download CSV Files

``` python
# Download single file

file_id = 'File ID obtained from data table, id column'
df = api.download_csv_file(id)
```

``` python
# Download multiple files

id_list = table['id'].to_list()
data = []

for id in id_list:
    df = api.download_csv_file(id)
    data.append(df)

all_data = pd.concat(data)
```
## Cells Table
### Download Cell ID Information
Retrieve a list of cell names and GUIDs from the Micantis database with flexible filtering options.

#### Optional parameters
- `search`: Search string (same syntax as the Micantis WebApp)
- `barcode`: Search for a specific barcode
- `limit`: Number of results to return (default: 500)
- `min_date`: Only return results after this date
- `max_date`: Only return results before this date
- `show_ignored`: Include soft-deleted files (default: `True`)

``` python
search = "*NPD*"
cells_df = api.get_cells_list(search=search)
cells_df.head()
```
### Download Cell Metadata

Fetch per-cell metadata and return a clean, wide-format DataFrame.

#### Parameters:
- `cell_ids`: **List[str]**  
  List of cell test GUIDs (**required**)

- `metadata`: **List[str] (optional)**  
  List of metadata **names** (e.g., `"OCV (V)"`) or **IDs**.  
  If omitted, all non-image metadata will be returned by default.

- `return_images`: **bool (optional)**  
  If `True`, includes image metadata fields. Default is `False`.

---

#### 📘 Examples

```python
# Example 1: Get all non-image metadata for a list of cells
cell_ids = cells_df["id"].to_list()
cell_metadata_df = api.get_cell_metadata(cell_ids=cell_ids)
```
```python
# Example 2: Get specific metadata fields by name
cell_metadata_df = api.get_cell_metadata(
    cell_ids=cell_ids,
    metadata=["Cell width", "Cell height"],
    return_images=False
)
```
```python
# Merge cell metadata table with cell names to get clean dataframe
# Merge id with Cell Name (as last column)
id_to_name = dict(zip(cells_df['id'], cells_df['name']))
cells_metadata_df['cell_name'] = cells_metadata_df['id'].map(id_to_name)
cells_metadata_df.head()
```

## Specifications Table
### Download Specifications List
Retrieve specifications with their associated user properties.

```python
# Get all specifications with their user properties
specs_df = api.get_specifications_table()
specs_df.head()
```

## Test Management
### Download Test Requests List
Retrieve test request data with flexible date filtering.

#### Optional parameters
- `since`: Date string in various formats (defaults to January 1, 2020 if not provided)
  - Full month names: `"May 1, 2025"`, `"January 15, 2024"`
  - ISO format: `"2025-05-01"` or `"25-05-01"`

```python
# Get all test requests (defaults to since 2020-01-01)
test_requests = api.get_test_request_list()

# Get test requests since a specific date using month name
test_requests = api.get_test_request_list(since="May 1, 2024")

# Get test requests using ISO format
test_requests = api.get_test_request_list(since="2024-05-01")
```

### Download Failed Test Requests
Retrieve only failed test requests with the same date filtering options.

```python
# Get failed test requests since a specific date
failed_requests = api.get_failed_test_requests(since="January 1, 2024")
failed_requests.head()
```

### Get Individual Test Request Details
Retrieve full details for a specific test request by ID.

**New Feature:** Multiple output format options for better data analysis!

#### Format Options
- `return_format='dict'`: Raw dictionary (default, backwards compatible)
- `return_format='dataframes'`: Returns 3 DataFrames - summary, tests, and status_log ⭐ **Recommended**
- `return_format='flat'`: Single-row DataFrame with basic info

```python
# Option 1: Dictionary format (default, backwards compatible)
request_id = "your-test-request-guid"
test_details = api.get_test_request(request_id)

# Option 2: DataFrames format (recommended for analysis) ⭐
test_details = api.get_test_request(request_id, return_format='dataframes')
print(test_details['summary'])      # Basic request information
print(test_details['tests'])        # All requested tests
print(test_details['status_log'])   # Status change history

# Option 3: Flat DataFrame (best for combining multiple requests)
test_details = api.get_test_request(request_id, return_format='flat')
```

#### Batch Processing Multiple Requests
```python
# Get summaries for multiple test requests
request_ids = test_requests['id'].head(10).to_list()

all_summaries = []
for req_id in request_ids:
    summary = api.get_test_request(req_id, return_format='flat')
    all_summaries.append(summary)

# Combine into single DataFrame
combined_df = pd.concat(all_summaries, ignore_index=True)
print(f"Retrieved {len(combined_df)} test requests")
combined_df.head()
```

## Write Cell Metadata
Micantis lets you programmatically assign or update metadata for each cell using either:
- the human-readable field name (e.g., "Technician", "Weight (g)")
- or the internal propertyDefinitionId (UUID)

#### 📘 Examples

```python
# Example 1: Update the technician field for a cell
changes = [
    {
        "id": "your-cell-test-guid-here",  # cell test GUID
        "field": "Technician",
        "value": "Mykela"
    },
    {
        "id": "your-cell-test-guid-here",
        "field": "Weight (g)",
        "value": 98.7
    }
]

api.write_cell_metadata(changes=changes)

# Verify the changes
api.get_cell_metadata(cell_ids=["your-cell-test-guid-here"], metadata=['Weight (g)', 'Technician'])
```

```python
# Example 2: Update using propertyDefinitionId (advanced)
changes = [
    {
        "id": "your-cell-test-guid-here",
        "propertyDefinitionId": "your-property-definition-guid",
        "value": 98.7
    }
]

api.write_cell_metadata(changes=changes)

# Verify the changes
api.get_cell_metadata(cell_ids=["your-cell-test-guid-here"], metadata=['Weight (g)', 'Technician'])
```

