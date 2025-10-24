import pytest
from datetime import datetime, timedelta

pytestmark = pytest.mark.asyncio

@pytest.mark.postgres
async def test_postgres_connect_disconnect(postgres_db):
    """Test PostgreSQL connection and disconnection."""
    # Fixture sets connected = True
    assert postgres_db.is_connected
    
    # Mock disconnect
    postgres_db._connected = False
    assert not postgres_db.is_connected
    
    # Mock reconnect
    postgres_db._connected = True
    assert postgres_db.is_connected

@pytest.mark.postgres
async def test_postgres_basic_operations(postgres_db, sample_data):
    """Test basic CRUD operations with PostgreSQL."""
    user = sample_data["users"][0]
    
    # Get mock connection
    mock_conn = await postgres_db._pool.acquire().__aenter__()
    mock_conn.execute.return_value = "INSERT 0 1"  # Postgres response format
    
    # Create table
    result = await postgres_db.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL
        )
    """)
    assert result == 1
    
    # Insert data
    result = await postgres_db.execute(
        "INSERT INTO users (id, name, email) VALUES (:id, :name, :email)",
        user
    )
    assert result == 1
    
    # Get the mock connection from the pool
    mock_conn = await postgres_db._pool.acquire().__aenter__()
    
    # Mock query to return user data
    mock_conn.fetch.return_value = [
        {"id": user["id"], "name": user["name"], "email": user["email"]}
    ]
    
    # Query data
    results = await postgres_db.query(
        "SELECT * FROM users WHERE id = :id",
        {"id": user["id"]}
    )
    assert len(results) == 1
    assert results[0]["name"] == user["name"]
    
    # Update data
    result = await postgres_db.execute(
        "UPDATE users SET name = :name WHERE id = :id",
        {"name": "Updated Name", "id": user["id"]}
    )
    assert result == 1

@pytest.mark.postgres
async def test_postgres_with_cache(postgres_db, memory_cache, sample_data):
    """Test PostgreSQL with caching."""
    postgres_db._cache = memory_cache
    
    # Get the mock connection
    mock_conn = await postgres_db._pool.acquire().__aenter__()
    mock_conn.fetch.return_value = [
        {"id": 1, "name": "Test Product", "price": 9.99}
    ]
    
    # First query - should hit database and cache result
    query = "SELECT * FROM products WHERE id = :id"
    params = {"id": 1}
    
    results1 = await postgres_db.query(query, params)
    assert results1[0]["name"] == "Test Product"
    
    # Second query - should hit cache
    results2 = await postgres_db.query(query, params)
    assert results2[0]["name"] == "Test Product"
    
    # Verify results are identical
    assert results1 == results2

@pytest.mark.timescale
async def test_timescale_hypertable(timescale_db):
    """Test TimescaleDB hypertable creation and basic operations."""
    from datetime import datetime
    
    # Get the mock connection
    mock_conn = await timescale_db._pool.acquire().__aenter__()
    mock_conn.execute.return_value = "INSERT 0 1"  # Postgres response format
    
    # Create a regular table (mocked)
    result = await timescale_db.execute("""
        CREATE TABLE metrics (
            time TIMESTAMPTZ NOT NULL,
            sensor_id TEXT NOT NULL,
            temperature DOUBLE PRECISION NOT NULL
        )
    """)
    assert result == 1
    
    # Convert to hypertable (mocked)
    success = await timescale_db.create_hypertable(
        "metrics",
        "time",
        chunk_time_interval="1 day"
    )
    assert success
    
    # Mock time bucket query results
    mock_conn.fetch.return_value = [
        {
            "bucket": datetime.now(),
            "sensor_id": "sensor1",
            "avg_temp": 21.0
        }
    ]
    
    # Test time bucket query
    results = await timescale_db.time_bucket_query(
        bucket_width="1 hour",
        time_column="time",
        table_name="metrics",
        select_columns=["sensor_id"],
        aggregates=["AVG(temperature) as avg_temp"],
        order_by="bucket DESC",
        limit=3
    )
    
    assert len(results) > 0
    assert "avg_temp" in results[0]
    assert "sensor_id" in results[0]
    assert "bucket" in results[0]

@pytest.mark.timescale
async def test_timescale_retention_policy(timescale_db):
    """Test TimescaleDB retention policy."""
    # Mocked - create hypertable
    success = await timescale_db.create_hypertable("logs", "time")
    assert success
    
    # Add retention policy (mocked)
    success = await timescale_db.add_retention_policy(
        "logs",
        interval="7 days"
    )
    assert success

@pytest.mark.timescale
async def test_timescale_continuous_aggregate(timescale_db):
    """Test TimescaleDB continuous aggregate creation."""
    # Mocked - create hypertable
    success = await timescale_db.create_hypertable("readings", "time")
    assert success
    
    # Create continuous aggregate (mocked)
    success = await timescale_db.continuous_aggregate(
        view_name="readings_hourly",
        hypertable="readings",
        bucket_width="1 hour",
        time_column="time",
        select_columns=["sensor_id"],
        aggregates=[
            "AVG(value) as avg_value",
            "MAX(value) as max_value",
            "MIN(value) as min_value"
        ],
        with_data=False
    )
    assert success
