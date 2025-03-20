from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles  # For serving static files
import mysql.connector
import os
import logging
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OpenAI API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# Initialize FastAPI
app = FastAPI()

# Serve static files (including favicon.ico)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Database connection
try:
    db = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )
    logger.info("✅ Database connected successfully!")
except mysql.connector.Error as e:
    logger.error(f"❌ Database connection failed: {e}")
    db = None

def get_video_context():
    """Fetch all frame descriptions from the database."""
    if not db:
        return None

    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT frame_time, description FROM image_analysis ORDER BY frame_time ASC")
        frames = cursor.fetchall()
        if not frames:
            return None

        # Combine descriptions into a single string
        context = "\n".join([f"At {frame['frame_time']} sec: {frame['description']}" for frame in frames])
        return context
    except mysql.connector.Error as e:
        logger.error(f"❌ Database error while fetching frames: {e}")
        return None
    finally:
        cursor.close()

def ask_openai(question, context):
    """Send the question and video context to OpenAI."""
    if not client:
        return "⚠️ OpenAI API key is missing!"

    try:
        response = client.chat.completions.create(  # ✅ Correct API call
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant that analyzes video frames."},
                {"role": "user", "content": f"Video context:\n{context}\n\nQuestion: {question}"}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"❌ OpenAI API error: {e}")
        return "⚠️ Failed to get a response from OpenAI."

@app.get("/")
def home():
    return {"message": "Welcome to VideoQueryAI!"}

@app.get("/favicon.ico")
async def favicon():
    return FileResponse("static/favicon.ico")

@app.get("/ask/")
def ask(question: str = Query(..., description="Ask a question about the video")):
    """Answer questions based on video frames using OpenAI."""
    logger.info(f"🔍 User question: {question}")

    # Get video context from the database
    context = get_video_context()
    if not context:
        return JSONResponse(content={"answer": "⚠️ No video data available."}, status_code=500)

    # Ask OpenAI
    answer = ask_openai(question, context)
    return {"answer": answer}
@app.get("/search/")
def search(query: str = Query(..., description="Search for a keyword in the video frames")):
    """Checks if the object is found in the video frames and returns a meaningful response."""
    logger.info(f"🔍 Searching for: {query}")

    if not db:
        return JSONResponse(content={"error": "⚠️ Database connection error."}, status_code=500)

    cursor = db.cursor()
    try:
        # Search for the query in the description field
        search_query = f"%{query}%"  # Allows partial matches
        cursor.execute("SELECT COUNT(*) FROM image_analysis WHERE description LIKE %s", (search_query,))
        result = cursor.fetchone()

        if result and result[0] > 0:
            return {"message": f"✅ {query.capitalize()} is found in the video."}
        else:
            return {"message": f"❌ {query.capitalize()} is not found in the video."}

    except mysql.connector.Error as e:
        logger.error(f"❌ Database error while searching: {e}")
        return JSONResponse(content={"error": "⚠️ Error while searching."}, status_code=500)
    finally:
        cursor.close()
