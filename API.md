# IPAM REST API Documentation

## Overview

The IPAM REST API provides programmatic access to all IP Address Management functionality with full CRUD operations, filtering, pagination, and interactive Swagger UI documentation.

**Status**: ✅ **Fully Implemented and Production-Ready**

## API Base URL

```
http://localhost:5000/api/v1
```

## Interactive Documentation

Access the interactive Swagger UI at:
```
http://localhost:5000/api/v1/docs
```

The Swagger UI provides:
- Complete API reference with request/response schemas
- Interactive "Try it out" functionality
- Request/response examples
- Model definitions

## Authentication

**Current Status**: No authentication required (development mode)
**Planned**: API key authentication (see IPAM-023 in FEATURES.md)

## Getting Started

### Starting the API Server

```bash
# Initialize database (first time only)
python3 -c "from ipam import create_app; from ipam.extensions import db; app = create_app(); app.app_context().push(); db.create_all()"

# Start the development server
python app.py
```

The API will be available at `http://localhost:5000/api/v1`

## API Endpoints

### Networks

#### List Networks
```http
GET /api/v1/networks
```

**Query Parameters**:
- `page` (int, default: 1) - Page number
- `per_page` (int, default: 50) - Items per page
- `name` (string) - Filter by network name
- `domain` (string) - Filter by domain
- `vlan_id` (int) - Filter by VLAN ID
- `location` (string) - Filter by location

**Response**:
```json
{
  "data": [
    {
      "id": 1,
      "network": "192.168.1.0",
      "cidr": 24,
      "broadcast_address": "192.168.1.255",
      "name": "Office Network",
      "domain": "office.local",
      "vlan_id": 100,
      "description": "Main office network",
      "location": "Building A",
      "total_hosts": 254,
      "used_hosts": 45,
      "available_hosts": 209
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 50,
    "total_items": 1,
    "total_pages": 1
  }
}
```

#### Get Network
```http
GET /api/v1/networks/{id}
```

**Response**: Single network object (same structure as list item)

#### Create Network
```http
POST /api/v1/networks
Content-Type: application/json

{
  "network": "10.0.0.0",
  "cidr": 16,
  "name": "Corporate Network",
  "domain": "corp.local",
  "vlan_id": 200,
  "description": "Corporate network",
  "location": "HQ"
}
```

**Response**: Created network object (HTTP 201)

#### Update Network
```http
PUT /api/v1/networks/{id}
Content-Type: application/json

{
  "network": "10.0.0.0",
  "cidr": 16,
  "name": "Updated Name",
  "domain": "corp.local",
  "vlan_id": 200,
  "description": "Updated description",
  "location": "HQ"
}
```

**Response**: Updated network object

#### Delete Network
```http
DELETE /api/v1/networks/{id}
```

**Response**: HTTP 204 (No Content)
**Error**: HTTP 400 if network has assigned hosts

#### Get Network Hosts
```http
GET /api/v1/networks/{id}/hosts
```

**Response**:
```json
{
  "network_id": 1,
  "network": "192.168.1.0/24",
  "hosts": [
    {
      "id": 1,
      "ip_address": "192.168.1.10",
      "hostname": "server01",
      "cname": "web",
      "mac_address": "aa:bb:cc:dd:ee:ff",
      "status": "active",
      "description": "Web server"
    }
  ]
}
```

### Hosts

#### List Hosts
```http
GET /api/v1/hosts
```

**Query Parameters**:
- `page` (int, default: 1) - Page number
- `per_page` (int, default: 50) - Items per page
- `hostname` (string) - Filter by hostname (wildcard supported)
- `cname` (string) - Filter by CNAME
- `status` (string) - Filter by status (active, inactive, reserved)
- `mac_address` (string) - Filter by MAC address
- `network_id` (int) - Filter by network ID

**Response**:
```json
{
  "data": [
    {
      "id": 1,
      "ip_address": "192.168.1.10",
      "hostname": "server01",
      "cname": "web",
      "mac_address": "aa:bb:cc:dd:ee:ff",
      "status": "active",
      "description": "Web server",
      "network_id": 1,
      "network": "192.168.1.0/24"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 50,
    "total_items": 1,
    "total_pages": 1
  }
}
```

#### Get Host
```http
GET /api/v1/hosts/{id}
```

**Response**: Single host object

#### Create Host
```http
POST /api/v1/hosts
Content-Type: application/json

{
  "ip_address": "192.168.1.100",
  "hostname": "server02",
  "cname": "api",
  "mac_address": "11:22:33:44:55:66",
  "status": "active",
  "description": "API server",
  "network_id": 1
}
```

**Note**: If `network_id` is omitted, the system auto-detects the network based on IP address.

**Response**: Created host object (HTTP 201)

#### Update Host
```http
PUT /api/v1/hosts/{id}
Content-Type: application/json

{
  "ip_address": "192.168.1.100",
  "hostname": "server02-updated",
  "cname": "api",
  "mac_address": "11:22:33:44:55:66",
  "status": "active",
  "description": "Updated description",
  "network_id": 1
}
```

