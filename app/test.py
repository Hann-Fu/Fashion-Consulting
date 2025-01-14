from src.services.consulting_service import consulting_main

prompt = "I need a black sweater, blue outdoor jacket with North Face print, and wind-prevention pants."
additional_info = {'gender': '1', 'season': ['spring','summer']}
print(consulting_main(prompt, additional_info))