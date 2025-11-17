### Apex Item

Item pricing tools

### Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
# 1. Get the app
cd $PATH_TO_YOUR_BENCH
bench get-app apex_item https://github.com/apexcadcam/apex_item_new.git

# 2. Install on your site
bench --site [your-site-name] install-app apex_item

# 3. Migrate database and load fixtures
bench --site [your-site-name] migrate

# 4. Build assets
bench build

# 5. Restart all services
bench restart

# 6. Clear cache
bench --site [your-site-name] clear-cache
```

### Features

- **Item Price Management**: Actual Qty, Reserved Qty, Available Qty fields
- **Stock Snapshot**: Refresh stock quantities manually
- **Auto-update**: Automatic quantity updates from Stock Ledger Entry
- **Mobile View**: Enhanced mobile item card display

### License

mit

