# Invoice Automation System

A web application for managing accounts-payable and accounts-receivable invoices. It combines a Flask API, a React interface, MongoDB storage, invoice document processing, and role-based review workflows.

## Features

- Upload PDF and image invoices for text extraction and categorization.
- Review, submit, approve, reject, cancel, and mark accounts-payable invoices as paid.
- Manage vendors, customers, products, and company details.
- Create and track accounts-receivable invoices.
- View dashboards, approval queues, audit history, and spending reports.
- Export invoice data to CSV and perform bulk approval.
- Authenticate users with JWTs and assign viewer, submitter, approver, and admin roles.
- Use the invoice assistant with a configured LLM provider or its built-in fallback mode.

## Technology

- **Backend:** Python 3.12, Flask, PyMongo, MongoDB
- **Document processing:** PyMuPDF, Tesseract OCR, scikit-learn
- **Frontend:** React 19, Vite, Axios, Chart.js

## Requirements

- Python 3.12
- Node.js 20.19+ or 22.12+
- MongoDB, available locally or through a MongoDB connection URI
- Tesseract OCR for OCR processing (optional)

On Ubuntu, install Tesseract with:

```bash
sudo apt install tesseract-ocr
```

## Getting started

Run MongoDB before starting the backend. The backend connects to MongoDB during startup and requires a working database connection.

### 1. Configure and start the backend

From the project directory:

```bash
cd backend
python3.12 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
```

Create a local environment file if you do not already have one:

```bash
cp -n .env.example .env
```

Edit `backend/.env` and set a unique JWT secret. For example, generate one with:

```bash
.venv/bin/python -c "import secrets; print(secrets.token_hex(32))"
```

Paste the generated value into `JWT_SECRET_KEY` in `.env`. Do not commit `.env` or share the secret. At minimum, check these settings:

```dotenv
FLASK_DEBUG=false
PORT=5000
MONGO_URI=mongodb://localhost:27017/
DB_NAME=invoice_db
JWT_SECRET_KEY=replace-with-a-generated-secret
CORS_ORIGINS=http://localhost:5173
```

Create the first administrator, then start the API:

```bash
.venv/bin/python create_admin.py
.venv/bin/python app.py
```

The API listens at `http://localhost:5000` by default. Its health endpoint is `http://localhost:5000/api/health`.

### 2. Start the frontend

Open a second terminal from the project directory:

```bash
cd frontend
npm ci
npm run dev
```

Open the local URL printed by Vite (normally `http://localhost:5173`). The frontend uses `http://localhost:5000` as its default API URL. To use a different backend URL, set `VITE_API_URL` in a frontend `.env` file before starting Vite.

## Configuration

| Variable | Purpose | Default |
| --- | --- | --- |
| `PORT` | Flask listening port | `5000` |
| `FLASK_DEBUG` | Enable Flask debug mode; leave disabled outside local debugging | `false` |
| `MONGO_URI` | MongoDB connection URI | `mongodb://localhost:27017/` |
| `DB_NAME` | MongoDB database name | `invoice_db` |
| `JWT_SECRET_KEY` | Secret used to sign authentication tokens | Must be set when debug is disabled |
| `JWT_ACCESS_TOKEN_EXPIRES` | Access-token lifetime in seconds | `3600` |
| `JWT_REFRESH_TOKEN_EXPIRES` | Refresh-token lifetime in seconds | `2592000` |
| `CORS_ORIGINS` | Comma-separated allowed frontend origins | `http://localhost:5173` |
| `OPENAI_API_KEY` | Optional API key for the OpenAI assistant provider | unset |
| `ANTHROPIC_API_KEY` | Optional API key for the Anthropic assistant provider | unset |
| `LLM_PROVIDER` | Assistant provider (`openai` or `anthropic`) | `anthropic` |
| `RATELIMIT_ENABLED` | Enable API rate limiting | `true` |
| `RATELIMIT_STORAGE_URL` | Rate-limit storage URI | `memory://` |
| `NOTIFICATIONS_ENABLED` | Enable email notifications | `false` |

The backend `.env.example` lists additional optional SMTP and approval-rule settings. Configure SMTP values if email notifications are enabled. Without an LLM API key, the assistant uses its fallback behavior.

## Tests and frontend checks

Run backend tests from the `backend` directory:

```bash
.venv/bin/python -m pytest tests/ -v
```

The test suite includes database-backed tests; start MongoDB before running the full suite.

Run frontend linting and a production build from `frontend`:

```bash
npm run lint
npm run build
```

## API overview

The backend API is served from the same origin as the Flask app. Important route groups include:

- Authentication: `/api/auth/*`
- Accounts payable invoices: `/upload`, `/invoices`, `/api/invoices/*`
- Vendors: `/api/vendors/*`
- Customers and products: `/api/customers/*`, `/api/products/*`
- Accounts receivable: `/api/ar/invoices/*`
- Company profile: `/api/company`
- Audit, reports, exports, and dashboards: `/api/audit/*`, `/api/reports/*`, `/api/export/*`, `/api/dashboard/*`
- Health check: `/api/health`

Most routes require an access token sent as a Bearer token in the HTTP Authorization header. See the [API reference](backend/API_DOCUMENTATION.md) and [authentication setup guide](backend/AUTH_SETUP.md) for details.

## Project layout

```text
backend/
  app.py                 Flask application and API routes
  config.py              Environment-based application settings
  db.py                  MongoDB connection and indexes
  services/              Authentication and business logic
  tests/                 Backend tests
  requirements.txt       Python dependencies
frontend/
  src/                   React application and components
  package.json           Frontend scripts and dependencies
```

Invoice uploads are stored in `backend/uploads/`. Keep uploaded documents and local environment files out of source control.

## Troubleshooting

- **`No module named 'flask'` or `No module named 'pymongo'`:** Install dependencies with `backend/.venv/bin/python -m pip install -r backend/requirements.txt`, then run backend scripts with `backend/.venv/bin/python`.
- **MongoDB connection refused or startup failure:** Start MongoDB and verify `MONGO_URI` and `DB_NAME` in `backend/.env`. The API currently requires MongoDB during startup.
- **JWT secret configuration error:** Set `JWT_SECRET_KEY` in `backend/.env`; do not use a placeholder outside local development.
- **Browser CORS error:** Add the frontend origin (including scheme and port) to `CORS_ORIGINS`.
- **OCR unavailable:** Install Tesseract and ensure its executable is on `PATH`.
- **Frontend cannot reach the API:** Confirm the backend is running and, if it is not on `localhost:5000`, set `VITE_API_URL`.
