from sqlalchemy import Column, Integer, LargeBinary, String
from database.database import Base

class Thumbnail(Base):
    __tablename__ = "thumbnails"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, unique=True, index=True)
    image_data = Column(LargeBinary)
