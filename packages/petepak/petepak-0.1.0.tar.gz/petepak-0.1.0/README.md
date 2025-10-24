# Petepak

**SQL-like data manipulation for Python lists of dictionaries**

Petepak provides a comprehensive set of functions for data manipulation that mimics SQL operations but works directly on Python lists of dictionaries. It's a lightweight alternative to pandas for simple data operations.

## Features

- 🔍 **SQL-like operations**: select, filter, join, group_by, order_by
- 🔗 **Multiple join types**: inner, left, right, outer joins  
- 📁 **CSV I/O**: read_csv, write_csv with schema support
- 🔄 **Data transformation**: rename, transform, distinct
- 📊 **Sorting algorithms**: bubble, merge, quick sort
- 🛡️ **Safe expressions**: Secure string-to-lambda conversion
- ⚡ **Lightweight**: No heavy dependencies like pandas

## Installation

### From PyPI (when published)

```bash
pip install petepak
```


## Quick Start

```python
from petepak import select, filter, join, group_by, order_by

# Sample data
users = [
    {'id': 1, 'name': 'Alice', 'age': 25, 'city': 'New York'},
    {'id': 2, 'name': 'Bob', 'age': 30, 'city': 'Boston'},
    {'id': 3, 'name': 'Charlie', 'age': 35, 'city': 'New York'}
]

orders = [
    {'user_id': 1, 'product': 'Laptop', 'amount': 1200},
    {'user_id': 2, 'product': 'Mouse', 'amount': 25},
    {'user_id': 1, 'product': 'Monitor', 'amount': 300}
]

# Filter users by age
young_users = filter(users, "a.age < 30")
print(young_users)  # [{'id': 1, 'name': 'Alice', 'age': 25, 'city': 'New York'}]

# Select specific columns
names = select(users, ['name', 'city'])
print(names)  # [{'name': 'Alice', 'city': 'New York'}, ...]

# Join users with orders
user_orders = join(users, orders, "a.id == b.user_id", join_type="inner")
print(user_orders)  # Combined data with prefixed columns

# Group by city
by_city = group_by(users, 'city')
print(by_city)  # [[users from New York], [users from Boston]]

# Sort by age
sorted_users = order_by(users, 'age', reverse=True)
print(sorted_users)  # Users sorted by age descending
```

## Core Operations

### Filtering Data

```python
from petepak import filter

data = [{'score': 90}, {'score': 75}, {'score': 85}]

# Using expression strings (SQL-like)
high_scores = filter(data, "a.score >= 80")
print(high_scores)  # [{'score': 90}, {'score': 85}]

# Using lambda functions (Python-like)
high_scores = filter(data, lambda row: row.get('score', 0) >= 80)
print(high_scores)  # [{'score': 90}, {'score': 85}]
```

### Joining Data

```python
from petepak import join

users = [{'id': 1, 'name': 'Alice'}, {'id': 2, 'name': 'Bob'}]
orders = [{'user_id': 1, 'product': 'Laptop'}, {'user_id': 2, 'product': 'Mouse'}]

# Inner join
result = join(users, orders, "a.id == b.user_id", join_type="inner")
print(result)
# [{'user_id': 1, 'user_name': 'Alice', 'order_user_id': 1, 'order_product': 'Laptop'}, ...]

# Left join
result = join(users, orders, "a.id == b.user_id", join_type="left")
# Includes all users, even those without orders
```

### CSV Operations

```python
from petepak import read_csv, write_csv

# Read CSV with schema
data = read_csv('users.csv', schema={'id': int, 'age': int, 'score': float})

# Write to CSV
write_csv(data, 'output.csv')
```

### Data Transformation

```python
from petepak import transform, rename, distinct

# Add computed columns
data = [{'name': 'Alice', 'score': 90}]
result = transform(data, 'grade', lambda row: 'A' if row['score'] >= 90 else 'B')
print(result)  # [{'name': 'Alice', 'score': 90, 'grade': 'A'}]

# Rename columns
renamed = rename(data, {'name': 'full_name'})
print(renamed)  # [{'full_name': 'Alice', 'score': 90}]

# Remove duplicates
unique = distinct(data, 'name')
```

## Advanced Examples

### E-commerce Analysis

```python
from petepak import *

# Load data
customers = read_csv('customers.csv', schema={'id': int, 'age': int})
orders = read_csv('orders.csv', schema={'customer_id': int, 'amount': float})

# Join customers with orders
customer_orders = join(customers, orders, "a.id == b.customer_id", 
                      join_type="left", list1_name="customer", list2_name="order")

# Filter high-value customers
high_value = filter(customer_orders, "a.order_amount > 100")

# Group by age ranges
age_groups = group_by(high_value, lambda row: (row['customer_age'] // 10) * 10)

# Display results
display_grouped(age_groups, 'age_range')
```

### Data Processing Pipeline

```python
from petepak import *

# 1. Load and clean data
raw_data = read_csv('sales.csv', schema={'amount': float, 'date': str})
clean_data = filter(raw_data, "a.amount > 0")

# 2. Transform data
processed = transform(clean_data, {
    'month': lambda row: row['date'].split('-')[1],
    'category': lambda row: 'high' if row['amount'] > 1000 else 'low'
})

# 3. Aggregate by month
monthly = group_by(processed, 'month')

# 4. Calculate totals
totals = []
for group in monthly:
    total = sum(row['amount'] for row in group)
    totals.append({'month': group[0]['month'], 'total': total})

# 5. Sort and display
final = order_by(totals, 'total', reverse=True)
display(final)
```

## API Reference

### Core Functions

- `select(rows, columns)` - Select specific columns
- `filter(rows, predicate)` - Filter rows using expressions or functions
- `join(list1, list2, expr, join_type)` - Join two datasets
- `group_by(rows, keys)` - Group rows by key values
- `order_by(rows, keys, reverse)` - Sort rows
- `distinct(rows, keys)` - Remove duplicate rows

### I/O Functions

- `read_csv(file_path, schema=None)` - Read CSV files
- `write_csv(rows, file_path)` - Write CSV files
- `display(rows)` - Pretty print data
- `display_grouped(groups, keys)` - Display grouped data

### Sorting Algorithms

- `bubble_sort(data, key, reverse)` - Bubble sort implementation
- `merge_sort(data, key, reverse)` - Merge sort implementation  
- `quick_sort(data, key, reverse)` - Quick sort implementation

## Development


### Running tests

```bash
pytest
```

### Code formatting

```bash
black petepak tests
```

### Linting

```bash
flake8 petepak tests
```


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

### 0.1.0 (2024-01-01)

- Initial release
- SQL-like data manipulation functions
- CSV I/O with schema support
- Multiple sorting algorithms
- Comprehensive test suite (137 tests)
- 78% code coverage
