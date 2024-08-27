from flask import Flask, request, Response
from flask_cors import CORS
import os
import boto3
import json
from langchain_community.retrievers import AmazonKnowledgeBasesRetriever
from botocore.config import Config
import time
from dotenv import load_dotenv

# Check if any of the required environment variables are missing
required_env_vars = ["AWS_REGION", "CUSTOMER_NAME", "KNOWLEDGE_BASE_ID"]
if any(env_var not in os.environ for env_var in required_env_vars):
    # Load environment variables from .env.local file only if any required variable is missing
    load_dotenv('.env.local')

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
}

product_details_cache = {
  "Market Entry Strategy": {
    "overview": "Market Entry Strategy involves understanding the target market, developing a suitable product portfolio, establishing effective distribution channels, and providing technological capabilities for smooth end-to-end processing. It requires a well-structured strategic plan, a business model focused on high-potential markets and distribution channels, a broad and competitive product offering, efficient enrollment and underwriting processes, responsive claims handling, superior back-office services, robust marketing programs, and competitive commissions. Successful market entry also involves measuring and monitoring results to make necessary adjustments.",
    "features": "Key features of Market Entry Strategy:\n\n1. **Product Creation**: Developing new products or revamping existing ones to meet market demands and maintain competitiveness.\n2. **Alternative Distribution Channels**: Exploring innovative distribution channels like embedded insurance-linked wellness programs or partnerships with retailers.\n3. **Bancassurance**: Utilizing bank data to simplify underwriting, enhance customer experience, and improve cross-selling performance.\n4. **Capital Management**: Leveraging reinsurance solutions to reduce regulatory capital requirements and release capital for other needs.\n5. **Acquisitions**: Supporting clients in acquiring or divesting businesses through diligence, co-investing, reinsuring risks, and providing financing.\n6. **Direct Policy Administration (DPA)**: Offering DPA services to clients to facilitate business acquisitions or transitions.\n7. **Collaboration and Partnership**: Working closely with clients, introducing insights, innovations, and training to ensure successful product launches and market entry.\n8. **Data and Analytics**: Utilizing data, predictive modeling, and risk scoring to identify better risks, simplify underwriting, and enhance customer experience.\n9. **Financial Strength and Execution Certainty**: Providing the capital, capacity, and expertise to complete transactions and support long-term partnerships.\n10. **Regulatory Expertise**: Navigating regulatory and tax issues to ensure smooth integration and approval of transactions.",
    "benefits": "The main benefits of using Market Entry Strategy mentioned in the context are:\n\n1. **Reach underinsured workers at a range of life stages via a cost-efficient distribution channel.**\n2. **Enhance voluntary offerings, protect profitability, and help employer clients respond to new and evolving market needs by being aware of changing demographics and risk factors.**\n3. **Provide the technological capabilities to make end-to-end processing as smooth and seamless as possible.**",
    "pricing": "The context does not provide any specific information about pricing structure or plans for Market Entry Strategy."
  }
}

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
    limit = request.args.get('limit', default=3, type=int)
    def generate():
        
        if products_cache["data"]:
            print("Returning cached products")
            for product in products_cache["data"][:limit]:
                yield f"data: {json.dumps(product)}\n\n"
            yield f"data: {json.dumps({'type': 'stop'})}\n\n"
            return

        # If cache is invalid or doesn't exist, proceed with the original logic
        # Step 1: Ask who the customer is
        customer_info_prompt = f"Who is {customer_name}? Provide a brief description of the company and its main business areas."
        customer_info_docs = products_retriever.get_relevant_documents(f"{customer_name} company and business areas")
        customer_info_context = "\n".join([doc.page_content for doc in customer_info_docs])
        
        customer_info_response = BEDROCK_CLIENT.converse(
            modelId="anthropic.claude-3-haiku-20240307-v1:0",
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
                            product_name = product["name"].lower().strip().replace(" ", "-")
                            if product_name not in processed_products:
                                # Extract link from metadata
                                metadata_link = doc.metadata.get('location', {}).get('webLocation', {}).get('url')
                                
                                # Use metadata link if available, otherwise use extracted link or default to "#"
                                product["external_link"] = metadata_link or product.get("link") or "#"
                                product["internal_link"] = f"/product/{product_name}"
                                # Ensure there's an icon, default to 'cube' if not provided
                                if not product.get("icon"):
                                    product["icon"] = "cube"
                                
                                products.append(product)
                                processed_products.add(product_name)
                                # print(f"Added product: {product_name} with link: {product['link']} and icon: {product['icon']}")
                                print(f"Product: {json.dumps(product, indent=2)}")
                                
                                # Yield the product immediately
                                yield f"data: {json.dumps(product)}\n\n"
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
        yield f"data: {json.dumps({'type': 'stop'})}\n\n"

    return Response(generate(), mimetype='text/event-stream')

@app.route('/product-details/<product_name>', methods=['GET'])
def get_product_details(product_name):
    print(f"Fetching details for product: {product_name}")

    def generate():
        if product_name in product_details_cache:
            print("Cache hit: Returning cached product details")
            product_details = product_details_cache[product_name]
            yield f"data: {json.dumps(product_details)}\n\n"
            yield f"data: {json.dumps({'type': 'stop'})}\n\n"
            return

        print("Cache miss: Generating product details")
        sections = [
            {"type": "overview", "prompt": f"Provide a brief, one paragraph overview of {product_name}."},
            {"type": "features", "prompt": f"List the key features of {product_name}."},
            {"type": "benefits", "prompt": f"Describe the main benefits of using {product_name}."},
            {"type": "pricing", "prompt": f"Explain the pricing structure or plans for {product_name}, if available."}
        ]

        product_details = {}

        for section in sections:
            # Convert product name to a friendly format
            friendly_product_name = ' '.join(word.capitalize() for word in product_name.split('-'))
            docs = products_retriever.get_relevant_documents(f"{friendly_product_name} {customer_name} {section['type']}")
            context = "\n\n".join([doc.metadata['location']['webLocation']['url'] + "\n\n" + doc.page_content for doc in docs])

            section_prompt = f"""
            Based on the following information about {friendly_product_name}, {section['prompt']}
            Use markdown formatting for better readability.
            If the information is not available in the context, state that it's not available.
            
            Context: {context}

            Do not include any framing language such as "According to the context" or "Here is an overview of" in your responses, just get straight to the point!
            """

            yield f"data: {json.dumps({'type': 'section_start', 'section': section['type']})}\n\n"

            response = BEDROCK_CLIENT.converse_stream(
                modelId="anthropic.claude-3-sonnet-20240229-v1:0",
                messages=[{"role": "user", "content": [{"text": section_prompt}]}],
                inferenceConfig={"maxTokens": 500, "temperature": 0, "topP": 1},
            )

            section_content = ""
            for chunk in response["stream"]:
                if "contentBlockDelta" in chunk:
                    text = chunk["contentBlockDelta"]["delta"]["text"]
                    section_content += text
                    yield f"data: {json.dumps({'type': 'content', 'section': section['type'], 'content': text})}\n\n"

            product_details[section['type']] = section_content
            yield f"data: {json.dumps({'type': 'section_end', 'section': section['type']})}\n\n"

        yield f"data: {json.dumps({'type': 'stop'})}\n\n"
        print("Updating product details cache")
        product_details_cache[product_name] = product_details

    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True)
