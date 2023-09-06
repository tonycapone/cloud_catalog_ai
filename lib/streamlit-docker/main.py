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
    print(BEDROCK_CLIENT.list_foundation_models())
    llm = Bedrock(
        client=BEDROCK_CLIENT, 
        model_id="anthropic.claude-v1", 
        model_kwargs={"temperature":.3, "max_tokens_to_sample": 1200 },
        verbose=True
    )
except:
    llm = OpenAI(temperature=0.3, openai_api_key=os.environ["OPENAI_API_KEY"])
    logger.info("Bedrock client not available. Using OpenAI")
st.set_page_config(
    page_title=customer_name+ " GenAI Demo", 
    page_icon=favicon_url if favicon_url else ":robot:",
    initial_sidebar_state='collapsed')
if chatbot_logo:
    st.image(chatbot_logo, width=100)

    st.subheader(customer_name + " GenAI Demo",)
assistant_tab, product_tab, query_tab = st.tabs(["Assistant", "Product Ideator", "Data Query"])

with assistant_tab:
    st.caption("A conversational chat assistant showing off the capabilities of Amazon Bedrock and Retrieval-Augmented-Generation (RAG)")
    if "generated" not in st.session_state:
        st.session_state["generated"] = []

    if "past" not in st.session_state:
        st.session_state["past"] = []

    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []
    if "prompt_modifier" not in st.session_state:
        st.session_state["prompt_modifier"] = "Informative, empathetic, and friendly"
    def handle_prompt_modifier_input():
        st.session_state["prompt_modifier"] = st.session_state["prompt_modifier_input"]

    with st.sidebar:
        st.header("Chatbot Prompt Engineering")
        st.text_area("Prompt Modifier", value=st.session_state['prompt_modifier'], key="prompt_modifier_input", on_change=handle_prompt_modifier_input)
        st.caption("The Prompt Modifier describes the tone of the assistant, i.e. 'Informative, empathetic, and friendly'")


    # Prompt template for internal data bot interface
    template = """You are a helpful and talkative """ + customer_name + """ assistant that answers questions directly and only using the information provided in the context below. 
    Do not include any framing language such as "According to the context" in your responses, but rather act is if the information is coming from your memory banks. 

    Simply answer the question clearly and with lots of detail using only the relevant details from the information below. If the context does not contain the answer, say "I don't know."
    I repeat DO NOT TALK ABOUT THE CONTEXT

    Finally, you should use the following guidance to control the tone: """ + st.session_state["prompt_modifier"] + """
    Now read this context and answer the question at the bottom. 

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
                    if source.metadata['title'] != "":
                        if source.metadata['title'] not in response_text:
                            response_text += f"[\"{source.metadata['title']}\"]({source.metadata['source']})\n"
                    else:
                        if source.metadata['source'] not in response_text:
                            response_text += f"[\"{source.metadata['source']}\"]({source.metadata['source']})\n"
                
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
    st.caption("Use this tool to generate product ideas. You can use the generated ideas to create a new product or to improve an existing one.")
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
    junction_schema_template = """
    Generate a database schema for a junction table called "junction_table" containg the ids for the below tables. Assume the ids for both tables are integers 0-9
    {table1}
    {table2}
    """

    products_schema_template = """"
    Generate a basic database schema for exactly 1 table called "{schema_type}_table" with exactly 5 columns for a database table containing a list of {schema_type} from """ + customer_name +  """, who is in the """ + customer_industry + """ industry.
    Only generate the schema, no explanatory language please.  
    CREATE TABLE"""

    json_template = """{schema}
    Generate a JSON array of exactly 10 items from the above table. The items should resemble something that would belong to """ + customer_name +  """, who is in the """ + customer_industry + """ industry, 
    Print it in JSON format The ids should number 0-9. No explanatory language please.
    [""" 

    junction_item_template = """{schema}
    Generate a JSON array of from a junction table with exactly 20 items from """ + customer_name +  """, who is in the """ + customer_industry + """ industry,
    in the above table, in JSON format. The ids will be numbered 0-9, Be sure to use a combination of ids from both tables. No explanatory language, just the JSON.
    ["""


    sql_template = """
    Generate a SQLite compatible SELECT statement that queries the below tables and achieves the following result. Be sure to alias any columns that are identifical. 
    
    tables: 
    {table1}
    {table2}
    {table3}

    
    request {sql_request}
    No explanatory language please, just the SELECT query. DO NOT include any additional SQL statements, just the SELECT statement.

    sql query:
    """

    explanation_template = """
    Answer the below question directly with the results from the SQL query below in plain English. Do not include any SQL tables or queries in your answer. Just plain english. 
    Question: {question}
    Query Result: {query_result}
    Answer: """

    schema_prompt = PromptTemplate(
        template=products_schema_template, input_variables=["schema_type"]
    )

    json_prompt = PromptTemplate(
        template=json_template, input_variables=["schema"], stop_sequences=["]"]
    )

    sql_prompt = PromptTemplate(
        template=sql_template, input_variables=["table1", "table2", "table3", "sql_request"]
    )
    junction_schema_prompt = PromptTemplate(
        template=junction_schema_template, input_variables=["table1", "table2"]
    )
    junction_item_prompt = PromptTemplate(
        template=junction_item_template, input_variables=["schema"]
    )
    explanation_prompt = PromptTemplate(
        template=explanation_template, input_variables=["question", "query_result"]
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
    
    junction_schema_chain = LLMChain(
        llm=llm,
        verbose=True,
        prompt=junction_schema_prompt,
        llm_kwargs={"stop_sequences": ["Generate"]})
    junction_item_chain = LLMChain(
        llm=llm,
        verbose=True,
        prompt=junction_item_prompt,
        llm_kwargs={"stop_sequences": ["]", "Generate"]})
    explanation_chain = LLMChain(
        llm=llm,
        verbose=True,
        prompt=explanation_prompt,
        llm_kwargs={"stop_sequences": ["Generate"]})

    
    @st.cache_data
    def load_product_schema():
        print("loading schema")
        schema = schema_chain(inputs={"schema_type":"products"})
        print("schema loaded")
        print(schema)
        return schema['text']
    
    if "product_schema" not in st.session_state:
        st.session_state["product_schema"] = load_product_schema()

    @st.cache_data
    def load_product_list():
        products= json_chain(st.session_state['product_schema'])["text"]
        print(products)
        products_table = json.loads("["+products + "]")
        return products_table
    @st.cache_data
    def load_customers_schema():
        print("loading schema")
        schema = schema_chain(inputs={"schema_type":"customers"})
        print("schema loaded")
        print(schema)
        return schema['text']
    @st.cache_data
    def load_customers_list():
        customers= json_chain(st.session_state['customers_schema'])["text"]
        print(customers)
        customers_table = json.loads("["+customers + "]")
        return customers_table
    @st.cache_data
    def load_junction_schema():
        print("loading schema")
        schema = junction_schema_chain(inputs={"table1":"products", "table2":"customers"})
        print("schema loaded")
        print(schema)
        return schema['text']
    @st.cache_data
    def load_junction_table():
        junction_table= junction_item_chain(st.session_state['junction_schema'])["text"]
        print(junction_table)
        junction_table = json.loads("[" + junction_table + "]")
        return junction_table

    if "products_table" not in st.session_state:
        st.session_state["products_table"] = load_product_list()
    if "customers_schema" not in st.session_state:
        st.session_state["customers_schema"] = load_customers_schema()
    if "customers_table" not in st.session_state:
        st.session_state["customers_table"] = load_customers_list()
    if "junction_schema" not in st.session_state:
        st.session_state["junction_schema"] = load_junction_schema()
    if "junction_table" not in st.session_state:
        st.session_state["junction_table"] = load_junction_table()
    if "question" not in st.session_state:
        st.session_state["question"] = ""

    products_table = pd.DataFrame(st.session_state["products_table"])
    customers_table = pd.DataFrame(st.session_state["customers_table"])
    junction_table = pd.DataFrame(st.session_state["junction_table"])

    st.code(st.session_state["customers_schema"])
    st.code(st.session_state["product_schema"])

    with st.expander("Data", expanded=False):
        st.table(products_table)
        st.table(customers_table)
        st.table(junction_table)
    
    def products_text_onchange():
        st.session_state["products_table"] = json.loads(st.session_state["products_text_input"])
    def customers_text_onchange():
        st.session_state["customers_table"] = json.loads(st.session_state["customers_text_input"])
    def junction_text_onchange():
        st.session_state["junction_table"] = json.loads(st.session_state["junction_text_input"])

    def submit_sql():
        sql_request = st.session_state["sql_request_input"]
        st.session_state["question"] = sql_request
        #clear the text input so that subsequent actions don't retrigger the onchange
        st.session_state["sql_request_input"] = ""
        sql_query = sql_chain.predict(table1=st.session_state["product_schema"], 
                                      table2=st.session_state["customers_schema"], 
                                      table3=st.session_state["junction_schema"], 
                                      sql_request=sql_request)
        # use a regex to replace the table name with 'df'
        # sql_query = re.sub(r'(?<=FROM )\w+', 'df', sql_query, flags=re.IGNORECASE)
        logger.info(sql_query)
        st.session_state["sql_query"] = sql_query

    sql_request = st.text_input("Enter a question about the above data:", value="", on_change=submit_sql, key="sql_request_input", placeholder="Enter your query here")
    if st.session_state["sql_query"]:
        st.subheader("Question")
        st.write(st.session_state["question"])
        with st.expander("SQL Query", expanded=False):
            st.subheader("SQL Query")
            st.write(st.session_state["sql_query"])
            st.write("")
        with st.expander("SQL Results", expanded=False):
            st.subheader("SQL Results")
            query_result = sqldf(st.session_state["sql_query"], globals())
            st.write(query_result)    
        st.subheader("Answer")
        answer = explanation_chain(inputs={"question":st.session_state["question"], "query_result":query_result.to_dict(orient="records")})
        st.text(answer["text"])
    with st.expander("Debug", expanded=False):
        st.subheader("Schema")
        st.write(st.session_state["product_schema"])
        st.subheader("Products")
        #format json for products table
        products = json.dumps(st.session_state["products_table"], indent=4)
        st.text_area(value=products, key="products_text_input", on_change=products_text_onchange, label="Products")
        st.subheader("Customers")
        customers = json.dumps(st.session_state["customers_table"], indent=4)
        st.text_area(value=customers, key="customers_text_input", on_change=customers_text_onchange, label="Customers")
        st.subheader("Junction")
        junction = json.dumps(st.session_state["junction_table"], indent=4)
        st.text_area(value=junction, key="junction_text_input", on_change=junction_text_onchange, label="Junction")
        st.subheader("Session State")
        st.write(st.session_state)


