````markdown
# Flask JWT Auth API

This is a minimal and extendable Flask API implementing **JWT Authentication** using `Flask-JWT-Extended`, with access and refresh token support, Redis-powered token revocation, role-based protection possibilities, and essential auth endpoints.

---

## 🚀 Features

- User registration and login
- JWT-based access and refresh tokens
- Logout with token revocation using Redis
- Fresh-token support for sensitive operations
- Profile management with protected routes
- Token verification and refresh flow
- Secure configuration via environment variables

---

## ⚙️ Environment Setup

### 1. Clone this repo:

```bash
git clone https://github.com/yourusername/flask_jwt_auth.git
cd flask_jwt_auth
````

### 2. Create and activate virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Export environment variables

```bash
export USER=user
export PWD=your_password
export HOST=localhost
export DB=your_db_name
export ENV=dev

# JWT secret key (use a strong, secure key!)
export JWT_SECRET_KEY=''

# Flask App Server
export API_HOST=0.0.0.0
export API_PORT=5000
```

---

## 🧪 API Endpoints & CURL Examples

### 🔐 Register a User

```bash
curl -X POST http://localhost:5000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "ezradev", "email": "ezra@example.com", "password": "securepass"}'
```

### 🔐 Login (Get Access & Refresh Tokens)

```bash
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "ezra@example.com", "password": "securepass"}'
```

### 🔒 Get Authenticated User Profile

```bash
curl -X GET http://localhost:5000/users/me \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

### ✏️ Update Username

```bash
curl -X PUT http://localhost:5000/users/me \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{"username": "ezra_updated"}'
```

### 🔄 Refresh Access Token

```bash
curl -X POST http://localhost:5000/auth/token/refresh \
  -H "Authorization: Bearer <REFRESH_TOKEN>"
```

### 🚪 Logout (Invalidate Access Token)

```bash
curl -X POST http://localhost:5000/auth/logout \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

---

## 🛠 Requirements

* Python 3.8+
* Redis running locally on `localhost:6379`
* Flask + Flask-JWT-Extended
* dotenv (optional for local `.env` loading)

---

## 📦 Project Structure

```
├── api/
│   └── v1/
│       └── views/
│           ├── __init__.py
│           └── users.py
├── models/
│   └── user.py
├── app.py
├── requirements.txt
└── README.md
```

---

## 🧱 Next Steps

* Add role-based access control
* Add email confirmation (optional)
* Add rate limiting to auth endpoints
* Enable HTTPS and secure cookies for production

---

## 💡 Tips

* Redis is used for blacklisting revoked tokens with TTL set to match the token's expiry.
* Refresh tokens must be kept secure and only used when access tokens expire.
* `@jwt_required(fresh=True)` ensures sensitive endpoints require a recently issued token.

---

## 📜 License

This project is open for learning and internal use. For full open-source use, add an appropriate license.

```

