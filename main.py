import yake
import os
import shutil
import re
import chromadb
import requests
from bs4 import BeautifulSoup
import torch
from PIL import Image
from pyt2s.services import stream_elements
from transformers import BlipProcessor, BlipForConditionalGeneration
from gtts import gTTS


from image_describer import generate_image_description
from audio import generate_audio_description
from av_merge import *
from bullet_points import *
from slide_deck import *

import google.generativeai as genai

# Configure the Generative AI model
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

def main(text_file, number_of_frames, input_type='File'):

    text_chunks, overall_keyword = slice_file_into_groups(text_file, number_of_frames, input_type)
    count = 0
    bullets = []
    delete_all_in_folder('final_deck_images')
    for chunk in text_chunks:
        top_keyword, search_phrase = get_keywords_in_chunk(chunk)
        chroma_client = chromadb.Client()
        collection_name = "text_chunk" + str(count)
        collection = chroma_client.create_collection(name=collection_name)

        if not top_keyword:
            print("No keywords found in chunk.")
            break 

        delete_all_in_folder('downloaded_images')
        search_images(search_phrase, 10)
        image_and_description = get_image_descriptions('downloaded_images') 
        print(type(image_and_description))
        print(image_and_description)
        for image, description in image_and_description.items():
            collection.add(
                documents=[description],
                ids = [image]
            )
        
        answer = collection.query(
            query_texts=[search_phrase + " " + top_keyword + chunk],  
            n_results=1 
        )
        print('\n\n')
        # print(answer)

        image_id = answer['ids'][0][0]  # Get the first ID
        image_description = answer['documents'][0][0]  # Get the first document

        print(f"Image ID: {image_id}")
        print(f"Image Description: {image_description}")

        copy_file(f'downloaded_images/{image_id}', 'final_deck_images', f'deck_image{count}.jpg')

        # Now we have the image and the description for the closest images
        query = "Given an image description:" + image_description + " and the combination with " + search_phrase + ", explain this in much more detail. Make sure it is in context with " + top_keyword + " and Assume you have everything, so don't ask for anything more. Get the best estimate and explain the concepts like a teacher. Make sure you give an explanation of the image as well in this. Make this to be under 1 minute if spoken out loud slowly. Also make sure that it is easy to understand if spoken and not written."
        response = model.generate_content(query)
        print(response.text)
        myobj = gTTS(text=response.text, lang='en', slow=False)
        myobj.save(f'output{count}.mp3')
        bullets_point_list = generate_bullet_points(response.text, overall_keyword)
        bullets.append(bullets_point_list)

        # generate_audio_description(response.text, count)
        # Stitch the image and audio together 
        # merge_video(f'output{count}.mp3', f'downloaded_images/{image_id}', count)
        count += 1

    audio_paths = ['output' + str(i) + '.mp3' for i in range(count)]
    image_paths = ['final_deck_images/deck_image' + str(i) + '.jpg' for i in range(count)]
    create_video(image_paths, audio_paths, bullets, 'final_video.mp4')
    # Now bullets has all the bullets it needs
    # Final Deck Images Has All the Images It Needs
    # Audio has all the audio it needs
    # create_video('final_deck_images', 'audio', bullets, 'final_video.mp4')




        


        

    

def slice_file_into_groups(filename, num_groups, input_type='File'):
    if input_type == 'File':
        with open(filename, 'r') as file:
            text = file.read()  # Read the entire file as a single string
    else:
        text = filename

    # Get the overall keyword of the text
    yake_extractor = yake.KeywordExtractor()
    keywords = yake_extractor.extract_keywords(text)
    overall_keyword = sorted(keywords, key=lambda x: x[1])[-1][0] if keywords else None
    # Split the text into chunks based on character count or another method
    words = text.split()
    chunk_size = len(words) // num_groups
    chunks = [' '.join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]
    
    return chunks, overall_keyword

def get_keywords_in_chunk(chunk):
    yake_extractor = yake.KeywordExtractor()
    keywords = yake_extractor.extract_keywords(chunk)
    
    if not keywords:
        return None, None  # Return None if no keywords found
    
    top_keyword = sorted(keywords, key=lambda x: x[1])[0][0]
    search_phrase = find_most_relevant_sentence(chunk, top_keyword)
    
    return top_keyword, search_phrase

def find_most_relevant_sentence(text, keyword):
    # Split text into sentences
    sentences = re.split(r'(?<=[.!?]) +', text)
    
    # Filter sentences that contain the keyword
    sentences_with_keyword = [sentence.strip() for sentence in sentences if keyword in sentence]
    
    # Return the first sentence that contains the keyword, if available
    if sentences_with_keyword:
        return sentences_with_keyword[0]  # Return just the first relevant sentence
    
    return None  # Return None if no sentence is found




# Assume this is good enough for now
def search_images(query, num_images=3):
    # Format the query for the URL
    query = '+'.join(query.split())
    url = f"https://www.google.com/search?hl=en&tbm=isch&q={query}"

    # Set up headers to mimic a browser request
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }

    # Get the search results
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find the image links
    img_tags = soup.find_all('img')
    
    img_urls = []
    for img in img_tags[1:]:  # Skip the first image which is usually a logo
        try:
            link = img['src']
            img_urls.append(link)
            if len(img_urls) >= num_images:
                break
        except KeyError:
            continue

    # Create a directory to save images
    if not os.path.exists('downloaded_images'):
        os.makedirs('downloaded_images')

    # Download the images
    downloaded_count = 0
    for i, img_url in enumerate(img_urls):
        try:
            # Download the image directly
            img_response = requests.get(img_url, headers=headers)
            if img_response.status_code == 200:
                with open(f'downloaded_images/image_{downloaded_count + 1}.jpg', 'wb') as img_file:
                    img_file.write(img_response.content)
                downloaded_count += 1

            if downloaded_count >= num_images:
                break  # Stop if we have downloaded the required number of images

        except Exception as e:
            print(f"Failed to download image {i + 1}: {e}")

    print(f'Downloaded {downloaded_count} images.')


def get_image_descriptions(folder_name):
    files = os.listdir(folder_name)
    image_and_description = {}
    for file in files:
        image_and_description[file] = generate_image_description(os.path.join(folder_name, file))
    return image_and_description

def delete_all_in_folder(folder_path):
    # Check if the folder exists
    if os.path.exists(folder_path) and os.path.isdir(folder_path):
        # Loop through all items in the folder
        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)
            # Remove the item (file or directory)
            if os.path.isfile(item_path):
                os.remove(item_path)
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)
        print(f"All items in '{folder_path}' have been deleted.")
    else:
        print(f"The folder '{folder_path}' does not exist or is not a directory.")



def copy_file(source_file_path, destination_folder, new_file_name=None):
    """
    Copy a file from the source path to the destination folder, with an optional new name.

    Parameters:
    - source_file_path: str, path to the file to be copied
    - destination_folder: str, path to the folder where the file will be copied
    - new_file_name: str, optional new name for the copied file
    """
    try:
        # Ensure the destination folder exists
        os.makedirs(destination_folder, exist_ok=True)

        # Determine the destination file path
        if new_file_name:
            destination_file_path = os.path.join(destination_folder, new_file_name)
        else:
            file_name = os.path.basename(source_file_path)
            destination_file_path = os.path.join(destination_folder, file_name)

        # Copy the file
        shutil.copy2(source_file_path, destination_file_path)  # copy2 preserves metadata
        print(f"Copied '{source_file_path}' to '{destination_file_path}'")

    except Exception as e:
        print(f"Error: {e}")


main('ch1.txt', 15, 'File')
# main('python_guide.txt',2, 'File')
