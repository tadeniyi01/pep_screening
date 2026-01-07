# config/prompts.py

class Prompts:
    # ReasoningAgent
    PEP_REASON = """
Explain why {name} qualifies as a Politically Exposed Person.
Positions: {positions}
Risk Level: {level}
Respond concisely.
"""
    
    ADVERSE_MEDIA_REASON = """
Explain the adverse media risk for {name}.
Headline: {headline}
"""

    ADVERSE_CLASSIFICATION = """
Analyze the news article below for adverse media risk regarding the subject '{name}'.

STRICT RULES:
1. Is the subject DIRECTLY involved in a crime, scandal, or investigation? (Negative)
2. Is the subject performing official duties, e.g., ordering arrests, discussing a budget, or giving a speech? (Neutral)
3. Is the subject mentioned in passing or listed as an authority figure responding to a crisis? (Neutral)

Article:
Headline: {headline}
Snippet: {excerpt}

Respond with:
- sentiment: Negative (if actual adverse risk), Neutral (if official duty or news), Positive (if heroic/good)
- is_adverse_involvement: true/false
- reasoning: Short explanation.
"""

    # ReasonSummarizationAgent
    SUMMARIZE_DETERMINATION = """
You are a compliance analyst producing an explainable PEP determination.

STRICT OUTPUT FORMAT (MANDATORY):
- Return a JSON ARRAY of STRINGS
- Each string = exactly ONE reason
- NO numbering
- NO newlines
- NO markdown
- NO headings

CONTENT RULES:
- Distinguish confirmed vs excluded roles
- Use confidence values
- Conservative tone for exclusions
- Return strictly a list of reasons

DATA:
{payload}
"""

    # SocialProfileAgent
    SOCIAL_MEDIA_DISCOVERY = """
You are a compliance intelligence system.

Task:
Identify OFFICIAL or widely recognized social media accounts
belonging to the public political figure below.

Rules:
- Only include accounts clearly associated with the individual
- Accounts may be verified OR widely cited by major media
- If uncertain, return empty object (null/None)
- Do NOT fabricate usernames or URLs

Entity:
Name: {name}
Country: {country}
"""

    # Bio Helper
    GENDER_INFERENCE = "Determine the gender of '{name}'. If unknown, set value to 'Unknown'."
    
    AGE_INFERENCE = "Calculate age from DOB {dob}." # Unused currently as logical calc is better
    
    LIFE_STATUS_INFERENCE = "Is '{name}' alive or deceased? If deceased, restrict 'status' to 'Deceased', else 'Alive' or 'Unknown'."
    
    ALIASES_INFERENCE = "List known aliases for '{name}'."
    
    DOB_INFERENCE = "Provide the date of birth of '{name}'."
    
    EDUCATION_INFERENCE = "Provide notable education background for '{name}'."
    
    RELATIVES_INFERENCE = "List close relatives of '{name}'."
    
    ASSOCIATES_INFERENCE = "List known associates of '{name}'."
    
    STATE_INFERENCE = "Which state or region does '{name}' belong to?"
    
    ACHIEVEMENTS_INFERENCE = "List widely recognized public achievements of {name}."
