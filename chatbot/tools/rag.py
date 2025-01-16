import json
import httpx
import traceback
from pydantic import BaseModel, Field
from time import time
from typing import Dict, List, Optional
from rapidfuzz import process, fuzz
from common.openai_client import async_openai_client
from chatbot.tools.context_builder import get_documents, RAGContext
from common.rag_db import (
    structured_data_collection,
    # pinecone_index,
    # PineconeIdx1536_Namespaces,
)
from chatbot.prompts import (
    NAME_MATCHER_SYS_PROMPT,
    NAME_MATCHER_USER_PROMPT,
    PRODUCT_INFO_SYS_PROMPT_CITE,
    PRODUCT_INFO_SYS_PROMPT,
)

from app.logger import get_logger

logger = get_logger("tools")


class NameMatcher(BaseModel):
    product_name: str = Field(
        description="Closest possible match of predicted product name with the valid product names."
    )


async def match_product_name_2(
    user_query: str, history: str, predicted_name: str, products_list: List[dict]
) -> dict:
    name_id_map = {item.get("name", ""): item.get("id", "") for item in products_list}
    valid_names = [item.get("name", "") for item in products_list]

    # Check for quicker exact match first
    for record in products_list:
        if (
            predicted_name.strip().lower() == record["name"].strip().lower()
        ):  # Match by first word
            print("####### quick exact match ###########", record)
            return {
                "product_name": record["name"],
                "product_id": record["id"],
            }

    match = ""
    messages = [
        {"role": "system", "content": NAME_MATCHER_SYS_PROMPT},
        {
            "role": "user",
            "content": NAME_MATCHER_USER_PROMPT.format(
                valid_names=valid_names,
                predicted_name=predicted_name,
                history=history,
                question=user_query,
            ),
        },
    ]
    completion = await async_openai_client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=messages,
        response_format=NameMatcher,
        temperature=0,
    )
    match = completion.choices[0].message.parsed.product_name
    print("####### gpt_match ###########", match)
    return {
        "product_name": match,
        "product_id": name_id_map.get(match, ""),
    }

async def match_product_name(
    user_query: str,
    history: str, 
    predicted_name: str,
    products_list: List[dict]
) -> dict:
    print("\n\n####### predicted_name ###########\n\n", predicted_name)
    match_data = {
        "product_name": None,
        "product_id": None
    }
    name_id_map = {item.get("name", ""): item.get("id", "") for item in products_list}
    valid_names = [item.get("name", "") for item in products_list]
    print("\n\n####### valid_names ###########\n\n", valid_names)
    clean_query = " ".join(user_query.lower().strip().split())
    clean_predicted = " ".join(predicted_name.lower().strip().split())

    if history:
        history_string = ""
        for record in history[::-1][:2]:
            for k, v in record.items():
                history_string += f"Question: {k}\nAnswer: {v}\n"
                if clean_predicted in k.lower() or clean_predicted in v.lower():
                    return {
                        "product_name": k,  #
                        "product_id": name_id_map.get(k, None)
                    }
                if clean_query in k.lower() or clean_query in v.lower():
                    return {
                        "product_name": k, 
                        "product_id": name_id_map.get(k, None)
                }
    
    # Check for quicker exact match first
    if predicted_name:
        for name in valid_names:
            clean_name = " ".join(name.lower().strip().split())
            if clean_predicted == clean_name:
                return {
                    "product_name": name,
                    "product_id": name_id_map[name]
                }
    
        
        results = process.extract(
            query=clean_predicted,
            choices=valid_names,
            limit=5,
            scorer=fuzz.partial_ratio,
            score_cutoff=90
        )
        
        
        final_results = []
        for result in results:
            name = result[0]
            partial_score = result[1]
            
            token_score = fuzz.token_set_ratio(name.lower(), predicted_name.lower())
            full_score = fuzz.ratio(name.lower(), predicted_name.lower())
            
            if token_score < 75 and full_score < 60:
                continue
                
            combined_score = (
                partial_score * 0.4 +  
                token_score * 0.4 +    
                full_score * 0.2     
            )
            
            if name[0].lower() == predicted_name[0].lower():
                combined_score += 10
                
            final_results.append({
                "name": name,
                "score": combined_score
            })
        
        
        if final_results:
            final_results.sort(key=lambda x: x["score"], reverse=True)
            if final_results[0]["score"] >= 85:
                best_match = final_results[0]["name"]
                return {
                    "product_name": best_match,
                    "product_id": name_id_map[best_match]
                }
    
    # history_string = ""
    # for record in history[::-1][:2]:
    #     for k, v in record.items():
    #         history_string += f"Question: {k}\nAnswer: {v}\n"

    for name in valid_names:
        clean_name = " ".join(name.lower().strip().split())
        if clean_query == clean_name:
            return {
                "product_name": name,
                "product_id": name_id_map[name]
            }
    
    # Get fuzzy matches for user query
    results = process.extract(
        query=clean_query,
        choices=valid_names,
        limit=5,
        scorer=fuzz.partial_ratio,
        score_cutoff=85
    )
    
    # Process user query matches
    final_results = []
    for result in results:
        name = result[0]
        partial_score = result[1]
        
        token_score = fuzz.token_set_ratio(name.lower(), user_query.lower())
        full_score = fuzz.ratio(name.lower(), user_query.lower())
        
        if token_score < 65 and full_score < 50:
            continue
            
        combined_score = (
            partial_score * 0.4 +
            token_score * 0.4 +
            full_score * 0.2
        )
        
        # Bonus for first letter match
        if name[0].lower() == user_query[0].lower():
            combined_score += 10
            
        final_results.append({
            "name": name,
            "score": combined_score
        })
    
    # Return best match if found
    if final_results:
        final_results.sort(key=lambda x: x["score"], reverse=True)
        if final_results[0]["score"] >= 75:
            best_match = final_results[0]["name"]
            return {
                "product_name": best_match,
                "product_id": name_id_map[best_match]
            }
    
    return match_data


