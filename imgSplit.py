import os
import subprocess

# Provide your video file name (Ensure it's in the same folder as the script)
video_path = "video.mp4"  # Change this to your actual video file

# Check if the video file exists
if not os.path.exists(video_path):
    print(f"❌ Error: The file '{video_path}' was not found.")
    exit()

# Create output folder for snapshots
output_folder = "snapshots"
os.makedirs(output_folder, exist_ok=True)

try:
    # Get video duration using ffprobe
    duration_command = f'ffprobe -i "{video_path}" -show_entries format=duration -v quiet -of csv="p=0"'
    duration = int(float(subprocess.check_output(duration_command, shell=True).decode().strip()))

    # Extract 1 frame per second using FFmpeg
    for i in range(duration):
        output_file = os.path.join(output_folder, f"snapshot_{i+1:04d}.jpg")  # Format: snapshot_0001.jpg
        snapshot_command = f'ffmpeg -i "{video_path}" -vf "select=eq(n\,{i*30})" -vsync vfr "{output_file}" -y'
        subprocess.run(snapshot_command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    print(f"✅ Extracted {duration} snapshots (1 per second). Check the 'snapshots' folder.")

except subprocess.CalledProcessError:
    print("❌ Error: FFmpeg or ffprobe is not installed or not found in the system PATH.")
    print("➡️ Please install FFmpeg and add it to the PATH.")
