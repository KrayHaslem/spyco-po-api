# SPYCO PO API

Flask backend for the SPYCO Purchase Order system.

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your database credentials
```

4. Create the PostgreSQL database:
```bash
createdb spyco_po
```

5. Run the server:
```bash
python app.py
```

The API will be available at `http://localhost:5000`.

## Creating the First Admin User

After starting the server, you can create the first admin user by making a direct database insert or using a Python shell:

```python
from app import create_app
from db import db
from models.user import User

app = create_app()
with app.app_context():
    user = User(
        email="admin@example.com",
        first_name="Admin",
        last_name="User",
        is_admin=True,
    )
    user.set_password("password123")
    db.session.add(user)
    db.session.commit()
    print(f"Created admin user: {user.email}")
```

## API Endpoints

### Authentication
- `POST /api/auth/login` - Login
- `POST /api/auth/logout` - Logout
- `GET /api/auth/check-login` - Check login status
- `POST /api/auth/change-password` - Change password

### Purchase Orders
- `GET /api/po/` - List POs
- `POST /api/po/` - Create PO
- `GET /api/po/<id>` - Get PO
- `PUT /api/po/<id>` - Update PO
- `DELETE /api/po/<id>` - Delete PO
- `POST /api/po/<id>/submit` - Submit for approval
- `POST /api/po/<id>/approve` - Approve PO
- `POST /api/po/<id>/reject` - Reject PO

### Lookup (for combo boxes)
- `GET /api/lookup/vendors/search` - Search vendors
- `POST /api/lookup/vendors` - Quick create vendor
- `GET /api/lookup/units/search` - Search units
- `POST /api/lookup/units` - Quick create unit
- `GET /api/lookup/departments` - List departments

### Admin (requires admin privileges)
- CRUD `/api/admin/departments`
- CRUD `/api/admin/users`
- CRUD `/api/admin/vendors`
- CRUD `/api/admin/units`
- CRUD `/api/admin/approvers`
