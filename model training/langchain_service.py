import json
import os
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage, SystemMessage
from langchain.chains import OpenAIModerationChain
from dotenv import load_dotenv  
from pydantic import BaseModel, Field, ValidationError
from typing import List


load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ---------- Step 1: Ask for User’s Goal ----------
def get_user_goal() -> str:
    goal = input("Enter your goal or idea: ")
    plan = input("Enter your plan(optional, could be empty): ")
    return goal, plan


# ---------- Step 2: Check Prompt Against Policies ----------
def check_policy(goal: str, plan: str) -> bool:
    """Uses OpenAI's Moderation API via LangChain to check content safety."""
    moderation_chain = OpenAIModerationChain(error_on_moderation=False)
    result = moderation_chain.invoke(goal + plan)
    if result["output"] == "Text was found that violates OpenAI's content policy.":
        return False
    return True  # Returns False if prohibited content is found, True if safe


# ---------- Step 3: Get Further Information Needed via Function Calling ----------
@DeprecationWarning
def get_further_info_fc(user_goal: str) -> dict:
    # Define a function schema for further information analysis.
    further_info_schema = {
        "name": "further_info_analyzer",
        "description": "Analyze the user's goal or plan to determine what further information is needed to tailor a plan."
                       "In addition, the user's personality should be considered. ",
        "parameters": {
            "type": "object",
            "properties": {
                "flag": {
                    "type": "boolean",
                    "description": "Indicates whether further information is needed."
                },
                "info_needed": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "keyword": {"type": "string", "description": "A keyword of information needed."},
                            "guide": {"type": "string", "description": "Instructions on what to provide."},
                            "auto_gen": {"type": "string", "description": "An example text that could give users a reference."}
                        },
                        "required": ["keyword", "guide", "auto_gen"]
                    },
                    "description": "List of additional information requirements for making a perfect plan.",
                    "additionalProperties": False
                },
                "strict": True
            },
            "required": ["flag", "info_needed"]
        }
    }

    # Build messages (using system and human messages)
    messages = [
        SystemMessage(content="You are a plan consultant who analyzes what further information is needed."),
        HumanMessage(content=f"User's goal/idea/plan: {user_goal}")
    ]

    # Initialize the ChatOpenAI model (using GPT-4o)
    chat = ChatOpenAI(model_name="gpt-4o-mini", temperature=1.0, openai_api_key=OPENAI_API_KEY)
    # Call the API with function calling enabled (forcing the call to further_info_analyzer)
    response = chat.invoke(
        messages,
        functions=[further_info_schema],
        function_call={"name": "further_info_analyzer"}
    )

    # Extract the function call data
    fc = response.additional_kwargs.get("function_call")
    if not fc:
        raise ValueError("No function call was returned for further info analysis.")
    arguments = fc.get("arguments")
    further_info = json.loads(arguments)
    return further_info

# Schema for the output format checking
class InfoNeeded(BaseModel):
    keyword: str = Field(description="A keyword of information needed")
    guide: str = Field(description="Instructions on what to provide")
    auto_gen: str = Field(description="An example text that could give users a reference")

class FurtherInfoResponse(BaseModel):
    flag: bool = Field(description="Indicates whether further information is needed")
    info_needed: List[InfoNeeded] = Field(description="List of additional information requirements")

def get_further_info_fc_pydantic_schema(user_goal: str, user_plan: str) -> FurtherInfoResponse:
    # Define a function schema for further information analysis

    # system_prompt_old = (
    #                 "You are a meticulous planning consultant specializing helping users to create a comprehensive, actionable plan."
    #                 "Please reason step by step::"
    #                 "Step1: Check the information provided by the user(goal or idea and plan)."
    #                 "Step2: Analyze how specific their plan is, what additional information is needed.(Number of questions should be 1-8 depends on the specificity of the content user provided)"
    #                 "Step3: Generate a list of questions that are specific and actionable to gather precise details."
    #                 "Requirement for the questions:"
    #                 "- Questions are specific and actionable to gather precise details."
    #                 "- The questions adapt to different types of goals, ensuring relevance."
    #                 "- Critical for plan creation"
    #                 )

    system_prompt = (
        "You are a meticulous planning consultant whose expertise lies in helping users design comprehensive and actionable plans. "
        "Follow a clear, step-by-step reasoning process as outlined below:"
        "Initial Review:"
        "- Examine the user's provided information, including their goal, idea, or plan."
        "- Identify the key elements and the level of detail already provided."
        "Specificity Analysis:"
        "- Assess how specific the user's plan is."
        "- Determine what additional details are required to make the plan fully actionable."
        "- Decide on the number of follow-up questions needed (between 1 to 8) based on the current specificity."
        "Question Generation:"
        "- Create a targeted list of specific and actionable questions that gather the precise details necessary for plan creation."
        "- Ensure each question is directly relevant to the user's goal and adapts to different types of objectives."
        "- Focus on questions that are critical for finalizing the plan."
        "Your responses should clearly outline each step, ensuring the questions and insights you provide are precise, actionable, and tailored to the user's needs."
    )
    
    further_info_schema = {
        "name": "further_info_analyzer",
        "description": "Analyze the user's input comprehensively to determine what crucial information is needed for creating a detailed, personalized plan.",
        "parameters": FurtherInfoResponse.model_json_schema()
    }

    user_plan = user_plan if user_plan else "No plan provided."

    template = PromptTemplate(
        input_variables = ['goal_or_idea', 'plan'],
        template = ("The information provided by the user:"
                    "Goal or Idea: {goal_or_idea}"
                    "Plan: {plan}")
    )
    
    prompt = template.format(goal_or_idea=user_goal, plan=user_plan)

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"{prompt}")
    ]


    chat = ChatOpenAI(model_name="gpt-4o", temperature=1.0, openai_api_key=OPENAI_API_KEY)
    response = chat.invoke(
        messages,
        functions=[further_info_schema],
        function_call={"name": "further_info_analyzer"}
    )

    # Extract and validate the response
    fc = response.additional_kwargs.get("function_call")
    if not fc:
        raise ValueError("No function call was returned for further info analysis.")
    try:
        arguments = json.loads(fc.get("arguments", "{}"))
        validated_response = FurtherInfoResponse.model_validate(arguments)
        return validated_response
    except ValidationError as e:
        raise ValueError(f"Invalid response format from LLM: {str(e)}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in LLM response: {str(e)}")


