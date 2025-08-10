Court Data Fetcher
A web application to fetch case metadata and orders/judgments from the Karimnagar District Court (https://karimnagar.dcourts.gov.in/). This project was built from scratch to meet the requirements of Task 1 in the provided internship assignment, without using pre-existing code or templates beyond open-source libraries cited below.
Court Chosen
Karimnagar District Court was selected due to its accessible case status page, which provides public access to case details via a JavaScript-driven interface. The site requires dynamic scraping, handled using Selenium.
Setup Instructions

Clone the Repository:git clone <repo-url>
cd court-data-fetcher


Install Dependencies:Ensure Python 3.8+ is installed, then run:pip install -r requirements.txt


Set Up PostgreSQL:
Option 1: Using Docker (recommended):docker-compose up -d

This starts a PostgreSQL container with the database court_db, user postgres, and password vagrant.
Option 2: Local PostgreSQL:Install PostgreSQL locally, create a database named court_db, and ensure the user/password match the .env configuration.


Configure Environment Variables:
Copy .env.sample to .env:cp .env.sample .env


Update .env with the correct DATABASE_URL if needed (default: postgresql://postgres:vagrant@localhost:5432/court_db).
Add ANTICAPTCHA_API_KEY for CAPTCHA solving (see CAPTCHA Strategy).


Initialize the Database:python init_db.py

This creates the necessary tables (case_queries) in the court_db database.
Run the Application:uvicorn app.main:app --reload

The app will be available at http://localhost:8000.
Access the App:Open http://localhost:8000 in a browser to use the form for fetching case details.

CAPTCHA Strategy
The Karimnagar District Court website uses an image-based CAPTCHA on its case status page. The current implementation integrates the Anti-Captcha service (anticaptchaofficial) to programmatically solve and bypass CAPTCHAs in a legal manner, as it complies with the service's terms and is used solely for accessing publicly available court data without violating any laws or site policies. Key details:

API Key: Requires an Anti-Captcha API key, set in the .env file as ANTICAPTCHA_API_KEY. A default placeholder key is included for testing but should be replaced with a valid key for production use.
Process: The CAPTCHA image is downloaded, sent to Anti-Captcha, and the solved text is entered into the form.
Fallback: If CAPTCHA solving fails after three attempts, a user-friendly error is displayed.
Note: Due to time constraints, alternative CAPTCHA strategies (e.g., manual input or court APIs) were not implemented. For production, consider integrating a service like 2Captcha or exploring court-provided APIs if available.

Environment Variables

DATABASE_URL: PostgreSQL connection string (e.g., postgresql://postgres:vagrant@localhost:5432/court_db).
ANTICAPTCHA_API_KEY: Anti-Captcha API key for CAPTCHA solving (e.g., your_anticaptcha_api_key_here).

Technologies Used
This project is built using Python as the primary programming language. Key technologies and libraries include:

Backend Framework: FastAPI for handling API endpoints and form submissions.
Database Management: PostgreSQL as the RDBMS, with SQLAlchemy for ORM and query logging, and psycopg2 for connectivity.
Web Scraping: Selenium for navigating and interacting with the dynamic court website, along with webdriver-manager for ChromeDriver handling.
CAPTCHA Solving: anticaptchaofficial for legally bypassing CAPTCHAs via API.
Templating and UI: Jinja2 for HTML templating, Bootstrap 5.3.3 (via CDN) for responsive styling.
Environment Management: python-dotenv for loading environment variables.
Other Utilities: requests for HTTP operations, beautifulsoup4 (optional for future parsing), and various support libraries like pydantic for data validation.

The full list of dependencies is specified in requirements.txt, which includes additional libraries for potential extensions (e.g., data processing with pandas, numpy; machine learning with tensorflow, scikit-learn), though not all are actively used in the core functionality.
Features Implemented

UI: A simple, responsive form (index.html) with dropdowns for Case Type and inputs for Case Number and Filing Year, styled with Bootstrap.
Backend: FastAPI handles form submissions, triggers Selenium-based scraping, and stores raw HTML responses in PostgreSQL.
Scraping: Selenium navigates the Karimnagar District Court website, selects the court complex, inputs case details, solves CAPTCHAs, and extracts case details (raw HTML for now).
Storage: Queries and raw HTML responses are logged in a PostgreSQL database (case_queries table).
Display: Raw case details are rendered in results.html with a "Back to Search" button.
Error Handling: User-friendly error messages for invalid inputs, site downtime, CAPTCHA failures, and unexpected errors.
PDF Links: The scraper captures raw HTML, which includes links to order/judgment PDFs, displayed for user download (parsing specific fields like parties or dates is incomplete).

Limitations and Future Improvements

Parsing: Currently, only raw HTML is stored and displayed due to time constraints. Future work includes parsing parties' names, filing/next-hearing dates, and PDF links using libraries like BeautifulSoup.
CAPTCHA Robustness: Relies on Anti-Captcha; exploring court APIs or manual CAPTCHA input could improve reliability.
Optional Features: Dockerfile, pagination for multiple orders, unit tests, and CI workflow were not implemented due to time limits but are planned for future iterations.
Security: No hard-coded secrets, but additional input sanitization could enhance robustness.

Notes

The app is robust against minor site layout changes due to flexible XPath/CSS selectors, but significant redesigns may require updates to the scraper.
The code is structured for clarity, with modular files (main.py, scraper.py, models.py, database.py) and comments.
The UI prioritizes simplicity and responsiveness, tested on desktop and mobile.

License
This project is licensed under the MIT License. See LICENSE file for details.