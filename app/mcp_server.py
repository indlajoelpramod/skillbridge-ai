import os
import sys
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP Server
mcp = FastMCP("SkillBridge MCP Server")

@mcp.tool()
def search_courses_and_certifications(role: str, level: str = "Beginner") -> str:
    """Searches for recommended online courses and professional certifications for a target career role.
    
    Args:
        role: The target career role (e.g., 'Software Developer', 'AI Engineer', 'Data Analyst', 'Cybersecurity Specialist').
        level: The learning stage (e.g., 'Beginner', 'Intermediate', 'Advanced').
    """
    role_lower = role.lower()
    level_lower = level.lower()
    
    courses = {
        "software developer": {
            "beginner": [
                "Python for Everybody Specialization (Coursera - University of Michigan)",
                "CS50: Introduction to Computer Science (Harvard edX)",
                "Programming Foundations with JavaScript, HTML and CSS (Coursera - Duke University)"
            ],
            "intermediate": [
                "Object-Oriented Data Structures in C++ (Coursera - University of Illinois)",
                "Java Programming and Software Engineering Fundamentals (Coursera - Duke)",
                "Spring Framework Dev (Udemy)"
            ],
            "advanced": [
                "Software Design and Architecture Specialization (Coursera - University of Alberta)",
                "Microservices with Spring Boot and Spring Cloud (Udemy)",
                "AWS Certified Developer - Associate (Certification Prep)"
            ]
        },
        "ai engineer": {
            "beginner": [
                "AI for Everyone (Coursera - DeepLearning.AI)",
                "Supervised Machine Learning: Regression and Classification (Coursera - Andrew Ng)",
                "Mathematics for Machine Learning Specialization (Coursera - Imperial College London)"
            ],
            "intermediate": [
                "Deep Learning Specialization (Coursera - Andrew Ng)",
                "TensorFlow Developer Professional Certificate (Coursera - DeepLearning.AI)",
                "Machine Learning with PyTorch (Udemy)"
            ],
            "advanced": [
                "Generative AI with Large Language Models (Coursera - DeepLearning.AI)",
                "Natural Language Processing Specialization (Coursera - DeepLearning.AI)",
                "Google Cloud Professional Machine Learning Engineer (Certification Prep)"
            ]
        },
        "data analyst": {
            "beginner": [
                "Google Data Analytics Professional Certificate (Coursera)",
                "Excel Skills for Business Specialization (Coursera - Macquarie University)",
                "Introduction to Structured Query Language (SQL) (Coursera - University of Michigan)"
            ],
            "intermediate": [
                "Data Analysis with Python (freeCodeCamp)",
                "Tableau Desktop Specialist (Certification Prep)",
                "Data Science Methodology (Coursera - IBM)"
            ],
            "advanced": [
                "Google Advanced Data Analytics Professional Certificate (Coursera)",
                "Data Analysis and Presentation Skills: the PwC Approach (Coursera)",
                "Microsoft Certified: Power BI Data Analyst Associate (PL-300)"
            ]
        },
        "cybersecurity specialist": {
            "beginner": [
                "Google Cybersecurity Professional Certificate (Coursera)",
                "CompTIA Security+ (Certification Prep)",
                "Introduction to IT & Cybersecurity (Cybrary)"
            ],
            "intermediate": [
                "Certified Information Systems Security Professional (CISSP) prep courses",
                "Practical Ethical Hacking (TCM Security)",
                "CompTIA Network+ (Certification Prep)"
            ],
            "advanced": [
                "Certified Ethical Hacker (CEH) (Certification Prep)",
                "Offensive Security Certified Professional (OSCP) Prep",
                "Advanced Penetration Testing Specialization (Coursera)"
            ]
        }
    }
    
    # Fallback default matching
    matched_role = "software developer"
    for known_role in courses:
        if known_role in role_lower:
            matched_role = known_role
            break
            
    matched_level = "beginner"
    if "inter" in level_lower:
        matched_level = "intermediate"
    elif "adv" in level_lower:
        matched_level = "advanced"
        
    recommended = courses[matched_role][matched_level]
    
    result = f"### Recommended Courses & Certifications for {role} ({matched_level.capitalize()}):\n"
    for i, c in enumerate(recommended, 1):
        result += f"{i}. {c}\n"
    return result

