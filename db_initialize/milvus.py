from pymilvus import connections, FieldSchema, CollectionSchema, DataType, Collection, utility
from dotenv import load_dotenv
import os
import pymysql
import json
import numpy as np
import logging
from time import sleep

# Configure logging
logging.basicConfig(filename='data_ingestion.log', level=logging.INFO,
                    format='%(asctime)s %(levelname)s:%(message)s')

# Load environment variables
load_dotenv()

# Database connection
def connect_to_db():
    try:
        connection = pymysql.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            db=os.getenv("DB_NAME"),
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        return connection
    except Exception as e:
        logging.error(f"Error connecting to the database: {e}")
        return None

# Fetch data with retries
def fetch_data(sql, retries=3, delay=5):
    for attempt in range(retries):
        connection = connect_to_db()
        if not connection:
            logging.error("Database connection failed.")
            sleep(delay)
            continue
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchall()
                return result
        except pymysql.MySQLError as e:
            logging.error(f"MySQL error on attempt {attempt+1}: {e}")
            sleep(delay)
        finally:
            connection.close()
    logging.error("All retries failed for fetching data.")
    return []

# Process embeddings efficiently
def process_embeddings(data, embedding_field='embeddings'):
    embeddings = []
    cleaned_data = []
    for record in data:
        try:
            embedding = json.loads(record[embedding_field])
            embeddings.append(np.array(embedding, dtype=np.float16))
            # Prepare cleaned record without 'embeddings'
            cleaned_record = {k: v for k, v in record.items() if k != embedding_field}
            cleaned_record['embedding'] = embeddings[-1]
            cleaned_data.append(cleaned_record)
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logging.error(f"Error processing embedding for item_id {record.get('item_id')}: {e}")
    return cleaned_data

# Create or get collection
def create_collection(name, schema):
    if name not in utility.list_collections():
        collection = Collection(name=name, schema=schema)
        logging.info(f"Collection '{name}' created.")
    else:
        collection = Collection(name=name)
        logging.info(f"Collection '{name}' already exists.")
    return collection

# Create index if not exists
def create_index(collection, field_name, index_params):
    try:
        if not collection.has_index(field_name):
            collection.create_index(field_name=field_name, index_params=index_params)
            logging.info(f"Index created for field '{field_name}' in collection '{collection.name}'.")
        else:
            logging.info(f"Index already exists for field '{field_name}' in collection '{collection.name}'.")
    except Exception as e:
        logging.error(f"Error creating index for '{collection.name}': {e}")

# Insert data with retries and duplicate checks
def insert_data(collection, data, batch_size=1000, retries=3, delay=5):
    # Fetch existing item_ids to prevent duplicates
    existing_ids = set()
    try:
        results = collection.query(expr="item_id >= 0", output=["item_id"])
        existing_ids = {item['item_id'] for item in results}
    except Exception as e:
        logging.error(f"Error fetching existing item_ids from '{collection.name}': {e}")

    # Filter out existing records
    new_data = [record for record in data if record['item_id'] not in existing_ids]
    if not new_data:
        logging.info(f"No new data to insert into '{collection.name}'.")
        return

    total_new = len(new_data)
    for i in range(0, total_new, batch_size):
        batch = new_data[i:i+batch_size]
        for attempt in range(retries):
            try:
                collection.insert(batch)
                logging.info(f"Batch {i//batch_size + 1} ({i+1}-{min(i+batch_size, total_new)}) inserted successfully into '{collection.name}'.")
                break
            except Exception as e:
                logging.error(f"Error inserting batch {i//batch_size + 1} into '{collection.name}' on attempt {attempt+1}: {e}")
                sleep(delay)
        else:
            logging.error(f"Failed to insert batch {i//batch_size + 1} into '{collection.name}' after {retries} attempts.")

# Define the common fields
fields = [
    FieldSchema(name="item_id", dtype=DataType.INT64, is_primary=True, auto_id=False),
    FieldSchema(name="embedding", dtype=DataType.FLOAT16_VECTOR, dim=768),
    FieldSchema(name="gender", dtype=DataType.INT32, description="Gender: MAN=1, WOMEN=2, UNISEX=3"),
    FieldSchema(name="spring", dtype=DataType.INT32, description="Spring season flag: 1=Yes, 0=No"),
    FieldSchema(name="summer", dtype=DataType.INT32, description="Summer season flag: 1=Yes, 0=No"),
    FieldSchema(name="autumn", dtype=DataType.INT32, description="Autumn season flag: 1=Yes, 0=No"),
    FieldSchema(name="winter", dtype=DataType.INT32, description="Winter season flag: 1=Yes, 0=No")
]

