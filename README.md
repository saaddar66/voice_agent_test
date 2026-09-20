# Voice AI Patient Registration System

## Overview

This technical assessment project provides the backend for a voice-assisted patient registration workflow. A caller can provide demographic information through a voice-agent integration, the information can be validated and confirmed by the agent, and the resulting patient record can be persisted to PostgreSQL and accessed through a FastAPI REST API.

The repository contains the FastAPI service and its Vapi custom-tool webhook. The phone number, voice agent, and LLM configuration are external to this repository.

## Architecture

```text
Caller
  |
  v
Phone / Voice AI platform (Vapi custom tool webhook)
  |
  v
FastAPI backend
  |-------------------- REST API (/patients)
  v
SQLAlchemy async database layer
  |
  v
PostgreSQL
```

- **Phone / Voice AI platform:** External voice platform; the repository exposes a Vapi-compatible webhook.
- **Voice agent / LLM:** External. No agent prompt, phone-number configuration, speech-to-text, text-to-speech, or LLM client is included in this repository.
- **FastAPI backend:** Receives REST requests and Vapi tool calls, validates payloads, and applies the CRUD operations.
- **PostgreSQL database:** Stores patient records through SQLAlchemy's asynchronous PostgreSQL engine.
- **REST API:** Exposes patient listing, retrieval, creation, update, deletion, and a root health-style response.

## Features

Implemented:

- Patient creation through a FastAPI REST endpoint and Vapi `create_patient` tool call.
- Required and optional demographic, insurance, emergency-contact, and language fields.
- Pydantic validation for required fields, name length, state and ZIP lengths, date of birth, sex values, and phone number format.
- Vapi tool response after a successful patient creation, including the generated patient ID.
- PostgreSQL persistence with asynchronous SQLAlchemy sessions.
- Patient listing with optional last-name, date-of-birth, and phone-number filters.
- Patient retrieval, update, and soft deletion.
- JSON response envelopes containing `data` and `error`.
- Error handlers for HTTP errors, request validation errors, and unexpected exceptions.
- Basic logging of unexpected server errors.

Partial or external:

- **Natural conversational registration, optional-field prompting, correction, read-back confirmation, call completion, and LLM behavior:** not implemented in this repository; these depend on the external voice-agent configuration.
- **Duplicate patient handling:** not implemented. There is no uniqueness constraint or duplicate-detection query.
- **Dashboard:** a `/dashboard` static mount is configured, but no `frontend/` directory is included.

## Tech Stack

| Component | Technology | Purpose |
|---|---|---|
| Web framework | FastAPI | REST API, request validation, OpenAPI/Swagger docs, and webhook handling |
| ASGI server | Uvicorn-compatible ASGI application | Runs `main:app` locally or in a hosting service |
| Validation and serialization | Pydantic | Request models, field validation, and response serialization |
| ORM/database access | SQLAlchemy async ORM | Models, queries, transactions, and async sessions |
| PostgreSQL driver | asyncpg | Asynchronous PostgreSQL connectivity |
| Database | PostgreSQL | Persistent patient storage |
| Voice integration | Vapi webhook payload models | Receives custom tool calls from Vapi |

## Project Structure

| Path | Purpose |
|---|---|
| `main.py` | Creates the FastAPI app, initializes database tables on startup, registers routers, mounts the dashboard path, and defines exception handlers. |
| `database.py` | Reads `DATABASE_URL`, creates the async SQLAlchemy engine/session factory, and provides the database dependency. |
| `models.py` | Defines the `Patient` SQLAlchemy model and `SexEnum`. |
| `schemas.py` | Defines response envelopes and patient create, update, and response schemas with Pydantic validators. |
| `crud.py` | Implements patient queries, creation, update, and soft deletion. |
| `routers/pateints.py` | Defines the `/patients` REST endpoints. The filename currently does not match the `routers.patients` import in `main.py`. |
| `routers/vapi.py` | Defines the `/vapi/function-webhook` endpoint and handles the Vapi `create_patient` tool. |

## Patient Data Model

