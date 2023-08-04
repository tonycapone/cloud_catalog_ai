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
from langchain.chains import LLMChain
from streamlit.logger import get_logger
import pandas as pd
from pandasql import sqldf
import re
from botocore.config import Config

logger = get_logger(__name__)

kendra_index_id = os.environ["KENDRA_INDEX_ID"]
aws_region = os.environ["AWS_REGION"]
customer_name = os.environ["CUSTOMER_NAME"]
favicon_url = os.environ["FAVICON_URL"] if "FAVICON_URL" in os.environ else None
chatbot_logo = os.environ["LOGO_URL"] if "LOGO_URL" in os.environ else None
bedrock_role = os.environ["BEDROCK_ASSUME_ROLE_ARN"] if "BEDROCK_ASSUME_ROLE_ARN" in os.environ else None
customer_industry = os.environ["CUSTOMER_INDUSTRY"] if "CUSTOMER_INDUSTRY" in os.environ else None

logger.info("Kendra index id: " + kendra_index_id)
logger.info("AWS region: " + aws_region)

code_whisperer = boto3
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
    RoleSessionName="bedrock")['Credentials']

    logger.info("Obtained Bedrock Temporary Credentials")
    from langchain.llms.bedrock import Bedrock
    config = Config(
        retries = {
      'max_attempts': 10,
      'mode': 'adaptive'
   }
)
    BEDROCK_CLIENT = boto3.client("bedrock", 'us-east-1', 
                                aws_access_key_id=bedrock_creds["AccessKeyId"], 
                                aws_secret_access_key=bedrock_creds["SecretAccessKey"], 
                                aws_session_token=bedrock_creds["SessionToken"],
                                config=config
                                )
    llm = Bedrock(
        client=BEDROCK_CLIENT, 
        model_id="anthropic.claude-v1", 
        model_kwargs={"temperature":.3, "max_tokens_to_sample": 1200 },
        verbose=True
    )
except:
    llm = OpenAI(temperature=0.3, openai_api_key=os.environ["OPENAI_API_KEY"])
    logger.info("Bedrock client not available. Using OpenAI")
st.set_page_config(page_title=customer_name+ " GenAI Demo", page_icon=favicon_url if favicon_url else ":robot:")
if chatbot_logo:
    st.image(chatbot_logo, width=100)

    st.subheader(customer_name + " GenAI Demo",)
