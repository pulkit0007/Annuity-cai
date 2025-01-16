# import traceback
# from typing import Optional
# from app.services.intent_classifier import predict_tool
# from pymongo import MongoClient
# from app.config import MONGODB_DB_NAME, MONGODB_URI, MONGODB_COLLECTION_NAME


# def check_queryType(product_names_record, query):

#     """
#     Check if the query contains any product name from the product_names_record.

#     Args:
#         product_names_record (list): List of product names to check against.
#         query (str): The query string to analyze.

#     Returns:
#         str: "ProductInfo" if a product name is found, otherwise "Not a ProductInfo".
#     """
#     # Normalize product names and query for case-insensitive matching
#     normalized_product_names = [name.lower() for name in product_names_record]
#     normalized_query = query.lower()

#     # Tokenize query into words for partial matches
#     query_words = normalized_query.split()

#     # Check if any product name contains any word from the query
#     for product_name in normalized_product_names:
#         if any(word in product_name for word in query_words):
#             return "ProductInfo"

#     return "AnnuitiesFAQ"


# def query_handler(message: str, history: Optional[str] = "", product_names_record = []) -> dict:

#     # Returns tuple, first element is LLM generated intent, second element is query_type

#     # print("product_names_record: ====> ", product_names_record)
#     query_type = check_queryType(product_names_record, message)
#     # print("query_type: ====> ", query_type)
#     # intent = predict_intent(message)
#     intent = {}
#     try:
#         intent = predict_tool(message, history)
#         print("intent================>>>", intent)
#         print("######################################################")
#         intent = intent.model_dump()
#     except Exception as e:
#         print(f"Error predicting tool: {e}")
#         print(traceback.format_exc())
#         intent = {"intent": "AnnuitiesFAQ"}
#     finally:
#         return intent, query_type


# def get_history_data():
#     try:
#         # Establish connection to MongoDB
#         client = MongoClient(MONGODB_URI)
#         print("Connected to MongoDB!")

#         # Access the specific database
#         db = client[MONGODB_DB_NAME]

#         # Access the specific collection
#         collection = db[MONGODB_COLLECTION_NAME]

#         # Access the chatlogs collection
#         chatlogs_collection = db['chatlogs']

#         # Example operation: Fetch all documents in the collection
#         documents = collection.find()

#         # Fetch the last 5 documents sorted by insertion order (assuming '_id' represents insertion order)
#         last_five_logs = chatlogs_collection.find().sort('_id', -1).limit(5)

#         # Extract the product_name from each document and store in a list
#         product_names = [doc['product_name'] for doc in documents]

#         # Initialize the dictionary for query-response mapping
#         query_response_dict = {}

#         # Process each log
#         for log in last_five_logs:
#             query = log['query']

#             # If the response is streaming, concatenate the 'data' values
#             if isinstance(log['response'], list):  # Assuming 'response' is a list of dictionaries
#                 full_response = ' '.join([entry['data'] for entry in log['response'] if 'data' in entry])
#             else:
#                 # Directly assign if response is a string
#                 full_response = log['response']

#             # Add to the dictionary
#             query_response_dict[query] = full_response

#         return product_names, query_response_dict

#     except Exception as e:
#         print(f"Error connecting to MongoDB: {e}")
#     finally:
#         # Close the connection
#         pass
#         #client.close()