The `patients` table contains:

| Field | Type | Required | Validation/default |
|---|---|---:|---|
| `patient_id` | UUID | Generated | Primary key; generated with `uuid.uuid4` |
| `first_name` | string | Yes | 1-50 characters |
| `last_name` | string | Yes | 1-50 characters |
| `date_of_birth` | date | Yes | Must not be in the future |
| `sex` | enum | Yes | `Male`, `Female`, `Other`, or `Decline to Answer`; common case/whitespace variations are normalized |
| `phone_number` | string | Yes | Exactly 10 digits |
| `email` | string | No | No email-format validator is defined |
| `address_line_1` | string | Yes | No additional length validator |
| `address_line_2` | string | No | No additional validator |
| `city` | string | Yes | No additional validator |
| `state` | string | Yes | Exactly 2 characters |
| `zip_code` | string | Yes | Exactly 5 characters |
| `insurance_provider` | string | No | None by default |
| `insurance_member_id` | string | No | None by default |
| `emergency_contact_name` | string | No | None by default |
| `emergency_contact_phone` | string | No | If supplied, exactly 10 digits |
| `preferred_language` | string | No | Defaults to `English` |
| `created_at` | timestamp | Generated | PostgreSQL server timestamp |
| `updated_at` | timestamp | Generated | PostgreSQL server timestamp; refreshed on update |
| `deleted_at` | timestamp | No | Set for soft deletion |

## API Endpoints

All patient responses use an envelope similar to `{"data": ..., "error": null}`. FastAPI's Swagger UI is available at `/docs` when the application starts successfully.

### `GET /`

Returns an online message and the documentation path.

```json
{
  "data": {
    "message": "Welcome to the Patient Registration System API",
    "docs": "/docs",
    "status": "online"
  },
  "error": null
}
```

### `GET /patients`

Lists non-deleted patients. Optional query parameters are `last_name`, `date_of_birth` (`YYYY-MM-DD`), and `phone_number`.

- `200 OK`: envelope containing a patient array.
- `422 Unprocessable Entity`: invalid query parameter format.

### `GET /patients/{id}`

Returns one non-deleted patient by UUID.

- `200 OK`: envelope containing the patient.
- `404 Not Found`: patient does not exist or is soft-deleted.
- `422 Unprocessable Entity`: invalid UUID.

### `POST /patients`

Creates a patient. The request body is a `PatientCreate` object using the fields in the data-model table.

```json
{
  "first_name": "Jane",
  "last_name": "Doe",
  "date_of_birth": "1990-01-15",
  "sex": "Female",
  "phone_number": "5551234567",
  "address_line_1": "100 Main Street",
  "city": "Austin",
  "state": "TX",
  "zip_code": "78701"
}
```

- `201 Created`: envelope containing the created patient and generated UUID.
- `422 Unprocessable Entity`: schema or field validation failure.
- `500 Internal Server Error`: unexpected database or server failure.

### `PUT /patients/{id}`

Updates any supplied fields using a `PatientUpdate` body.

- `200 OK`: envelope containing the updated patient.
- `404 Not Found`: patient does not exist or is soft-deleted.
- `422 Unprocessable Entity`: invalid UUID or request data.

### `DELETE /patients/{id}`

Soft-deletes a patient by setting `deleted_at`; the record is excluded from normal patient queries.

- `200 OK`: envelope containing the updated record.
- `404 Not Found`: patient does not exist or is already soft-deleted.
- `422 Unprocessable Entity`: invalid UUID.

### `POST /vapi/function-webhook`

Accepts a Vapi payload containing `message.tool.name`, `message.toolCallId`, and `message.tool.arguments`.

- A `create_patient` tool call validates the arguments, creates a patient, and returns a Vapi `results` array with `toolCallId` and a result string.
- A request without a tool call returns `{"status": "ok"}`.
- An unknown tool returns a result with `status: "error"`.
- Validation and database exceptions are caught inside the tool handler and returned as an error result rather than an HTTP error.
- Invalid top-level request structure returns `422 Unprocessable Entity` through the global validation handler.

