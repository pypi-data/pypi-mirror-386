from causum import UniversalClient

client = UniversalClient(profiles="./profiles.json")

# Query MongoDB ED
result = client.execute(
    profile="mongodb_ed",
    query='db.vitals_ed.find({})',
    max_rows=2
)

print(result)
print('.' * 34)

# Query PostgreSQL Admin
result = client.execute(
    profile="postgres_admin",
    query="SELECT * FROM patients LIMIT 2"
)

print(result)
print('.' * 34)