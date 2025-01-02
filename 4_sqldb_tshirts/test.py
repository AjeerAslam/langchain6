from langchain_community.utilities import SQLDatabase
import app

username='root' 
port='3306' 
host='localhost' 
password='Atk%408522' 
database='atliq_tshirts'

mysql_uri = f"mysql+mysqlconnector://{username}:{password}@{host}:{port}/{database}"
db = SQLDatabase.from_uri(mysql_uri)

# question='give me t-shirt and brand which have colour black'

# query,result=app.retry(question,db)



# df=app.create_dataframe(result)

import streamlit as st

st.title("AtliQ T Shirts: Database Q&A 👕")

question = st.text_input("Question: ")


