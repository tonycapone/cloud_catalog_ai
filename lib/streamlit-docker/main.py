"""Python file to serve as the frontend"""
import streamlit as st
from streamlit_chat import message
import os
from langchain.llms import OpenAI
import boto3
import json
import base64
from aws_langchain.kendra_index_retriever import KendraIndexRetriever
from langchain.prompts import PromptTemplate
from langchain.chains import ConversationalRetrievalChain
from langchain.chains import RetrievalQA
from langchain.chains import LLMChain
from streamlit.logger import get_logger

logger = get_logger(__name__)

kendra_index_id = os.environ["KENDRA_INDEX_ID"]
aws_region = os.environ["AWS_REGION"]
customer_name = os.environ["CUSTOMER_NAME"]
favicon_url = os.environ["FAVICON_URL"] if "FAVICON_URL" in os.environ else None
chatbot_logo = os.environ["LOGO_URL"] if "LOGO_URL" in os.environ else None
bedrock_role = os.environ["BEDROCK_ASSUME_ROLE_ARN"] if "BEDROCK_ASSUME_ROLE_ARN" in os.environ else None

logger.info("Kendra index id: " + kendra_index_id)
logger.info("AWS region: " + aws_region)


# Kendra retriever
retriever = KendraIndexRetriever(
    kendraindex=kendra_index_id,
    awsregion=aws_region,
    return_source_documents=False
)

# Try Bedrock first then fall back to OpenAI
try: 
    bedrock_creds = boto3.client("sts").assume_role(
    RoleArn=bedrock_role,
    RoleSessionName="bedrock",)['Credentials']

    logger.info("Obtained Bedrock Temporary Credentials")
    from langchain.llms.bedrock import Bedrock
    BEDROCK_CLIENT = boto3.client("bedrock", 'us-east-1', 
                                aws_access_key_id=bedrock_creds["AccessKeyId"], 
                                aws_secret_access_key=bedrock_creds["SecretAccessKey"], 
                                aws_session_token=bedrock_creds["SessionToken"])
    llm = Bedrock(
        client=BEDROCK_CLIENT, 
        model_id="anthropic.claude-v1", 
        model_kwargs={"temperature":.3, "max_tokens_to_sample": 400}
    )
except:
    llm = OpenAI(temperature=0.3, openai_api_key=os.environ["OPENAI_API_KEY"])
    logger.info("Bedrock client not available. Using OpenAI")
st.set_page_config(page_title=customer_name+ " GenAI Demo", page_icon=favicon_url if favicon_url else ":robot:")
if chatbot_logo:
    st.image(chatbot_logo, width=100)

    st.subheader(customer_name + " GenAI Demo",)
assistant_tab, product_tab = st.tabs(["Assistant", "Product Ideator"])

with assistant_tab:
    # Prompt template for internal data bot interface
    template = """You are a helpful and talkative """ + customer_name + """ assistant that answers questions directly and only using the information provided in the context below. 
    Do not include any framing language such as "According to the context" in your responses. You should pretend as if you already know the answer to the question. 

    Simply answer the question clearly and with lots of detail using only the relevant details from the information below. If the context does not contain the answer, say "I don't know."
    I repeat DO NOT TALK ABOUT THE CONTEXT
    Now read this context and answer the question at the bottom. Make it fun and use emojis where appropriate.
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
        if("I apologize" not in result ["answer"] and "I don't know" not in result["answer"] and len(result['source_documents']) > 0):
            print(result['source_documents'])
            response_text = """
{}

You might find these links helpful:

