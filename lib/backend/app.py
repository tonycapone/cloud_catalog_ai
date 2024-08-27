from flask import Flask, request, Response
from flask_cors import CORS
import os
import boto3
import json
from langchain_community.retrievers import AmazonKnowledgeBasesRetriever
from botocore.config import Config
import time

app = Flask(__name__)
CORS(app)

# Environment variables
aws_region = os.environ["AWS_REGION"]
customer_name = os.environ["CUSTOMER_NAME"]
knowledge_base_id = os.environ["KNOWLEDGE_BASE_ID"]

# AWS setup
config = Config(retries={'max_attempts': 10, 'mode': 'adaptive'})
BEDROCK_CLIENT = boto3.client("bedrock-runtime", 'us-east-1', config=config)

# Retriever setup
retriever = AmazonKnowledgeBasesRetriever(
    knowledge_base_id=knowledge_base_id,
    retrieval_config={"vectorSearchConfiguration": {"numberOfResults": 4}},
)

# Products retriever setup
products_retriever = AmazonKnowledgeBasesRetriever(
    knowledge_base_id=knowledge_base_id,
    retrieval_config={"vectorSearchConfiguration": {"numberOfResults": 10}},
)

# Question rewriting template
condense_question_template = """Given the following conversation and a follow up question, rephrase the follow up question to be a standalone question, in its original language.

Chat History:
{chat_history}

Follow Up Input: {question}
Standalone question:"""

# Prompt template
template = """
Human: You are a helpful and talkative {customer_name} assistant that answers questions directly and only using the information provided in the context below. 
Guidance for answers:
    - Do not include any framing language such as "According to the context" in your responses, but rather act is if the information is coming from your memory banks. 
    - Simply answer the question clearly and with lots of detail using only the relevant details from the information below. If the context does not contain the answer, say "I don't know."
    - Use the royal "We" in your responses. 
    - Use line breaks to separate paragraphs or distinct points. Insert a "<br>" tag at the end of each paragraph or where you want a line break.
    - Finally, you should use the following guidance to control the tone: {prompt_modifier}

Now read this context and answer the question at the bottom. 

Context: {context}

Question: "Hey {customer_name} Chatbot! {question}

A:
"""

# Add a cache dictionary and cache expiration time (e.g., 1 hour)
products_cache = {
    "data": None,
    "timestamp": 0
}
CACHE_EXPIRATION = 3600  # 1 hour in seconds

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    question = data['question']
    chat_history = data.get('chat_history', [])
    prompt_modifier = data.get('prompt_modifier', "Informative, empathetic, and friendly")

    print(f"Chat history: {chat_history}")
    def generate():
        # Rewrite question if there's chat history
        if len(chat_history) >= 2:
            chat_history_str = "\n".join([f"Human: {chat_history[i]}\nAI: {chat_history[i+1]}" for i in range(0, len(chat_history) - 1, 2)])
            rewrite_prompt = condense_question_template.format(chat_history=chat_history_str, question=question)
            print(f"Rewrite prompt: {rewrite_prompt}")
            try:
                rewrite_response = BEDROCK_CLIENT.converse(
                    modelId="anthropic.claude-3-sonnet-20240229-v1:0",
                    messages=[{"role": "user", "content": [{"text": rewrite_prompt}]}],
                    inferenceConfig={"maxTokens": 512, "temperature": 0, "topP": 1},
                )
                rewritten_question = rewrite_response["output"]["message"]["content"][0]["text"]
            except Exception as e:
                print(f"Error in question rewriting: {e}")
                rewritten_question = question
        else:
            print(f"No chat history, using original question: {question}")
            rewritten_question = question
        print(f"Rewritten question: {rewritten_question}")
        # Retrieve relevant documents
        docs = retriever.get_relevant_documents(rewritten_question)
        context = "\n".join([doc.page_content for doc in docs])

        # Extract sources
        sources = []
        for doc in docs:
            if doc.metadata['location'] != "":
                url = doc.metadata['location']['webLocation']['url']
                if url not in sources:
                    sources.append(url)

        # Yield the sources immediately
        yield f"data: {json.dumps({'type': 'metadata', 'sources': sources})}\n\n"

        # Construct the prompt
        prompt = template.format(
            customer_name=customer_name,
            prompt_modifier=prompt_modifier,
            context=context,
            question=rewritten_question
        )

        # Prepare messages for converse_stream
        messages = []

        # Add chat history
        for i in range(0, len(chat_history) - 1, 2):
            messages.append({"role": "user", "content": [{"text": chat_history[i]}]})
            messages.append({"role": "assistant", "content": [{"text": chat_history[i+1]}]})
        messages.append({"role": "user", "content": [{"text": prompt}]})

        print(f"Messages: {json.dumps(messages, indent=2)}")
        # Stream the response using ConverseStream
        response = BEDROCK_CLIENT.converse_stream(
            modelId="anthropic.claude-3-sonnet-20240229-v1:0",
            messages=messages,
            system=[{"text": f"You are a helpful and talkative {customer_name} assistant. {prompt_modifier}"}],
            inferenceConfig={
                "temperature": 0,
                "maxTokens": 1000,
            }
        )
        for chunk in response["stream"]:
            if "contentBlockDelta" in chunk:
                text = chunk["contentBlockDelta"]["delta"]["text"]
                yield f"data: {json.dumps({'type': 'content', 'content': text})}\n\n"

        yield f"data: {json.dumps({'type': 'stop'})}\n\n"

    return Response(generate(), mimetype='text/event-stream')

