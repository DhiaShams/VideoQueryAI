import os
import cv2
import base64
import mysql.connector
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
db = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME")
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

cursor = db.cursor()

def encode_image(image_path):
    """Convert image to base64 encoding."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def analyze_frame(image_path):
    """Send image to OpenAI API and get response."""
    base64_image = encode_image(image_path)

    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "You are an AI that analyzes images and describes them."},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Describe the contents of this image."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }
        ],
        max_tokens=200
    )

    return response.choices[0].message.content

def save_to_database(frame_name, analysis_result):
    """Store image analysis in MySQL database."""
    sql = "INSERT INTO image_analysis (frame_name, description) VALUES (%s, %s)"
    values = (frame_name, analysis_result)
    cursor.execute(sql, values)
    db.commit()

frame_folder = os.path.abspath("../extracted_frames")  # Moves one level up from src

# Process each frame
for frame in os.listdir(frame_folder):
    frame_path = os.path.join(frame_folder, frame)
    if frame.endswith(".jpg") or frame.endswith(".png"):
        result = analyze_frame(frame_path)
        save_to_database(frame, str(result))
        print(f"Processed {frame} and saved result.")

# Close database connection
cursor.close()
db.close()