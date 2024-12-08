
# StefanParagon: Receipt Scanner and Analyzer

StefanParagon is a Flask-based web application that allows users to upload and analyze receipt images. The application leverages OpenAI's language models to extract structured data such as store details, product information, and total amounts. It includes features to validate and export receipt data.

## Features
- **Receipt Scanning**: Upload receipt images for analysis.
- **Data Extraction**: Automatically extract detailed receipt information, including products, store details, and totals.
- **Validation**: Cross-check itemized totals with the receipt's declared total.
- **Data Export**: Export analyzed data as Excel files.
- **Persistent Storage**: Save receipts and their data in a SQLite database.

---

## Requirements
Ensure you have the following installed on your system:
- Python 3.8+
- SQLite

### Python Dependencies
All required Python packages are listed in the `requirements.txt` file:
- Flask
- Gunicorn
- Pydantic
- Pandas
- OpenPyXL
- OpenAI
- Instructor
- Python-dotenv

Install dependencies with:

```bash
pip install -r requirements.txt
```

---

## Project Structure
```
.
├── app
│   ├── db
│   │   └── receipts.db        # SQLite database (auto-created)
│   ├── models
│   │   ├── database.py        # Database initialization and interactions
│   │   └── llm.py             # LLM integration and analysis logic
│   ├── static
│   │   ├── css
│   │   │   └── style.css      # Custom styles
│   │   └── data			   # Scanned images storage
│   ├── templates
│   │   ├── base.html          # Base HTML template
│   │   ├── scan.html          # Receipt scanning and analysis interface
│   │   └── about.html         # About page
│   ├── __init__.py            # Application initialization
│   └── routes.py              # Routes and core logic
├── requirements.txt           # Python dependencies
├── wsgi.py                    # WSGI entry point
└── README.md                  # Project documentation
```

---

## How to Run

### 1. Set up the database
Run the application once to initialize the SQLite database. The database will be created at `app/db/receipts.db`.

### 2. Start the Flask Application
Run the app using Flask's development server:

```bash
python wsgi.py
```

Access the application in your browser at: `http://127.0.0.1:5000`.

### 3. Upload and Analyze Receipts
- Navigate to the "Scan" page.
- Upload a receipt image.
- Analyze the receipt and save the results.

### 5. Export Data
Export analyzed data as an Excel file from the "Export" section.

---

## Environment Variables
The application requires an .env file to securely manage sensitive keys and variables. Add the following variables:

```bash
OPENAI_API_KEY=your_openai_api_key
```

The application automatically loads these variables using `python-dotenv`.

---

## Known Issues
- Image quality significantly affects extraction accuracy.
- Long receipts may result in token overflow errors during analysis.

---

## Contributing
Contributions are welcome! Please fork the repository and submit a pull request.

---

## License
This project is licensed under the MIT License.