assistant_tab, product_tab, query_tab = st.tabs(["Assistant", "Product Ideator", "Data Query"])

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
        user_input = st.session_state['input']
        st.session_state['input'] = ""

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
        product_description = product_chain(st.session_state["product_idea_input"])["text"]

        st.session_state["product_description"] = product_description
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
                    "steps": 40
                })
            )

        response_body = json.loads(image_response.get('body').read())

        image_bytes = response_body['artifacts'][0]["base64"]
        #save image locally
        with open("./image.png", "wb") as fh:
            fh.write(base64.decodebytes(image_bytes.encode()))
            fh.close()

    product_template = """Generate an brand new innovative, fun, and creative """ + customer_name + """ product idea description 
    based on the below product idea.  Be sure to format it in Markdown. Do not include any framing language, just the product description.

    Product Idea: {idea}
    
    New Product Description: """

    PRODUCT_PROMPT = PromptTemplate(
        template=product_template, input_variables=["idea"]
    )
    chain_type_kwargs = {"prompt": PRODUCT_PROMPT, "stop_sequences": "You are a"}

    product_chain = LLMChain(
        llm=llm, 
        verbose=True, 
        prompt=PRODUCT_PROMPT,
    )

    press_release_template = """
    Generate a 4 paragraph press release for a new product from """ + customer_name + """ based on the below product description and format it in Markdown
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
        prod_desc_tab, press_release_tab = st.tabs(["Product Description", "Press Release"])
        with prod_desc_tab:
            st.write("")
            
            st.image("./image.png", width=200)
                    
            st.write(st.session_state["product_description"])
        with press_release_tab:
            st.write("")
            press_release = press_release_chain(st.session_state["product_description"])
            st.session_state["press_release"] = press_release["text"]
            st.write (st.session_state["press_release"])


with query_tab:
    if "sql_query" not in st.session_state:
        st.session_state["sql_query"] = ""
    products_schema_template = """"
    Generate a basic database schema with exactly 5 columns for a database table containing a list of products or services from """ + customer_name +  """, who is in the """ + customer_industry + """ industry.
    Only generate the schema, no explanatory language please.  """

    json_template = """{schema}
    Generate a JSON array of exactly 10 products from """ + customer_name +  """, who is in the """ + customer_industry + """ industry, 
    in the above table, in JSON format. No explanatory language please.""" 

    sql_template = """
    Generate a SQLite compatible SELECT statement that queries the below table and achieves the following result 
    
    table: {schema}
    
    request {sql_request}
    No explanatory language please, just the SELECT query. DO NOT include any additional SQL statements, just the SELECT statement.

    sql query:
    """
    schema_prompt = PromptTemplate(
        template=products_schema_template, input_variables=[]
    )

    json_prompt = PromptTemplate(
        template=json_template, input_variables=["schema"], stop_sequences=["]"]
    )

    sql_prompt = PromptTemplate(
        template=sql_template, input_variables=["schema", "sql_request"], stop_sequences=[";"]
    )

    schema_chain = LLMChain(
        llm=llm,
        verbose=True,
        prompt=schema_prompt,
        llm_kwargs={"stop_sequences": ["Generate"]},
    )

    sql_chain = LLMChain(
        llm=llm, 
        verbose=True, 
        prompt=sql_prompt,
        llm_kwargs={'stop_sequences': [';', "Generate"]})
    json_chain = LLMChain(
        llm=llm, 
        verbose=True, 
        prompt=json_prompt,
        llm_kwargs={'stop_sequences': [']']})

    # @st.cache_data
    # def load_product_schema():
    #     print("loading schema")
    #     schema = schema_chain(inputs={})
    #     print("schema loaded")
    #     print(schema)
    #     return schema['text']
    
    @st.cache_data
    def load_product_list():
        products= json_chain(schema)["text"]
        print(products)
        products_table = json.loads(products + "]")
        return products_table
        
    schema = """
id INT PRIMARY KEY
name VARCHAR(50)
description TEXT
price DECIMAL(10,2)
category VARCHAR(20)
created_at DATETIME
available BOOLEAN
    """

    df = pd.DataFrame(st.session_state["products_table"])
    with st.expander("Data", expanded=False):
        st.table(df)
    def products_text_onchange():
        st.session_state["products_table"] = json.loads(st.session_state["products_text_input"])

    def submit_sql():
        sql_request = st.session_state["sql_request_input"]
        st.session_state["sql_request_input"] = ""
        sql_query = sql_chain.predict(schema=schema, sql_request=sql_request)
        # use a regex to replace the table name with 'df'
        sql_query = re.sub(r'(?<=FROM )\w+', 'df', sql_query, flags=re.IGNORECASE)
        logger.info(sql_query)
        st.session_state["sql_query"] = sql_query

    sql_request = st.text_input("Enter a question about the above data:", value="", on_change=submit_sql, key="sql_request_input", placeholder="Enter your SQL query here")
    if st.session_state["sql_query"]:
        st.subheader("SQL Query")
        st.write(st.session_state["sql_query"])
        st.write("")
        st.subheader("SQL Results")
        st.write(sqldf(st.session_state["sql_query"], globals()))    
    with st.expander("Debug", expanded=False):
        st.subheader("Schema")
        st.write(schema)
        st.subheader("Products")
        #format json for products table
        text = json.dumps(st.session_state["products_table"], indent=4)
        st.text_area(value=text, key="products_text_input", on_change=products_text_onchange, label="Products")
        st.write(st.session_state)


