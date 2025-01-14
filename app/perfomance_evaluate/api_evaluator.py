from src.extensions.chatgpt_client import client
from evaluator_prompt import evaluator_beta_v0
from prompt_generator import sythetic_prompts
from src.services.consulting_service import consulting_main
import os
import json
import multiprocessing as mp


def prompt_iterator(prompt_list: list):
    """
    # *@param prompt_list: A list of prompts to be iterated.
    # *@return: A dictionary containing the prompt and the response.
    # *Description:
    #   This function takes a list of prompts and iterates through them, generating a response for each.
    """
    score = []
    for prompt in prompt_list:
        _, result= consulting_main(prompt)
        img_list = []
        for _, value in result.items():
                img_list.append(os.path.join('static/imgs', f"{value[0]}.jpg"))
        score.append(recommendation_evaluator(prompt, img_list))
    
    return score

def recommendation_evaluator(origin_prompt: str, images: list) -> dict:
    """
    # TODO: Complete and verify this function.
    # *@param origin_prompt: The user's question or request about clothing parts.
    # *@param images: The recommended images for the user.
    # *@return score: A dictionary containing the score of the recommendation.
    # *Description:
    #   This function take the origin prompt and the recommended images, and send them to the OpenAI API to evaluate the recommendation.
    #   It uses function calling to ensure the response includes the desired information.
    """
    
    messages = [{
        "role": "user",
        "content": (
            f"{origin_prompt}"
        )
    }]
    
    response = client.chat.completions.create(
        model="text-davinci-003",  
        messages=messages,
        functions=[evaluator_beta_v0],
        function_call={"name": "prompt_handler"}  # Force the model to call this specific function
    )
    
    arguments = response.choices[0].message.function_call.arguments
    parsed_arguments = json.loads(arguments)
    
    return parsed_arguments


# run the prompt_iterator function parrallelly(multi-process) in the background
def run_prompt_iterator():
    """
    # *@param prompt_list: A list of prompts to be iterated.
    # *@return: A dictionary containing the prompt and the response.
    # *Description:
    #   This function takes a list of prompts and iterates through them, generating a response for each.
    """
    prompt_list=sythetic_prompts
    pool = mp.Pool(mp.cpu_count())
    results = pool.map(prompt_iterator, [prompt_list])
    pool.close()
    # Combine the results
    return results
