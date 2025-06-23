import kagglehub
import os
import zipfile

# using kagglehub, download "manisha717/dataset-of-pdf-files" as dataset/pdfs.zip if dataset/pdfs.zip doesn't exist
if not os.path.exists("dataset/pdfs.zip"):
    os.makedirs("dataset", exist_ok=True)
    path = kagglehub.dataset_download("manisha717/dataset-of-pdf-files")
    
    # Find the zip file in the downloaded path
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith(".zip"):
                source_zip = os.path.join(root, file)
                os.rename(source_zip, "dataset/pdfs.zip")
                break

# unzip dataset/pdfs.zip in samples/ (samples/ might not exists)
os.makedirs("samples", exist_ok=True)
with zipfile.ZipFile("dataset/pdfs.zip", 'r') as zip_ref:
    zip_ref.extractall("samples/")