# Kalandar

A simple calendar web application built with Python, Flask, Jinja2, and SQLite.

## Features

- Create, view, and delete calendar events
- Responsive UI using Bootstrap
- Interactive calendar view using FullCalendar.js

## Prerequisites

- Python 3.7+
- pip

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/kalandar.git
cd kalandar
```

2. Create and activate a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Run the application:

```bash
python main.py
```

5. Open your web browser and navigate to: `http://127.0.0.1:5000`

## Project Structure

```
kalandar/
│
├── kalandar/              # Application package
│   ├── __init__.py        # Application factory and database setup
│   ├── views.py           # Main application routes
│   ├── models.py          # Database models
│   ├── static/            # Static files (CSS, JS)
│   │   └── css/
│   │       └── styles.css
│   └── templates/         # Jinja2 templates
│       ├── base.html
│       ├── home.html
│       ├── calendar.html
│       └── create_event.html
│
├── main.py                # Application entry point
└── requirements.txt       # Project dependencies
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.