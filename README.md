# Mini Jira API

A production-grade, modular, and secure RESTful backend API for a Mini Jira-like Project Management System built with **Django 6.1**, **Django REST Framework (DRF)**, **SimpleJWT**, **django-filter**, and **drf-spectacular**.

---

## 1. Project Overview & Architecture

### Purpose
The Mini Jira API provides modern project management capabilities, including user authentication, team collaboration, project team assignments, task/card creation and assignment, a controlled workflow state machine (`TODO` → `IN_PROGRESS` → `READY_FOR_REVIEW` → `DONE`), comment discussions, and an immutable audit activity history trail.

### Key Architectural Principles
- **Domain-Driven Modular Packaging**: Located under `apps/` with clear separation of responsibilities (`accounts`, `teams`, `projects`, `tasks`, `comments`, `activities`, `utils`).
- **One Responsibility Per File**: Strict single-responsibility files (`serializers/`, `views/`, `services/`, `selectors/`, `models/`, `permissions/`, `filters/`, `urls/`, `tests/`).
- **Service-Selector Pattern**:
  - **Services (`services/`)**: Encapsulate write operations, business invariants, row-locking (`select_for_update()`), and atomic audit logging (`@transaction.atomic`).
  - **Selectors (`selectors/`)**: Handle read-only queries with IDOR security checks, prefetching (`select_related`, `prefetch_related`), and annotation logic.
- **Server-Side Authorization**: Every endpoint validates authorization on the backend. Client payloads cannot override server-controlled fields (e.g. `reporter`, `author`, `created_by`).
- **IDOR Prevention**: Querysets are filtered at the database level based on user membership before any filtering/searching parameters are applied.
- **Immutable Audit Trail**: `ActivityLog` entries are append-only. Overridden `save()` and `delete()` methods prevent modification or deletion.

---

## 2. Technology Stack

- **Framework**: Python 3.13+, Django 6.1, Django REST Framework 3.18
- **Authentication**: `djangorestframework-simplejwt` (JWT access & refresh tokens with rotation and blacklisting)
- **Filtering & Search**: `django-filter`
- **OpenAPI Documentation**: `drf-spectacular` (OpenAPI 3.0, Swagger UI, Redoc)
- **Database**: PostgreSQL / SQLite (PostgreSQL-compatible ORM constraints, indexes, and regex checks)

---

## 3. Installation & Setup

### Prerequisites
- Python 3.11+
- Virtual Environment tool (`venv`)

### Installation Steps

1. **Clone repository and navigate to root directory**:
   ```bash
   cd mini-jira-api
   ```

2. **Create and activate virtual environment**:
   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\activate

   # Linux/macOS
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

---

## 4. Environment Variables & Database Configuration

Create a `.env` file in the project root directory (or use environment variables):

```env
SECRET_KEY=your-secure-django-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=sqlite:///db.sqlite3
```

### Running Migrations

Apply database schema migrations:
```bash
python manage.py migrate
```

### Creating Superuser (Optional Admin Panel Access)

```bash
python manage.py createsuperuser
```

---

## 5. Running the Development Server

Start Django's development server:
```bash
python manage.py runserver 8000
```
The server will run at `http://127.0.0.1:8000/`.

---

## 6. Running Tests

Run the comprehensive automated test suite across all domain applications:

```bash
python manage.py test apps.accounts apps.teams apps.projects apps.tasks apps.comments apps.activities
```

---

## 7. Interactive API Documentation

Interactive OpenAPI documentation is generated dynamically via `drf-spectacular`:

- **Swagger UI**: [http://127.0.0.1:8000/api/v1/docs/](http://127.0.0.1:8000/api/v1/docs/)
- **Redoc**: [http://127.0.0.1:8000/api/v1/redoc/](http://127.0.0.1:8000/api/v1/redoc/)
- **Raw OpenAPI Schema (YAML)**: [http://127.0.0.1:8000/api/v1/schema/](http://127.0.0.1:8000/api/v1/schema/)

Generate schema artifact manually:
```bash
python manage.py spectacular --file schema.yml
```

---

## 8. Core Business Rules & Permissions

### Role Matrix
1. **Project Reporter (Creator)**:
   - Creator of the project.
   - Full permissions: update project settings, assign/remove teams, soft-delete project, assign/reassign tasks, approve/reject task transitions (`READY_FOR_REVIEW` → `DONE` / `TODO`), delete comments for moderation.
2. **Team Member**:
   - User belonging to a `Team` assigned to the `Project`.
   - Access permissions: create tasks in project, view project tasks, view project activities, add comments, edit/delete own comments.
3. **Task Assignee**:
   - User assigned to a specific task (must belong to a team assigned to the project or be the reporter).
   - Workflow permissions: move task `TODO` → `IN_PROGRESS` and `IN_PROGRESS` → `READY_FOR_REVIEW`.
4. **Outsider (Unassigned User)**:
   - Zero access to unassigned projects or tasks (`404 Not Found`).

### Task Workflow State Machine
```text
  [TODO]  ----(Assignee)---->  [IN_PROGRESS]  ----(Assignee)---->  [READY_FOR_REVIEW]
     ^                                                                      |
     |                                                                      |
     +--------------------------(Reporter Rejects)--------------------------+
                                                                            |
                                                                   (Reporter Approves)
                                                                            v
                                                                         [DONE]
```

- **Transitions**:
  - `TODO` → `IN_PROGRESS`: Executed by **Assignee**.
  - `IN_PROGRESS` → `READY_FOR_REVIEW`: Executed by **Assignee**.
  - `READY_FOR_REVIEW` → `DONE`: Executed by **Project Reporter** (Approval).
  - `READY_FOR_REVIEW` → `TODO`: Executed by **Project Reporter** (Rejection).
- **Direct Status Modification**: Updating task `status` via `PATCH /api/v1/tasks/{id}/` is strictly blocked (`400 Bad Request`). Status changes must go through `POST /api/v1/tasks/{id}/transition/`.

---

## 9. Exhaustive API Endpoint Reference

### Response Standard Wrapper Format

#### Success Response (200 OK / 201 Created)
```json
{
  "success": true,
  "message": "Optional human-readable message",
  "data": { ... }
}
```

#### Error Response (400 / 401 / 403 / 404)
```json
{
  "success": false,
  "error": {
    "code": "ValidationError | PermissionDenied | NotFound | InvalidToken",
    "message": "Error summary description",
    "details": { ... }
  }
}
```

---

### Authentication Endpoints

#### 1. Register User
- **Method**: `POST`
- **URL**: `/api/v1/auth/register/`
- **Authentication**: None (Public)
- **Request Body**:
  ```json
  {
    "email": "user@example.com",
    "password": "StrongPassword123!",
    "first_name": "John",
    "last_name": "Doe"
  }
  ```
- **Response Codes**: `201 Created`, `400 Bad Request`
- **Success Response (201 Created)**:
  ```json
  {
    "success": true,
    "message": "User registered successfully.",
    "data": {
      "user": {
        "id": 1,
        "email": "user@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "full_name": "John Doe",
        "date_joined": "2026-09-08T20:00:00Z"
      },
      "tokens": {
        "refresh": "eyJhbGciOi...",
        "access": "eyJhbGciOi..."
      }
    }
  }
  ```

#### 2. Login User
- **Method**: `POST`
- **URL**: `/api/v1/auth/login/`
- **Authentication**: None (Public)
- **Request Body**:
  ```json
  {
    "email": "user@example.com",
    "password": "StrongPassword123!"
  }
  ```
- **Response Codes**: `200 OK`, `401 Unauthorized`
- **Success Response (200 OK)**:
  ```json
  {
    "success": true,
    "message": "Login successful.",
    "data": {
      "user": {
        "id": 1,
        "email": "user@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "full_name": "John Doe",
        "date_joined": "2026-09-08T20:00:00Z"
      },
      "tokens": {
        "refresh": "eyJhbGciOi...",
        "access": "eyJhbGciOi..."
      }
    }
  }
  ```

#### 3. Refresh Access Token
- **Method**: `POST`
- **URL**: `/api/v1/auth/refresh/`
- **Authentication**: None
- **Request Body**:
  ```json
  {
    "refresh": "eyJhbGciOi..."
  }
  ```
- **Response Codes**: `200 OK`, `401 Unauthorized`
- **Success Response (200 OK)**:
  ```json
  {
    "success": true,
    "data": {
      "access": "eyJhbGciOi..."
    }
  }
  ```

#### 4. Logout User
- **Method**: `POST`
- **URL**: `/api/v1/auth/logout/`
- **Authentication**: Bearer JWT (`IsAuthenticated`)
- **Request Body**:
  ```json
  {
    "refresh": "eyJhbGciOi..."
  }
  ```
- **Response Codes**: `200 OK`, `400 Bad Request`, `401 Unauthorized`
- **Success Response (200 OK)**:
  ```json
  {
    "success": true,
    "message": "Successfully logged out."
  }
  ```

#### 5. Retrieve / Update User Profile
- **Method**: `GET`, `PATCH`
- **URL**: `/api/v1/auth/me/`
- **Authentication**: Bearer JWT (`IsAuthenticated`)
- **Request Body (PATCH)**:
  ```json
  {
    "first_name": "Jane",
    "last_name": "Smith"
  }
  ```
- **Response Codes**: `200 OK`, `401 Unauthorized`
- **Success Response (200 OK)**:
  ```json
  {
    "success": true,
    "data": {
      "id": 1,
      "email": "user@example.com",
      "first_name": "Jane",
      "last_name": "Smith",
      "full_name": "Jane Smith",
      "date_joined": "2026-09-08T20:00:00Z"
    }
  }
  ```

---

### Teams & Team Membership Endpoints

#### 6. List / Create Teams
- **Method**: `GET`, `POST`
- **URL**: `/api/v1/teams/`
- **Authentication**: Bearer JWT (`IsAuthenticated`)
- **Request Body (POST)**:
  ```json
  {
    "name": "Backend Engineering",
    "description": "Core API and Database team"
  }
  ```
- **Response Codes**: `200 OK` (GET), `201 Created` (POST), `400 Bad Request`

#### 7. Retrieve / Update / Delete Team
- **Method**: `GET`, `PATCH`, `DELETE`
- **URL**: `/api/v1/teams/{id}/`
- **Authentication**: Bearer JWT (`IsAuthenticated`, `IsTeamMember`)
- **Path Parameters**: `id` (integer)
- **Response Codes**: `200 OK`, `403 Forbidden`, `404 Not Found`

#### 8. List / Add Team Members
- **Method**: `GET`, `POST`
- **URL**: `/api/v1/teams/{id}/members/`
- **Authentication**: Bearer JWT (`IsAuthenticated`, `IsTeamMember`)
- **Path Parameters**: `id` (integer - Team ID)
- **Request Body (POST)**:
  ```json
  {
    "email": "developer@example.com"
  }
  ```
- **Response Codes**: `200 OK` (GET), `201 Created` (POST), `400 Bad Request`

#### 9. Remove Team Member
- **Method**: `DELETE`
- **URL**: `/api/v1/teams/{id}/members/{user_id}/`
- **Authentication**: Bearer JWT (`IsAuthenticated`, `IsTeamMember`)
- **Path Parameters**: `id` (integer - Team ID), `user_id` (integer - User ID)
- **Response Codes**: `200 OK`, `400 Bad Request`, `404 Not Found`

---

### Projects & Project Team Assignment Endpoints

#### 10. List / Create Projects
- **Method**: `GET`, `POST`
- **URL**: `/api/v1/projects/`
- **Authentication**: Bearer JWT (`IsAuthenticated`)
- **Query Parameters (GET)**: `search`, `ordering`, `page`, `page_size`
- **Request Body (POST)**:
  ```json
  {
    "key": "CORE",
    "title": "Core Banking Redesign",
    "description": "API migration project"
  }
  ```
- **Response Codes**: `200 OK` (GET), `201 Created` (POST), `400 Bad Request`

#### 11. Retrieve / Update / Delete Project
- **Method**: `GET`, `PATCH`, `DELETE`
- **URL**: `/api/v1/projects/{id}/`
- **Authentication**: Bearer JWT (`HasProjectAccess` for GET, `IsProjectReporter` for PATCH/DELETE)
- **Path Parameters**: `id` (integer)
- **Response Codes**: `200 OK`, `403 Forbidden`, `404 Not Found`

#### 12. Assign Team to Project
- **Method**: `POST`
- **URL**: `/api/v1/projects/{id}/teams/`
- **Authentication**: Bearer JWT (`IsProjectReporter`)
- **Path Parameters**: `id` (integer - Project ID)
- **Request Body**:
  ```json
  {
    "team_id": 1
  }
  ```
- **Response Codes**: `201 Created`, `400 Bad Request`, `403 Forbidden`

#### 13. Remove Team from Project
- **Method**: `DELETE`
- **URL**: `/api/v1/projects/{id}/teams/{team_id}/`
- **Authentication**: Bearer JWT (`IsProjectReporter`)
- **Path Parameters**: `id` (integer - Project ID), `team_id` (integer - Team ID)
- **Response Codes**: `200 OK`, `403 Forbidden`, `404 Not Found`

---

### Tasks & Workflow Endpoints

#### 14. List / Create Project Tasks
- **Method**: `GET`, `POST`
- **URL**: `/api/v1/projects/{project_id}/tasks/`
- **Authentication**: Bearer JWT (`HasProjectAccess`)
- **Path Parameters**: `project_id` (integer)
- **Query Parameters (GET)**: `status`, `priority`, `assignee`, `search`, `ordering`, `page`, `page_size`
- **Request Body (POST)**:
  ```json
  {
    "title": "Implement OAuth2 Flow",
    "description": "Setup JWT token validation",
    "priority": "HIGH",
    "assignee_id": 2
  }
  ```
- **Response Codes**: `200 OK` (GET), `201 Created` (POST), `400 Bad Request`, `404 Not Found`

#### 15. Global Tasks Listing
- **Method**: `GET`
- **URL**: `/api/v1/tasks/`
- **Authentication**: Bearer JWT (`IsAuthenticated`)
- **Query Parameters**:
  - `project`: Filter by project ID
  - `assignee`: Filter by assignee user ID
  - `status`: Filter choice (`TODO`, `IN_PROGRESS`, `READY_FOR_REVIEW`, `DONE`)
  - `priority`: Filter choice (`LOW`, `MEDIUM`, `HIGH`, `URGENT`)
  - `search`: Searches across task title, description, and project key/title
  - `ordering`: Safe sorting (`created_at`, `-created_at`, `updated_at`, `priority`, `title`)
  - `page`, `page_size`: Pagination control

#### 16. Retrieve / Update / Delete Task
- **Method**: `GET`, `PATCH`, `DELETE`
- **URL**: `/api/v1/tasks/{id}/`
- **Authentication**: Bearer JWT (`HasTaskAccess`)
- **Path Parameters**: `id` (integer)
- **Request Body (PATCH)**: (Status modifications forbidden via PATCH)
  ```json
  {
    "title": "Updated Task Title",
    "priority": "URGENT"
  }
  ```
- **Response Codes**: `200 OK`, `400 Bad Request`, `404 Not Found`

#### 17. Assign / Reassign Task
- **Method**: `POST`
- **URL**: `/api/v1/tasks/{id}/assign/`
- **Authentication**: Bearer JWT (`IsProjectReporter`)
- **Path Parameters**: `id` (integer - Task ID)
- **Request Body**:
  ```json
  {
    "assignee_id": 3
  }
  ```
- **Response Codes**: `200 OK`, `400 Bad Request`, `403 Forbidden`

#### 18. Transition Task Status (Workflow State Machine)
- **Method**: `POST`
- **URL**: `/api/v1/tasks/{id}/transition/`
- **Authentication**: Bearer JWT (`HasTaskAccess`)
- **Path Parameters**: `id` (integer - Task ID)
- **Request Body**:
  ```json
  {
    "status": "IN_PROGRESS"
  }
  ```
- **Allowed Transitions & Permissions**:
  - `TODO` → `IN_PROGRESS` (Assignee)
  - `IN_PROGRESS` → `READY_FOR_REVIEW` (Assignee)
  - `READY_FOR_REVIEW` → `DONE` (Project Reporter Approval)
  - `READY_FOR_REVIEW` → `TODO` (Project Reporter Rejection)
- **Response Codes**: `200 OK`, `400 Bad Request`, `403 Forbidden`

---

### Comments & Activities Endpoints

#### 19. List / Create Task Comments
- **Method**: `GET`, `POST`
- **URL**: `/api/v1/tasks/{task_id}/comments/`
- **Authentication**: Bearer JWT (`HasTaskAccess`)
- **Path Parameters**: `task_id` (integer)
- **Request Body (POST)**:
  ```json
  {
    "content": "PR is ready for review."
  }
  ```
- **Response Codes**: `200 OK` (GET), `201 Created` (POST), `404 Not Found`

#### 20. Update / Delete Comment
- **Method**: `PATCH`, `DELETE`
- **URL**: `/api/v1/comments/{id}/`
- **Authentication**: Bearer JWT (`IsCommentAuthor` for PATCH, `IsCommentAuthorOrReporter` for DELETE)
- **Path Parameters**: `id` (integer - Comment ID)
- **Response Codes**: `200 OK`, `403 Forbidden`, `404 Not Found`

#### 21. List Project Audit Activities
- **Method**: `GET`
- **URL**: `/api/v1/projects/{project_id}/activities/`
- **Authentication**: Bearer JWT (`HasProjectAccess`)
- **Path Parameters**: `project_id` (integer)
- **Response Codes**: `200 OK`, `404 Not Found`

#### 22. List Task Audit Activities
- **Method**: `GET`
- **URL**: `/api/v1/tasks/{task_id}/activities/`
- **Authentication**: Bearer JWT (`HasTaskAccess`)
- **Path Parameters**: `task_id` (integer)
- **Response Codes**: `200 OK`, `404 Not Found`