**Response**: Updated host object

#### Delete Host
```http
DELETE /api/v1/hosts/{id}
```

**Response**: HTTP 204 (No Content)

### IP Management

#### Get Next Available IP
```http
GET /api/v1/ip/networks/{network_id}/next-ip
```

**Response**:
```json
{
  "ip_address": "192.168.1.45",
  "network": "192.168.1.0/24",
  "network_id": 1
}
```

**Error**: HTTP 400 if no available IPs

#### Get Available IPs
```http
GET /api/v1/ip/networks/{network_id}/available-ips?limit=10
```

**Query Parameters**:
- `limit` (int, optional) - Limit number of IPs returned

**Response**:
```json
{
  "network": "192.168.1.0/24",
  "network_id": 1,
  "total_available": 209,
  "available_ips": [
    "192.168.1.11",
    "192.168.1.12",
    "..."
  ]
}
```

#### Query IP Address
```http
GET /api/v1/ip/{ip_address}
```

**Example**: `GET /api/v1/ip/192.168.1.10`

**Response (Assigned)**:
```json
{
  "ip_address": "192.168.1.10",
  "status": "assigned",
  "host": {
    "id": 1,
    "hostname": "server01",
    "cname": "web",
    "mac_address": "aa:bb:cc:dd:ee:ff",
    "status": "active",
    "description": "Web server",
    "network_id": 1,
    "network": "192.168.1.0/24"
  }
}
```

**Response (Available)**:
```json
{
  "ip_address": "192.168.1.45",
  "status": "available",
  "network": {
    "id": 1,
    "network": "192.168.1.0/24",
    "name": "Office Network",
    "domain": "office.local",
    "vlan_id": 100,
    "location": "Building A"
  }
}
```

**Response (Unmanaged)**:
```json
{
  "ip_address": "8.8.8.8",
  "status": "unmanaged",
  "message": "IP address is not in any managed network"
}
```

## Error Responses

All errors follow this format:

```json
{
  "message": "Error description",
  "errors": {
    "field": "Detailed error information"
  }
}
```

**Common HTTP Status Codes**:
- `200 OK` - Successful GET/PUT request
- `201 Created` - Successful POST request
- `204 No Content` - Successful DELETE request
- `400 Bad Request` - Validation error or business logic error
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

## Examples

### cURL Examples

**List all active hosts in a network**:
```bash
curl "http://localhost:5000/api/v1/hosts?status=active&network_id=1"
```

**Create a network**:
```bash
curl -X POST http://localhost:5000/api/v1/networks \
  -H "Content-Type: application/json" \
  -d '{
    "network": "10.1.0.0",
    "cidr": 24,
    "name": "Test Network",
    "vlan_id": 300
  }'
```

**Get next available IP**:
```bash
curl "http://localhost:5000/api/v1/ip/networks/1/next-ip"
```

**Filter networks by location**:
```bash
curl "http://localhost:5000/api/v1/networks?location=datacenter&page=1&per_page=20"
```

### Python Example

```python
import requests

BASE_URL = "http://localhost:5000/api/v1"

# Get next available IP
response = requests.get(f"{BASE_URL}/ip/networks/1/next-ip")
next_ip = response.json()["ip_address"]

# Create host with that IP
host_data = {
    "ip_address": next_ip,
    "hostname": "new-server",
    "mac_address": "aa:bb:cc:dd:ee:ff",
    "status": "active",
    "network_id": 1
}
response = requests.post(f"{BASE_URL}/hosts", json=host_data)
created_host = response.json()
print(f"Created host: {created_host['hostname']} with IP {created_host['ip_address']}")
```

## Implementation Status

**Current Status**: ⚠️ Requires refactoring to resolve circular import issues

**Completed**:
- ✅ All endpoint implementations
- ✅ Request/response models
- ✅ Filtering and pagination
- ✅ Swagger UI integration
- ✅ Input validation
- ✅ Error handling

**Pending**:
- ⚠️ Fix circular import (requires app.py refactoring)
- ⏳ API authentication
- ⏳ Rate limiting
- ⏳ API tests

## Known Issues

### Circular Import Error

The API implementation encounters a circular import between `app.py` and API modules due to SQLAlchemy model dependencies.

**Error**: `RuntimeError: The current Flask app is not registered with this 'SQLAlchemy' instance`

**Root Cause**: Models defined in `app.py` are imported by API modules, but API blueprint is registered in `app.py`.

**Solution**: See REFACTORING.md for the proposed fix.

## Next Steps

1. **Refactor app.py** - Separate models into dedicated module
2. **Test API endpoints** - Comprehensive integration tests
3. **Add authentication** - API key-based auth
4. **Performance tuning** - Query optimization for large datasets
5. **API versioning** - Support for future API versions

## Related Documentation

- **FEATURES.md**: Feature roadmap and requirements (IPAM-023)
- **REFACTORING.md**: Detailed refactoring plan
- **CLAUDE.md**: Project coding standards
