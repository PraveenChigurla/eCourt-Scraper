from sqlalchemy import Column, Integer, String, DateTime, Text
from app.database import Base
from datetime import datetime

class CaseQuery(Base):
    __tablename__ = "case_queries"
    id = Column(Integer, primary_key=True, index=True)
    case_type = Column(String, index=True)
    case_number = Column(String, index=True)
    filing_year = Column(String, index=True)
    query_time = Column(DateTime, default=datetime.utcnow)
    raw_response = Column(Text)
    parties = Column(Text)
    filing_date = Column(String)
    next_hearing_date = Column(String)
    pdf_link = Column(String)