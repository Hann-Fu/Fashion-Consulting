handler_beta_v0 =  {
    "name": "prompt_handler",
    "description": (
        "Analyze the customer's prompt and identify the types of clothing parts (tops, pants, outerwear, dress_skirt). "
        "Return a concise summary according to the prompt for each clothing part, without using phrases like 'is requested' or 'are needed.' "
        "This summary should focus solely on the features to facilitate similar item retrieval."
    ),
    "parameters" : {
        "type": "object",
        "properties": {
            "polite_reply" : {
                "type": "string",
                "description": "Act like a consulting chatbot, greeting to user."
            },
            "analysis" : {
                "type": "array",
                "items" : {
                    "type" : "object",
                    "properties" :{
                        "part" : {"type" : "string", 
                                  "enum" : ["tops", "pants", "outerwear", "dress_skirt"],
                                  "description" : "Identifier of the clothing part."},
                        "summary" : {"type" : "string",
                                     "description" : "Concise feature description of the clothing part."}
                    }

                },
                "description": "Analyze the customer's request, identify the part of clothing the customer wants, give the list of the part and corresponding summary."
            },
        },
        "description": "Response contain polite reply and analysis of the customer's request."

        },

    "required": ["polite_reply", "analysis"],
    }


handler_beta_v1 = {
    "name": "prompt_handler",
    "description": (
        "Context: A dedicated fashion consulting system. "
        "Input : The customer's prompt describing desired outfit. "
        "Output: Greeting first(mandatory), then clothing parts the customer wants, along with feature descriptions. "
        "Usage: This summary should focus solely on the features to facilitate item retrieval. "
        "Workflow: "
        "Step0(Initiation): Greet the user(Mandatory, what ever the input is.). "
        "Step1(Analysis): Analyze the customer's prompt. "
        "Step2(Classify): Identify the types of clothing parts the customer wants. "
        "Step3(Reasoning): Figure out the color, material, sleeve length, neckline, style, fit, occasion, seasonality, patterns or prints, and unique design details."
        "Step4(Conclusion): Finally speculate and give a concise summary for each clothing part according to the analysis result."
        "In Addition, if the customer's prompt is irrelevant, randomly give feedback."
    ),
    "parameters" : {
        "type": "object",
        "properties": {
            "polite_reply" : {
                "type": "string",
                "description": "Act like a consulting chatbot, greeting to user. "
            },
            "analysis" : {
                "type": "array",
                "items" : {
                    "type" : "object",
                    "properties" :{
                        "part" : {"type" : "string", 
                                  "enum" : ["tops", "pants", "outerwear", "dress_skirt"],
                                  "description" : "Identifier of desired clothing parts(one or more)."},
                        "summary" : {"type" : "string",
                                     "description" : "Concise feature description of the clothing part."}
                    }

                },
                "description": "Analyze the customer's request, identify the part of clothing the customer wants, give the list of the part and corresponding summary."
            },
        },
        "description": "Response MUST contain polite reply and analysis of the customer's request."

        },

    "required": ["polite_reply", "analysis"],
    }

'''
Prompt generator act like a user, it will generate 10 prompts in different aspects, 
like color, style, material, style, fit, occasion, seasonality, pattern, unique design, and part they desired(implicitly).
output: 10 prompts in different aspects in a list.
'''



