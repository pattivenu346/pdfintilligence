from datetime import datetime
from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base


class Paper(Base):
    __tablename__ = "papers"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(300), default="Untitled paper")
    subject: Mapped[str] = mapped_column(String(300), default="Unknown", index=True)
    course_code: Mapped[str] = mapped_column(String(80), default="Unknown", index=True)
    department: Mapped[str] = mapped_column(String(120), default="Unknown", index=True)
    semester: Mapped[str] = mapped_column(String(40), default="Unknown", index=True)
    regulation: Mapped[str] = mapped_column(String(80), default="Unknown")
    year: Mapped[str] = mapped_column(String(10), default="Unknown", index=True)
    month: Mapped[str] = mapped_column(String(30), default="Unknown")
    exam_type: Mapped[str] = mapped_column(String(80), default="Unknown")
    duration: Mapped[str] = mapped_column(String(60), default="Unknown")
    marks: Mapped[str] = mapped_column(String(30), default="Unknown")
    university: Mapped[str] = mapped_column(String(300), default="Unknown")
    page_count: Mapped[int] = mapped_column(Integer, default=0)
    pdf_path: Mapped[str] = mapped_column(String(1000))
    content_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    text_content: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
