# Product Requirements Document (PRD)
## Apex Item - Item Pricing Tools

**Version:** 1.0.0  
**Date:** 2025-11-18  
**Status:** Approved  
**App Name:** apex_item  
**License:** MIT

---

## 1. Executive Summary

### 1.1 Overview
Apex Item is a Frappe Framework application designed to enhance Item Price management within ERPNext/Frappe systems. The app extends the standard Item Price doctype with real-time stock quantity tracking, automated updates, and an enhanced mobile-responsive user interface.

### 1.2 Problem Statement
Standard Item Price management lacks:
- Real-time visibility of stock availability
- Automatic synchronization with stock movements
- Mobile-optimized viewing experience
- Configurable display options for sales teams

### 1.3 Solution Overview
Apex Item provides:
- Automatic calculation and display of stock quantities (actual, reserved, available, waiting)
- Real-time synchronization with stock transactions
- Mobile-responsive card view for better sales team experience
- Configurable field display and customization options

---

## 2. Business Requirements

### 2.1 Business Objectives
- Improve sales team efficiency by providing real-time stock visibility
- Reduce manual data entry and errors
- Enhance mobile user experience for field sales teams
- Provide accurate stock availability at point of sale

### 2.2 Target Users
- **Primary Users:** Sales teams, Sales managers, Sales executives
- **Secondary Users:** Inventory managers, System administrators

### 2.3 Business Value
- **Time Savings:** Automatic stock updates eliminate manual refresh requirements
- **Accuracy:** Real-time data reduces inventory discrepancies
- **Productivity:** Mobile-optimized interface improves field sales efficiency
- **Revenue Impact:** Better stock visibility leads to informed sales decisions

---

## 3. Functional Requirements

### 3.1 Core Features

#### 3.1.1 Stock Quantity Management
**Priority:** High  
**Description:** Extend Item Price doctype with stock quantity fields

**Requirements:**
- Add custom fields to Item Price doctype:
  - `stock_warehouse` (Link to Warehouse) - Warehouse for stock calculation
  - `actual_qty` (Float, Read-only) - Total actual stock quantity
  - `reserved_qty` (Float, Read-only) - Total reserved quantity (sales + production + subcontract)
  - `available_qty` (Float, Read-only) - Available quantity (actual - reserved)
  - `waiting_qty` (Float, Read-only) - Quantity on confirmed Purchase Orders not yet received
  - `item_group` (Link to Item Group, Read-only) - Item Group from linked Item
  - `item_image` (Attach Image, Read-only) - Item image from linked Item

**Business Rules:**
- All quantity fields must be read-only and auto-calculated
- `available_qty = actual_qty - reserved_qty`
- `stock_warehouse` can be manually set or auto-populated from Item's default warehouse
- Quantity calculations must consider all warehouses if no specific warehouse is set

#### 3.1.2 Automatic Stock Updates
**Priority:** High  
**Description:** Automatically update Item Price stock quantities when related documents change

**Trigger Events:**
1. **Bin Updates** (`on_update` event)
   - When Bin actual_qty or reserved_qty changes
   - Update related Item Prices for the affected item and warehouse

2. **Stock Ledger Entry** (`on_submit`, `on_cancel` events)
   - When stock transactions are submitted or cancelled
   - Update Item Prices for affected items

3. **Sales Order** (`on_submit`, `on_cancel`, `on_update_after_submit` events)
   - When Sales Orders affect stock reservations
   - Update Item Price reserved quantities

4. **Purchase Order** (`on_submit`, `on_cancel`, `on_update_after_submit` events)
   - When Purchase Orders are confirmed or cancelled
   - Update Item Price waiting quantities

5. **Purchase Receipt** (`on_submit`, `on_cancel` events)
   - When goods are received or receipt is cancelled
   - Update Item Price actual quantities

**Business Rules:**
- Updates should be queued for background processing to avoid blocking transactions
- Updates should be batched for performance
- Failed updates should be logged but not block the triggering transaction

