## Postgres setup

```
docker run --name local-postgres \
  -e POSTGRES_PASSWORD=mysecretpassword \
  -v pgdata:/var/lib/postgresql/data \
  -p 5432:5432 \
  -d postgres
```

## Data Definition scripts

create database 
```
Get-Content setup.sql | docker exec -i postgres-local psql -U postgres
```