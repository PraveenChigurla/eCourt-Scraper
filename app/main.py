from fastapi import FastAPI, Form, Depends, HTTPException, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models import CaseQuery
from app.scraper import scrape_case_details
from pydantic import BaseModel

app = FastAPI()
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

class CaseInput(BaseModel):
    case_type: str
    case_number: str
    filing_year: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/", response_class=HTMLResponse)
async def get_form(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/fetch-case", response_class=HTMLResponse)
async def fetch_case(
    request: Request,
    case_type: str = Form(...),
    case_number: str = Form(...),
    filing_year: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        # Validate inputs
        if not case_type or not case_number or not filing_year:
            raise HTTPException(status_code=400, detail="All fields are required")

        # Scrape case details
        result = scrape_case_details(case_type, case_number, filing_year)

        # Store in DB (raw_response only, as other fields are not parsed)
        db_query = CaseQuery(
            case_type=case_type,
            case_number=case_number,
            filing_year=filing_year,
            raw_response=result["raw_response"]
        )
        db.add(db_query)
        db.commit()
        db.refresh(db_query)

        # Render results in the same tab
        return templates.TemplateResponse(
            "results.html",
            {
                "request": request,
                "raw_content": result["raw_response"]
            }
        )
    except HTTPException as e:
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "error": str(e.detail)}
        )
    except Exception as e:
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "error": f"Server error: {str(e)}"}
        )