#### 3.1.3 Scheduled Reconciliation
**Priority:** Medium  
**Description:** Periodic reconciliation to ensure data consistency

**Requirements:**
- Cron job scheduled every 5 minutes (`*/5 * * * *`)
- Reconcile Item Price quantities for recently modified Bins (last 15 minutes)
- Limit to 500 items per run to avoid performance issues
- Should be resilient to failures (log errors, don't crash)

**Business Rules:**
- Only process Bins modified in the last 15 minutes
- Process maximum 500 items per run
- Safe to run even if workers are down

#### 3.1.4 Manual Stock Refresh
**Priority:** High  
**Description:** Allow users to manually refresh stock quantities

**Features:**
1. **Form View Refresh**
   - "Refresh Stock" button in Item Price form
   - Refreshes current Item Price record only
   - Shows visual feedback (loading, success/error message)

2. **List View Bulk Refresh**
   - "Refresh Stock (Current View)" button in Item Price list
   - Refreshes all items matching current filters
   - Respects filter limit (default 1000 items max)

3. **API Endpoints**
   - `refresh_item_price(name)` - Refresh single Item Price
   - `refresh_item_prices(names)` - Refresh multiple Item Prices
   - `refresh_item_prices_by_filters(filters, limit)` - Refresh by filters
   - `update_all_item_price_qty()` - System Manager only, refresh all

**Business Rules:**
- Bulk refresh operations should have safety limits
- Progress feedback for large operations
- Throttling for auto-refresh (60 seconds minimum between refreshes)

#### 3.1.5 Item Price Card Configuration
**Priority:** Medium  
**Description:** Configurable mobile card view for Item Price list

**Custom DocTypes:**
1. **Item Price Card Setting** (Single DocType)
   - `show_item_image` (Check) - Show/hide item images in cards
   - `empty_state_text` (Small Text) - Custom empty state message
   - `card_fields` (Child Table) - Configured card fields

2. **Item Price Card Field** (Child DocType)
   - `fieldname` (Select) - Field to display
   - `label` (Data) - Custom label
   - `css_class` (Data) - CSS class for styling
   - `is_full_width` (Check) - Full width display
   - `hide_if_zero` (Check) - Hide if value is zero

**Allowed Fieldnames:**
- `price_list_rate`, `currency`, `available_qty`, `actual_qty`, `reserved_qty`
- `waiting_qty`, `brand`, `item_group`, `stock_warehouse`, `item_code`, `item_name`, `uom`

**Business Rules:**
- Default configuration must be provided on installation
- Users can customize field order, labels, and display options
- Configuration changes must be cached for performance

#### 3.1.6 Mobile-Responsive Card View
**Priority:** High  
**Description:** Enhanced mobile view for Item Price list

**Features:**
1. **Responsive Design**
   - Desktop: Standard list view
   - Mobile (≤768px): Card-based view
   - Automatic switching based on screen width

2. **Card Display**
   - Item name and code as header
   - Optional item image thumbnail
   - Configurable fields in grid layout (3 columns)
   - Full-width fields for special cases (e.g., waiting_qty)

3. **Visual Features**
   - Color-coded quantities (green for available, red for zero)
   - Icons for field types
   - Clickable cards to open Item Price form
   - Custom styling via CSS classes

4. **Auto-Sync**
   - Automatic background refresh when list view loads
   - Throttled to maximum once per 60 seconds per route+filter combination
   - Subtle success indicator

**Business Rules:**
- Cards should only show on mobile devices
- Desktop users see standard list view
- Auto-refresh should not interfere with user actions
- Empty state should be user-friendly

---

## 4. Technical Specifications

### 4.1 Technology Stack

**Backend:**
- **Language:** Python 3.10+
- **Framework:** Frappe Framework 15.x
- **ORM:** Frappe Database API
- **Caching:** Redis (via Frappe Cache)
- **Queue System:** Frappe Background Jobs

**Frontend:**
- **Language:** JavaScript (ES6+)
- **Framework:** Frappe UI
- **Libraries:** jQuery, Frappe Client API
- **Styling:** CSS3 with media queries

**Database:**
- **Type:** MariaDB/PostgreSQL (via Frappe)
- **Access:** Frappe ORM

### 4.2 Architecture

#### 4.2.1 Module Structure
```
apex_item/
├── api.py                      # API endpoints
├── item_price_config.py        # Card configuration logic
├── item_price_hooks.py         # Document event handlers
├── install.py                  # Installation hooks
├── hooks.py                    # Frappe hooks configuration
├── fixtures/                   # Custom fields and property setters
├── doctype/                    # Custom DocTypes
│   ├── item_price_card_field/
│   └── item_price_card_setting/
└── public/js/                  # Frontend JavaScript
    ├── item_price_form.js
    └── item_price_list.js
```

#### 4.2.2 Key Components

**1. Stock Calculation Engine (`item_price_hooks.py`)**
- `_get_stock_snapshot()` - Calculate stock quantities from Bin and Purchase Orders
- `set_stock_fields()` - Apply snapshot to Item Price document
- `update_item_prices_for_item()` - Batch update for multiple Item Prices
- Uses background jobs for performance

**2. Configuration Manager (`item_price_config.py`)**
- Field definitions and metadata
- Default card configuration
- Field validation and normalization

**3. API Layer (`api.py`)**
- Whitelisted API methods
- Caching for card configuration
- Bulk update operations

**4. Frontend Controllers**
- Form view controller (`item_price_form.js`)
- List view controller (`item_price_list.js`)
- Card rendering and responsive logic

### 4.3 Data Model

#### 4.3.1 Item Price Extensions
- Custom fields added via fixtures
- No database schema changes (uses Frappe custom fields)
- Fields stored in `tabCustom Field` and Item Price table

#### 4.3.2 Custom DocTypes
- **Item Price Card Setting:** Single DocType with child table
- **Item Price Card Field:** Child DocType for field configuration

### 4.4 Caching Strategy

**Cache Keys:**
- `apex_item:item_price_card_config` - Card configuration cache
- Cache includes user and settings signature
- Invalidated when List View Settings or Card Settings change

**Cache Invalidation:**
- On List View Settings modification
- On Item Price Card Setting modification
- Manual clear via API

---

## 5. API Documentation

### 5.1 Public API Endpoints

All endpoints require authentication and appropriate permissions.

#### 5.1.1 Get Item Price Card Config
```python
@frappe.whitelist()
def get_item_price_card_config(force: bool = False) -> Dict[str, Any]
```
**Purpose:** Get mobile card configuration for Item Price list  
**Parameters:**
- `force` (bool, optional): Force refresh from database, bypass cache  
**Returns:** Dictionary with card configuration  
**Response Format:**
```json
{
  "show_item_image": 0,
  "empty_state_text": "لا توجد أصناف مطابقة",
  "fields": [
    {
      "fieldname": "price_list_rate",
      "label": "Price",
      "css_class": "price",
      "is_full_width": 0,
      "hide_if_zero": 0
    }
  ]
}
```

#### 5.1.2 Refresh Item Price
```python
@frappe.whitelist()
def refresh_item_price(name: str) -> dict
```
**Purpose:** Refresh stock quantities for a single Item Price  
**Parameters:**
- `name` (str, required): Item Price name  
**Returns:** Updated stock snapshot  
**Response Format:**
```json
{
  "actual_qty": 100.0,
  "reserved_qty": 20.0,
  "available_qty": 80.0,
  "waiting_qty": 50.0,
  "stock_warehouse": "Warehouse - ABC"
}
```

#### 5.1.3 Refresh Multiple Item Prices
```python
@frappe.whitelist()
def refresh_item_prices(names: list[str] | str) -> int
```
**Purpose:** Bulk refresh multiple Item Prices  
**Parameters:**
- `names` (list[str] | str): List of Item Price names or comma-separated string  
**Returns:** Number of items updated  

#### 5.1.4 Refresh by Filters
```python
@frappe.whitelist()
def refresh_item_prices_by_filters(filters=None, limit: int = 1000) -> int
```
**Purpose:** Refresh Item Prices matching list view filters  
**Parameters:**
- `filters` (dict | str, optional): Frappe filters (JSON string or dict)
- `limit` (int, default: 1000): Maximum items to refresh  
**Returns:** Number of items updated  

#### 5.1.5 Update All Item Prices
```python
@frappe.whitelist()
def update_all_item_price_qty() -> dict
```
**Purpose:** Refresh all Item Prices in the system  
**Permissions:** System Manager only  
**Parameters:** None  
**Returns:** Summary with updated count  
**Response Format:**
```json
{
  "success": true,
  "updated": 1500,
  "total": 1500,
  "message": "✓ Updated 1500 Item Prices successfully!"
}
```

#### 5.1.6 Get Card Setting Debug
```python
@frappe.whitelist()
def get_item_price_card_setting_debug() -> Dict[str, Any]
```
**Purpose:** Get raw Item Price Card Setting for debugging  
**Returns:** Complete card setting document  

#### 5.1.7 Ensure Card Setting
```python
@frappe.whitelist()
def ensure_item_price_card_setting() -> Dict[str, Any]
```
**Purpose:** Create or update Item Price Card Setting with defaults  
**Returns:** Card setting document  

#### 5.1.8 Reset Card Setting
```python
@frappe.whitelist()
def reset_item_price_card_setting() -> Dict[str, Any]
```
**Purpose:** Forcefully recreate Item Price Card Setting with defaults  
**Returns:** Card setting document  

---

## 6. User Stories

### 6.1 As a Sales Executive
- **US-1:** As a sales executive, I want to see real-time stock availability in Item Price list, so I can confidently quote delivery times to customers.
- **US-2:** As a sales executive, I want to refresh stock quantities on-demand, so I have the latest data when making sales decisions.
- **US-3:** As a sales executive using a mobile device, I want to view Item Prices in an optimized card format, so I can quickly access information in the field.

### 6.2 As a Sales Manager
- **US-4:** As a sales manager, I want stock quantities to update automatically when stock moves, so my team always has accurate information.
- **US-5:** As a sales manager, I want to customize which fields appear in the mobile card view, so the display matches our sales process.

### 6.3 As a System Administrator
- **US-6:** As a system administrator, I want the app to install with sensible defaults, so setup is quick and straightforward.
- **US-7:** As a system administrator, I want to bulk refresh all Item Prices, so I can ensure data consistency after system changes.
- **US-8:** As a system administrator, I want automatic reconciliation to run periodically, so data stays accurate even if background jobs fail.

---

## 7. UI/UX Requirements

### 7.1 Item Price Form View

**Requirements:**
1. **Stock Fields Section**
   - Display stock_warehouse, actual_qty, reserved_qty, available_qty, waiting_qty
   - All quantity fields should be read-only with clear labels
   - Visual indicator for zero available quantity

2. **Actions**
   - "Refresh Stock" button in toolbar
   - Menu item for refresh action
   - Loading indicator during refresh
   - Success/error alert after refresh

**Design Guidelines:**
- Use standard Frappe form styling
- Quantity fields should be right-aligned
- Color code available quantity (green if >0, red if 0)

### 7.2 Item Price List View

**Requirements:**
1. **Desktop View**
   - Standard Frappe list view
   - Custom indicator based on available quantity
   - "Refresh Stock (Current View)" button in toolbar

2. **Mobile View (≤768px)**
   - Hide standard list view
   - Display card-based layout
   - Responsive grid (3 columns)
   - Click cards to open form

3. **Card Design**
   - Header: Item image (optional), Item name, Item code
   - Body: Configurable fields in grid
   - Full-width fields span 3 columns
   - Color-coded values
   - Touch-friendly sizing

4. **Auto-Refresh**
   - Automatic background refresh on load
   - Throttled to 60 seconds minimum
   - Subtle success notification

**Design Guidelines:**
- Cards should be visually distinct and easy to scan
- Use icons to enhance field identification
- Maintain Frappe design language
- Ensure WCAG AA accessibility compliance

### 7.3 Item Price Card Setting Form

**Requirements:**
1. **Settings Section**
   - Show item image checkbox
   - Empty state text input

2. **Card Fields Table**
   - Add/remove/reorder fields
   - Configure label, CSS class, full-width, hide-if-zero
   - Preview of allowed fields

**Design Guidelines:**
- Use Frappe child table component
- Provide field validation and help text
- Show preview of configuration

---

## 8. Integration Points

### 8.1 ERPNext Integration

**Required DocTypes:**
- Item Price (extends)
- Bin (listens to events)
- Stock Ledger Entry (listens to events)
- Sales Order (listens to events)
- Purchase Order (listens to events)
- Purchase Receipt (listens to events)
- Item (references)
- Item Group (references)
- Warehouse (references)

**Integration Methods:**
- Document events (hooks)
- Custom fields (fixtures)
- Property setters (fixtures)

### 8.2 Frappe Framework Integration

**Hooks Used:**
- `doc_events` - Document event handlers
- `doctype_js` - Form view JavaScript
- `doctype_list_js` - List view JavaScript
- `scheduler_events` - Scheduled tasks
- `fixtures` - Custom fields and property setters
- `after_install` - Installation setup
- `after_migrate` - Migration setup
- `before_uninstall` - Cleanup

**Dependencies:**
- Frappe Framework 15.x
- ERPNext (optional, but recommended)

---

## 9. Performance Requirements

### 9.1 Response Times
- Card configuration API: < 200ms (cached)
- Single Item Price refresh: < 500ms
- Bulk refresh (100 items): < 5 seconds
- List view load with auto-refresh: < 3 seconds

### 9.2 Scalability
- Support for 10,000+ Item Prices
- Batch processing for bulk operations
- Background jobs for event-driven updates
- Efficient database queries with proper indexing

### 9.3 Optimization Strategies
- Redis caching for card configuration
- Batch updates for multiple Item Prices
- Debounced/throttled auto-refresh
- Limit bulk operations (default 1000 items)

---

## 10. Security Requirements

### 10.1 Authentication & Authorization
- All API endpoints require authentication
- Bulk operations restricted to appropriate roles
- System Manager only for `update_all_item_price_qty()`

### 10.2 Data Protection
- Read-only fields cannot be modified via API
- Input validation on all API parameters
- SQL injection prevention via Frappe ORM

### 10.3 Error Handling
- Graceful error handling for failed updates
- Error logging without exposing sensitive information
- User-friendly error messages

---

## 11. Installation & Configuration

### 11.1 Prerequisites
- Frappe Framework 15.x installed
- Bench CLI installed
- Redis and MariaDB/PostgreSQL running
- ERPNext installed (recommended)

### 11.2 Installation Steps

1. **Get the app:**
   ```bash
   cd $PATH_TO_YOUR_BENCH
   bench get-app apex_item https://github.com/apexcadcam/apex_item_new.git
   ```

2. **Install on site:**
   ```bash
   bench --site [your-site-name] install-app apex_item
   ```

3. **Migrate database:**
   ```bash
   bench --site [your-site-name] migrate
   ```

4. **Build assets:**
   ```bash
   bench build
   ```

5. **Restart services:**
   ```bash
   bench restart
   ```

6. **Clear cache:**
   ```bash
   bench --site [your-site-name] clear-cache
   ```

### 11.3 Configuration

**Initial Setup:**
- Custom fields are automatically installed
- Default Item Price Card Setting is created
- Scheduled task is automatically registered

**Customization:**
1. Navigate to Item Price Card Setting
2. Configure card fields, labels, and display options
3. Enable/disable item images
4. Set custom empty state message

**Optional:**
- Configure default warehouse per item (if using ERPNext)
- Adjust scheduled reconciliation frequency (if needed)

### 11.4 Uninstallation

**Cleanup Process:**
- Custom fields are removed
- Property setters are removed
- Database columns are dropped (if applicable)
- Custom DocTypes are removed
- Scheduled tasks are removed

**Manual Cleanup:**
- Review and backup any customizations before uninstalling
- Ensure no dependencies on custom fields before removal

---

## 12. Testing Requirements

### 12.1 Unit Tests

**Test Coverage Required:**
- Stock calculation logic
- Field configuration utilities
- API endpoint validation
- Cache management

**Test Files:**
- `tests/test_item_price_hooks.py`
- `tests/test_item_price_config.py`
- `tests/test_api.py`

### 12.2 Integration Tests

**Test Scenarios:**
1. Bin update triggers Item Price refresh
2. Stock Ledger Entry submission updates Item Prices
3. Sales Order affects reserved quantities
4. Purchase Order affects waiting quantities
5. Scheduled reconciliation runs successfully

**Test Files:**
- `tests/test_integration.py`

### 12.3 Frontend Tests

**Test Coverage:**
- Form view refresh button functionality
- List view card rendering (mobile)
- Auto-refresh throttling
- Responsive layout switching

**Test Files:**
- `tests/test_frontend.py` (if applicable)

### 12.4 Performance Tests

**Test Scenarios:**
- Bulk refresh with 1000+ items
- Concurrent API requests
- Cache hit/miss performance
- Scheduled task execution time

### 12.5 Acceptance Criteria

**Installation:**
- ✅ App installs without errors
- ✅ Custom fields are created correctly
- ✅ Default configuration is applied
- ✅ Scheduled task is registered

**Functionality:**
- ✅ Stock quantities calculate correctly
- ✅ Automatic updates work on document events
- ✅ Manual refresh updates data
- ✅ Mobile card view displays correctly
- ✅ Configuration changes apply immediately

**Performance:**
- ✅ API responses meet timing requirements
- ✅ Bulk operations complete within limits
- ✅ No performance degradation on list view

---

## 13. Future Enhancements

### 13.1 Potential Features (Not in Scope)

1. **Multi-Warehouse View**
   - Display stock from multiple warehouses in one view
   - Warehouse-specific pricing

2. **Stock Alerts**
   - Low stock notifications
   - Out of stock warnings

3. **Analytics Dashboard**
   - Stock movement trends
   - Sales velocity metrics

4. **Export/Import**
   - Bulk update via Excel import
   - Export stock snapshot

5. **Mobile App Integration**
   - Native mobile app support
   - Offline mode capability

---

## 14. Glossary

- **Item Price:** Frappe doctype for storing item pricing information
- **Bin:** ERPNext doctype tracking stock in warehouses
- **Stock Ledger Entry:** Transaction record for stock movements
- **Actual Qty:** Total physical stock quantity
- **Reserved Qty:** Quantity allocated to sales orders, production, or subcontracting
- **Available Qty:** Quantity available for sale (Actual - Reserved)
- **Waiting Qty:** Quantity on confirmed Purchase Orders not yet received
- **DocType:** Frappe term for a data model/table
- **Hook:** Frappe mechanism for extending functionality
- **Fixture:** Predefined data loaded during app installation

---

## 15. Change Log

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0.0 | 2025-11-18 | Initial PRD | Apex Item Team |

---

## 16. Approval

**Product Owner:** _________________  
**Technical Lead:** _________________  
**Date:** _________________

---

*End of PRD*

