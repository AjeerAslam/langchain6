import mysql.connector
from mysql.connector import Error
import ast
import streamlit as st
import PyPDF2
from langchain_community.utilities import SQLDatabase
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
import re
import os

# Try to import sqlparse with fallback
# try:
#     import sqlparse
#     from sqlparse.sql import IdentifierList, Identifier, Where, Comparison
#     from sqlparse.tokens import Keyword, DML, Name
#     SQLPARSE_AVAILABLE = True
# except ImportError:
#     SQLPARSE_AVAILABLE = False
#     st.warning("SQL parsing features limited - install sqlparse with: pip install sqlparse")

# --- Your existing database connection functions ---
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

# --- Add the new query analysis functions here ---


# def check_syntax_errors(query):
#     """Check for basic SQL syntax errors"""
#     if not SQLPARSE_AVAILABLE:
#         # Simple regex check as fallback
#         return bool(re.match(r'^\s*SELECT\s+.+\s+FROM\s+.+', query, re.IGNORECASE))
    
#     try:
#         parsed = sqlparse.parse(query)
#         return bool(parsed and len(parsed) > 0)
#     except Exception:
#         return False

# def validate_table_columns(query, db_schema):
#     """Check if tables and columns mentioned in query exist in schema"""
#     if not SQLPARSE_AVAILABLE:
#         return True  # Skip validation if sqlparse not available
    
#     try:
#         parsed = sqlparse.parse(query)[0]
#         tables_in_query = set()
#         columns_in_query = set()
        
#         # Extract tables and columns from query
#         for token in parsed.tokens:
#             if isinstance(token, Identifier):
#                 parts = [p.value for p in token.flatten() if p.ttype is Name]
#                 if len(parts) > 1:
#                     tables_in_query.add(parts[0])
#                     columns_in_query.add(parts[-1])
#                 else:
#                     columns_in_query.add(parts[0])
        
#         # Check against schema (simplified check)
#         schema_str = str(db_schema).lower()
#         missing_tables = [t for t in tables_in_query if t.lower() not in schema_str]
#         missing_columns = [c for c in columns_in_query if c.lower() not in schema_str]
        
#         return not (missing_tables or missing_columns)
#     except Exception as e:
#         print(f"Error validating tables/columns: {e}")
#         return True  # Assume valid if validation fails

# def calculate_query_accuracy(query, db_schema):
#     """Calculate overall query accuracy score (0-1)"""
#     if not check_syntax_errors(query):
#         return 0.0
    
    
#     schema_score = 1.0 if validate_table_columns(query, db_schema) else 0.5
    
#     # Weighted average
#     accuracy = (schema_score * 0.4)
#     return round(accuracy, 2)

# --- Then continue with your existing functions ---


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
        feedback_fewshot = cursor.fetchall()
        return feedback_fewshot
    except Exception as e:
        print(f"Error reading query log: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if db_connection:
            db_connection.close()

def connectDatabase(username, port, host, password, database):
    try:
        mysql_uri = f"mysql+mysqlconnector://{username}:{password}@{host}:{port}/{database}"
        connection = SQLDatabase.from_uri(mysql_uri)
        return connection
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

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

def getDatabaseSchema(db):
    return db.get_table_info() if db else "Please connect to database"

llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro-latest", api_key="AIzaSyDKAeomvp2rp8ICJ7IF0z8rTcZkDih8mog", verbose=True)

def convert_few_shots_to_string(few_shots):
    result = ""
    for item in few_shots:
        result += f"question: {item['question']}\ncurrect_sql_query: {item['currect_sql_query']}\n\nwrong_query_previously_generated_by_you: {item['wrong_query_previously_generated_by_you']}\n"
    return result

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



def getQueryFromLLM(question, db, human_schema=None):
    code_generated_schema = getDatabaseSchema(db)
    human_generated_schema = read_human_schema() if not human_schema else human_schema
    full_schema = f"{code_generated_schema}\n {human_generated_schema}"

    feedback_few_shots = get_human_feedback()
    few_shots_explicit = [
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

    few_shots = few_shots_explicit + feedback_few_shots
    few_shots = convert_few_shots_to_string(few_shots)

    schema_template = """below is the schema of MYSQL database, read the schema carefully about the table and column names. Also take care of table or column name case sensitivity.
    Finally answer user's question in the form of SQL query.

    {schema}

    please only provide the SQL query and nothing else

    for example:
    """
    
    few_shot_template = few_shots
    
    question_template = """
    your turn:
    question: {question}
    SQL query:
    please only provide the SQL query and nothing else
    """

    template = schema_template + few_shot_template + question_template
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | llm

    response = chain.invoke({
        "question": question,
        "schema": full_schema
    })
    return response.content

def retry(question, db=None, human_schema=None):
    try:
        query = getQueryFromLLM(question, db, human_schema)
        print(query, 'query')

        if query.startswith("```sql"):
            query = query.replace("```sql", "").replace("```", "").strip()

        result = run_local_db(query)
        print(result, 'result')

        return query, result
    except Exception as e:
        print(f"Error: {e}")
        return retry(question, db)


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

# Connect to the database
db = connectDatabase(username='root', port='3306', host='localhost', password='password', database='universitymanagement')

# Streamlit app
st.title("College database: Chat Interface")

accuracy = get_accuracy()
st.write("Model accuracy = " + str(accuracy) + "%")
# File uploader for PDF files in the sidebar
uploaded_file = st.sidebar.file_uploader("Upload a PDF file for human schema", type="pdf")
human_schema = ""

if uploaded_file is not None:
    pdf_reader = PyPDF2.PdfReader(uploaded_file)
    num_pages = len(pdf_reader.pages)

    for page_num in range(num_pages):
        page = pdf_reader.pages[page_num]
        human_schema += page.extract_text()

# Input question
question = st.text_input("Question: ")

if question:
    query, result = retry(question, db, human_schema)
    st.write("Generated Query:", query)

    if isinstance(result, str) and "Error" in result:
        st.write("Query Execution Error:")
        st.write(result)
        st.write("Query Accuracy: 0% (query failed to execute)")
    else:
        try:
            result_list = ast.literal_eval(str(result))
            st.dataframe(result_list)
            
            # Calculate and display query accuracy
            # db_schema = getDatabaseSchema(db)
            # accuracy = calculate_query_accuracy(query, db_schema)
            # st.write(f"Query Accuracy: {accuracy * 100:.0f}%")
            
            # Display detailed feedback
            # with st.expander("Accuracy Breakdown"):
            
            #     st.write("**Schema Validation:**", "✅ Passed" if validate_table_columns(query, db_schema) else "❌ Failed")
            #     st.write("**Syntax Check:**", "✅ Valid" if check_syntax_errors(query) else "❌ Invalid")
                
        except (ValueError, SyntaxError):
            st.write("The query result could not be parsed. Raw output:")
            st.write(result)
            st.write("Query Accuracy: 0% (result parsing failed)")