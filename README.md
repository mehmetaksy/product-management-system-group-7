# Product Management System – Group 7

CMPE341 Database Design & Management term project (Atılım University, 2026-2027 Fall).

A web application for **NetPoint**, a (fictional) IT & network equipment shop in Ankara,
for managing products, categories, suppliers and orders,
built with **Flask** and **PostgreSQL 16**, packaged with **Docker Compose**.

## Run

```bash
git clone <repo-url>
cd product-management-system-group-7
docker compose up --build
```

Open: **http://localhost** (on the server: `http://<SERVER_IP>`)

The database is created automatically from `db/init.sql` with all tables and sample data.

## Test accounts

| Role  | Username | Password |
|-------|----------|----------|
| admin | admin    | admin123 |
| staff | elif.sales  | staff123 |
| staff | kerem.depot | staff456 |

## Roles and permissions

| Action                                         | admin | staff |
|------------------------------------------------|:-----:|:-----:|
| View products, categories, suppliers, orders   |  ✔    |  ✔    |
| View reports (3 SQL queries)                   |  ✔    |  ✔    |
| Create orders                                  |  ✔    |  ✔    |
| Add / edit / delete products, categories, suppliers | ✔ |  ✘    |
| Edit / delete orders                           |  ✔    |  ✘    |
| Manage users                                   |  ✔    |  ✘    |

Passwords are stored hashed (PBKDF2-SHA256, `werkzeug.security`).

## Project structure

```
├── docker-compose.yml   # db + web services
├── db/
│   ├── init.sql         # tables, constraints, sample data
│   └── queries.sql      # the 3 report queries
└── app/
    ├── Dockerfile
    ├── requirements.txt
    ├── app.py           # Flask application
    ├── static/          # bootstrap.min.css (works offline)
    └── templates/       # HTML pages
```

## Useful commands

```bash
docker compose down -v                                         # stop and delete data (re-runs init.sql next time)
docker exec -it pms_db psql -U pms_user -d product_db          # open SQL console
docker exec -i pms_db psql -U pms_user -d product_db < db/queries.sql   # run the 3 queries
```

## Team

- Name Surname – Student ID
- Name Surname – Student ID
- Name Surname – Student ID
