from flask import Flask, request, send_file, render_template
from gtts import gTTS
from moviepy.editor import ImageSequenceClip, AudioFileClip, concatenate_videoclips
from PIL import Image
import os

app = Flask(__name__)

# Ensure the uploads folder exists
os.makedirs('uploads', exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_audio', methods=['POST'])
def generate_audio():
    data = request.get_json()
    text = data.get('text', '')

    if not text:
        return "Text is required", 400

    # Generate speech
    tts = gTTS(text=text, lang='hi', slow=False)
    tts.save("output.mp3")

    # Return the audio file
    return send_file("output.mp3", mimetype='audio/mp3', as_attachment=True)

@app.route('/generate_video', methods=['POST'])
def generate_video():
    return create_video(False)

@app.route('/generate_complete_video', methods=['POST'])
def generate_complete_video():
    print("generate_complete_video endpoint hit")  # Debugging line
    return create_video(True)

def create_video(include_audio):
    # Get the images from the request
    images = request.files.getlist('images')

    if not images:
        return "No images uploaded", 400

    # Save and resize images temporarily
    image_paths = []
    target_size = (640, 480)  # Set your target size here

    for img in images:
        # Save the uploaded image
        image_path = os.path.join('uploads', img.filename)
        img.save(image_path)

        # Resize the image
        with Image.open(image_path) as image:
            resized_image = image.resize(target_size)
            resized_image_path = os.path.join('uploads', f"resized_{img.filename}")
            resized_image.save(resized_image_path)
            image_paths.append(resized_image_path)

    # Generate video from images with each image shown for a specified duration
    duration_per_image = 5  # Duration for each image in seconds
    clips = [ImageSequenceClip([img_path], fps=1/duration_per_image).set_duration(duration_per_image) for img_path in image_paths]
    
    # Concatenate all the clips into one video
    video = concatenate_videoclips(clips, method='compose')

    if include_audio:
        # Load the audio file
        audio_path = 'output.mp3'  # Use the saved audio file from generate_audio
        audio_clip = AudioFileClip(audio_path)

        # Repeat the video sequence to match the duration of the audio
        video_duration = video.duration
        audio_duration = audio_clip.duration

        # Calculate how many times we need to repeat the video sequence
        repeat_count = int(audio_duration // video_duration) + 1

        # Repeat the video to match the audio duration
        repeated_clips = [video] * repeat_count
        final_video = concatenate_videoclips(repeated_clips, method='compose').set_duration(audio_duration)

        # Set the audio for the video
        final_video = final_video.set_audio(audio_clip)

        output_video_path = os.path.join(r"C:\Users\MohammedBilalAhmed\Desktop\recovery\ai", 'complete_output_video.mp4')
        
        # Write the final video with audio
        final_video.write_videofile(output_video_path, codec='libx264', audio_codec='aac')
    else:
        output_video_path = os.path.join(r"C:\Users\MohammedBilalAhmed\Desktop\recovery\ai", 'output_video.mp4')
        video.write_videofile(output_video_path, codec='libx264')

    # Clean up temporary files
    for image_path in image_paths:
        os.remove(image_path)

    # Return the video file
    return send_file(output_video_path, mimetype='video/mp4', as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
