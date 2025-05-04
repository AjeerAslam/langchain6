from langchain_community.utilities import SQLDatabase
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
import streamlit as st
import ast
import PyPDF2
import mysql.connector
from mysql.connector import Error

# Function to establish a database connection
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
        raise Exception(f"Failed to connect to database: {e}")

# Function to connect to the database using SQLDatabase
def connectDatabase(username, port, host, password, database):
    try:
        mysql_uri = f"mysql+mysqlconnector://{username}:{password}@{host}:{port}/{database}"
        db = SQLDatabase.from_uri(mysql_uri)
        return db
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

# Function to execute a query on the local database
def run_local_db(query):
    db_connection = get_db_connection(username='root', host='localhost', password='password', database='universitymanagement')
    try:
        cursor = db_connection.cursor(dictionary=True)
        cursor.execute(query)
        result = cursor.fetchall()
        return result
    except Exception as e:
        return f"Error executing query: {e}"
    finally:
        if cursor:
            cursor.close()
        if db_connection:
            db_connection.close()

# Function to get the database schema
def getDatabaseSchema(db):
    return db.get_table_info() if db else "Please connect to database"

# Initialize the LLM model
llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro-latest", api_key="AIzaSyDKAeomvp2rp8ICJ7IF0z8rTcZkDih8mog")

# Function to read the human-generated schema from a file
def read_human_schema(file_name="human_schema.txt"):
    import os
    human_schema_file = os.path.join(os.getcwd(), file_name)
    human_generated_schema = ""
    try:
        with open(human_schema_file, 'r') as file:
            human_generated_schema = file.read()
    except FileNotFoundError:
        print(f"Error: The file '{human_schema_file}' was not found.")
    except Exception as e:
        print(f"Error reading file: {e}")
    return human_generated_schema

# Function to convert few-shot examples to a string
def convert_few_shots_to_string(few_shots):
    result = ""
    for item in few_shots:
        result += f"question: {item['question']}\ncurrect_sql_query: {item['currect_sql_query']}\n\nwrong_query_previously_generated_by_you: {item['wrong_query_previously_generated_by_you']}\n"
    return result

# Function to get human feedback from the database
def get_human_feedback():
    db_connection = get_db_connection(username='root', host='localhost', password='password', database='universitymanagement')
    try:
        cursor = db_connection.cursor(dictionary=True)
        query = """
        SELECT question, currect_query as currect_sql_query, model_query as wrong_query_previously_generated_by_you
        FROM human_feedback_backup
        WHERE is_right='no'
        UNION ALL
        SELECT question, model_query as currect_sql_query, null as wrong_query_previously_generated_by_you
        FROM human_feedback_backup
        WHERE is_right='yes'
        """
        cursor.execute(query)
        query_log_data = cursor.fetchall()
        return query_log_data
    except Exception as e:
        print(f"Error reading query log: {e}")
        return []
    finally:
        if cursor:
            cursor.close()

