import os
from dotenv import load_dotenv
from app.logger import get_logger

from fastapi import HTTPException

import boto3

# Load environment variables from .env file
load_dotenv()

logger = get_logger("configs")

def get_secret(secret_name, region_name="us-east-2"):
    """Fetch secrets from AWS Secrets Manager."""
    client = boto3.client("secretsmanager", region_name=region_name)
    try:
        response = client.get_secret_value(SecretId=secret_name)
        return eval(response["SecretString"])
    except Exception as e:
        logger.error(f"Error during AWS Secret: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get secrets.")

# Set intent classification threshold
INTENT_CLASSIFICATION_THRESHOLD = 0.5

try:
    
    print('ENVIRONMENT====' , os.environ.get('ENVIRONMENT'))
    if os.environ.get('ENVIRONMENT') == 'DEMO':        
        secret_name = "cai-demo"# Name of your secret in Secrets Manager
    else:
        secret_name = "cai-development"   # Name of your secret in Secrets Manager
        
    secrets = get_secret(secret_name)
    
    OPENAI_API_KEY = secrets.get("OPENAI_APIKEY")
    PINECONE_API_KEY = secrets.get("PINECONE_APIKEY")
    
    REDIS_ENDPOINT = secrets.get("REDIS_ENDPOINT")
    REDIS_SSL = secrets.get("REDIS_SSL")
    REDIS_PREFIX = secrets.get("REDIS_PREFIX") 
    REDIS_PASSWORD = secrets.get("REDIS_PASSWORD") 
    REDIS_TOPIC = secrets.get("REDIS_TOPIC") 
    
    AWS_ACCESS_KEY_ID = secrets.get("AWS_ACCESS_KEY_ID") 
    AWS_SECRET_ACCESS_KEY = secrets.get("AWS_SECRET_ACCESS_KEY") 
    AWS_REGION = secrets.get("AWS_REGION") 
    S3_BUCKET_NAME = secrets.get("S3_BUCKET_NAME") 
    
    POSTGRES_PORT = secrets.get("POSTGRES_PORT")
    POSTGRES_PASS = secrets.get("POSTGRES_PASS")
    POSTGRES_SERVER = secrets.get("POSTGRES_SERVER")
    POSTGRES_DB = secrets.get("POSTGRES_DB")
    POSTGRES_NAME = secrets.get("POSTGRES_NAME")
    
    PINECONE_ENVIRONMENT = secrets.get("PINECONE_ENVIRONMENT")
    PINECONE_INDEX = secrets.get("PINECONE_INDEX")
    PINECONE_NAMESPACE = secrets.get("PINECONE_NAMESPACE")
    
    MONGODB_URI = secrets.get("MONGODB_URI")
    MONGODB_DB_NAME = secrets.get("MONGODB_DB_NAME")
    MONGODB_COLLECTION_NAME = secrets.get("MONGODB_COLLECTION_NAME")
            

except Exception as e:
    
    try:
        logger.warning("Falling back to environment variables.")
        OPENAI_API_KEY = os.getenv("OPENAI_APIKEY")
        PINECONE_API_KEY = os.getenv("PINECONE_APIKEY")
        
        REDIS_ENDPOINT = os.getenv("REDIS_ENDPOINT")
        REDIS_SSL = os.getenv("REDIS_SSL")
        REDIS_PREFIX = os.getenv("REDIS_PREFIX") 
        REDIS_PASSWORD = os.getenv("REDIS_PASSWORD") 
        REDIS_TOPIC = os.getenv("REDIS_TOPIC") 
        
        AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID") 
        AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY") 
        AWS_REGION = os.getenv("AWS_REGION") 
        S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME") 
        
        POSTGRES_PORT = os.getenv("POSTGRES_PORT")
        POSTGRES_PASS = os.getenv("POSTGRES_PASS")
        POSTGRES_SERVER = os.getenv("POSTGRES_SERVER")
        POSTGRES_DB = os.getenv("POSTGRES_DB")
        POSTGRES_NAME = os.getenv("POSTGRES_NAME")

        PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT")
        PINECONE_INDEX = os.getenv("PINECONE_INDEX")
        PINECONE_NAMESPACE = os.getenv("PINECONE_NAMESPACE")
        
        MONGODB_URI = os.getenv("MONGODB_URI")
        MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME")
        MONGODB_COLLECTION_NAME = os.getenv("MONGODB_COLLECTION_NAME")
        
    except Exception as e: 
        logger.error(f"Error initializing secret keys: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get the secret keys.")