Example tool arguments:

```json
{
  "message": {
    "type": "function-call",
    "toolCallId": "tool-call-1",
    "tool": {
      "name": "create_patient",
      "arguments": {
        "first_name": "Jane",
        "last_name": "Doe",
        "date_of_birth": "1990-01-15",
        "sex": "Female",
        "phone_number": "5551234567",
        "address_line_1": "100 Main Street",
        "city": "Austin",
        "state": "TX",
        "zip_code": "78701"
      }
    }
  }
}
```

## Voice Agent Flow

The code supports the backend portion of this flow:

1. A caller interacts with an externally configured voice agent.
2. The agent sends a Vapi `create_patient` tool call to the webhook.
3. The webhook validates the supplied required and optional fields.
4. The webhook creates the patient record in PostgreSQL.
5. The webhook returns a success or error result to Vapi.

The repository does not contain the voice prompt or agent configuration, so caller questioning, invalid-input correction, read-back confirmation, interruption handling, and ending the call cannot be verified from this codebase.

## Setup and Installation

The repository does not currently include `requirements.txt` or a packaging file. From PowerShell on Windows:

1. Clone and enter the repository:

   ```powershell
   git clone <repository-url>
   cd voice_agent_test
   ```

2. Create and activate a virtual environment:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. Install the packages imported by the application:

   ```powershell
  python -m pip install fastapi uvicorn sqlalchemy asyncpg pydantic python-dotenv
   ```

4. Create the local environment file from the template and edit it with your PostgreSQL details:

   ```powershell
  Copy-Item .env.example .env
  notepad .env
   ```

  The application loads `.env` automatically through `python-dotenv`. Do not commit `.env`.

5. Ensure PostgreSQL is running and the target database exists. The application creates the `patients` table on startup with SQLAlchemy metadata; it does not create the PostgreSQL database itself or run migrations.

6. Fix the current router filename/import mismatch before starting: rename `routers\pateints.py` to `routers\patients.py`, or change the import in `main.py` to match the existing filename. The current source imports `routers.patients` and therefore does not start as checked out.

7. Start the FastAPI server:

   ```powershell
   python -m uvicorn main:app --reload
   ```

## Environment Variables

The application reads one environment variable from `.env` or the process environment:

```text
DATABASE_URL=postgresql+asyncpg://<user>:<password>@<host>:5432/<database>
```

If `DATABASE_URL` is not set, the code defaults to `postgresql+asyncpg://postgres:postgres@localhost/db`. No Vapi API key or LLM API key is read by this repository. The committed `.env.example` contains placeholders only; keep real credentials in the ignored `.env` file or in the hosting platform's environment settings.

## Running Locally

After correcting the router filename/import mismatch and configuring PostgreSQL:

```powershell
python -m uvicorn main:app --reload
```

The local API is available at `http://127.0.0.1:8000` and the Swagger documentation is at `http://127.0.0.1:8000/docs`.

## Deployment

The intended deployment architecture is:

```text
Voice AI platform
        |
        v
Render FastAPI service
        |
        v
PostgreSQL database
```

Deploy the FastAPI application with an ASGI start command such as `uvicorn main:app --host 0.0.0.0 --port $PORT`, provide a reachable PostgreSQL instance, and configure `DATABASE_URL` in the hosting platform. The router filename/import mismatch must be resolved before deployment. No deployment is included in this repository.

## Live Demo

Replace these placeholders before submission:

Phone Number: `+1 943 500 9356`

API Base URL: `https://your-api-url.onrender.com`

API Documentation: `https://your-api-url.onrender.com/docs`

## API Testing

Assuming the server is running locally:

```powershell
curl.exe http://127.0.0.1:8000/
curl.exe "http://127.0.0.1:8000/patients?last_name=Doe"
curl.exe -X POST http://127.0.0.1:8000/patients `
  -H "Content-Type: application/json" `
  -d '{"first_name":"Jane","last_name":"Doe","date_of_birth":"1990-01-15","sex":"Female","phone_number":"5551234567","address_line_1":"100 Main Street","city":"Austin","state":"TX","zip_code":"78701"}'
curl.exe -X POST http://127.0.0.1:8000/vapi/function-webhook `
  -H "Content-Type: application/json" `
  -d '{"message":{"type":"ping"}}'
```

