import os
import sys
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

RAW_DIR = Path(__file__).parent / 'raw'

FILE_TO_TABLE = {
    "olist_orders_dataset.csv": "orders",
    "olist_order_items_dataset.csv": "order_items",
    "olist_order_payments_dataset.csv": "order_payments",
    "olist_order_reviews_dataset.csv": "order_reviews",
    "olist_customers_dataset.csv": "customers",
    "olist_products_dataset.csv": "products",
    "olist_sellers_dataset.csv": "sellers",
    "olist_geolocation_dataset.csv": "geolocation",
    "product_category_name_translation.csv": "product_category_translation",
}

def get_engine():
    host = os.environ["POSTGRES_HOST"]
    port = os.environ["POSTGRES_PORT"]
    db = os.environ["POSTGRES_DB"]
    user = os.environ["POSTGRES_USER"]
    pw = os.environ["POSTGRES_PASSWORD"]
    url = f"postgresql+psycopg2://{user}:{pw}@{host}:{port}/{db}"
    return create_engine(url)

def load_all():
    if not RAW_DIR.exists() or not any(RAW_DIR.glob('*csv')):
        sys.exit(
            f'No CSV files found in {RAW_DIR}.'
        )

    engine = get_engine()

    for filename, table_name in FILE_TO_TABLE.items():
        path = RAW_DIR / filename
        if not path.exists():
            print(f' NOT FOUND: {filename}')
            continue

        print(f' loading {filename} -> table {table_name}', end=' ', flush=True)
        df = pd.read_csv(path)

        for col in df.columns:
            if 'date' in col or 'timestamp' in col:
                df[col] = pd.to_datetime(df[col], errors='coerce')

        df.to_sql(table_name, engine, if_exists='replace', index=False, chunksize=5000)
        print(f'Completed ({len(df):,}) rows')

    print('\nAll tables loaded. Commencing sanity check... ')
    with engine.connect() as conn:
        from sqlalchemy import text

        tables = conn.execute(
            text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
        ).fetchall()
        for (t,) in tables:
            count = conn.execute(text(f'SELECT COUNT(*) FROM "{t}"')).scalar()
            print(f' {t}: {count:,} rows')


if __name__=='__main__':
    load_all()