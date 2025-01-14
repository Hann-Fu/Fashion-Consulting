# Evaluate the fashion consulting system's recommendation is aligned with the customer's request or not.
evaluator_beta_v0 = {
    "name": "evaluator",
    "description": (
        "Context: A dedicated fashion consulting system. "
        "Input : The customer's request and the system's recommendation(part and corresponded images). "
        "Output: The evaluation score of the system's recommendation on diverse aspects(only evaluate the attributes protentially mentioned in prompt). "
        "Usage:  Evaluation score to give feedback to facilitate item retrieval. "

    ),
    "parameters" : {
        "type": "object",
        "properties": {
            "part_score" : {
                "type": "float",
                "description": "Is the part of clothing the customer wants included in the recommendation.  "
            },
            "color_score" : {
                "type": "float",
                "description": "Is the color of the clothing of recommendations aligned with the customer's request."
            },
            "occasion_score" : {
                "type": "float",
                "description": "Is the occasion of the clothing of recommendations fit the customer's request."
            },
            "style_score" : {
                "type": "float",
                "description": "Is the style of the clothing of recommendations fit the customer's request."
            },
            "seasonality_score" : {
                "type": "float",
                "description": "Is the seasonality of the clothing of recommendations fit the customer's request."
            },
            "unique_design_score" : {
                "type": "float",
                "description": "Is the unique design of the clothing of recommendations fit the customer's request."
            },
            "pattern_score" : {
                "type": "float",
                "description": "Is the pattern of the clothing of recommendations fit the customer's request."
            },
            "material_score" : {
                "type": "float",
                "description": "How well the recommended item’s fabric matches user’s preference (e.g., cotton, linen, leather)."
            },
            "fit_score" : {
                "type": "float",
                "description": "Is the fit of the clothing of recommendations fit the customer's request."
            },
            "overall_compatibility_score": {
                "type": "float",
                "description" : "An average or weighted sum of all relevant scores for a quick read."}
            
        },
        "description": "Only if the corresponded attribute mentioned in the prompt. For each attribute, give a score from 1.0-10.0."

        },

    "required": [],
    }