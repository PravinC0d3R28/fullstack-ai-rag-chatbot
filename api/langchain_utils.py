from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from typing import List
from langchain_core.documents import Document
import os
from chroma_utils import vectorstore
retriever = vectorstore.as_retriever(search_kwargs={"k": 2})

output_parser = StrOutputParser()

# Set up prompts and chains
contextualize_q_system_prompt = (
    "Given a chat history and the latest user question "
    "which might reference context in the chat history, "
    "formulate a standalone question which can be understood "
    "without the chat history. Do NOT answer the question, "
    "just reformulate it if needed and otherwise return it as is."
)

contextualize_q_prompt = ChatPromptTemplate.from_messages([
    ("system", contextualize_q_system_prompt),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])


qa_prompt = ChatPromptTemplate.from_messages([
    # Define the chatbot's role and purpose
("system", 
     """You are an support chatbot for student assistance designed for Manipal University Jaipur.
     Your role is to assist students, parents, and stakeholders with queries about admissions, 
     fees, scholarships, curriculum, placements, and general college-related information based on given context. 
     Your responses should be truthful, non-offensive, and strictly based on the provided knowledge base. 
     Instructions:
     1. Think as if the context is only your information you know.
     2. If the question is out of your knowledge base, respond with "I'm sorry, I don't have that information at the moment."
     3. If the question is not related to college, respond with "I'm sorry, I can only provide you college related information."
     4. Answer to each query should be short and concise without extra bluff.
     5. When a user asks a question, respond based on the provided context. 
        If additional clarification is required, ask concise follow-up questions.
     6. For complex queries, break your response into short, easily understandable points.
     7. Avoid making assumptions or providing information beyond the given context.
     8. Usually you will be catering to Indian users so for admissions, scholarships, and fees-related queries, use structured tabular responses with relevant details (e.g., dates, amounts, links).
     9. For curriculum or placement-related queries, provide insights based on the provided data and avoid opinions.
     10. Always reference past user queries from the conversation history if relevant.
     """),
    ("system", "Here is the Context that might contain data you need to answer the human input: {context}. Here is the chat history for your reference: "),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "Here is the question you need to answer: {input}")
])



def get_rag_chain(model="llama-3.1-8b-instant"):
    if model=="mistral":
        llm = ChatOllama(model="mistral")
    else:
        llm = ChatGroq(model=model)
    history_aware_retriever = create_history_aware_retriever(llm, retriever, contextualize_q_prompt)
    print(history_aware_retriever)
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
    print(question_answer_chain)
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)    
    return rag_chain
