from enum import Enum
import json
import os
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.chains import OpenAIModerationChain
from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError
from typing import List, Union


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
# ---------- Openai Styled Function Calling ----------
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


# ---------- Function Calling with Pydantic Schema ----------
# Schema for the output format checking
class InfoNeeded(BaseModel):
    keyword: str = Field(description="A keyword of information needed")
    guide: str = Field(description="Instructions on what to provide")
    auto_gen: str = Field(description="An example text that could give users a reference")

class FurtherInfoResponse(BaseModel):
    flag: bool = Field(description="Indicates whether further information is needed")
    info_needed: List[InfoNeeded] = Field(description="List of additional information requirements")

further_info_schema = {
    "name": "further_info_analyzer",
    "description": "Analyze the user's input comprehensively to determine what crucial information is needed for creating a detailed, personalized plan.",
    "parameters": FurtherInfoResponse.model_json_schema()
}

def get_further_info_fc_pydantic_schema(user_goal: str, user_plan: str) -> FurtherInfoResponse:
    # Define a function schema for further information analysis

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
    
    user_prompt = (
        "The information provided by the user:"
        f"Goal or Idea: {user_goal}"
        f"Plan: {user_plan or 'No plan provided.'}"
    )

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]

    model = ChatOpenAI(model_name="gpt-4o", temperature=1.0, openai_api_key=OPENAI_API_KEY)

    response = model.invoke(
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

# ---------- Structured Output with JSON Schema ----------

def get_further_info_structured_output(user_goal: str, user_plan: str) -> dict:

    json_schema  = {
        "name": "further_info_analyzer",
        "description": "Analyze the user's input comprehensively to determine what crucial information is needed for creating a detailed, personalized plan.",
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
    
    user_prompt = (
        "The information provided by the user:"
        f"Goal or Idea: {user_goal}"
        f"Plan: {user_plan or 'No plan provided.'}"
    )

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]


    llm = ChatOpenAI(model_name="gpt-4o", temperature=1.0, openai_api_key=OPENAI_API_KEY)
    structured_llm = llm.with_structured_output(json_schema)
    response = structured_llm.invoke(messages)

    return response["info_needed"]

# ---------- Step 3-2: Ask the User to Provide Further Details ----------
def get_user_further_details(info_needed: list) -> list:

    details = []
    for info in info_needed:
        # Prompt the user based on the guide provided in each info requirement
        user_input = input(f"Provide details for '{info.keyword}' (Guide: {info.guide}): ")
        details.append({"keyword": {info.keyword}, "details": user_input})
    return details

# ---------- Step 4: Generate the Final Plan by Integrating Inputs ----------
def get_final_plan(user_goal: str, user_details: list) -> str:
    # Construct the final prompt by combining the user’s original goal and further details.
    combined_details = "\n".join(
        [f"{detail['keyword']}: {detail['details']}" for detail in user_details]
    )

    prompt_text = ("According to the following information, generate a tailored plan."
                    f"User's original goal: {user_goal}"
                    f"Additional details:{combined_details}")

    messages = [
        SystemMessage(content="You are a helpful planner that creates a comprehensive, detailed plan in markdown format for user by provided information."),
        HumanMessage(content=prompt_text)
    ]

    model = ChatOpenAI(model_name="gpt-4o", temperature=1.0)
    response = model.invoke(
        messages,
        top_p=0.95,
        temperature=1.02,
    )
    final_plan = response.content

    return final_plan

# ---------- Step 5: Generate Time Series Data Based on the Final Plan ----------
@DeprecationWarning
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

# ---------------------------------------------------------------

class Ymd(BaseModel):
    date: str = Field(
        description="The date of the task in YYYY-MM-DD format"
    )

class SpecificType(BaseModel):
    specific: list[Ymd] = Field(description="Specify dates for this task")


class OnWorkdayType(BaseModel):
    on_workday: list[int] = Field(
        description=(
            "List of integers representing the weekdays the task should be performed on. "
            "Use 1 for Monday, 2 for Tuesday, ..., up to 5 for Friday. "
            "For example, [1, 2, 3] for Monday to Wednesday, or [3, 5] for Wednesday and Friday."
        )
    )


class OnWeekendType(BaseModel):
    on_weekend: list[int] = Field(
        description=(
            "List of integers representing the weekends the task should be performed on. "
            "Use 1 for Saturday, 2 for Sunday, or [1, 2] for both."
        )
    )


class OnWeekdayType(BaseModel):
    on_weekday: list[int] = Field(
        description=(
            "List of integers representing the weekdays the task should be performed on. "
            "Use 1 for Monday, 2 for Tuesday, ..., up to 5 for Friday. "
            "For example, [1, 2, 3] for Monday to Wednesday, or [3, 7] for Wednesday and Sunday."
        )
    )   


class OnMonthdayType(BaseModel):
    on_monthday: list[int] = Field(
        description=(
            "List of integers representing the monthdays the task should be performed on. "
            "Use 1 for the first day of the month, 2 for the second day, ..., up to 28/29/30/31 for the last day of the month(depends on the month). "
            "For example, [1, 2, 3] for the first three days of the month, or [3, 5] for the third and fifth days of the month."
        )
    )


class PeriodicType(BaseModel): 
    periodic: int = Field(description="Specify the period of the task in days")


class RepeatType(str, Enum):
    SPECIFIC = "Specific"
    EVERYDAY = "Everyday"
    ON_WORKDAY = "On workday"
    ON_WEEKEND = "On Weekend"
    ON_WEEKDAY = "On weekday"
    ON_MONTHDAY = "On monthday"
    PERIODIC = "Periodic"

class Quantization(BaseModel):
    progress_start: int = Field(description="The start progress of the task")
    goal: int = Field(description="The goal of the task")

class AcrossTimeAttribute(BaseModel):
    start_date: str = Field(description="The start date of the task in YYYY-MM-DD format")
    end_date: str = Field(description="The end date of the task in YYYY-MM-DD format")
    repeat: RepeatType = Field(description="The repeat type of the task")
    schedule: Union[SpecificType, OnWorkdayType, OnWeekendType, OnWeekdayType, OnMonthdayType, PeriodicType] = Field(description="The schedule of the task")


class SingleTimeAttribute(BaseModel):
    date: str = Field(description="The date of the task in YYYY-MM-DD format")


class TimeSeriesTask(BaseModel):
    task_name: str = Field(description="The name of the task")
    description: str = Field(description="The description of the task")
    task_duration: Union[SingleTimeAttribute, AcrossTimeAttribute] = Field(description="The duration type of the task")
    time_in_day: str = Field(description="The time of the day the task should be performed in HH:MM format")
    quantization: Union[Quantization, None] = Field(description="The quantization of the task")
    notes: str = Field(description="Give some notes of the task")

class Tasks(BaseModel):
    tasks_name: list[str] = Field(description="The name of the tasks")
    tasks: list[TimeSeriesTask] = Field(description="The list of tasks")

def get_time_series_data_tool_call(final_plan: dict) -> dict:

    system_prompt = (
        #"You are a helpful assistant that analyzes the final plan and generates the time series tasks list(due to the plan's content, generate 3-12 tasks)."
        "You are a helpful assistant that analyzes the final plan and generates the time series tasks list."
        "Step1: Analyze the final plan that how many tasks it needs to be done, then put the task names into the tasks_name list."
        "Step2: For each task, generate the details of the task, including the description, duration, time of the day, quantization, and notes."
        "*Make sure the tasks are independent and not overlapping with each other and cover all the plan's content."
        "*The tasks should be in the order of the plan's content."
    )    
    user_prompt = (
        "The final plan:"
        f"{final_plan}"
    )
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]
    model = ChatOpenAI(model_name="gpt-4o", temperature=1.0)
    model = model.with_structured_output(Tasks)
    response = model.invoke(messages)
    return response.tasks

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
    # goal = 'Pass the exam.'
    # plan = 'Python programming final exam with 75% score.'
    # step1 = get_further_info_fc_pydantic_schema(goal,plan)
    # info_needed = step1.info_needed
    # info_needed_list = get_user_further_details(info_needed)
    # final_plan = get_final_plan(goal,info_needed_list)
    # print(final_plan)
    # print("--------------------------------")
    # time_series_plan = get_time_series_data_tool_call(final_plan)
    # print(time_series_plan)
    final_plan = {
        "plan": """

---

## Week 1-2: Foundation & Diagnostic Test
### Tasks:
- ✅ Take a **full-length TOEFL diagnostic test** (official ETS sample)
- ✅ Identify strengths and weaknesses
- ✅ Familiarize yourself with the **TOEFL format & scoring system**
- ✅ Gather high-quality resources:
  - **Reading:** TOEFL practice books (Official Guide, Cambridge, Barron’s)
  - **Listening:** TED Talks, NPR, BBC, TOEFL Listening practice
  - **Speaking:** TOEFL Speaking templates, practice prompts
  - **Writing:** Sample essays, TOEFL integrated & independent writing strategies

### Focus Areas:
📖 **Reading**: Practice **skimming & scanning techniques**  
🎧 **Listening**: Improve **note-taking** while listening  
🗣 **Speaking**: Learn TOEFL **speaking templates**  
✍ **Writing**: Learn **essay structures & thesis development**  

---

## Week 3-4: Deep Practice for Each Section
### Tasks:
- ✅ **Reading:** Practice 3-5 passages daily, summarize main ideas
- ✅ **Listening:** Listen to 3 recordings daily, take notes, summarize
- ✅ **Speaking:** Answer 3 speaking prompts daily, record responses
- ✅ **Writing:** Write 2 essays per week (1 integrated, 1 independent)

### Focus Areas:
📖 **Reading**: Focus on **inference questions & vocabulary**  
🎧 **Listening**: Identify **speaker’s tone & purpose**  
🗣 **Speaking**: Improve **fluency & pronunciation**  
✍ **Writing**: Work on **coherence & strong arguments**  

---

## Week 5-6: Advanced Strategies & Timed Practice
### Tasks:
- ✅ **Reading:** Timed practice tests, analyze mistakes
- ✅ **Listening:** Listen without transcripts, write summaries
- ✅ **Speaking:** Improve **pronunciation, intonation, and stress**
- ✅ **Writing:** Use **advanced linking words & varied sentence structures**

### Focus Areas:
📖 **Reading**: Recognizing **author’s purpose & tone**  
🎧 **Listening**: Master **paraphrasing spoken information**  
🗣 **Speaking**: Speak **naturally without hesitating**  
✍ **Writing**: Avoid **common grammar mistakes & repetition**  

---

## Week 7-8: Full-Length Tests & Targeted Improvement
### Tasks:
- ✅ Take **one full-length TOEFL test per week**
- ✅ Identify weak sections and adjust study focus
- ✅ **Reading:** Focus on **speed and accuracy**
- ✅ **Listening:** Train with **academic lectures & discussions**
- ✅ **Speaking:** Get feedback from **native speakers or tutors**
- ✅ **Writing:** Improve clarity and **persuasive arguments**

---

## Week 9-10: Intense Practice & Score Optimization
### Tasks:
- ✅ Simulate **real TOEFL test conditions** (strict timing)
- ✅ Use **AI tools (ChatGPT), Grammarly, and tutors** for feedback
- ✅ **Reading:** Master difficult texts & complex question types
- ✅ **Listening:** Improve ability to catch **small details**
- ✅ **Speaking:** Reduce **hesitation and unnatural pauses**
- ✅ **Writing:** Perfect **introduction and conclusion writing**

---

## Week 11-12: Final Practice & Test Readiness
### Tasks:
- ✅ Take **2 full-length TOEFL tests** under timed conditions
- ✅ Revise all **common TOEFL mistakes**
- ✅ Practice stress management techniques
- ✅ Get enough sleep before the exam

---



"""
    }
    time_series_plan = get_time_series_data_tool_call(final_plan)
    print(time_series_plan)

