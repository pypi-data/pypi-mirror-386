from pyspark.sql import SparkSession

from src.utilities import (
    remove_duplicates,
    fill_nulls,
    flatten_json,
    mask_dataframe
)
import json

spark = SparkSession.builder.master("local[*]").appName("Test").getOrCreate()


def test_remove_duplicates():
    df = spark.createDataFrame([
        ("Alice", "NY"), ("Alice", "NY"), ("Bob", "LA")
    ], ["name", "city"])
    result = remove_duplicates(df)
    assert result.count() == 2


def test_fill_nulls():
    df = spark.createDataFrame([
        (None, "NY"), ("Bob", None)
    ], ["name", "city"])
    result = fill_nulls(df, {"name": "NA", "city": "Unknown City"})
    rows = result.collect()
    assert rows[0]["name"] == "NA"
    assert rows[1]["city"] == "Unknown City"


def test_flatten_json_exploding_arrays():
    data = [{
        "id": 1,
        "name": "John",
        "address": {"city": "NY", "zipcode": 12345},
        "phones": [
            {"type": "home", "number": "1234"},
            {"type": "work", "number": "5678"}
        ]
    }]
    df = spark.read.json(spark.sparkContext.parallelize(data))

    result = flatten_json(df, explode_arrays=True)
    # Check flattened columns
    expected_cols = {
         "id",
         "name",
         "address_city",
         "address_zipcode",
         "phones_type",
         "phones_number"
                    }
    assert set(result.columns) == expected_cols
    assert result.count() == 2

    expected_row0 = {
        "id": 1,
        "name": "John",
        "address_city": "NY",
        "address_zipcode": 12345,
        "phones_type": "home",
        "phones_number": "1234"
        }

    expected_row1 = {
        "id": 1,
        "name": "John",
        "address_city": "NY",
        "address_zipcode": 12345,
        "phones_type": "work",
        "phones_number": "5678"
        }

    rows = result.collect()

    assert rows[0].asDict() == expected_row0
    assert rows[1].asDict() == expected_row1


def test_flatten_json_no_exploding_arrays():
    data = [{
        "id": 1,
        "name": "John",
        "address": {"city": "NY", "zipcode": 12345},
        "phones": [
            {"type": "home", "number": "1234"},
            {"type": "work", "number": "5678"}
        ]
    }]
    df = spark.read.json(spark.sparkContext.parallelize(data))

    result = flatten_json(df, explode_arrays=False)
    # Check flattened columns
    expected_cols = {"id", "name", "address_city", "address_zipcode", "phones"}
    assert set(result.columns) == expected_cols
    # Check number of output rows count
    assert result.count() == 1
    rows = result.collect()
    expected_row0 = {
        "id": 1,
        "name": "John",
        "address_city": "NY",
        "address_zipcode": 12345,
        "phones": [
            {"number": "1234", "type": "home"},
            {"number": "5678", "type": "work"}
            ]}

    row0 = rows[0].asDict()
    row0["phones"] = json.loads(row0["phones"])

    assert row0 == expected_row0


def test_full_mask():
    df = spark.createDataFrame(
        [
            (1, "Alice", "alice@example.com", "9876543210"),
            (2, "Bob", "bob@example.com", "9123456789"),
            (3, None, None, None),   # Null edge case
        ],
        ["id", "name", "email", "phone"]
    )
    masked = mask_dataframe(df, ["name"], default_mask="MASKED")
    rows = masked.select("name").collect()
    assert all(r.name == "MASKED" or r.name is None for r in rows)


def test_partial_mask():
    df = spark.createDataFrame(
        [
            (1, "Alice", "alice@example.com", "9876543210"),
            (2, "Bob", "bob@example.com", "9123456789"),
            (3, None, None, None),   # Null edge case
        ],
        ["id", "name", "email", "phone"]
    )
    masked = mask_dataframe(df, {"name": "partial"})
    rows = [r.name for r in masked.select("name").collect()]

    expected = ["Al***", "Bo*", None]
    for original, masked_val, expected_val in zip(
        ["Alice", "Bob", None],
        rows,
        expected,
    ):
        if original is None:
            assert masked_val is None
        else:
            # first 2 chars preserved
            assert masked_val.startswith(original[:2])
            # rest must be *
            assert set(masked_val[2:]) <= {"*"}
            # same length
            assert len(masked_val) == len(original)
            # matches expected output
            assert masked_val == expected_val


def test_hash_mask():
    df = spark.createDataFrame(
        [
            (1, "Alice", "alice@example.com", "9876543210"),
            (2, "Bob", "bob@example.com", "9123456789"),
            (3, None, None, None),   # Null edge case
        ],
        ["id", "name", "email", "phone"]
    )
    masked = mask_dataframe(df, {"email": "hash"})
    rows = [r.email for r in masked.select("email").collect()]

    for val in rows:
        if val is not None:
            # sha2 returns 64-char hex string (not bytes!)
            assert isinstance(val, str)
            assert len(val) == 64
            # ensure it only contains hex characters
            int(val, 16)  # will raise ValueError if not valid hex


def test_custom_expr_mask():
    df = spark.createDataFrame(
        [
            (1, "Alice", "alice@example.com", "9876543210"),
            (2, "Bob", "bob@example.com", "9123456789"),
            (3, None, None, None),   # Null edge case
        ],
        ["id", "name", "email", "phone"]
    )
    phone_expr = "expr:concat('XXX', substr(phone, -4, 4))"
    masked = mask_dataframe(df, {"phone": phone_expr})
    rows = [r.phone for r in masked.select("phone").collect()]
    assert rows[0] == "XXX3210"
    assert rows[1] == "XXX6789"
    assert rows[2] is None  # null case handled


def test_skip_nonexistent_column():
    df = spark.createDataFrame(
        [
            (1, "Alice", "alice@example.com", "9876543210"),
            (2, "Bob", "bob@example.com", "9123456789"),
            (3, None, None, None),   # Null edge case
        ],
        ["id", "name", "email", "phone"]
    )
    # Should not raise error if column doesn't exist
    masked = mask_dataframe(df, {"nonexistent": "full"})
    assert "nonexistent" not in masked.columns
