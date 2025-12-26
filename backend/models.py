from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Context Data
    trusted_ip = Column(String, nullable=True) # IP used during enrollment

    # Relationship
    biometrics = relationship("BiometricTemplate", back_populates="owner")
    logs = relationship("AccessLog", back_populates="user")

class BiometricTemplate(Base):
    __tablename__ = "biometric_templates"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # The secret token/seed used for BioHashing (Keep secret!)
    seed_token = Column(Integer, nullable=False)
    
    # Face BioHash
    biohash_data = Column(String, nullable=False)

    # Fingerprint Fuzzy Vault (Stored as JSON string)
    fingerprint_vault = Column(String, nullable=True)

    # Palm Vault (Stored as JSON string)
    palm_vault = Column(String, nullable=True)

    owner = relationship("User", back_populates="biometrics")

class AccessLog(Base):
    __tablename__ = "access_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    ip_address = Column(String)
    trust_score = Column(String) # Store as string "0.85" for simplicity or Float
    decision = Column(String) # ALLOW / DENY
    
    user = relationship("User", back_populates="logs")