# Function to generate an SQL query using the LLM
def getQueryFromLLM(question, db, human_schema=None):
    code_generated_schema = getDatabaseSchema(db)
    human_generated_schema = read_human_schema() if not human_schema else human_schema
    full_schema = f"{code_generated_schema}\n {human_generated_schema}"
    feedback_few_shots = get_human_feedback()
    few_shots = [
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
    few_shots = few_shots + feedback_few_shots
    few_shots = convert_few_shots_to_string(few_shots)
    template1 = """below is the schema of MYSQL database, read the schema carefully about the table and column names. Also take care of table or column name case sensitivity.
    Finally answer user's question in the form of SQL query.

    {schema}

    please only provide the SQL query and nothing else

    for example:
    """
    template2 = few_shots
    template3 = """
    your turn:
    question: {question}
    SQL query:
    please only provide the SQL query and nothing else
    """
    template = template1 + template2 + template3
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | llm
    response = chain.invoke({
        "question": question,
        "schema": full_schema
    })
    return response.content

# Function to insert human feedback into the database
def insert_human_feedback(connection, question, model_query, is_right, currect_query=None, error_description=None):
    try:
        cursor = connection.cursor()
        insert_query = """
        INSERT INTO human_feedback_backup (question, model_query, is_right, currect_query, error_description)
        VALUES (%s, %s, %s, %s, %s)
        """
        values = (question, model_query, is_right, currect_query, error_description if error_description else None)
        cursor.execute(insert_query, values)
        connection.commit()
        st.write("human_feedback inserted successfully.")
    except Error as e:
        st.write(f"Error: {e}")
    finally:
        cursor.close()

# Function to get user feedback on the query
def get_input_feedback():
    is_right = st.text_input("Is the model output correct? (yes/no):  ").strip().lower()
    if is_right:
        correct_qry = None
        error_description = None
        if is_right == 'no':
            correct_qry = st.text_input("Enter the correct query: ")
            if correct_qry:
                error_description = st.text_input("Why is the model output wrong? Please provide explanation:  ")
                if error_description:
                    return is_right, correct_qry, error_description
    return is_right, None, None

# Function to clear session state
def clear_session_state():
    for key in st.session_state.keys():
        del st.session_state[key]

# Function to refresh the browser
def refresh_browser():
    clear_session_state()
    st.components.v1.html("""
        <script>
            window.location.reload();
        </script>
    """, height=0)

# Function to get accuracy history
# def get_accuracy_history():
#     try:
#         db_connection = get_db_connection(username='root', host='localhost', password='password', database='universitymanagement')
#         cursor = db_connection.cursor(dictionary=True)
#         query = """
#         SELECT created_at, is_right 
#         FROM human_feedback 
#         ORDER BY created_at DESC 
#         LIMIT 30;
#         """
#         cursor.execute(query)
#         feedback_data = cursor.fetchall()
#         accuracy_history = []
#         correct_count = 0
#         for i, feedback in enumerate(feedback_data):
#             if feedback['is_right'] == 'yes':
#                 correct_count += 1
#             accuracy_history.append((correct_count / (i + 1)) * 100)
#         return accuracy_history
#     except Exception as e:
#         print(f"Error reading query log: {e}")
#         return []
#     finally:
#         if cursor:
#             cursor.close()
#         if db_connection:
#             db_connection.close()

# Function to get current accuracy
def get_accuracy():
    try:
        db_connection = get_db_connection(username='root', host='localhost', password='password', database='universitymanagement')
        cursor = db_connection.cursor(dictionary=True)
        query = """        
        SELECT (cnt/30)*100 AS accuracy FROM (
            SELECT COUNT(*) AS cnt FROM (
                SELECT * 
                FROM universitymanagement.human_feedback_backup
                ORDER BY created_at DESC 
                LIMIT 30
            ) latest WHERE is_right='yes'
        ) acc;
        """
        cursor.execute(query)
        query_log_data = cursor.fetchall()
        return query_log_data[0]['accuracy'] if query_log_data else 0
    except Exception as e:
        print(f"Error reading query log: {e}")
        return 0
    finally:
        if cursor:
            cursor.close()
        if db_connection:
            db_connection.close()

# Main function to set up the interaction
def main(human_schema=None):
    db_connection = get_db_connection(username='root', host='localhost', password='password', database='universitymanagement')
    print("Connected to db_connection.")
    if not db_connection:
        print("Failed to connect to the database. Exiting.")
        return

    db_langchain = connectDatabase(username='root', port='3306', host='localhost', password='password', database='universitymanagement')
    print("Connected to db_langchain.")
    if not db_langchain:
        print("Failed to connect to the database. Exiting.")
        return

    question = st.text_input("Enter your question:  ")
    if question:
        model_query = getQueryFromLLM(question, db_langchain, human_schema)
        st.write(f"Model generated query: {model_query}")

        # Remove triple backticks and "sql" prefix if present
        if model_query.startswith("```sql"):
            model_query = model_query.replace("```sql", "").replace("```", "").strip()

        # Execute the query and display the result
        result = run_local_db(model_query)
        st.write("Query Result:")
        if isinstance(result, str) and "Error" in result:
            st.write(result)
        else:
            try:
                result_list = ast.literal_eval(str(result))
                st.dataframe(result_list)
            except (ValueError, SyntaxError):
                st.write("The query result could not be parsed. Raw output:")
                st.write(result)

        # Ask for user feedback
        is_right, correct_qry, error_description = get_input_feedback()
        if is_right:
            if is_right == 'yes':
                insert_human_feedback(db_connection, question, model_query, is_right, correct_qry, error_description)
            else:
                if correct_qry and error_description:
                    insert_human_feedback(db_connection, question, model_query, is_right, correct_qry, error_description)

            if db_connection:
                db_connection.close()
                print("MySQL connection closed.")

# Streamlit app
st.title("Train the Model with Human Feedback")

accuracy = get_accuracy()
st.write("Accuracy = " + str(accuracy) + "%")

# File uploader for PDF files in the sidebar
uploaded_file = st.sidebar.file_uploader("Choose a PDF file", type="pdf")
human_schema = ""
if uploaded_file is not None:
    pdf_reader = PyPDF2.PdfReader(uploaded_file)
    num_pages = len(pdf_reader.pages)
    for page_num in range(num_pages):
        page = pdf_reader.pages[page_num]
        human_schema = page.extract_text()

main(human_schema)