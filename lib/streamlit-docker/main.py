"""Python file to serve as the frontend"""
import streamlit as st
from streamlit_chat import message
import os
import urllib.parse
from langchain.llms import OpenAI
import boto3
import json
from aws_langchain.kendra_index_retriever import KendraIndexRetriever
from langchain.prompts import PromptTemplate
from langchain.chains import ConversationalRetrievalChain
from streamlit.logger import get_logger

logger = get_logger(__name__)

kendra_index_id = os.environ["KENDRA_INDEX_ID"]
aws_region = os.environ["AWS_REGION"]
customer_name = os.environ["CUSTOMER_NAME"]
favicon_url = os.environ["FAVICON_URL"] if "FAVICON_URL" in os.environ else None
chatbot_logo = os.environ["LOGO_URL"] if "LOGO_URL" in os.environ else None

logger.info("Kendra index id: " + kendra_index_id)
logger.info("AWS region: " + aws_region)
secrets_manager = boto3.client("secretsmanager", region_name=aws_region)
bedrock_creds = boto3.client("sts").assume_role(
    RoleArn="arn:aws:iam::444931483884:role/central-bedrock-access",
    RoleSessionName="bedrock",
)['Credentials']
print(bedrock_creds)

# Kendra retriever
retriever = KendraIndexRetriever(
    kendraindex=kendra_index_id,
    awsregion=aws_region,
    return_source_documents=False
)



# def load_chain():
#     """Logic for loading the chain you want to use should go here."""
#     llm = OpenAI(temperature=0)
#     chain = ConversationChain(llm=llm)
#     return chain
# llm = OpenAI(temperature=0)
# chain = load_chain()

from langchain.llms.bedrock import Bedrock
BEDROCK_CLIENT = boto3.client("bedrock", 'us-east-1', 
                              aws_access_key_id=bedrock_creds["AccessKeyId"], 
                              aws_secret_access_key=bedrock_creds["SecretAccessKey"], 
                              aws_session_token=bedrock_creds["SessionToken"])
llm = Bedrock(
    client=BEDROCK_CLIENT, model_id="anthropic.claude-v1", model_kwargs={"temperature":.3, "max_tokens_to_sample": 300}
)

# Prompt template for internal data bot interface
template = """You are  helpful and talkative """ + customer_name + """ assistant that answers questions directly and only using the information provided in the context below. 
Do not include any framing language such as "According to the context" in your responses. You should pretend as if you already know the answer to the question. 

Simply answer the question clearly and with lots of detail using only the relevant details from the information below. If the context does not contain the answer, say "I don't know."
I repeat DO NOT TALK ABOUT THE CONTEXT
Now read this context and answer the question at the bottom:
Context: {context}"

Question: "Hey """ + customer_name + """ Chatbot! {question}
Answer: """

condensed_question_template = """Given the following conversation and a follow up question, rephrase the follow up question to be a standalone question.

Chat History:
{chat_history}
Follow Up Input: {question}
Standalone question:"""
CONDENSE_QUESTION_PROMPT = PromptTemplate.from_template(condensed_question_template)

PROMPT = PromptTemplate(
    template=template, input_variables=["context", "question"]
)
st.set_page_config(page_title=customer_name+ " ChatBot", page_icon=favicon_url if favicon_url else ":robot:")

if chatbot_logo:
    st.image(chatbot_logo, width=100)

st.subheader(customer_name + " ChatBot",)




chain_type_kwargs = {"prompt": PROMPT}
qa = ConversationalRetrievalChain.from_llm(
    llm=llm, 
    retriever=retriever,  # ☜ DOCSEARCH
    return_source_documents=True,        # ☜ CITATIONS
    return_generated_question=True,          # ☜ ANSWER
    condense_question_prompt=CONDENSE_QUESTION_PROMPT,
    verbose=True,



)

qa.combine_docs_chain.llm_chain.prompt = PROMPT

# From here down is all the StreamLit UI.
# if favicon_url is defined, use it

if "generated" not in st.session_state:
    st.session_state["generated"] = []

if "past" not in st.session_state:
    st.session_state["past"] = []

if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

def submit():
    st.session_state['user_input'] = st.session_state['input']
    st.session_state['input'] = ""





user_input = st.session_state['user_input'] if 'user_input' in st.session_state else None

if user_input:
    st.session_state.past.append(user_input)
    # output = chain.run(input=user_input)
    result = qa({"question":user_input, "chat_history": st.session_state["chat_history"]})
    logger.info(result)
    if("I don't know" not in result["answer"] and len(result['source_documents']) > 0):
        source_url = result['source_documents'][0].metadata['source']
        safe_source_url = urllib.parse.quote_plus(source_url)
        response_text = result["answer"].strip() + "\n" + source_url
        # chat_history = [(user_input, result["answer"])]
        # st.session_state["chat_history"].append((user_input, result["answer"]+ "Source Document Text: " + result['source_documents'][0].page_content))
        st.session_state["chat_history"].append((user_input, result["answer"]))
    else:
        response_text = "Sorry, I don't know the answer to that question."
    logger.info("Condensed query: " + result["generated_question"])
    logger.info("Response text: " + response_text)
    st.session_state.generated.append(response_text)
    st.session_state.condensed_query = result["generated_question"]
    #remove old chat history older than 2 messages
    if len(st.session_state["chat_history"]) > 2:
        st.session_state["chat_history"].pop(0)







if st.session_state["generated"]:
    for i in range(len(st.session_state["generated"]) - 1, -1, -1):
        index = len(st.session_state["generated"]) - i - 1
        message(st.session_state["past"][index], is_user=True, key=str(index) + "_user")
        message(st.session_state["generated"][index], key=str(index), logo=chatbot_logo, avatar_style="no-avatar")



st.text_input(label="You: ", key="input", value="", on_change=submit, placeholder="Ask a question!", )
st.write("")
st.write("")
st.write("")
st.write("")
st.write("")
st.write("")
st.write("")
st.write("")
with st.expander("Debug", expanded=False):
    st.write(st.session_state)
    st.text_input(label="access_key_id", key="access_key_id", value="", placeholder="access_key_id")
    st.text_input(label="secret_key", key="secret_key", value="", placeholder="secret_key")
    st.text_input(label="session_token", key="session_token", value="", placeholder="session_token")





