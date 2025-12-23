import logging
import os
import io
import azure.functions as func
from unstructured.partition.auto import partition
from azure.storage.blob import BlobServiceClient

app = func.FunctionApp()

@app.blob_trigger(arg_name="myblob", 
                  path="input-files/{name}",
                  connection="AzureWebJobsStorage")
def BlobToMarkdown(myblob: func.InputStream):
    # Added a version tag so you can see the change in the logs
    logging.info(f"--- V3 (BytesIO) Triggered: {myblob.name} ---")

    try:
        # 1. Read the blob content
        blob_data = myblob.read()
        
        # 2. Wrap in BytesIO to make it a true 'file' object
        file_obj = io.BytesIO(blob_data)

        # 3. Partition using the 'file' parameter (NOT content)
        # We also provide metadata_filename to help the library guess the file type
        elements = partition(file=file_obj, metadata_filename=myblob.name)

        # 4. Convert to Markdown
        md_content = "\n\n".join([str(el) for el in elements])

        # 5. Connect and Upload
        connection_string = os.environ["AzureWebJobsStorage"]
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        
        base_name = os.path.basename(myblob.name)
        file_root = os.path.splitext(base_name)[0]
        output_filename = f"{file_root}.md"

        blob_client = blob_service_client.get_blob_client(container="output-files", blob=output_filename)
        blob_client.upload_blob(md_content, overwrite=True)

        logging.info(f"Successfully converted {myblob.name} to {output_filename}")

    except Exception as e:
        logging.error(f"Error processing blob {myblob.name}: {str(e)}")