@mcp.tool()
def get_skill_requirements(role: str) -> str:
    """Retrieves the core technical and soft skills required for a given career role.
    
    Args:
        role: The target career role (e.g. 'Software Developer', 'AI Engineer', 'Data Analyst', 'Cybersecurity Specialist').
    """
    role_lower = role.lower()
    
    skills = {
        "software developer": {
            "hard": ["Python", "Java", "C++ or C#", "Git", "SQL & Databases", "Data Structures & Algorithms", "HTML/CSS/JS"],
            "soft": ["Problem Solving", "Teamwork", "Agile Methodologies", "Debugging/Critique Resiliency"]
        },
        "ai engineer": {
            "hard": ["Python", "PyTorch/TensorFlow", "scikit-learn", "Probability & Statistics", "Linear Algebra", "NLP/LLMs", "Vector Databases"],
            "soft": ["Research Mindset", "Ethics in AI", "Technical Communication", "Logical Reasoning"]
        },
        "data analyst": {
            "hard": ["SQL", "Microsoft Excel", "Python or R", "Tableau/Power BI", "Statistics & Probability", "Data Cleaning", "Data Visualization"],
            "soft": ["Business Acumen", "Presentation Skills", "Attention to Detail", "Storytelling with Data"]
        },
        "cybersecurity specialist": {
            "hard": ["Network Security Protocols", "Linux/Bash", "SIEM Tools (Splunk)", "Cryptography basics", "Ethical Hacking", "Python/Go scripting"],
            "soft": ["Risk Assessment", "Critical Thinking", "Stress Management", "Incident Response Communication"]
        }
    }
    
    matched_role = "software developer"
    for known_role in skills:
        if known_role in role_lower:
            matched_role = known_role
            break
            
    role_skills = skills[matched_role]
    
    result = f"### Required Skills for {role}:\n"
    result += "**Technical Skills:**\n"
    for s in role_skills["hard"]:
        result += f"- {s}\n"
    result += "\n**Soft Skills:**\n"
    for s in role_skills["soft"]:
        result += f"- {s}\n"
        
    return result

@mcp.tool()
def get_job_market_insights(role: str, location: str = "Global") -> str:
    """Provides simulated job market insights, demand trends, and salary ranges for a career role.
    
    Args:
        role: The career role to analyze.
        location: Optional location (e.g. 'US', 'India', 'Global').
    """
    role_lower = role.lower()
    
    insights = {
        "software developer": {
            "demand": "Very High (8/10)",
            "salary": "$80,000 - $130,000 (US), ₹6,00,000 - ₹15,00,000 (India)",
            "trends": "Increased shift towards full-stack capability and cloud-native application development."
        },
        "ai engineer": {
            "demand": "Exponentially High (10/10)",
            "salary": "$110,000 - $180,000 (US), ₹10,00,000 - ₹25,00,000 (India)",
            "trends": "Huge surge in demand for engineering generative AI pipelines, LLM fine-tuning, and agent orchestration."
        },
        "data analyst": {
            "demand": "High (7/10)",
            "salary": "$65,000 - $95,000 (US), ₹4,50,000 - ₹10,00,000 (India)",
            "trends": "Strong migration towards analytics dashboard automation and predictive modeling using simple Python scripts."
        },
        "cybersecurity specialist": {
            "demand": "Extremely High (9/10)",
            "salary": "$90,000 - $145,000 (US), ₹7,00,000 - ₹18,00,000 (India)",
            "trends": "Greater focus on cloud security, zero-trust architectures, and DevSecOps integrations."
        }
    }
    
    matched_role = "software developer"
    for known_role in insights:
        if known_role in role_lower:
            matched_role = known_role
            break
            
    info = insights[matched_role]
    
    return f"""### Job Market Insights for {role} ({location}):
- **Current Demand:** {info['demand']}
- **Average Salary Range:** {info['salary']}
- **Industry Trend:** {info['trends']}
"""

@mcp.tool()
def generate_practice_exercise(topic: str, difficulty: str = "Medium") -> str:
    """Generates a technical interview question or practice challenge for a given study topic.
    
    Args:
        topic: The study topic (e.g. 'Python list comprehension', 'SQL Joins', 'Neural Networks').
        difficulty: The difficulty level ('Easy', 'Medium', 'Hard').
    """
    return f"""### Practice Exercise ({difficulty} - Topic: {topic}):
**Question:**
Design a solution / write code to solve the following:
Explain or implement the core mechanism of "{topic}".

**Example Test Scenario:**
Input: Standard input scenario for {topic}
Expected Output: Correct, optimized resolution.

**Mentor Tips:**
- Focus on edge cases.
- Analyze the time and space complexity of your approach.
"""

if __name__ == "__main__":
    # Standard FastMCP stdio entrypoint
    mcp.run()
