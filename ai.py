from openai import OpenAI
import json
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def analyze_resume(resume_text, user_goal):
    prompt = f"""
    you are a senior software enginner and hiring manager. 
    
    Eveluate the resume based on the users goal.
user goal: {user_goal}

STRICT RULES:
- Extract only relevant skills for this goal
- Remove Irrelevant tools [excel for backend, etc]
- Identify real gaps
- Generate roadmap only for missing fields, not for existing skills
- Make output DIFFERENT based on goal

Return only JSON:
{{
"skills": ["list of relevant skills"],
missing_skills: ["list of missing skills"],
roadmap: ["list of steps to acquire missing skills"],
interview_questions: ["list of potential interview questions based on the resume and goal"]
}}

Resume:
{resume_text}

    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.3,
            messages=[
                {
                    "role": "system",
                    "content": "You are a Strict Hiring Manager.",
                },
                {"role": "user", "content": prompt},
            ],
        )
        content = response.choices[0].message.content.strip()
        start = content.find("{")
        end = content.rfind("}") + 1
        return json.loads(content[start:end])
    except Exception as e:
        return {
            "skills": [],
            "missing_skills": [],
            "roadmap": [],
            "interview_questions": [],
            "error": f"Failed to analyze resume. {str(e)}",
        }
