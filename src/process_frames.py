import cv2
import os
import base64
import mysql.connector
import time
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection
def get_db_connection():
    try:
        return mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
        )
    except mysql.connector.Error as err:
        print(f"❌ Database connection error: {err}")
        return None

# OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Function to encode image to base64
def encode_image(frame):
    _, buffer = cv2.imencode(".jpg", frame)
    return base64.b64encode(buffer).decode("utf-8")

# Function to analyze frame using OpenAI
def analyze_frame(frame):
    try:
        base64_image = encode_image(frame)

        response = client.chat.completions.create(
            model="gpt-4-vision-preview",  # Using GPT-4 Vision model
            messages=[
                {
                    "role": "system",
                    "content": "Analyze objects, people, actions, and text in the given image."
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Analyze this image and describe its contents."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }
            ],
            max_tokens=200
        )

        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ OpenAI API error: {e}")
        return "Analysis failed"

# Function to save analysis results to MySQL
def save_to_database(frame_time, analysis_result):
    db = get_db_connection()
    if db is None:
        return
    
    try:
        with db.cursor() as cursor:
            sql = "INSERT INTO image_analysis (frame_time, description) VALUES (%s, %s)"
            cursor.execute(sql, (frame_time, analysis_result))
            db.commit()
    except mysql.connector.Error as err:
        print(f"❌ Database insert error: {err}")
    finally:
        db.close()

# Open video file
video_path = "sample_videos/sample.mp4"
cap = cv2.VideoCapture(video_path)

if not cap.isOpened():
    print("❌ Error: Could not open video file!")
    exit()

fps = int(cap.get(cv2.CAP_PROP_FPS))
frame_interval = max(fps // 2, 1)  # Process 1 frame every half a second (adaptive)
frame_count = 0

while True:
    ret, frame = cap.read()
    if not ret:
        print("✅ End of video or read error.")
        break  # Stop if video ends

    # Process frame at set intervals
    if frame_count % frame_interval == 0:
        timestamp = time.strftime("%H-%M-%S", time.gmtime(cap.get(cv2.CAP_PROP_POS_MSEC) / 1000))
        print(f"🔍 Processing frame at {timestamp}...")

        # Send to OpenAI for analysis
        analysis_result = analyze_frame(frame)
        print(f"📊 Analysis Result: {analysis_result}")

        # Save to database
        save_to_database(timestamp, str(analysis_result))

    frame_count += 1

    # Display video
    cv2.imshow("Real-time Video Analysis", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
print("✅ Real-time video analysis completed!")
