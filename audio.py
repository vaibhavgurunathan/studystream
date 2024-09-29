from pyt2s.services import stream_elements

# Default Voice
def generate_audio_description(txt, counter):

    # Custom Voice
    print(txt)
    data = stream_elements.requestTTS(txt, stream_elements.Voice.Russell.value)

    output_file_name = f'output{counter}.mp3'
    print(output_file_name)
    with open(output_file_name, '+wb') as file:
        print(file)
        file.write(data)
    
    print('DONE')


