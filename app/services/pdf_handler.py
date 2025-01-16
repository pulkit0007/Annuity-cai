import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
import os
from app.logger import get_logger
from app.config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, S3_BUCKET_NAME
from pathlib import Path
from datetime import datetime
import json

logger = get_logger("pdf_handler")

class PDFHandler:
    def __init__(self):
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id = AWS_ACCESS_KEY_ID,
            aws_secret_access_key = AWS_SECRET_ACCESS_KEY,
            region_name = AWS_REGION
        )
        self.bucket_name = S3_BUCKET_NAME
        self.processed_files = set()  # Store processed files to avoid duplication
        self.local_folder = "files/"
        
    def get_pdf_count_local(self):
        """Retrieve the count of PDF files in the S3 bucket or fall back to the local folder."""
        try:
            logger.info("checking local folder for pdf files.")
            if not os.path.exists(self.local_folder):
                logger.warning(f"Local folder '{self.local_folder}' does not exist.")
                return 0, []
            
            local_pdfs = [os.path.join(self.local_folder, f) for f in os.listdir(self.local_folder) if f.endswith('.pdf')]
            logger.info(f"Found {len(local_pdfs)} PDF(s) in the local folder.")
            
            # File to store the JSON data
            json_file_path = os.path.join(self.local_folder, 'pdf_metadata.json')

            # Load existing JSON data or create a new one
            if os.path.exists(json_file_path):
                with open(json_file_path, 'r') as json_file:
                    pdf_metadata = json.load(json_file)
            else:
                pdf_metadata = {}
                
            # Track new PDFs to be added
            new_entries = 0

            # Update JSON with the latest PDFs if they don't exist
            for pdf in local_pdfs:
                pdf_name = os.path.basename(pdf)
                if pdf_name not in pdf_metadata:
                    creation_time = os.path.getctime(pdf)
                    created_time_str = datetime.fromtimestamp(creation_time).strftime('%Y-%m-%d %H:%M:%S')

                    # Add new entry
                    pdf_metadata[pdf_name] = {
                        "creation_time": created_time_str
                    }
                    new_entries += 1
                    logger.info(f"Added new PDF to metadata: {pdf_name} ({created_time_str})")
                    
            # Save only if new entries were added
            if new_entries > 0:
                with open(json_file_path, 'w') as json_file:
                    json.dump(pdf_metadata, json_file, indent=4)
                    logger.info(f"Updated PDF metadata saved to {json_file_path}")
            else:
                print("No new pdf file is added")
                logger.info("No new PDFs to add to metadata.")
            
            print("local_pdfs: ", local_pdfs)
            
            latest_pdf = max(local_pdfs, key=os.path.getctime)
            
            created_time = datetime.fromtimestamp(os.path.getctime(latest_pdf))

            print(f"Latest PDF: {latest_pdf}")
            print(f"Last created: {created_time}")
            
            
            return len(local_pdfs), local_pdfs

        except Exception as e:
            logger.error(f"Error retrieving PDF files: {str(e)}")
            raise

    def get_pdf_count_aws(self):
        """Retrieve the count of PDF files in the S3 bucket or fall back to the local folder."""
        try:
            logger.info("Attempting to fetch PDF files from S3...")
            response = self.s3_client.list_objects_v2(Bucket=self.bucket_name, Prefix="pdfs/")
            
            # Debug response structure
            logger.debug(f"S3 response: {response}")
            
            if 'Contents' in response and response['Contents']:
                pdf_files = [obj['Key'] for obj in response['Contents'] if obj['Key'].endswith('.pdf')]
                if pdf_files:
                    logger.info(f"Found {len(pdf_files)} PDF(s) in S3 bucket.")
                    return len(pdf_files), pdf_files
            
            # If no PDFs found in S3, check the local folder
            logger.info("No PDFs found in S3 bucket, checking local folder.")
            if not os.path.exists(self.local_folder):
                logger.warning(f"Local folder '{self.local_folder}' does not exist.")
                return 0, []
            
            local_pdfs = [f for f in os.listdir(self.local_folder) if f.endswith('.pdf')]
            logger.info(f"Found {len(local_pdfs)} PDF(s) in the local folder.")
            return len(local_pdfs), local_pdfs

        except (NoCredentialsError, PartialCredentialsError) as e:
            logger.error("AWS credentials error: Ensure your credentials are properly set.")
            raise
        except Exception as e:
            logger.error(f"Error retrieving PDF files: {str(e)}")
            raise

    def process_new_files(self):
        """Check for new PDF files and process them."""
        count, pdf_files = self.get_pdf_count()
        new_files = [file for file in pdf_files if file not in self.processed_files]

        if new_files:
            for file in new_files:
                self.process_file(file)
            self.processed_files.update(new_files)  # Mark as processed

        return new_files

    def process_file(self, file_key):
        """Placeholder for processing a single PDF file."""
        logger.info(f"Processing file: {file_key}")
        # Logic for downloading, extracting vectors, and storing in PostgreSQL
        local_file = self.local_folder
        try:
            self.s3_client.download_file(self.bucket_name, file_key, local_file)
            logger.info(f"File {file_key} downloaded successfully.")
            # Insert vector extraction and database logic here
        except Exception as e:
            logger.error(f"Error processing file {file_key}: {str(e)}")
        finally:
            if os.path.exists(local_file):
                os.remove(local_file)  # Clean up local file
