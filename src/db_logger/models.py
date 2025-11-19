# app/db_logger/models.py
from sqlalchemy import Column, Integer, String, Text, DateTime, BigInteger
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from .base import Base

class LLMLog(Base):
    __tablename__ = "llm_logs"

    id = Column(Integer, primary_key=True, index=True)
    response_html = Column(Text, nullable=False)
    model = Column(String(100), nullable=False)
    request_ts = Column(DateTime(timezone=True), server_default=func.now())
    response_ts = Column(DateTime(timezone=True), nullable=False)
    latency_ms = Column(Integer, nullable=False)
    error = Column(Text, nullable=True)


class ShopifyProductRaw(Base):
    __tablename__ = "shopify_products_raw"

    product_id = Column(BigInteger, primary_key=True)
    handle = Column(Text)
    title = Column(Text)
    url = Column(Text)
    description = Column(Text, nullable=True)
    product_type = Column(Text, nullable=True)
    images = Column(JSONB, nullable=True)
    variants = Column(JSONB, nullable=True)
    product_json = Column(JSONB, nullable=False)
    fetched_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    run_id = Column(Integer, primary_key=True, autoincrement=True)
    pipeline_name = Column(Text)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    finished_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(Text)  # 'running' | 'ok' | 'error'
    products_raw_count = Column(Integer, nullable=True)
    qdrant_upserted_count = Column(Integer, nullable=True)
    error = Column(Text, nullable=True)