"""Python file to serve as the frontend"""
import streamlit as st
from streamlit_chat import message
import os
import json
import urllib.parse
from langchain.chains import ConversationChain
from langchain.llms import OpenAI
from aws_langchain.kendra_index_retriever import KendraIndexRetriever
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from streamlit.logger import get_logger

logger = get_logger(__name__)

logger.info('Hello world')
kendra_index_id = os.environ["KENDRA_INDEX_ID"]
aws_region = os.environ["AWS_REGION"]
logger.info("Kendra index id: " + kendra_index_id)
logger.info("AWS region: " + aws_region)
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
llm = OpenAI(temperature=0)
# chain = load_chain()


# Prompt template for internal data bot interface
template = """You are a talkative AI Retrieval Augmented knowledge bot who answers questions with only the data provided as context. You give lots of detail in your answers, and if the answer to the question is not present in the context section at the bottom, you say "I don't know".  

  Now read this context and answer the question at the bottom:
Context: "{context}"

Question: {question}
Answer:"""

PROMPT = PromptTemplate(
    template=template, input_variables=["context", "question"]
)

chain_type_kwargs = {"prompt": PROMPT}
qa = RetrievalQA.from_chain_type(
    llm,
    chain_type="stuff",
    retriever=retriever,
    chain_type_kwargs=chain_type_kwargs,
    return_source_documents=True,
)


# From here down is all the StreamLit UI.
st.set_page_config(page_title="7-Eleven ChatBot", page_icon="https://www.7-eleven.com/favicon/favicon-us.ico")
st.header("7-Eleven ChatBot")

if "generated" not in st.session_state:
    st.session_state["generated"] = []

if "past" not in st.session_state:
    st.session_state["past"] = []
def get_text():
    input_text = st.text_input(label="You: ", key="input")
    logger.info("Input text: " + input_text)
    return input_text
user_input = get_text()

if user_input:
    st.session_state.past.append(user_input)
    # output = chain.run(input=user_input)
    result = qa(user_input)
    if("I don't know" not in result["result"] and len(result['source_documents']) > 0):
        source_url = result['source_documents'][0].metadata['source']
        safe_source_url = urllib.parse.quote_plus(source_url)
        response_text = result["result"].strip() + "\n" + source_url
    else:
        response_text = "I don't know"
    logger.info("Response text: " + response_text)
    st.session_state.generated.append(response_text)



if st.session_state["generated"]:

    for i in range(len(st.session_state["generated"]) - 1, -1, -1):

        message(st.session_state["past"][i], is_user=True, key=str(i) + "_user")
        message(st.session_state["generated"][i], key=str(i), logo="https://images.contentstack.io/v3/assets/blt79dc99fad342cc45/bltaea3ad03c180ee64/633f08d845693810d212c437/7_Eleven_Horizontal_2022_RGB_thumb_1639377127_8824.png", avatar_style="no-avatar")










