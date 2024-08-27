from flask import Flask, request, Response
from flask_cors import CORS
import os
import boto3
import json
from langchain_community.retrievers import AmazonKnowledgeBasesRetriever
from botocore.config import Config

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
    - Finally, you should use the following guidance to control the tone: {prompt_modifier}

Now read this context and answer the question at the bottom. 

Context: {context}

Question: "Hey {customer_name} Chatbot! {question}

A:
"""

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

if __name__ == '__main__':
    app.run(debug=True)
