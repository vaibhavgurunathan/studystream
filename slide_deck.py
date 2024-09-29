import pygame
from PIL import Image, ImageDraw, ImageFont
import time
import moviepy.editor as mp

def create_slide(image_path, audio_path, bullet_points, slide_number):
    # Load the image
    image = Image.open(image_path)
    
    # Create a new image for the slide
    slide_width = 800  # Width for the slide
    slide_height = max(image.height, 200)  # Ensure enough height for the text

    # Create a blank slide image
    slide_image = Image.new("RGB", (slide_width, slide_height), "white")
    draw = ImageDraw.Draw(slide_image)

    # Load a font (you might need to specify a path to a .ttf file)
    font = ImageFont.load_default()
    bullet_margin = 20

    # Draw bullet points on the left
    y_text = bullet_margin
    for point in bullet_points:
        draw.text((bullet_margin, y_text), f"• {point}", font=font, fill="black")
        text_bbox = draw.textbbox((bullet_margin, y_text), f"• {point}", font=font)
        y_text += text_bbox[3] - text_bbox[1] + 5  # Adjust line spacing

    # Calculate the new size for the image (30% of slide width)
    image_width = int(slide_width * 0.3)
    image_height = int(image.height * (image_width / image.width))  # Maintain aspect ratio

    # Resize the image
    image_resized = image.resize((image_width, image_height))

    # Paste the image on the right side of the slide
    slide_image.paste(image_resized, (slide_width - image_width, 0))  # Paste image on the right

    # Save the updated slide image
    slide_image_path = f"slide_with_bullets_{slide_number}.png"
    slide_image.save(slide_image_path)
    
    return slide_image_path


def create_video(image_paths, audio_paths, bullet_points_list, output_video_path):
    clips = []
    
    for slide_number, (image, audio, bullets) in enumerate(zip(image_paths, audio_paths, bullet_points_list)):
        slide_image_path = create_slide(image, audio, bullets, slide_number)
        
        # Create a video clip from the image
        clip = mp.ImageClip(slide_image_path).set_duration(mp.AudioFileClip(audio).duration)
        clip = clip.set_audio(mp.AudioFileClip(audio))  # Add audio to the clip
        clips.append(clip)

    # Concatenate all the clips into one video
    final_video = mp.concatenate_videoclips(clips)
    final_video.write_videofile(output_video_path, fps=24)