@app.route('/products', methods=['GET'])
def get_products():
    # Add a configurable limit parameter with a default of 12
    limit = request.args.get('limit', default=1, type=int)

    # Check if cache is valid
    current_time = time.time()
    if products_cache["data"] and (current_time - products_cache["timestamp"]) < CACHE_EXPIRATION:
        print("Returning cached products")
        return json.dumps(products_cache["data"][:limit])

    # If cache is invalid or doesn't exist, proceed with the original logic
    # Step 1: Ask who the customer is
    customer_info_prompt = f"Who is {customer_name}? Provide a brief description of the company and its main business areas."
    customer_info_docs = products_retriever.get_relevant_documents(f"{customer_name} company and business areas")
    customer_info_context = "\n".join([doc.page_content for doc in customer_info_docs])
    
    customer_info_response = BEDROCK_CLIENT.converse(
        modelId="anthropic.claude-3-sonnet-20240229-v1:0",
        messages=[{"role": "user", "content": [{"text": f"{customer_info_prompt}\n\nCustomer Context: {customer_info_context}"}]}],
        inferenceConfig={"maxTokens": 500, "temperature": 0, "topP": 1},
    )
    customer_info = customer_info_response["output"]["message"]["content"][0]["text"]
    print(f"Customer Info: {customer_info}")

    # Step 2: Generate specific product questions
    question_generation_prompt = f"""
    Based on this information about {customer_name}:
    {customer_info}
    
    Generate 3-5 specific questions about their products, services, or solutions. These questions should help identify distinct offerings. Format your response as a Python list of strings.
    """
    question_docs = products_retriever.get_relevant_documents(f"{customer_name} products and services")
    question_context = "\n".join([doc.page_content for doc in question_docs])
    
    question_response = BEDROCK_CLIENT.converse(
        modelId="anthropic.claude-3-sonnet-20240229-v1:0",
        messages=[{"role": "user", "content": [{"text": f"{question_generation_prompt}\n\nAdditional Context: {question_context}"}]}],
        inferenceConfig={"maxTokens": 500, "temperature": 0.2, "topP": 1},
    )
    questions_str = question_response["output"]["message"]["content"][0]["text"]
    print(f"Generated Questions: {questions_str}")
    
    # Parse the questions string into a list
    import ast
    try:
        questions = ast.literal_eval(questions_str)
    except:
        questions = [f"What are the main products and services offered by {customer_name}?"]

    # Step 3: Retrieve documents and extract product information
    products = []
    processed_products = set()  # Set to keep track of processed product names

    for question in questions:
        if len(products) >= limit:
            break  # Stop processing if we've reached the limit

        docs = products_retriever.get_relevant_documents(question)
        
        for doc in docs:
            if len(products) >= limit:
                break  # Stop processing if we've reached the limit

            extraction_prompt = f"""
            Extract structured product or service information from the following text, focusing on answering: {question}
            
            Return the result as a JSON array of objects with the following structure:
            [
                {{
                    "name": "Specific product or service name",
                    "description": "A brief, clear description of the product or service",
                    "link": "URL to the product or service page if available, otherwise null",
                    "icon": "An appropriate Font Awesome icon name (without the 'fa-' prefix) that represents this product or service"
                }}
            ]
            If no clear products or services are identified, return an empty array.

            Text: {doc.page_content}
            """
            
            try:
                extraction_response = BEDROCK_CLIENT.converse(
                    modelId="anthropic.claude-3-sonnet-20240229-v1:0",
                    messages=[{"role": "user", "content": [{"text": extraction_prompt}]}],
                    inferenceConfig={"maxTokens": 1000, "temperature": 0, "topP": 1},
                )
                response_content = extraction_response["output"]["message"]["content"][0]["text"]
                print(f"API Response for '{question}': {response_content}")
                
                # Use regex to find the JSON array in the response
                import re
                json_match = re.search(r'\[.*?\]', response_content, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    extracted_info = json.loads(json_str)
                else:
                    print(f"No JSON array found in the response for question: {question}")
                    continue
                
                for product in extracted_info:
                    if len(products) >= limit:
                        break  # Stop processing if we've reached the limit

                    if product.get("name") and product.get("name") != "Unknown Product":
                        product_name = product["name"].lower().strip()
                        if product_name not in processed_products:
                            # Extract link from metadata
                            metadata_link = doc.metadata.get('location', {}).get('webLocation', {}).get('url')
                            
                            # Use metadata link if available, otherwise use extracted link or default to "#"
                            product["link"] = metadata_link or product.get("link") or "#"
                            
                            # Ensure there's an icon, default to 'cube' if not provided
                            if not product.get("icon"):
                                product["icon"] = "cube"
                            
                            products.append(product)
                            processed_products.add(product_name)
                            print(f"Added product: {product_name} with link: {product['link']} and icon: {product['icon']}")
                        else:
                            print(f"Skipping duplicate product: {product_name}")
            except json.JSONDecodeError as e:
                print(f"JSON decode error for question '{question}': {str(e)}")
                print(f"Problematic JSON string: {json_str if 'json_str' in locals() else 'Not available'}")
            except Exception as e:
                print(f"Error extracting product information for question '{question}': {str(e)}")
                print(f"Document content: {doc.page_content}")
            
    print(f"Total unique products extracted: {len(products)}")

    # Update the cache
    products_cache["data"] = products
    products_cache["timestamp"] = current_time

    return json.dumps(products[:limit])

@app.route('/product-details/<product_name>', methods=['GET'])
def get_product_details(product_name):
    def generate():
        # Initial query to gather basic information about the product
        docs = products_retriever.get_relevant_documents(f"{product_name} {customer_name}")
        context = "\n\n".join([doc.metadata['location']['webLocation']['url'] + "\n\n" + doc.page_content for doc in docs])

        print(context)
        # Generate a concise summary of the product
        summary_prompt = f"""
        Based on the following information about {product_name}, provide a concise summary of the product or service.
        Focus on its key features, benefits, and its role in {customer_name}'s offerings.
        
        Write the summary in markdown format.
        
        Context: {context}

        Summary:
        """

        yield f"data: {json.dumps({'type': 'initial'})}\n\n"

        response = BEDROCK_CLIENT.converse_stream(
            modelId="anthropic.claude-3-sonnet-20240229-v1:0",
            messages=[{"role": "user", "content": [{"text": summary_prompt}]}],
            inferenceConfig={"maxTokens": 1000, "temperature": 0, "topP": 1},
        )

        for chunk in response["stream"]:
            if "contentBlockDelta" in chunk:
                text = chunk["contentBlockDelta"]["delta"]["text"]
                yield f"data: {json.dumps({'type': 'content', 'content': text})}\n\n"

        yield f"data: {json.dumps({'type': 'stop'})}\n\n"

    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True)
