from model import ImageTranslator

file_path =  "path/to/file.png"
model = ImageTranslator(file_path, from_language='auto', to_language='en')
model.run()
model.preview()