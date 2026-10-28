# TasteMatch | Restaurant Recommendation Platform

TasteMatch is a full-stack restaurant discovery and recommendation platform designed to help users explore restaurants based on cuisine, budget, location, and personal preferences.

The project combines a responsive web interface with a Python backend, structured restaurant data, and a foundation for personalized recommendations using machine learning.

## Features

- **Restaurant Discovery:** Browse restaurant listings with names, cuisines, ratings, prices, and locations.
- **Interactive Search:** Search by restaurant name and filter results by cuisine, price range, and location.
- **Restaurant Data Management:** Import restaurant records from a CSV dataset into a relational database.
- **RESTful API:** Retrieve restaurant information, manage user preferences, submit ratings, and record user interactions.
- **Recommendation Architecture:** Support for recommendation services using collaborative filtering and restaurant attributes.
- **Responsive Interface:** A clean, accessible layout designed for desktop and mobile screens.
- **Legal Information Pages:** Dedicated privacy policy and terms of service pages.

## Technology Stack

| Category | Technologies |
|---|---|
| Backend | Python, FastAPI, Uvicorn |
| Database and ORM | PostgreSQL, SQLAlchemy |
| Data Processing | Pandas |
| Machine Learning | scikit-learn, Surprise |
| Data Validation | Pydantic |
| Frontend | HTML5, CSS3, JavaScript |
| Configuration | Environment variables, `pydantic-settings` |

## Project Structure

```text
restaurant_recommender/
├── app/
│   ├── routers/
│   │   ├── restaurants.py
│   │   ├── recommendations.py
│   │   └── users.py
│   ├── services/
│   │   └── recommender.py
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   ├── database.py
│   └── config.py
├── data/
│   └── restaurants.csv
├── ml/
│   └── artifacts/
├── web/
│   ├── index.html
│   ├── styles.css
│   ├── app.js
│   ├── privacy.html
│   └── terms.html
├── import_restaurants.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

*Note: The structure above describes the main project components. Some directories or files may vary depending on the current implementation.*

## Getting Started

### Prerequisites

- Python installed on your system
- Git
- A database supported by the project configuration, such as PostgreSQL or SQLite
- The project dataset, subject to its distribution license

### 1. Clone the repository

```bash
git clone https://github.com/haninatwi0/TasteMatch.git
cd TasteMatch
```

### 2. Create a virtual environment

**Windows PowerShell**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks script execution