schema = CollectionSchema(fields=fields, description="Clothing Items", enable_dynamic_field=False)

# Connect to Milvus
connections.connect(host='standalone', port='19530')

# Define collections and their specific index parameters
collections_info = {
    "tops": {
        "sql": """SELECT 
                    embeddings.item_id, 
                    embeddings.description_embeddings AS embeddings,
                    CASE 
                        WHEN item_info.gender IN ('MEN', 'BOYS') THEN 1
                        WHEN item_info.gender IN ('WOMEN', 'GIRLS') THEN 2
                        WHEN item_info.gender = 'UNISEX' THEN 3
                        ELSE 4
                    END AS gender,
                    item_info.spring,
                    item_info.summer,
                    item_info.autumn,
                    item_info.winter
                FROM embeddings 
                INNER JOIN item_info ON embeddings.item_id = item_info.item_id
                WHERE item_info.mastertype = 'Tops' AND item_info.exist_flag = 1""",
        "index_params": {"metric_type": "COSINE", "index_type": "HNSW", "params": {"M": 32, "efConstruction": 256}}
    },
    "pants": {
        "sql": """SELECT 
                    embeddings.item_id, 
                    embeddings.description_embeddings AS embeddings,
                    CASE 
                        WHEN item_info.gender IN ('MEN', 'BOYS') THEN 1
                        WHEN item_info.gender IN ('WOMEN', 'GIRLS') THEN 2
                        WHEN item_info.gender = 'UNISEX' THEN 3
                        ELSE 4
                    END AS gender,
                    item_info.spring,
                    item_info.summer,
                    item_info.autumn,
                    item_info.winter
                FROM embeddings 
                INNER JOIN item_info ON embeddings.item_id = item_info.item_id
                WHERE item_info.mastertype = 'Pants' AND item_info.exist_flag = 1""",
        "index_params": {"metric_type": "COSINE", "index_type": "HNSW", "params": {"M": 16, "efConstruction": 128}}
    },
    "outerwear": {
        "sql": """SELECT 
                    embeddings.item_id, 
                    embeddings.description_embeddings AS embeddings,
                    CASE 
                        WHEN item_info.gender IN ('MEN', 'BOYS') THEN 1
                        WHEN item_info.gender IN ('WOMEN', 'GIRLS') THEN 2
                        WHEN item_info.gender = 'UNISEX' THEN 3
                        ELSE 4
                    END AS gender,
                    item_info.spring,
                    item_info.summer,
                    item_info.autumn,
                    item_info.winter
                FROM embeddings 
                INNER JOIN item_info ON embeddings.item_id = item_info.item_id
                WHERE item_info.mastertype = 'Outerwear' AND item_info.exist_flag = 1""",
        "index_params": {"metric_type": "COSINE", "index_type": "HNSW", "params": {"M": 16, "efConstruction": 128}}
    },
    "dress_skirt": {
        "sql": """SELECT 
                    embeddings.item_id, 
                    embeddings.description_embeddings AS embeddings,
                    CASE 
                        WHEN item_info.gender IN ('MEN', 'BOYS') THEN 1
                        WHEN item_info.gender IN ('WOMEN', 'GIRLS') THEN 2
                        WHEN item_info.gender = 'UNISEX' THEN 3
                        ELSE 4
                    END AS gender,
                    item_info.spring,
                    item_info.summer,
                    item_info.autumn,
                    item_info.winter
                FROM embeddings 
                INNER JOIN item_info ON embeddings.item_id = item_info.item_id
                WHERE item_info.mastertype = 'Dresses & Skirts' AND item_info.exist_flag = 1""",
        "index_params": {"metric_type": "COSINE", "index_type": "HNSW", "params": {"M": 16, "efConstruction": 128}}
    }
}

for name, info in collections_info.items():
    # Create or get collection
    collection = create_collection(name, schema)
    
    # Create index
    create_index(collection, 'embedding', info['index_params'])
    
    # Fetch and process data
    data = fetch_data(info['sql'])
    if not data:
        logging.info(f"No data fetched for collection '{name}'. Skipping insertion.")
        continue
    
    data = process_embeddings(data)
    
    # Insert data
    insert_data(collection, data)
    
 
