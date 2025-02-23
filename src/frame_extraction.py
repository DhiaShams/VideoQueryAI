import cv2
import os
import time

# Define video source
video_path = "sample_videos/sample.mp4"  # Ensure sample.mp4 exists in this folder
cap = cv2.VideoCapture(video_path)

if not cap.isOpened():
    print("Error: Could not open video file!")
    exit()

# Create folder to store extracted frames
output_folder = "extracted_frames"
os.makedirs(output_folder, exist_ok=True)

# Get video FPS
fps = int(cap.get(cv2.CAP_PROP_FPS))
if fps == 0:
    print("Error: Could not retrieve FPS. Video might be corrupted.")
    cap.release()
    exit()

# Define frame extraction interval (every 1 second)
frame_rate = 1  # Extract 1 frame per second
frame_interval = fps * frame_rate
frame_count = 0

while True:
    ret, frame = cap.read()

    if not ret:
        print("End of video or read error.")
        break  # Stop if video ends

    if frame_count % frame_interval == 0:
        timestamp = time.strftime("%H-%M-%S", time.gmtime(cap.get(cv2.CAP_PROP_POS_MSEC) / 1000))
        frame_filename = f"{output_folder}/frame_{timestamp}.jpg"

        if frame is None:
            print(f"Skipping frame {frame_count}: Empty frame.")
            continue

        # Resize frame
        frame_resized = cv2.resize(frame, (640, 640))

        # Save frame
        success = cv2.imwrite(frame_filename, frame_resized)
        if success:
            print(f"✅ Saved: {frame_filename}")
        else:
            print(f"❌ Failed to save: {frame_filename}")

    frame_count += 1

# Release resources
cap.release()
cv2.destroyAllWindows()
print("Frame extraction completed!")