def get_structured_data(
    product_name: str = None, product_id: str = None
) -> Dict[str, str]:
    RELEVANT_FIELDS = [
        "product_name",
        "issuer_name",
        "issue_date",
        "product_type",
        "payout_timeline",
        "is_on_sale",
    ]
    if product_id:
        document = structured_data_collection.find_one({"product_id": product_id}) or {}
    elif product_name:
        document = (
            structured_data_collection.find_one({"product_name": product_name}) or {}
        )
    else:
        document = {}
    answer = {}
    if document:
        answer = {k: v for k, v in document.items() if k in RELEVANT_FIELDS}
    return json.dumps(answer)


# TODO: Rotate keys.
async def get_qwen_embedding(text: str) -> list[float]:
    API_URL = "https://bn8f4rd8lcq64bqo.us-east-1.aws.endpoints.huggingface.cloud"
    headers = {
        "Accept": "application/json",
        "Authorization": "Bearer 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",
        "Content-Type": "application/json",
    }

    async def aquery(url, headers, json_payload):
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=json_payload)
            response.raise_for_status()
            return response.json()[0]

    output = await aquery(
        API_URL,
        headers,
        {
            "inputs": text,
        },
    )
    return output


# async def get_prospectus_text(query, top_k=10, filters={}):
#     vector = await get_qwen_embedding(query)
#     _results = pinecone_index.query(
#         namespace=PineconeIdx1536_Namespaces.doc_rag,
#         vector=vector,
#         include_metadata=True,
#         filter=filters,
#         top_k=top_k,
#     )
#     res = _results["matches"]
#     texts = [match["metadata"]["text"] for match in res]
#     logger.info(f"Getting RAG response =======> {len(texts)}")
#     return texts


async def get_rag_answer(
    question: str,
    products: list,
    history: str,
    tool_spec: Optional[dict] = None,
):
    pass
    try:
        start = time()
        predicted_product_name = tool_spec.get("product_name", "")

        matched_product_names = await match_product_name(
            question, history, predicted_product_name, products
        )
        matched_product_names_2 = await match_product_name_2(
            question, history, predicted_product_name, products
        )
        print("####### matched_product_names ###########", matched_product_names)
        print("####### matched_product_names_gpt ###########", matched_product_names_2)
        if matched_product_names:
            product_name = matched_product_names.get("product_name", "")
            product_id = matched_product_names.get("product_id", "")

            header = f"Product Name: {product_name}\n"
            struct_data = (
                get_structured_data(product_id=product_id)
                if product_id
                else get_structured_data(product_name=product_name)
            )
            struct_data_message = [
                {
                    "type": "text",
                    "text": f"Basic Facts: {struct_data}\n\n",
                }
            ]
            query_vector = await get_qwen_embedding(question)

            filters = (
                {"product_id": product_id}
                if product_id
                else {"product_name": product_name}
            )

            documents = get_documents(query_vector, top_k=20, filters=filters)

            # TODO: Flip with_references to True when using citations
            context_builder = RAGContext(documents, with_references=True)
            context_builder.build_context()
            print("###### context_builder ######\n\n ",context_builder)
            messages = (
                struct_data_message
                + context_builder.messages
                + [
                    {
                        "type": "text",
                        "text": f"Current Question: {question}. Let's begin!",
                    }
                ]
            )
            user_message = {"role": "user", "content": messages}

        else:
            user_message = {
                "role": "user",
                "content": f"Context: Could not find any product matching the query. Please answer as best as you can and mention that you could not find any product matching the query. Current Question: {question}",
            }

        # TODO: Use cite enabled system prompt when using citations
        messages = [
            {
                "role": "system", 
                "content": PRODUCT_INFO_SYS_PROMPT_CITE
            },
            user_message,
        ]

        response_stream = await async_openai_client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0.7,
            max_tokens=1024,
            stream=True,
        )
        # messages = [
        #     {"role": "system", "content": PRODUCT_INFO_SYS_PROMPT},
        #     user_message,
        # ]
        # # def return_test():
        # #     return "Test Response"
        # # response_stream =  await return_test()
        # response_stream = await async_openai_client.chat.completions.create(
        #     model="gpt-4o",
        #     messages=messages,
        #     temperature=0.7,
        #     max_tokens=1024,
        #     stream=True,
        # )
        print("####### response_stream ###########", response_stream)
        logger.info(f"RAG answer time: {time() - start}")
        return response_stream
    except Exception as e:
        logger.error(f"Error processing RAG answer: {e}")
        logger.error(traceback.format_exc())
        raise
