from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

engine = create_engine("sqlite:///scvds.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class Contract(Base):
    __tablename__ = "contracts"
    id = Column(Integer, primary_key=True)
    filename = Column(String(255))
    file_path = Column(String(500))
    uploaded_at = Column(DateTime, default=datetime.now)


class Result(Base):
    __tablename__ = "results"
    id = Column(Integer, primary_key=True)
    contract_id = Column(Integer)
    vulnerability_type = Column(String(100))
    confidence = Column(Float)
    severity = Column(String(20))
    recommendation = Column(Text)
    analyzed_at = Column(DateTime, default=datetime.now)


Base.metadata.create_all(bind=engine)
