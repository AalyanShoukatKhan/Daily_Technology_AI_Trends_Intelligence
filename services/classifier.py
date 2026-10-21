import re
CATEGORIES = ["Artificial Intelligence and Machine Learning","Cybersecurity","Software Development","Cloud Computing and DevOps","Data Science and Analytics","Hardware and Devices","General Technology"]
RULES = [
 ("Cybersecurity", r"cyber|security|vulnerab|ransomware|breach|malware|zero.day|exploit|phishing"),
 ("Artificial Intelligence and Machine Learning", r"artificial intelligence|\\bai\\b|machine learning|llm|neural network|openai|anthropic|gemini|hugging face"),
 ("Cloud Computing and DevOps", r"cloud|kubernetes|devops|aws|azure|gcp|serverless|container"),
 ("Software Development", r"developer|programming|github|software|javascript|python|framework|open source"),
 ("Data Science and Analytics", r"data science|analytics|database|sql|data lake|warehouse"),
 ("Hardware and Devices", r"chip|processor|gpu|hardware|smartphone|device|laptop|semiconductor"),
]
def classify(title, description="", hint="General Technology"):
    text = (title+" "+description).lower()
    for category, pattern in RULES:
        if re.search(pattern, text): return category
    return hint if hint in CATEGORIES else "General Technology"
def tags_for(title, description=""):
    text=(title+" "+description).lower()
    terms=["AI","cybersecurity","cloud","open-source","research","product launch","policy","vulnerability","developer tools"]
    return [x for x in terms if x.lower() in text][:5]
