# QA Portal FNOL - Project Overview

Welcome to the QA Portal for First Notice of Loss (FNOL) calls! This document provides a complete project overview to help another developer understand the architecture, technical stack, current status, and future-ready features of this application.

## 🏗 System Architecture & Tech Stack

This project is built using a straightforward, robust, and lightweight stack that ensures maintainability and fast iterations.

### Frontend
- **HTML/CSS/JavaScript**: We deliberately kept the frontend simple and dependency-light. The user interface relies entirely on plain HTML, Vanilla CSS, and Vanilla JavaScript. **No complex frontend frameworks** (like React, Vue, or Angular) are required to run or edit this project.
- **Plotly (for Charts)**: All data visualizations and charts in the dashboard are generated using **Plotly**. The charts are rendered in the Python backend (inside `qa_dashboard/charts/`) and securely passed to the frontend templates as JSON objects. The frontend simply mounts these Plotly JSONs into the designated div containers, making it very easy to update chart types or add new data without rewriting frontend logic.

### Backend
- **Django (Python)**: The core framework is Django. It handles routing, database connections, authentication, data processing (like aggregating QA scores and token costs), and serving the rendered HTML templates.

### Database
- **Currently SQLite**: For ease of use during development and Phase 1, the app uses Django's default SQLite database (`db.sqlite3`).
- **Production Ready**: Because we use Django's ORM (`models.py`), the database layer is fully abstracted. We can easily connect the application to a real, robust production database (like PostgreSQL, MySQL, or Oracle) simply by updating the `DATABASES` configuration in `settings.py`. The models are already structured with proper relations (`CustomUser`, `CallReport`, `QACategory`, `QAQuestion`, `Utterance`).

---

## 👥 User Roles & Views (Phase 1 vs. Future Phases)

We have already designed and built a **complete, full-scale role-based access control (RBAC) system** internally. The DB modeling and view structure support complex hierarchies:

- **TOP_MANAGEMENT**: Has access to everything, including global overviews and cost dashboards.
- **MANAGER**: Has access to their specific team's aggregated stats and the individual agents reporting to them (`agent__manager=self`).
- **AGENT**: Has access only to their own call reports and quality progression.

### 🛑 Important Note on Phase 1 Implementation
Even though this intricate user group system and specific views (`manager_dashboard`, `agent_dashboard`, `agent_detail`, etc.) are fully developed and exist in the codebase:
- **Phase 1 uses a simplified approach**: We currently just want a single, simple dashboard.
- **What this means for the UI**: Access to these specific tailored pages has been intentionally **commented out or hidden** from the main navigation interface. 
- **Logout removed**: We also removed/disabled the logout functionality and complex authentication walls for now to streamline the Phase 1 demonstration.

Rest assured, the logic (`decorators.py`, DB queries in `services.py`) is already written. When we are ready to roll out Phase 2, we just need to uncomment the navigation links and re-enable the standard login/logout flow.

---

## 📂 Key Directories & Files

- `qa_dashboard/models.py`: Defines the database schema, including our `CustomUser` (with roles), `CallReport` (handling cost and tokens), and QA specific models.
- `qa_dashboard/views.py`: Contains the controller logic. You will see the functions for all specific roles here (even if they are currently hidden in the UI).
- `qa_dashboard/services.py`: Handles the heavy lifting for DB queries, aggregating stats, and filtering by date ranges.
- `qa_dashboard/charts/`: This module handles all the Plotly figure generation. Functions here take queried data and return Plotly JSONs for the views.
- `qa_dashboard/templates/`: Contains all the plain HTML files. You will notice `{% block content %}` structures standard to Django.

## 🚀 Getting Started

To work on this project locally, standard Django commands apply:
```bash
python manage.py generate_mock_data 
python manage.py runserver
```
This will generate mock data for the database (updated to the date of the day you run the command) and run the development server.

To access the dashboard, go to http://127.0.0.1:8000/ and use the following credentials:
Username: [topmanager]
Password: [password123]
(-> We created this in the generate mock data command)

If you need to change anything regarding the charts, look into `qa_dashboard/charts/*.py`. If you need to modify the UI, simply edit the HTML/CSS in `qa_dashboard/templates/` and `qa_dashboard/static/`.

*We are ready to scale when needed.*
