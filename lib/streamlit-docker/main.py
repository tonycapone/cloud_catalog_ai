"""Python file to serve as the frontend"""
import streamlit as st
from streamlit_chat import message
import os
import urllib.parse
from langchain.llms import OpenAI
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
template = """You are a talkative and helpful AI Retrieval Augmented knowledge bot who answers questions with only the data provided as context. You give lots of detail in your answers, and if the answer to the question is not present in the context section at the bottom, you say "I don't know".  

Now read this context and answer the question at the bottom:
Context: "{context}"

Question: {question}
Answer:"""

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




