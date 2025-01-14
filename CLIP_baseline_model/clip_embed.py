import os
import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from transformers import CLIPProcessor, CLIPModel, pipeline
from PIL import Image
import pymysql
from dotenv import load_dotenv
import json

torch_dtype = torch.float16
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
clip = CLIPModel.from_pretrained("openai/clip-vit-large-patch14").to(device)
clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-large-patch14")
summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6", device=0 if torch.cuda.is_available() else -1)
tokenizer = clip_processor.tokenizer



# TODO: Change the print to logger.

# Function to connect to the database
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
        print("Connection successful!")
        return connection
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        return None

# Function to fetch data from a table
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

def insert_data_to_db_using_sql(connection, sql):
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql)
            connection.commit()
            return True
    except Exception as e:
        print(f"Error inserting data: {e}")
        return False

def update_data_in_db_using_sql(connection, sql):
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql)
            connection.commit()
            return True
    except Exception as e:
        print(f"Error updating data: {e}")
        return False

def delete_data_from_db_using_sql(connection, sql):
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql)
            connection.commit()
            return True
    except Exception as e:
        print(f"Error deleting data: {e}")
        return False

# Function to close the connection
def close_connection(connection):
    try:
        if connection:
            connection.close()
            print("Connection closed.")
    except Exception as e:
        print(f"Error closing the connection: {e}")


def summarize_text(text, summarizer):
    summary = summarizer(text, max_length=64, min_length=32, do_sample=False)
    return summary[0]['summary_text']

sql = 'SELECT item_id, description FROM item_info LIMIT 10'
conn = connect_to_db()
id_description = get_data_from_db_using_sql(conn, sql)
df = pd.DataFrame(id_description)

for index, row in df.iterrows():
    tokens = None
    description = row['description']
    tokens = tokenizer(description, truncation=False, return_tensors="pt")
    if tokens.input_ids.shape[1] > 64:
        summarized_description = summarize_text(description, summarizer)
        df.at[index, 'description'] = summarized_description

class EmbeddingsDataset(Dataset):
    def __init__(self, df, transform=None):
        self.data = df
        self.transform = transform
        self.IMAGE_PATH  = r"C:\Users\admin\Desktop\　\development\Resource\imgs"

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data.iloc[idx]
        item_id = item['item_id']
        description = item['description']
        image_path = os.path.join(self.IMAGE_PATH, f"{item_id}.jpg")
        image = Image.open(image_path)
        if self.transform:
            image = self.transform(image)  
        description = tokenizer(description, return_tensors="pt", truncation=True, padding='max_length').to(device)
        image = clip_processor(images=image, return_tensors="pt").to(device)      
        return item_id, image, description

dataset = EmbeddingsDataset(df, transform=transforms.ToTensor())
dataloader = DataLoader(dataset, batch_size=64, shuffle=False)


clip.eval()
with torch.no_grad():
    for item_id, images, descriptions in dataloader:
        image_features = clip.get_image_features(images)
        text_features = clip.get_text_features(descriptions)
        similarities = (100.0 * image_features @ text_features.T).softmax(dim=-1)
        similarities = similarities.cpu().numpy().astype(float).round(3)
        for i in range(len(item_id)):
            image_feature_json = json.dumps(image_features[i].cpu().numpy().tolist())
            text_feature_json = json.dumps(text_features[i].cpu().numpy().tolist())
            similarity = similarities[i]
            sql = f"INSERT INTO clip_embeddings(item_id, image_feature, text_feature, similarity) VALUES ({item_id[i]}, '{image_feature_json}', '{text_feature_json}', '{similarity}')"
            connect = connect_to_db()
            update_data_in_db_using_sql(connect, sql)
            close_connection(connect)
        
