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
    db_connection = get_db_connection(username='root', host='localhost', password='Atk@8522', database='atliq_tshirts')

    
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
        query_log_data = cursor.fetchall()

        return query_log_data

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
        db = SQLDatabase.from_uri(mysql_uri)
    except Exception as e:
        print(f"Error reading query log: {e}")
    return db


def runQuery(query,db):
    return db.run(query) if db else "Please connect to database"


def getDatabaseSchema(db):
    return db.get_table_info() if db else "Please connect to database"




llm = ChatGoogleGenerativeAI(model="gemini-pro",api_key="AIzaSyDKAeomvp2rp8ICJ7IF0z8rTcZkDih8mog",verbose=True)




def getResponseForQueryResult(question, query, result, db):
    template2 = """below is the schema of MYSQL database, read the schema carefully about the table and column names of each table.
    Also look into the conversation if available
    Finally write a response in natural language by looking into the conversation and result.

    {schema}

    Here are some example for you:
    question: how many albums we have in database
    SQL query: SELECT COUNT(*) FROM album;
    Result : [(34,)]
    Response: There are 34 albums in the database.

    question: how many users we have in database
    SQL query: SELECT COUNT(*) FROM customer;
    Result : [(59,)]
    Response: There are 59 amazing users in the database.

    question: how many users above are from india we have in database
    SQL query: SELECT COUNT(*) FROM customer WHERE country=india;
    Result : [(4,)]
    Response: There are 4 amazing users in the database.

    your turn to write response in natural language from the given result :
    question: {question}
    SQL query : {query}
    Result : {result}
    Response:
    """

    prompt2 = ChatPromptTemplate.from_template(template2)
    chain2 = prompt2 | llm

    response = chain2.invoke({
        "question": question,
        "schema": getDatabaseSchema(db),
        "query": query,
        "result": result
    })

    return response.content


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

    # Get code-generated schema from the database
    code_generated_schema = getDatabaseSchema(db)

    human_generated_schema=read_human_schema() if not human_schema else human_schema

    # Combine schemas
    full_schema = f"{code_generated_schema}\n {human_generated_schema}"

    feedback_few_shots=get_human_feedback()

    few_shots=[
                {
                    "question": "how many albums we have in database ?",
                    "currect_sql_query": "SELECT COUNT(*) FROM album",
                    "wrong_query_previously_generated_by_you": "null"
                },
                {
                    "question": "how many customers are from Brazil in the database ?",
                    "currect_sql_query": "SELECT COUNT(*) FROM customer WHERE country='Brazil'",
                    "wrong_query_previously_generated_by_you": "null"
                }
    ]

    few_shots=few_shots+feedback_few_shots
    few_shots=convert_few_shots_to_string(few_shots)

    

    # Define the template
    template1 = """below is the schema of MYSQL database, read the schema carefully about the table and column names. Also take care of table or column name case sensitivity.
    Finally answer user's question in the form of SQL query.

    {schema}

    please only provide the SQL query and nothing else

    for example:
    """
    
    template2=few_shots

    template3="""
    your turn:
    question: {question}
    SQL query:
    please only provide the SQL query and nothing else
    """

    template=template1+template2+template3
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
        # mysql_uri = f"mysql+mysqlconnector://{username}:{password}@{host}:{port}/{database}"
        # db = SQLDatabase.from_uri(mysql_uri)

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
    

    
# def create_dataframe(result):
#     # Convert string to list
#     data=ast.literal_eval(result)

#     # Generate dynamic column names based on the number of columns in the data
#     num_columns = len(data[0])
#     columns = [str(i+1) for i in range(num_columns)]

#     # Create DataFrame
#     df = pd.DataFrame(data, columns=columns)

#     return df




db=connectDatabase(username='root', port='3306', host='localhost', password='Atk%408522', database='atliq_tshirts')

# username='root' 
# port='3306' 
# host='localhost' 
# password='Atk%408522' 
# database='atliq_tshirts'

# mysql_uri = f"mysql+mysqlconnector://{username}:{password}@{host}:{port}/{database}"
# db = SQLDatabase.from_uri(mysql_uri)



question='give me t-shirt and brand which have colour black'





# df=create_dataframe("[(1,2),(3,4),(5,6)]")



st.title("AtliQ T Shirts: Database Q&A 👕")




# File uploader for PDF files in the sidebar
uploaded_file = st.sidebar.file_uploader("Choose a PDF file", type="pdf")

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
    query,result=retry(question,db,human_schema)
    st.write(query)
    # st.write(result)
    data=ast.literal_eval(result)
    st.dataframe(data)



# display(df)

# response = getResponseForQueryResult(question, query, result, db)

# print (response)













