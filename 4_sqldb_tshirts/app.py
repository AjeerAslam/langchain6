# import pandas as pd
import mysql.connector
from mysql.connector import Error
import ast
import streamlit as st
import PyPDF2


# Establishing database connection
def get_db_connection(username, host, password, database):
    try:
        connection = mysql.connector.connect(
            host=host,
            database=database,
            user=username,
            password=password
        )
        if connection.is_connected():
            print("Connected to MySQL database")
            return connection
        else:
            raise Exception("Failed to connect to database.")
    except Error as e:
        raise Exception("Failed to connect to database:{e}")

def get_human_feedback():

    # Establish the database connection using your existing function
    db_connection = get_db_connection(username='root', host='localhost', password='password', database='universitymanagement')

    
    try:

        # Create a cursor from the existing connection
        cursor = db_connection.cursor(dictionary=True)

        # Query to fetch the query log entries from the table
        query = """
        SELECT question, currect_query as currect_sql_query, model_query as wrong_query_previously_generated_by_you
        FROM human_feedback
        WHERE is_right='no'
        UNION ALL
        SELECT question, model_query as currect_sql_query, null as wrong_query_previously_generated_by_you
        FROM human_feedback
        WHERE is_right='yes'
        """
        
        cursor.execute(query)

        # Fetch all rows as a list of dictionaries
        feedback_fewshot = cursor.fetchall()

        return feedback_fewshot

    except Exception as e:
        print(f"Error reading query log: {e}")
        return []

    finally:
        # Close the cursor
        if cursor:
            cursor.close()




from langchain_community.utilities import SQLDatabase
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI


def connectDatabase(username, port, host, password, database):
    try:
        mysql_uri = f"mysql+mysqlconnector://{username}:{password}@{host}:{port}/{database}"
        connection = SQLDatabase.from_uri(mysql_uri)
    except Exception as e:
        print(f"Error reading query log: {e}")
    return connection


def runQuery(query,db):
    return db.run(query) if db else "Please connect to database"


def getDatabaseSchema(db):
    return db.get_table_info() if db else "Please connect to database"




llm = ChatGoogleGenerativeAI(model="gemini-pro",api_key="AIzaSyDKAeomvp2rp8ICJ7IF0z8rTcZkDih8mog",verbose=True)



def convert_few_shots_to_string(few_shots):
    result = ""
    for item in few_shots:
        result += f"question: {item['question']}\ncurrect_sql_query: {item['currect_sql_query']}\n\nwrong_query_previously_generated_by_you: {item['wrong_query_previously_generated_by_you']}\n"
    return result



def read_human_schema(file_name="human_schema.txt"):

    import os
    
    # Get the absolute path of the human_schema.txt file
    human_schema_file = os.path.join(os.getcwd(), file_name)

    # Initialize an empty string to store the content
    human_generated_schema = ""

    try:
        # Attempt to open and read the file
        with open(human_schema_file, 'r') as file:
            human_generated_schema = file.read()
    
    except FileNotFoundError:
        print(f"Error: The file '{human_schema_file}' was not found.")
    
    except Exception as e:
        print(f"Error reading file: {e}")

    return human_generated_schema


def getQueryFromLLM(question, db , human_schema = None):

    # Get code-generated schema from the database langchain
    code_generated_schema = getDatabaseSchema(db)

    human_generated_schema=read_human_schema() if not human_schema else human_schema
    # human_generated_schema=human_schema

    # Combine schemas
    full_schema = f"{code_generated_schema}\n {human_generated_schema}"

    feedback_few_shots=get_human_feedback()

    few_shots_explicit=[
                {
                    "question": "How many students are there in this college",
                    "currect_sql_query": "SELECT COUNT(*) FROM Students",
                    "wrong_query_previously_generated_by_you": "null"
                },
                {
                    "question": "How many professors belong to the Computer Science department?",
                    "currect_sql_query": "SELECT COUNT(*) FROM professors WHERE DepartmentID = 1",
                    "wrong_query_previously_generated_by_you": "null"
                }
    ]

    few_shots=few_shots_explicit+feedback_few_shots
    few_shots=convert_few_shots_to_string(few_shots)

    
    # prompt to model
    # Define the template
    schema_template = """below is the schema of MYSQL database, read the schema carefully about the table and column names. Also take care of table or column name case sensitivity.
    Finally answer user's question in the form of SQL query.

    {schema}

    please only provide the SQL query and nothing else

    for example:
    """
    
    few_shot_template=few_shots
    
    question_template="""
    your turn:
    question: {question}
    SQL query:
    please only provide the SQL query and nothing else
    """

    template=schema_template+few_shot_template+question_template
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | llm

    # Generate the query
    response = chain.invoke({
        "question": question,
        "schema": full_schema
    })
    return response.content






def retry(question,db=None,human_schema=None):
    try:
       

        query = getQueryFromLLM(question,db, human_schema)
        print(query,'query')

        # validate_query
        # query = validate_query(query,question,db)
        # print(query,'query2')

        result = runQuery(query, db)
        print(result)
        return query,result
        

    except:
        return retry(question,db)
    

    

db=connectDatabase(username='root', port='3306', host='localhost', password='password', database='universitymanagement')


st.title("College database: Chat Interface")


# File uploader for PDF files in the sidebar
# uploaded_file = st.sidebar.file_uploader("Choose a PDF file", type="pdf")
uploaded_file= None
human_schema = ""
if uploaded_file is not None:
    # Read the PDF file
    pdf_reader = PyPDF2.PdfReader(uploaded_file)
    num_pages = len(pdf_reader.pages)


    # Display the content of each page
    for page_num in range(num_pages):
        page = pdf_reader.pages[page_num]
        human_schema = page.extract_text()



question = st.text_input("Question: ")
if question:
    print(human_schema)
    query,result=retry(question,db,human_schema)
    st.write(query)
    # st.write(result)
    result_list=ast.literal_eval(result)
    
    st.dataframe(result_list)



