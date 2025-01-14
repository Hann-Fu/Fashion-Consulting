import json
import os
from typing import List
from dotenv import load_dotenv
import numpy as np
from PIL import Image
from pymilvus import Collection
from IPython.display import display
from src.services import handlers
from src.extensions.gemini_client import genai
from src.extensions.chatgpt_client import client
# from src.extensions.milvus_connection import init_milvus

load_dotenv()

def openai_consulting_response(prompt: str) -> dict:

    """
    # *@param prompt: The user's question or request about clothing parts.
    # *@return parsed_arguments: A dictionary containing the parsed arguments from the function call.
                                {'polite_reply': "Hello! Let's see what you're looking for.",
                                'analysis': [{'part': 'top', 'summary': 'black sweater'},
                                            {'part': 'outwear', 'summary': 'blue outdoor jacket with North Face print'},
                                            {'part': 'pants', 'summary': 'wind-prevention pants'}
                                            ]}
    # *Description:
    #   This function sends a prompt to the OpenAI API to analyze the type of clothing parts the customer wants.
    #   It uses function calling to ensure the response includes the desired information.
    """
    model_openai = os.getenv("OPEN_AI_MODEL")

    function_prompt_handler = handlers.handler_beta_v1

    messages = [{
        "role": "user",
        "content": (
            "Analyze what type of clothing the customer(top, pants, outwear, dress, or "
            "two or three of them) through the user's question, use function calling. \n"
            f"{prompt}"
            "The output should indicate which part the customer want, and what kind of clothing item does customer want for each part."
        )
    }]
    
    
    response = client.chat.completions.create(
        model=model_openai,  
        messages=messages,
        functions=[function_prompt_handler],
        function_call={"name": "prompt_handler"}  # Force the model to call this specific function
    )

    arguments = response.choices[0].message.function_call.arguments
    parsed_arguments = json.loads(arguments)
    
    return parsed_arguments

def embedding_gemini(user_input: str) -> np.ndarray:
    """
    #* @param user_input: Text input
    #* @return: text_feature: Embedding tensor of the text
    # Description:
        This function takes in text input and returns the embedding of the text
    """

    result = genai.embed_content(
                    model="models/text-embedding-004",
                    content=user_input)
    vector = np.array(result['embedding'], dtype=np.float16)

    return vector


def milvus_retrieve(collection_name: str, query_vector: np.ndarray) -> List[int]:
    """
    #* @param collection_name: Name of the collection in Milvus
    #* @param embedding: Embedding tensor of the text
    #* @return: List of ids of the retrieved embeddings
    # Description:
        This function retrieves the embeddings from Milvus and returns the ids of the retrieved embeddings
    """
    # connections.connect(host='localhost', port='19530')
    collection = Collection(name=collection_name)
    search_params = {"metric_type": "COSINE", "params": {"nprobe": 16}}
    results = collection.search(data=[query_vector], anns_field='embedding', param=search_params, limit=5)

    return results


def milvus_retrieve_filter(collection_name: str, query_vector: np.ndarray, filter_expr: str) -> List[int]:
    """
    #* @param collection_name: Name of the collection in Milvus
    #* @param embedding: Embedding tensor of the text
    #* @return: List of ids of the retrieved embeddings
    # Description:
        This function retrieves the embeddings from Milvus and returns the ids of the retrieved embeddings
    """
    # connections.connect(host='localhost', port='19530')
    collection = Collection(name=collection_name)
    # search_params = {"metric_type": "COSINE", "params": {"nprobe": 16}}
    search_params = {"metric_type": "COSINE", "params": {"efSearch": 16}}
    results = collection.search(data=[query_vector], anns_field='embedding', param=search_params, limit=5, expr=filter_expr)

    return results


