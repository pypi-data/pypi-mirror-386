# CESNET ServicePath Plugin for NetBox

A NetBox plugin for managing service paths and segments in network infrastructure with advanced geographic path visualization and financial tracking.

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![PyPI version](https://img.shields.io/pypi/v/cesnet-service-path-plugin.svg)](https://pypi.org/project/cesnet-service-path-plugin/)
[![Python versions](https://img.shields.io/pypi/pyversions/cesnet-service-path-plugin.svg)](https://pypi.org/project/cesnet-service-path-plugin/)
[![NetBox compatibility](https://img.shields.io/badge/NetBox-4.4-blue.svg)](https://github.com/netbox-community/netbox)

## 📑 Table of Contents

- [Overview](#overview)
- [Compatibility Matrix](#compatibility-matrix)
- [Features](#features)
- [Data Model](#data-model)
- [Installation and Configuration](#installation-and-configuration)
  - [Prerequisites](#prerequisites)
  - [Step-by-Step Installation](#step-1-enable-postgis-in-postgresql)
- [Additional Configuration](#additional-configuration)
  - [Custom Status Choices](#custom-status-choices)
  - [Custom Kind Choices](#custom-kind-choices)
  - [Currency Configuration](#currency-configuration)
- [Geographic Path Data](#geographic-path-data)
- [Financial Information Management](#financial-information-management)
- [API Usage](#api-usage)
- [Development](#development)
- [Navigation and UI](#navigation-and-ui)
- [Troubleshooting](#troubleshooting)
- [Credits](#credits)
- [License](#license)

## Overview

The CESNET ServicePath Plugin extends NetBox's capabilities by providing comprehensive network service path management with:
- Interactive geographic path visualization using Leaflet maps, introduced in version 5.0.x
- Support for KML, KMZ, and GeoJSON path data
- **Financial information tracking for segments** (new in 5.2.0)
- Service path and segment relationship management
- Advanced filtering and search capabilities
- REST API and GraphQL support

## Compatibility Matrix

| NetBox Version | Plugin Version |
|----------------|----------------|
|     4.4        |      5.2.x     |
|     4.4        |      5.1.x     |
|     4.3        |      5.0.x     |
|     4.2        |      4.0.x     |
|     3.7        |      0.1.0     |

## Features

### Service Path Management
- Define experimental, core, and customer service paths
- Track service path status and metadata
- Link multiple segments to create complete paths
- Visual relationship mapping

### Segment Management
- Track network segments between locations
- Monitor installation and termination dates
- Manage provider relationships and contracts
- Link circuits to segments
- Automatic status tracking based on dates
- **Geographic path visualization with actual route data**
- Segment types (dark fiber, optical spectrum, ethernet) with type specific data
- **Financial information tracking with multi-currency support** (new in 5.2.0)

### Financial Information Management
- **Monthly charge tracking** with configurable currencies
- **Non-recurring charge** (one-time setup/installation fees)
- **Commitment period** tracking in months
- **Automatic cost calculations**:
  - Total commitment cost (monthly × commitment period)
  - Total cost including setup fees
- **Permission-based access control** - financial data visible only to authorized users
- **Multi-currency support** with configurable currency list
- **Integrated with segment detail view** - no separate navigation required
- **REST API support** - financial data included in segment API responses

### Geographic Features
- **Interactive map visualization** with multiple tile layers (OpenStreetMap, satellite, topographic) and multiple color schema (status, provider, segment type)
- **Path data upload** supporting KML, KMZ, and GeoJSON formats
- **Automatic path length calculation** in kilometers
- **Multi-segment path support** with complex routing
- **Fallback visualization** showing straight lines when path data unavailable
- **Overlapping segment detection** and selection on maps
- **Path data export** as GeoJSON for external use
- An example of a geographic service path visualized using the plugin:
    ![Sample Service Path Map](./docs/sample_path.png)

### Integration Features
- **Template extensions** for Circuits, Providers, Sites, and Locations
- **Custom table columns** showing segment relationships
- **Advanced filtering** including path data availability
- **REST API endpoints** with geographic data support
- **GraphQL schema** with geometry field support

## Data Model

### Service Path
- Name and status tracking
- Service type classification (experimental/core/customer)
- Multiple segment support through mappings
- Comments and tagging support

### Segment
- Provider and location tracking
- Date-based lifecycle management with visual status indicators
- Circuit associations
- **Geographic path geometry** storage (MultiLineString)
- **Path metadata** including length, source format, and notes
- **Financial information** (optional one-to-one relationship)
- Automated status monitoring

### Segment Financial Info (New in 5.2.0)
- **Monthly charges** with currency selection
- **Non-recurring charges** for setup/installation
- **Commitment period** tracking
- **Automatic cost calculations**
- **Notes** field for additional financial context
- **Permission-based visibility**

### Geographic Path Data
- **MultiLineString geometry** storage in WGS84 (EPSG:4326)
- **Multiple path segments** support for complex routes
- **Automatic 2D conversion** from 3D path data
- **Length calculation** using projected coordinates
- **Source format tracking** (KML, KMZ, GeoJSON, manual)

## Installation and Configuration

⚠️ **Important**: This plugin requires PostGIS and geographic libraries. Standard NetBox installations need additional setup steps.

### Prerequisites

Before installing the plugin, ensure you have:

1. **PostgreSQL with PostGIS extension** (version 3.0 or higher recommended)
2. **System libraries**: GDAL, GEOS, and PROJ runtime binaries
3. **NetBox 4.4 or higher**

#### Installing System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install postgresql-15-postgis-3 gdal-bin libgdal34 libgeos-c1t64 libproj25
```

**Note**: Package names may vary by Ubuntu/Debian version. Use `apt-cache search libgdal` to find the correct version for your system.

**macOS:**
```bash
brew install postgresql postgis gdal geos proj
```

**Docker users**: The official `netboxcommunity/netbox` images do **NOT** include PostGIS and GDAL libraries by default. You will need to create a custom Docker image. See the Docker-specific instructions below.

### Step 1: Enable PostGIS in PostgreSQL

Connect to your NetBox database and enable the PostGIS extension:

```sql
-- Connect to your NetBox database
\c netbox

-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- Verify installation
SELECT PostGIS_version();
```

### Step 2: Configure NetBox Database Engine

**CRITICAL**: Update your NetBox `configuration.py` to use the PostGIS database engine:

```python
# Set the database engine to PostGIS
DATABASE_ENGINE = "django.contrib.gis.db.backends.postgis"

# PostgreSQL database configuration
DATABASE = {
    "ENGINE": DATABASE_ENGINE,  # Must use PostGIS engine
    "NAME": environ.get("DB_NAME", "netbox"),
    "USER": environ.get("DB_USER", ""),
    "PASSWORD": read_secret("db_password", environ.get("DB_PASSWORD", "")),
    "HOST": environ.get("DB_HOST", "localhost"),
    "PORT": environ.get("DB_PORT", ""),
    "OPTIONS": {"sslmode": environ.get("DB_SSLMODE", "prefer")},
    "CONN_MAX_AGE": int(environ.get("DB_CONN_MAX_AGE", "300")),
}
```

**Note**: This is just an example. If you're using NetBox Docker, this can be configured via environment variables in your `docker-compose.yml` or similar configuration files.

### Step 3: Install the Plugin

#### Standard Installation (pip)

```bash
pip install cesnet_service_path_plugin
```

#### Docker Installation

The official NetBox Docker images do not include the required geographic libraries. You need to create a custom Docker image.

**Option 1: Create a Custom Dockerfile**

Create a `Dockerfile` extending the official NetBox image:

```dockerfile
FROM netboxcommunity/netbox:v4.4

# copy plugin requirements
COPY ./plugin_requirements.txt /opt/netbox/

# Install git and minimal PostGIS runtime dependencies
RUN apt-get update && apt-get install -y \
    git \
    gdal-bin \
    libgdal34 \
    libgeos-c1t64 \
    libproj25 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install PostGIS and geospatial Python dependencies
RUN /usr/local/bin/uv pip install \
    psycopg2-binary \
    -r /opt/netbox/plugin_requirements.txt
```

**Note**: Library package names (like `libgdal34`) may vary depending on the base image's Ubuntu/Debian version. Check available packages if you encounter errors.

Then create a `plugin_requirements.txt` file:
```
cesnet_service_path_plugin
```

Build your custom image:
```bash
docker build -t netbox-with-gis:latest .
```

Update your `docker-compose.yml` to use the custom image:
```yaml
services:
  netbox:
    image: netbox-with-gis:latest
    # ... rest of your configuration
```

**Option 2: Use docker-compose override**

Add a `docker-compose.override.yml` file:

```yaml
version: '3.8'
services:
  netbox:
    build:
      context: .
      dockerfile: Dockerfile.custom
```

For detailed Docker setup instructions, see [using netbox-docker with plugins](https://github.com/netbox-community/netbox-docker/wiki/Using-Netbox-Plugins).

### Step 4: Enable and configure the Plugin

Add the plugin to your NetBox `configuration/plugins.py`:

```python
PLUGINS = [
    'cesnet_service_path_plugin',
]

PLUGINS_CONFIG = {
    "cesnet_service_path_plugin": {
        'currencies': [
            ('CZK', 'Czech Koruna'),
            ('EUR', 'Euro'),
            ('USD', 'US Dollar'),
        ],
        'default_currency': 'EUR',
    },
}
```

### Step 5: Run Database Migrations

Apply the plugin's database migrations:

```bash
cd /opt/netbox/netbox
source venv/bin/activate
python manage.py migrate cesnet_service_path_plugin
```

**Docker users:**
```bash
docker exec -it netbox python /opt/netbox/netbox/manage.py migrate cesnet_service_path_plugin
```

### Step 6: Restart NetBox

Restart your NetBox services to load the plugin:

```bash
sudo systemctl restart netbox netbox-rq
```

**Docker users:**
```bash
docker-compose restart netbox netbox-worker
```

### Verification

To verify the installation:

1. Log into NetBox
2. Check that "Service Paths" appears in the navigation menu
3. Navigate to **Service Paths → Segments** to confirm the plugin is working

For geographic feature verification, you can use the diagnostic function in the Django shell:

```python
python manage.py nbshell

from cesnet_service_path_plugin.utils import check_gis_environment
check_gis_environment()
```

## Additional Configuration

### Custom Status Choices

Extend or override default status choices in your `configuration.py`:

```python
FIELD_CHOICES = {
    'cesnet_service_path_plugin.choices.status': (
        ('custom_status', 'Custom Status', 'blue'),
        # ('status_value', 'Display Name', 'color'),
    )
}
```

Status choice format:
- Value: Internal database value
- Name: UI display name
- Color: Badge color (blue, green, red, orange, yellow, purple, gray)

Default statuses (Active, Planned, Offline) will be merged with custom choices.

### Custom Kind Choices

Extend or override default kind choices in your `configuration.py`:

```python
FIELD_CHOICES = {
    'cesnet_service_path_plugin.choices.kind': (
        ('custom_kind', 'Custom Kind Name', 'purple'),
        # ('kind_value', 'Display Name', 'color'),
    )
}
```

Kind choice format:
- Value: Internal database value
- Name: UI display name
- Color: Badge color (blue, green, red, orange, yellow, purple, gray)

Default kinds:
- experimental: Experimentální (cyan)
- core: Páteřní (blue)
- customer: Zákaznická (green)

Custom kinds will be merged with the default choices.

### Currency Configuration

Configure available currencies and default currency for financial information:

```python
PLUGINS_CONFIG = {
    "cesnet_service_path_plugin": {
        'currencies': [
            ('CZK', 'Czech Koruna'),
            ('EUR', 'Euro'),
            ('USD', 'US Dollar'),
            ('GBP', 'British Pound'),
            ('JPY', 'Japanese Yen'),
        ],
        'default_currency': 'EUR',
    },
}
```

**Configuration options:**
- `currencies`: List of (code, name) tuples for available currencies
- `default_currency`: Default currency code to use when creating new financial records

**Default values if not configured:**
- Currencies: CZK, EUR, USD
- Default currency: CZK

## Geographic Path Data

### Supported Formats

- **GeoJSON** (.geojson, .json): Native web format
- **KML** (.kml): Google Earth format
- **KMZ** (.kmz): Compressed KML with enhanced support for complex files

### Path Data Features

- **Automatic format detection** from file extension
- **Multi-layer KMZ support** with comprehensive extraction
- **3D to 2D conversion** for compatibility
- **Path validation** with detailed error reporting
- **Length calculation** using accurate projections

### Map Visualization

- **Multiple tile layers**: OpenStreetMap, satellite imagery, topographic maps
- **Interactive controls**: Pan, zoom, fit-to-bounds
- **Segment information panels** with detailed metadata
- **Overlapping segment handling** with selection popups
- **Status-based color coding** for visual identification

## Financial Information Management

### Adding Financial Information

Financial information can be added to any segment through the segment detail view:

1. Navigate to a segment's detail page
2. Click "Add Financial Info" (requires appropriate permissions)
3. Fill in the financial details:
   - **Monthly Charge**: Regular recurring fee
   - **Currency**: Select from configured currencies
   - **Non-recurring Charge**: One-time setup/installation fee
   - **Commitment Period**: Number of months for contract commitment
   - **Notes**: Additional context or details

### Viewing Financial Information

Financial information is displayed on the segment detail page for users with view permissions:
- Monthly charge with currency
- Non-recurring charge (if applicable)
- Commitment period
- Automatically calculated total costs
- Additional notes

### Permission Requirements

Financial information has separate permissions from segments:
- **View**: `cesnet_service_path_plugin.view_segmentfinancialinfo`
- **Add**: `cesnet_service_path_plugin.add_segmentfinancialinfo`
- **Change**: `cesnet_service_path_plugin.change_segmentfinancialinfo`
- **Delete**: `cesnet_service_path_plugin.delete_segmentfinancialinfo`

Users without view permission will not see financial information in the UI or API responses.

### Financial Calculations

The plugin automatically calculates:
- **Total Commitment Cost**: Monthly charge × Commitment period (months)
- **Total Cost Including Setup**: Total commitment cost + Non-recurring charge

These calculations are available in both the UI and API responses.

## API Usage

The plugin provides comprehensive REST API and GraphQL support:

### REST API Endpoints

- `/api/plugins/cesnet-service-path-plugin/segments/` - Segment management
- `/api/plugins/cesnet-service-path-plugin/service-paths/` - Service path management
- `/api/plugins/cesnet-service-path-plugin/segments/{id}/geojson-api/` - Geographic data
- `/api/plugins/cesnet-service-path-plugin/segment-financial-info/` - Financial information management

#### Example of segment with path file PATCH and POST 
See [detailed example in docs](./docs/API_path.md).

#### Financial Information in API

Segment API responses include a `financial_info` field:
```json
{
  "id": 1,
  "name": "Example Segment",
  "financial_info": {
    "monthly_charge": "1000.00",
    "charge_currency": "EUR",
    "non_recurring_charge": "5000.00",
    "commitment_period_months": 36,
    "total_commitment_cost": "36000.00",
    "total_cost_including_setup": "41000.00",
    "notes": "Special discount applied"
  }
}
```

**Note**: The `financial_info` field will be `null` if:
- No financial information exists for the segment
- The authenticated user lacks view permissions

### Geographic API Features

- **Lightweight list serializers** for performance
- **Detailed geometry serializers** for map views
- **GeoJSON export** endpoints
- **Path bounds and coordinates** in API responses

### GraphQL Support

Full GraphQL schema with:
- **Geographic field support** for path geometry
- **Filtering capabilities** on all geographic fields
- **Nested relationship queries**

## Development

### Setting Up Development Environment

1. Clone the repository:
```bash
git clone https://github.com/CESNET/cesnet_service_path_plugin.git
cd cesnet_service_path_plugin
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate  # Windows
```

3. Install development dependencies:
```bash
pip install -e ".[dev]"
```

4. Install geographic dependencies:
```bash
# Ubuntu/Debian - only runtime libraries needed
sudo apt-get install gdal-bin libgdal34 libgeos-c1t64 libproj25

# macOS
brew install gdal geos proj

# Install Python packages
pip install geopandas fiona shapely
```

**Note**: For development, you typically only need the runtime libraries. The Python packages (geopandas, fiona, shapely) use precompiled wheels that already include the necessary bindings. Development headers (`-dev` packages) are only needed if you're compiling these libraries from source.

### Testing Geographic Features

Use the built-in diagnostic function:
```python
from cesnet_service_path_plugin.utils import check_gis_environment
check_gis_environment()
```

## Navigation and UI

The plugin adds a **Service Paths** menu with:
- **Segments** - List and manage network segments
- **Segments Map** - Interactive map view of all segments
- **Service Paths** - Manage service path definitions
- **Mappings** - Relationship management tools

### Template Extensions

Automatic integration with existing NetBox models:
- **Circuit pages**: Show related segments
- **Provider pages**: List provider segments
- **Site/Location pages**: Display connected segments
- **Tenant pages**: Show associated provider information

### Financial Information Display

Financial information appears on segment detail pages when:
- User has view permission
- Segment has financial information attached
- Displayed in a dedicated panel with all cost details and calculations

## Troubleshooting

### Common Issues

1. **PostGIS not enabled**: Ensure PostGIS extension is installed in your database
2. **GDAL library missing**: Install system GDAL runtime libraries (`gdal-bin`, `libgdal34`) before Python packages
3. **Path upload fails**: Check file format and ensure it contains LineString geometries
4. **Map not loading**: Verify JavaScript console for tile layer errors
5. **Library version mismatch**: If you encounter errors about missing libraries, check that library package names match your OS version (e.g., `libgdal34` vs `libgdal32`)
6. **Financial info not visible**: Check user permissions for `view_segmentfinancialinfo`
7. **Currency not appearing**: Verify plugin configuration in `configuration/plugins.py`

### Debug Mode

Enable detailed logging for geographic operations:
```python
LOGGING = {
    'loggers': {
        'cesnet_service_path_plugin.utils': {
            'level': 'DEBUG',
            'handlers': ['console'],
        },
    },
}
```

## Credits

- Created using [Cookiecutter](https://github.com/audreyr/cookiecutter) and [`netbox-community/cookiecutter-netbox-plugin`](https://github.com/netbox-community/cookiecutter-netbox-plugin)
- Based on the [NetBox plugin tutorial](https://github.com/netbox-community/netbox-plugin-tutorial)
- Geographic features powered by [GeoPandas](https://geopandas.org/), [Leaflet](https://leafletjs.com/), and [PostGIS](https://postgis.net/)

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.