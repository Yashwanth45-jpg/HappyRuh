# /src/db_logger/crud.py
"""
Create, Read, Update, Delete (CRUD) operations for the database models.
This replaces the functions previously in the old `db.py` file.
"""
import datetime
from .db import get_db_session
from .models import PipelineRun, ShopifyProductRaw
from sqlalchemy.dialects.postgresql import insert

def upsert_raw_product(product_data: dict):
    """
    Inserts or updates a single raw Shopify product in the database.
    This is a convenience wrapper around the batch function.
    """
    upsert_raw_products_batch([product_data])

def upsert_raw_products_batch(products_data: list[dict]):
    """
    Inserts or updates a batch of raw Shopify products in the database.
    This uses a modern SQLAlchemy 2.0 style "INSERT ... ON CONFLICT DO UPDATE".

    :param products_data: A list of dictionaries, each containing product info.
    """
    if not products_data:
        return

    # Prepare the values for insertion
    insert_values = []
    for p_data in products_data:
        insert_values.append({
            "product_id": p_data["id"],
            "handle": p_data.get("handle"),
            "title": p_data.get("title"),
            "url": p_data.get("url"),
            "description": p_data.get("description"),
            "product_type": p_data.get("product_type"),
            "images": p_data.get("images"),
            "variants": p_data.get("variants"),
            "product_json": p_data.get("product_json"),
            "fetched_at": p_data.get("fetched_at"),
        })

    stmt = insert(ShopifyProductRaw).values(insert_values)

    # Define the update statement for the "ON CONFLICT" clause
    update_stmt = stmt.on_conflict_do_update(
        index_elements=['product_id'],
        set_=dict(
            handle=stmt.excluded.handle,
            title=stmt.excluded.title,
            url=stmt.excluded.url,
            description=stmt.excluded.description,
            product_type=stmt.excluded.product_type,
            images=stmt.excluded.images,
            variants=stmt.excluded.variants,
            product_json=stmt.excluded.product_json,
            fetched_at=stmt.excluded.fetched_at,
        )
    )
    
    with get_db_session() as session:
        session.execute(update_stmt)
        session.commit()


def fetch_all_raw_products() -> list[dict]:
    """
    Fetches all raw products from the database.
    """
    with get_db_session() as session:
        results = session.query(ShopifyProductRaw).all()
        return [
            {
                "product_id": p.product_id,
                "handle": p.handle,
                "title": p.title,
                "url": p.url,
                "product_json": p.product_json,
            }
            for p in results
        ]

# ----- Pipeline Run Logs -----

def create_pipeline_run(pipeline_name: str) -> int:
    """
    Creates a new record for a pipeline run and returns the run ID.
    """
    with get_db_session() as session:
        new_run = PipelineRun(pipeline_name=pipeline_name, status='running')
        session.add(new_run)
        session.commit()
        session.refresh(new_run)
        return new_run.run_id

def finish_pipeline_run(
    run_id: int,
    status: str,
    products_raw_count: int | None = None,
    qdrant_upserted_count: int | None = None,
    error: str | None = None
):
    """
    Updates a pipeline run record to mark it as finished.
    """
    with get_db_session() as session:
        run = session.query(PipelineRun).filter(PipelineRun.run_id == run_id).one()
        run.status = status
        run.products_raw_count = products_raw_count
        run.qdrant_upserted_count = qdrant_upserted_count
        run.error = error
        session.commit()

def get_last_pipeline_runs(limit: int = 10) -> list[dict]:
    """
    Retrieves the most recent pipeline runs.
    """
    with get_db_session() as session:
        runs = session.query(PipelineRun).order_by(PipelineRun.run_id.desc()).limit(limit).all()
        return [
            {
                "run_id": r.run_id,
                "pipeline_name": r.pipeline_name,
                "started_at": r.started_at,
                "finished_at": r.finished_at,
                "status": r.status,
                "products_raw_count": r.products_raw_count,
                "qdrant_upserted_count": r.qdrant_upserted_count,
                "error": r.error,
            }
            for r in runs
        ]

def fetch_all_raw_products() -> list[dict]:
    """
    Fetches all raw products from the database.
    """
    with get_db_session() as session:
        results = session.query(ShopifyProductRaw).all()
        r=[]
        for p in results:
            r.append(normalize_product(p.product_json))
        
        return r

def normalize_product(p):
    # Extract price safely
    price_amount = (
        p.get("variants", {}).get("edges", [{}])[0]
        .get("node", {}).get("price", {}).get("amount", "0")
    )

    currency = (
        p.get("variants", {}).get("edges", [{}])[0]
        .get("node", {}).get("price", {}).get("currencyCode", "INR")
    )

    images = [
        {"src": edge["node"]["src"]}
        for edge in p.get("images", {}).get("edges", [])
        if "node" in edge and "src" in edge["node"]
    ]

    return {
        "id": p.get("id"),
        "title": p.get("title"),
        "handle": p.get("handle"),
        "body_html": p.get("descriptionHtml"),
        "vendor": "HappyRuH",
        "product_type": p.get("productType"),
        "variants": [
            {"price": price_amount, "currency": currency}
        ],
        "images": images,
        "options": []
    }