""".format(result["answer"].strip())
            for source in result['source_documents']:
                if source.metadata['title'] not in response_text:
                    response_text += f"[\"{source.metadata['title']}\"]({source.metadata['source']})\n"
            
            logger.info(response_text)
            st.session_state["chat_history"].append((user_input, result["answer"]))
        else:
            response_text = "Sorry, I don't know the answer to that question."
        logger.info("Condensed query: " + result["generated_question"])
        logger.info("Response text: " + response_text)
        st.session_state.generated.append(f'{response_text}')
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

with product_tab:
    st.subheader("Product Ideator")
    st.write("Use this tool to generate product ideas. You can use the generated ideas to create a new product or to improve an existing one.")
    st.write("")

    def submit_product():
        st.session_state['product_idea_input'] = st.session_state['product_input']
        st.session_state['product_input'] = ""
            #{
  #"modelId": "stability.stable-diffusion-xl",
  #"contentType": "application/json",
  #"accept": "application/json",
  #"body": "{\"text_prompts\":[{\"text\":\"John Wick's Revenge Energy Drink - An ultra-caffeinated energy drink inspired by the high-octane action of the John Wick films. Each can contains extracts of exotic herbs and spices from around the globe, hand-selected by John Wick himself, to give you an energy boost for any dangerous mission. The sleek black can features the iconic \\\"Baba Yaga\\\" logo and a list of ingredients in multiple languages to reflect John Wick's international exploits. One sip of this and you'll be ready to take on the Russian mob, the Italian Camorra and anyone else who gets in your way. The perfect fuel for a night of revenge.\"}],\"cfg_scale\":10,\"seed\":0,\"steps\":50}"
#}
    product_template = """Generate an brand new innovative and interesting """ + customer_name + """ product idea description 
    based on the below product idea. Be creative and have fun!

    Product Idea: {idea}
    
    New Product Description: """

    PRODUCT_PROMPT = PromptTemplate(
        template=product_template, input_variables=["idea"]
    )
    chain_type_kwargs = {"prompt": PRODUCT_PROMPT, "stop_sequences": "You are a"}

    # retrieve_chain = RetrievalQA.from_llm(
    #     llm=llm, 
    #     retriever=retriever,  # ☜ DOCSEARCH
    #     verbose=True,
    #     prompt=PROMPT,
    #     # chain_type_kwargs=chain_type_kwargs
    # )
    # retrieve_chain.verbose = True

    product_chain = LLMChain(
        llm=llm, 
        verbose=True, 
        prompt=PRODUCT_PROMPT,
    )

    press_release_template = """
    Generate a press release for a new product from """ + customer_name + """ based on the below product description.
    {product_description}

    Press Release: """


    PRESS_RELEASE_PROMPT = PromptTemplate(
        template=press_release_template, input_variables=["product_description"]
    )


    press_release_chain = LLMChain(llm=llm, verbose=True, prompt=PRESS_RELEASE_PROMPT)


    if "product_idea_input" not in st.session_state:
        st.session_state["product_idea_input"] = ""
    if "product_description" not in st.session_state:
        st.session_state["product_description"] = ""
    if "press_release" not in st.session_state:
        st.session_state["press_release"] = ""

    st.text_input("What is your product idea?", key="product_input", value="", on_change=submit_product, placeholder="Enter your product here")

    if st.session_state["product_idea_input"]:
        product_description = product_chain(st.session_state["product_idea_input"])["text"]

        st.session_state["product_description"] = product_description

        st.write("")
        st.header("Product Description")
        st.write(st.session_state["product_description"])

        #{
  #"modelId": "stability.stable-diffusion-xl",
  #"contentType": "application/json",
  #"accept": "application/json",
  #"body": "{\"text_prompts\":[{\"text\":\"John Wick's Revenge Energy Drink - An ultra-caffeinated energy drink inspired by the high-octane action of the John Wick films. Each can contains extracts of exotic herbs and spices from around the globe, hand-selected by John Wick himself, to give you an energy boost for any dangerous mission. The sleek black can features the iconic \\\"Baba Yaga\\\" logo and a list of ingredients in multiple languages to reflect John Wick's international exploits. One sip of this and you'll be ready to take on the Russian mob, the Italian Camorra and anyone else who gets in your way. The perfect fuel for a night of revenge.\"}],\"cfg_scale\":10,\"seed\":0,\"steps\":50}"
#}
        image_response = BEDROCK_CLIENT.invoke_model(
            modelId="stability.stable-diffusion-xl",
            contentType="application/json",
            accept="application/json",
            body=json.dumps({
                "text_prompts": [
                    {
                        "text": st.session_state["product_description"]
                    }
                ],
                "cfg_scale": 10,
                "seed": 0,
                "steps": 50
            })
        )
        print(image_response)

        response_body = json.loads(image_response.get('body').read())

        image_bytes = response_body['artifacts'][0]["base64"]
        #save image locally
        with open("./image.png", "wb") as fh:
            fh.write(base64.decodebytes(image_bytes.encode()))
            fh.close()

        st.image("./image.png", use_column_width=True)
        st.write("")
        press_release = press_release_chain(st.session_state["product_description"])
        st.session_state["press_release"] = press_release["text"]
        st.header("Press Release")
        st.write (st.session_state["press_release"])
        st.session_state["product_idea_input"] = None







