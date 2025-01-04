

from langchain_community.utilities import SQLDatabase
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
import streamlit as st
import ast
import PyPDF2
from streamlit_javascript import st_javascript



def connectDatabase(username, port, host, password, database):
    mysql_uri = f"mysql+mysqlconnector://{username}:{password}@{host}:{port}/{database}"
    db = SQLDatabase.from_uri(mysql_uri)
    return db


def runQuery(query,db):
    return db.run(query) if db else "Please connect to database"


def getDatabaseSchema(db):
    return db.get_table_info() if db else "Please connect to database"


llm = ChatGoogleGenerativeAI(model="gemini-pro",api_key="AIzaSyDKAeomvp2rp8ICJ7IF0z8rTcZkDih8mog")



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

def convert_few_shots_to_string(few_shots):
    result = ""
    for item in few_shots:
        result += f"question: {item['question']}\ncurrect_sql_query: {item['currect_sql_query']}\n\nwrong_query_previously_generated_by_you: {item['wrong_query_previously_generated_by_you']}\n"
    return result


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

def getQueryFromLLM(question, db , human_schema = None):

    # Get code-generated schema from the database
    code_generated_schema = getDatabaseSchema(db)

    human_generated_schema=read_human_schema() 
    # human_generated_schema=human_schema

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

import mysql.connector
from mysql.connector import Error
from langchain_community.utilities import SQLDatabase

def connectDatabase(username, port, host, password, database):
    mysql_uri = f"mysql+mysqlconnector://{username}:{password}@{host}:{port}/{database}"
    db = SQLDatabase.from_uri(mysql_uri)
    return db

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
        

# Function to get the model's query based on the question
def get_query_from_model(question, model):
    # Assume `model` is an object with a `generate_query` method
    query = model.generate_query(question)
    return query

# Function to log the query based on user feedback
def insert_human_feedback(connection, question, model_query, is_right, currect_query=None, error_description=None):
    try:
        cursor = connection.cursor()
        
        # SQL query to insert the data
        insert_query = """
        INSERT INTO human_feedback (question, model_query, is_right, currect_query, error_description)
        VALUES (%s, %s, %s, %s, %s)
        """
        
        # Values to insert
        values = (question, model_query, is_right, currect_query, error_description if error_description else None)
        
        # Execute the query
        cursor.execute(insert_query, values)
        connection.commit()
        st.write("human_feedback inserted successfully.")
    
    except Error as e:
        st.write(f"Error: {e}")
    
    finally:
        cursor.close()

def get_input_feedback():
    is_right = st.text_input("Is the model output correct? (yes/no):  ").strip().lower()

    if is_right:

        # Step 3: If wrong, capture explanation
        currect_qry = None
        error_description = None
        if is_right == 'no':
            currect_qry = st.text_input("Enter the currect query: ")
            if currect_qry:
                error_description = st.text_input("Why is the model output wrong? Please provide explanation:  ")
                if error_description:
                    return is_right, currect_qry, error_description
    return is_right, None, None

    

# # Function to capture user feedback and log data
# def capture_feedback_and_log(question, db_connection, db_langchain):

#     # Step 1: Get the query from the model
#     query = getQueryFromLLM(question,db_langchain)
#     print(f"Model generated query: {query}")

#     # Step 2: Ask user if the output is correct
#     is_right = input("Is the model output correct? (yes/no): ").strip().lower()

#     # Step 3: If wrong, capture explanation
#     error_description = None
#     if is_right == 'no':
#         error_description = input("Why is the model output wrong? Please provide explanation: ")

#     # Step 4: Insert data into database
#     insert_human_feedback(db_connection, question, query, is_right, error_description)
def clear_session_state():
    for key in st.session_state.keys():
        del st.session_state[key]

def refresh_browser():
    clear_session_state()
    st.components.v1.html("""
        <script>
            window.location.reload();
        </script>
    """, height=0)
    

# Main function to set up the interaction
def main():

    # Get database connection
    db_connection = get_db_connection(username='root', host='localhost', password='Atk@8522', database='atliq_tshirts')
    print("Connected to db_connection.")

    if not db_connection:
        print("Failed to connect to the database. Exiting.")
        return

    db_langchain=connectDatabase(username='root', port='3306', host='localhost', password='Atk%408522', database='atliq_tshirts')
    print("Connected to db_langchain.")

    if not db_langchain:
        print("Failed to connect to the database. Exiting.")
        return

    
    question = st.text_input("Enter your question:  ")
    if question:
        # if question.lower() == 'exit':
        #     break

        # Step 1: Get the query from the model
        model_query = getQueryFromLLM(question,db_langchain)
        st.write(f"Model generated query: {model_query}")

        # Step 2: Ask user if the output is correct
        is_right, currect_qry, error_description = get_input_feedback()

        if is_right:
            # Step 4: Insert data into database
            if is_right == 'yes':
                insert_human_feedback(db_connection, question, model_query, is_right, currect_qry, error_description)
            else:
                if currect_qry and error_description:
                    insert_human_feedback(db_connection, question, model_query, is_right, currect_qry, error_description)


        

            # Close the database connection
            if db_connection:
                db_connection.close()
                print("MySQL connection closed.")



st.title("Train the Model with Human Feedback")




# File uploader for PDF files in the sidebar
if st.sidebar.button("Give more feedback"):
    refresh_browser()
# uploaded_file = st.sidebar.file_uploader("Choose a PDF file", type="pdf")

# human_schema = ""
# if uploaded_file is not None:
#     # Read the PDF file
#     pdf_reader = PyPDF2.PdfReader(uploaded_file)
#     num_pages = len(pdf_reader.pages)


#     # Display the content of each page
#     for page_num in range(num_pages):
#         page = pdf_reader.pages[page_num]
#         human_schema = page.extract_text()


main()


# query,result=retry(question,db,human_schema)
# st.write(query)
# # st.write(result)
# data=ast.literal_eval(result)
# st.dataframe(data)



