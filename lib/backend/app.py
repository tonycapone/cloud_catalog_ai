from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import boto3
from langchain.prompts import PromptTemplate
from langchain.chains import ConversationalRetrievalChain
from langchain_aws import ChatBedrock
from langchain_community.retrievers import AmazonKnowledgeBasesRetriever
from botocore.config import Config

app = Flask(__name__)
CORS(app)

# Environment variables
aws_region = os.environ["AWS_REGION"]
customer_name = os.environ["CUSTOMER_NAME"]
knowledge_base_id = os.environ["KNOWLEDGE_BASE_ID"]

# AWS and LangChain setup
config = Config(retries={'max_attempts': 10, 'mode': 'adaptive'})
BEDROCK_CLIENT = boto3.client("bedrock-runtime", 'us-east-1', config=config)

llm = ChatBedrock(
    client=BEDROCK_CLIENT,
    model_id="anthropic.claude-3-sonnet-20240229-v1:0",
    model_kwargs={"temperature": 0},
    verbose=True,
)

retriever = AmazonKnowledgeBasesRetriever(
    knowledge_base_id=knowledge_base_id,
    retrieval_config={"vectorSearchConfiguration": {"numberOfResults": 4}},
)

# Prompt templates
template = """
Human: You are a helpful and talkative {customer_name} assistant that answers questions directly and only using the information provided in the context below. 
Guidance for answers:
    - Do not include any framing language such as "According to the context" in your responses, but rather act is if the information is coming from your memory banks. 
    - Simply answer the question clearly and with lots of detail using only the relevant details from the information below. If the context does not contain the answer, say "I don't know."
    - Use the royal "We" in your responses. 
    - Finally, you should use the following guidance to control the tone: {prompt_modifier}

Now read this context and answer the question at the bottom. 

Context: {context}"

Question: "Hey {customer_name} Chatbot! {question}

A:
According to the context provided,
"""

condensed_question_template = """Human: Given the following conversation and a follow up question, rephrase the follow up question to be a standalone question.

Chat History:
{chat_history}
Follow Up Input: {question}

A:
Standalone question:"""

CONDENSE_QUESTION_PROMPT = PromptTemplate.from_template(condensed_question_template)
PROMPT = PromptTemplate(template=template, input_variables=["context", "question", "customer_name", "prompt_modifier"])

qa = ConversationalRetrievalChain.from_llm(
    llm=llm, 
    retriever=retriever,
    return_source_documents=True,
    return_generated_question=True,
    condense_question_prompt=CONDENSE_QUESTION_PROMPT,
    verbose=True,
)

qa.combine_docs_chain.llm_chain.prompt = PROMPT

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    question = data['question']
    chat_history = data.get('chat_history', [])
    prompt_modifier = data.get('prompt_modifier', "Informative, empathetic, and friendly")

    result = qa({
        "question": question,
        "chat_history": chat_history,
        "customer_name": customer_name,
        "prompt_modifier": prompt_modifier
    })

    response_text = result["answer"].strip()
    sources = []
    for source in result['source_documents']:
        if source.metadata['location'] != "":
            url = source.metadata['location']['webLocation']['url']
            if url not in sources:
                sources.append(url)

    return jsonify({
        "answer": response_text,
        "sources": sources,
        "generated_question": result["generated_question"]
    })

if __name__ == '__main__':
    app.run(debug=True)