def retriever(arguments: dict) -> dict:
    """
    # * @param arguments: List of retrieve objects
    # * @return: Dictionary of {part :image ids}
    # Description:
        This function retrieves the similar image ids based on the prompts and clothing parts
    # TODO: Parallelize the retrieval process
    """
    filter_dict = {
        'gender': arguments['gender'],
        'season': arguments['season']
    }


    part_img_ids = {}
    for part in arguments['analysis']:
        part_name = part['part']
        summary = part['summary']
        vector = embedding_gemini(summary)
        filter_expr = build_filter_expr(filter_dict)
        results = milvus_retrieve_filter(part_name, vector, filter_expr)

        # results = milvus_retrieve(part_name, vector)
        img_ids = [item.id for item in results[0]]
        part_img_ids[part_name] = img_ids

    return part_img_ids

def build_filter_expr(filter_dict: dict) -> str:
    """
    Build a Milvus 'expr' string based on user-provided filter dictionary.

    Example filter_dict:
        {
            'gender': '3',
            'season': ['spring', 'summer']
        }
    """
    expr_list = []

    # ----------------------------
    # Gender logic
    # possible values: 1, 2, 3
    # if 1 => "gender in [1,3]"
    # if 2 => "gender in [2,3]"
    # if 3 => "gender in [3]"
    # else => don't filter by gender
    # ----------------------------
    if 'gender' in filter_dict:
        gender_val = filter_dict['gender']
        if gender_val == '1':
            expr_list.append("gender in [1,3]")
        elif gender_val == '2':
            expr_list.append("gender in [2,3]")
        elif gender_val == '3':
            expr_list.append("gender in [3]")
        # if not 1/2/3 => do nothing

    # ----------------------------
    # Season logic
    # possible values: 'spring', 'summer', 'autumn', 'winter'
    # if a given season is in list => that field must equal 1
    # e.g. ['spring','summer'] => "spring == 1" AND "summer == 1"
    # ----------------------------
    if 'season' in filter_dict:
        season_list = filter_dict['season']
        for s in season_list:
            if s == 'spring':
                expr_list.append("spring == 1")
            elif s == 'summer':
                expr_list.append("summer == 1")
            elif s == 'autumn':
                expr_list.append("autumn == 1")
            elif s == 'winter':
                expr_list.append("winter == 1")

    # Combine into a single expr string
    if expr_list:
        return " and ".join(expr_list)
    else:
        # No filters to apply
        return ""

def display_image(img_id_list) -> None:
    image_folder = os.getenv("IMG_FOLDER_PATH")
    for item in img_id_list[0]:
        print(f"Item ID: {item.id}")
        image_path = os.path.join(image_folder, f"{item.id}.jpg")
        image = Image.open(image_path)
        display(image)

def addition_info_append(task_package: dict, additional_info: dict) -> dict:
    """
    # * @param task_package: The task package that needs to be appended
    # * @param additional_info: Additional information to be appended
    # * @return: The appended task package
    # Description:
        This function appends the additional information to the task package
    """
    try:
        if additional_info:
            task_package['gender'] = additional_info['gender']
            task_package['season'] = additional_info['season']
        else:
            task_package['gender'] = '3'
            task_package['season'] = None
    except Exception as e:
        task_package['gender'] = '3'
        task_package['season'] = None
        print(f"Error: {e}")
        return task_package
    
    return task_package


def consulting_main(prompt: str, additional_info: dict = None):
    """
    # * @param arguments: User's prompt
    # * @param additional_info: User's gender, season.
                            {'gender': '3', 'season': ['spring','summer']}
    # * @return: Greeting sentence, Dictionary of {part :image ids}
    # Description:
        The main function that orchestrates the consulting service
    """
    # init_milvus()
    # connections.connect(alias="default",host='localhost',port='19530')

    response = openai_consulting_response(prompt)
    # If greeting is not present, give a default greeting('Hi there, how can I help you today?')
    if 'polite_reply' not in response:
        response['polite_reply'] = "Hi there, how can I help you today?"
    greeting = response['polite_reply']
    task_package = addition_info_append(response, additional_info)
    res_dict = retriever(task_package)

    return greeting, res_dict


