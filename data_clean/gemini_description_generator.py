from dotenv import load_dotenv
import os
import google.generativeai as genai
import PIL.Image
import pymysql
from time import sleep
from multiprocessing import Process, Queue
import multiprocessing

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

simple_prompt = """
Provide a detailed description of the clothing item in the image. 
Include the garment type, color, material, sleeve length, neckline, style, fit, suitable occasions, seasonality, any patterns or prints, and unique design details.(In English)
Example: A white cotton T-shirt with soft ribbed texture, short sleeves, casual style, a round neck, slim fit, everyday wear, suitable for spring or summer, solid white color with a subtle crown print.
"""


generator_prompt = """
Generate a concise yet comprehensive description of a clothing item based on its image by the following steps:
Step 1. Tokenize & Tag
Identify descriptive tokens (e.g., color, material, sleeve length, neckline) and parts of speech (adjectives vs. nouns).
Step 2. Synonym & Lemma Normalization
Map any synonyms or variant phrases to a consistent set of terms (e.g., “neckline” ↔ “collar,” “sleeve” ↔ “sleeves”).  
Step 3. Extract the following key attributes
- Garment Type (e.g., T-shirt, jacket, hoodie)  
- Color (e.g., white, black, red)  
- Material (e.g., cotton, denim, polyester)  
- Sleeve Length (e.g., short, long)  
- Neckline (e.g., round, V-neck)  
- Style & Fit (e.g., casual, slim, oversized)  
- Suitable Occasions & Seasonality (e.g., everyday wear, formal, spring, winter)  
- Patterns or Prints (e.g., floral, striped, solid)  
- Unique Design Details (e.g., ribbed texture, embroidered logo)
Step 4. Cross-Feature Generation 
Recognize combined insights (e.g., “cotton + spring” = lightweight fabric suitable for mild weather).
Step 5. Domain-Aware Refinement 
Filter out redundant words (stopwords, repeated adjectives) but highlight significant domain-specific features (e.g., “worn denim” or “ribbed texture”).
Finally, provide a concise yet comprehensive description** of the clothing item IN ENGLISH, incorporating all the above features.  

Example Output:
> A white cotton T-shirt with a soft ribbed texture, short sleeves, a round neck, casual style, slim fit, suitable for everyday wear in spring or summer, and a subtle crown print.
"""

image_folder = r"imgs_path"

# ----------------- Database Functions -----------------

def connect_to_db():
    try:
        load_dotenv()  # Load environment variables
        connection = pymysql.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            db=os.getenv("DB_NAME"),
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        # print("Connection successful!")
        return connection
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        return None
    

def get_data_from_db_using_sql(connection, sql):
    try:
        with connection.cursor() as cursor:
            # Example SQL query to fetch data
            sql_query = f"{sql}"
            cursor.execute(sql_query)
            result = cursor.fetchall()  # Fetch all rows
            return result
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None
    

def update_data_in_db_using_sql(connection, sql):
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql)
            connection.commit()
            return True
    except Exception as e:
        print(f"Error updating data: {e}")
        return False

def close_connection(connection):
    try:
        if connection:
            connection.close()
    except Exception as e:
        print(f"Error closing the connection: {e}")

# ----------------- Main Functions -----------------

def get_all_ids():
    con = connect_to_db()
    # sql = 'SELECT item_id FROM classify_amazon WHERE item_label <> 0 AND img_text_prob < 30 AND generate_description IS NULL'
    sql = 'SELECT goodsNo as item_id FROM musina_info WHERE generate_description IS NULL'
    result = get_data_from_db_using_sql(con, sql)
    con.close()
    return result

def update_one_id(id:int):
    try:
        con = connect_to_db()
        item_id = id
        image_path = os.path.join(image_folder, f"{item_id}.jpg")
        upload_image = PIL.Image.open(image_path)
        response = model.generate_content([generator_prompt, upload_image])
        generate_description = response.text
        # remove the /n at the end of the sentence
        generate_description = response.text.replace("\n", "").replace('"', "").replace("'", "")
        update_sql = f"UPDATE musina_info SET generate_description = '{generate_description}' WHERE goodsNo = {item_id}"
        update_data_in_db_using_sql(con, update_sql)
        print(generate_description)
        close_connection(con)
    except Exception as e:
        print(f"Error: {e}")
        sleep(10)

def get_an_id(q: Queue) -> int:
    try:
        item = q.get_nowait()
        return item['item_id']
    except Exception as e:
        raise e


def worker(shared_queue):
    while True:
        try:
            id = get_an_id(shared_queue)
            update_one_id(id)
        except multiprocessing.queues.Empty:
            break  # Exit the loop if the queue is empty
        except Exception as e:
            print(f"Worker encountered an error: {e}")
            break  # Optionally handle or log the exception



if __name__ == "__main__":

    multiprocessing.set_start_method('spawn')
    result = get_all_ids()
    
    shared_queue = Queue()

    for item in result:
        shared_queue.put(item)

    # Create a pool of worker processes
    num_workers = 60
    processes = []
    for _ in range(num_workers):
        p = Process(target=worker, args=(shared_queue,))
        processes.append(p)
        p.start()
    
    # Wait for all processes to finish
    for p in processes:
        p.join()