from redashAPI import RedashAPIClient

# Create API client instance
"""
    :args:
    API_KEY
    REDASH_HOST (optional): `http://localhost:5000` by default
"""
Redash = RedashAPIClient(API_KEY, REDASH_HOST)
### EXAMPLE ###

# List all Data Sources
res = Redash.get('data_sources')
res.json()
"""
[
    {
        'name': 'data_source1',
        'pause_reason': None,
        'syntax': 'sql',
        'paused': 0,
        'view_only': False,
        'type': 'pg',
        'id': 1
    },
    ...
]
"""

# Retrieve specific Data Source
res = Redash.get('data_sources/1')
res.json()
"""
{
    "scheduled_queue_name": "scheduled_queries",
    "name": "test1",
    "pause_reason": "None",
    "queue_name": "queries",
    "syntax": "sql",
    "paused": 0,
    "options": {
        "password": "--------",
        "dbname": "bi",
        "user": ""
    },
    "groups": {
        "1":False
    },
    "type": "pg",
    "id": 1
}
"""

# Create New Data Source
Redash.post('data_sources', {
    "name": "New Data Source",
    "type": "pg",
    "options": {
        "dbname": DB_NAME,
        "host": DB_HOST,
        "user": DB_USER,
        "passwd": DB_PASSWORD,
        "port": DB_PORT
    }
})
"""
{
    "scheduled_queue_name": "scheduled_queries",
    "name": "New Data Source",
    "pause_reason": "None",
    "queue_name": "queries",
    "syntax": "sql",
    "paused": 0,
    "options": {
        "dbname": DB_NAME,
        "host": DB_HOST,
        "user": DB_USER,
        "passwd": DB_PASSWORD,
        "port": DB_PORT
    },
    "groups": {
        "2": False
    },
    "type": "pg",
    "id": 2
}
"""

# Delete specific Data Source
Redash.delete('data_sources/2')

### EXAMPLE ###

Redash.create_data_source("pg", "First Data Source", {
    "dbname": DB_NAME,
    "host": DB_HOST,
    "user": DB_USER,
    "passwd": DB_PASSWORD,
    "port": DB_PORT
})

### EXAMPLE ###

Redash.create_query(1, "First Query", "SELECT * FROM table_name;")

### EXAMPLE ###

Redash.refresh_query(1)


### EXAMPLE ###

Redash.generate_query_results(1)

### EXAMPLE ###

Redash.query_and_wait_result(1, 'select * from my_table;', 60)

### EXAMPLE 1 ###

Redash.create_visualization(1, "table", "First Visualization", columns=[
    {"name": "column1", "type": "string"},
    {"name": "column2", "type": "datetime"}
])

### EXAMPLE 2 ###
Redash.create_visualization(1, "line", "Second Visualization", x_axis="column1", y_axis=[
    {"type": "line", "name": "column2", "label": "c2"}
])

## EXAMPLE ###

Redash.create_dashboard("First Dashboard")
### EXAMPLE 1 ###

Redash.add_widget(1, text="Test")

### EXAMPLE 2 ###
Redash.add_widget(1, visualization_id=1, full_width=True)

### EXAMPLE ###

url = Redash.publish_dashboard(1)