Use the UUID returned by the create request to test `GET /patients/{id}`, `PUT /patients/{id}`, and `DELETE /patients/{id}`.

## Security

- The database connection string is read from an environment variable rather than hard-coded as the preferred configuration path.
- Request data is validated server-side with Pydantic.
- Phone numbers and dates are checked before patient creation or update.
- No credentials, API keys, or tokens are present in the repository.

Authentication, authorization, encryption configuration, audit controls, and HIPAA compliance are not implemented by this project.

## Error Handling

The global handlers return a consistent `{"data": null, "error": "..."}` shape for HTTP errors, validation errors, and unexpected exceptions. Standard patient-route failures include `404 Not Found` for missing records and `422 Unprocessable Entity` for invalid path, query, or body data. Unexpected API errors return `500 Internal Server Error` and are logged with a traceback. Vapi tool failures are returned as a tool result with `status: "error"`; they do not generally become HTTP 500 responses.

## Known Limitations

- The checked-in router filename does not match the import in `main.py`, so the application cannot start until that mismatch is corrected.
- There is no dependency lockfile or requirements file.
- The configured `/dashboard` mount points to a missing `frontend/` directory.
- Voice provider, phone-number, LLM, prompt, transcript, and call-recovery configuration are external and not included.
- Duplicate detection is not implemented.
- There is no authentication or authorization.
- The application does not provide production HIPAA compliance or healthcare-specific audit controls.
- Database initialization uses `create_all` at startup rather than migrations.
- The Vapi handler catches broad exceptions and returns the exception text in its tool result; this would need tightening for production use.
- Free-tier hosting constraints such as cold starts, resource limits, and database availability may affect a hosted demo.

## Design Decisions and Trade-offs

- FastAPI provides a small REST and webhook surface with automatic OpenAPI documentation and Pydantic validation.
- PostgreSQL is used for relational persistence, while SQLAlchemy's async API keeps database calls non-blocking.
- The voice provider is treated as an integration boundary rather than reimplementing speech recognition, speech synthesis, or an LLM in the assessment codebase.
- Patient schemas, SQLAlchemy models, CRUD operations, and routers are separated into focused modules.
- Startup table creation and a simple CRUD layer reduce setup time for a short assessment, at the cost of lacking migration management and production hardening.

## Testing

No automated tests are included in the repository. Python compilation checks pass, but importing `main` currently fails because `main.py` imports `routers.patients` while the file is named `routers/pateints.py`.

## Future Improvements

The following are future improvements and are not currently implemented:

- Authentication and authorization.
- Automated unit, integration, and webhook contract tests.
- Database migrations and stricter transaction/error handling.
- Better duplicate detection and patient matching.
- Call recovery, interruption handling, and resumable registration.
- Call transcript storage and an audit trail.
- A working administrative dashboard.
- Multi-language support beyond the stored language field.
- Appointment scheduling.
- Production privacy, security, monitoring, and healthcare compliance controls.

## Assessment Requirements Coverage

| Requirement | Implementation status |
|---|---|
| Real phone number | **Not Implemented in repository**; placeholder only, external configuration required |
| Natural voice interaction | **Partial**; Vapi webhook exists, but the voice agent configuration is external |
| LLM-powered conversation | **Not Implemented in repository**; no LLM integration or prompt is included |
| Patient validation | **Implemented** through Pydantic and field validators |
| Confirmation before saving | **Not verifiable / Partial**; no confirmation logic is present in the repository |
| Persistent database | **Implemented** with PostgreSQL and async SQLAlchemy |
| REST API | **Implemented** with FastAPI patient CRUD endpoints |
| Error handling | **Implemented** with global API handlers and Vapi tool error results |
| Deployment | **Partial**; deployment architecture is defined, but no live deployment or URL is included |