# ---------- Step 3-2: Ask the User to Provide Further Details ----------
def get_user_further_details(info_needed: list) -> list:
    details = []
    for info in info_needed:
        # Prompt the user based on the guide provided in each info requirement
        user_input = input(f"Provide details for '{info['keyword']}' (Guide: {info['guide']}): ")
        details.append({"keyword": info["keyword"], "details": user_input})
    return details

# ---------- Step 4: Generate the Final Plan by Integrating Inputs ----------
def get_final_plan(user_goal: str, user_details: list) -> dict:
    # Construct the final prompt by combining the user’s original goal and further details.
    combined_details = "\n".join(
        [f"{detail['keyword']}: {detail['details']}" for detail in user_details]
    )
    final_prompt_text = f"User's original goal: {user_goal}\nAdditional details:\n{combined_details}\nGenerate a tailored plan."

    # Define the function schema for the final plan generation.
    final_plan_schema = {
        "name": "final_result_generator",
        "description": "Generate a tailored plan based on the user's goal and provided details.",
        "parameters": {
            "type": "object",
            "properties": {
                "plan": {"type": "string", "description": "The final tailored plan in markdown format."}
            },
            "required": ["plan"]
        }
    }

    messages = [
        SystemMessage(content="You are a helpful planner that creates tailored plans."),
        HumanMessage(content=final_prompt_text)
    ]

    chat = ChatOpenAI(model_name="gpt-4o", temperature=1.0)
    response = chat(
        messages,
        functions=[final_plan_schema],
        function_call={"name": "final_result_generator"}
    )

    fc = response.additional_kwargs.get("function_call")
    if not fc:
        raise ValueError("No function call was returned for final plan generation.")
    arguments = fc.get("arguments")
    final_plan = json.loads(arguments)
    return final_plan

# ---------- Step 5: Generate Time Series Data Based on the Final Plan ----------
def get_time_series_data(final_plan: dict) -> dict:
    # Extract the plan text from the final plan response.
    plan_text = final_plan.get("plan", "")
    prompt_text = f"Based on the following plan, generate a time series data in JSON format with dates and corresponding values:\n{plan_text}"

    # Define the function schema for time series data generation.
    time_series_schema = {
        "name": "time_series_generator",
        "description": "Generate time series data based on the provided plan.",
        "parameters": {
            "type": "object",
            "properties": {
                "time_series": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "date": {"type": "string", "description": "Date in YYYY-MM-DD format"},
                            "value": {"type": "number", "description": "A numeric value for that date"}
                        },
                        "required": ["date", "value"]
                    },
                    "description": "The list of time series data points."
                }
            },
            "required": ["time_series"]
        }
    }

    messages = [
        SystemMessage(content="You are a data generator that creates time series data."),
        HumanMessage(content=prompt_text)
    ]

    chat = ChatOpenAI(model_name="gpt-4o", temperature=1.0)
    response = chat(
        messages,
        functions=[time_series_schema],
        function_call={"name": "time_series_generator"}
    )

    fc = response.additional_kwargs.get("function_call")
    if not fc:
        raise ValueError("No function call was returned for time series data generation.")
    arguments = fc.get("arguments")
    time_series_data = json.loads(arguments)
    return time_series_data

# ---------- Main Workflow ----------
def main():
    # Step 1: Ask for the user's goal.
    user_goal = get_user_goal()

    # Step 2: Check if the user's input conflicts with policies.
    if not check_policy(user_goal):
        print("Your input conflicts with our policies. Please modify your goal.")
        return

    # Step 3: Use function calling to determine further information needed.
    try:
        further_info = get_further_info_fc(user_goal)
        print("Additional information required:", further_info)
    except Exception as e:
        print("Error during further information analysis:", e)
        return

    # Step 3-2: Ask the user to provide the required further details.
    user_details = get_user_further_details(further_info["info_needed"])

    # Step 4: Build and generate the final tailored plan.
    try:
        final_plan = get_final_plan(user_goal, user_details)
        print("Final Plan:", final_plan)
    except Exception as e:
        print("Error during final plan generation:", e)
        return

    # Step 5: Generate time series data based on the final plan.
    try:
        time_series_data = get_time_series_data(final_plan)
        print("Time Series Data:", time_series_data)
    except Exception as e:
        print("Error during time series data generation:", e)


# Test Code
if __name__ == "__main__":
    a = get_further_info_fc_pydantic_schema('Pass the exam.','Python programming final exam with 75% score.')
    print(a.flag)

