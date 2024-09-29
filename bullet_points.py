import google.generativeai as genai

# Configure the Generative AI model
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

def generate_bullet_points(text, overall_keyword):
    query = "Give 3-7 bullet points about the following text that can be used in a slide deck. Remember to be as concise as possible while still getting the point across. Only 12 words per bullet point maximum. Make sure it is in context with " + overall_keyword + " Here's the text: " + text
    response = model.generate_content(query)
    bullet_point_list = extract_bullet_points(response.text)
    return bullet_point_list


def extract_bullet_points(text):
    # Split the text by lines and filter for bullet points
    lines = text.strip().split('\n')
    bullet_points = []
    
    for line in lines:
        line = line.strip()
        if line.startswith('*'):
            bullet_points.append(line[2:].strip())  # Remove the '* ' and leading whitespace
            
    return bullet_points

