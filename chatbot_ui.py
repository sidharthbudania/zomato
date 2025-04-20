import os
os.environ["TRANSFORMERS_NO_TF"] = "1"
import gradio as gr
import pandas as pd
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone, ServerlessSpec
from transformers import pipeline
from spellchecker import SpellChecker

embed_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
generator = pipeline("text2text-generation", model="google/flan-t5-large")
spell = SpellChecker()

pc = Pinecone(api_key="pcsk_6g2xEN_D9LVKCQgFYtrVorReLXaRBfFgLm4YbNVLzyndYfQ5Vs7ZabKbJxt62SVZEoujB3")
index_name = "zomato"


if index_name not in pc.list_indexes().names():
    pc.create_index(
        name=index_name,
        dimension=384,
        metric="euclidean",
        spec=ServerlessSpec(
            cloud="aws",
            region="us-east-1"
        )
    )

index = pc.Index(index_name)
conversation_history = []

def clean_input(text):
    words = text.lower().split()
    corrected = [spell.correction(word) or word for word in words]
    return " ".join(corrected)

def is_low_info_query(query):
    return query.strip().lower() in [
        "no", "yes", "yeah", "okay", "hmm", "a restaurant", "some restaurant", "something else",
        "restaurant", "any restaurant", "just a restaurant", "not sure", "any"
    ] or len(query.strip()) <= 3

def get_default_restaurant():
    return {
        "name": "The Spicy Bowl",
        "cuisine": "Andhra, Biryani, Chinese",
        "price": "150",
        "address": "MVP Colony, Vizag"
    }

def retrieve_similar_docs(query, top_k=5):
    query_vector = embed_model.encode(query).tolist()
    result = index.query(vector=query_vector, top_k=top_k, include_metadata=True)
    return result['matches']

def generate_response(context, query):
    prompt = f"""You are a helpful assistant that recommends restaurants in Vizag. The user may ask casually or vaguely, so use your best judgment and always suggest something useful.

Context:
{context}

User: {query}
Assistant:"""
    result = generator(prompt, max_length=200, do_sample=True)
    answer = result[0]['generated_text'].strip()
    if not answer or "i don't know" in answer.lower():
        fallback = get_default_restaurant()
        return f"You could try {fallback['name']}! They serve {fallback['cuisine']} at ₹{fallback['price']} in {fallback['address']}."
    return answer

def generate_rag_response(query):
    cleaned_query = clean_input(query)

    if is_low_info_query(cleaned_query):
        fallback = get_default_restaurant()
        return f"You could try {fallback['name']}! They offer {fallback['cuisine']} at ₹{fallback['price']} in {fallback['address']}."

    retrieved_docs = retrieve_similar_docs(cleaned_query)
    if not retrieved_docs:
        fallback = get_default_restaurant()
        return f"Hmm, I couldn't find anything specific. But you could check out {fallback['name']}, known for {fallback['cuisine']} in {fallback['address']}."

    context = "\n".join([
        f"{doc['metadata'].get('name', 'Unnamed')}: {doc['metadata'].get('cuisine', '')}, ₹{doc['metadata'].get('price', '')}, rated {doc['metadata'].get('ratings', 'N/A')} at {doc['metadata'].get('address', '')}"
        for doc in retrieved_docs
    ])
    return generate_response(context, cleaned_query)

def update_conversation(user_msg, bot_msg):
    conversation_history.append({"user": user_msg, "bot": bot_msg})
    if len(conversation_history) > 5:
        conversation_history.pop(0)

def rag_chatbot(query, chat_history):
    response = generate_rag_response(query)
    chat_history.append({"role": "user", "content": query})
    chat_history.append({"role": "assistant", "content": response})
    update_conversation(query, response)
    return chat_history, chat_history

def load_restaurant_data():
    try:
        results = index.query(vector=[0.0] * 384, top_k=100, include_metadata=True)
        rows = []
        for item in results['matches']:
            meta = item.get('metadata', {})
            rows.append({
                "Name": meta.get("name", ""),
                "Cuisine": meta.get("cuisine", ""),
                "Price for One": meta.get("price", ""),
                "Ratings": meta.get("ratings", ""),
                "Address": meta.get("address", "")
            })
        return pd.DataFrame(rows)
    except Exception:
        return pd.DataFrame()

with gr.Blocks(title="Restaurant Info Chatbot") as demo:
    gr.Markdown("## Restaurant Info Chatbot with RAG")
    gr.Markdown("Chat with the bot about restaurants. Data powered by web scraping and retrieval-augmented generation.")

    with gr.Tab("Chatbot"):
        chatbot = gr.Chatbot(type="messages")
        msg = gr.Textbox(placeholder="Ask about restaurants...", label="Your question")
        clear = gr.Button("Clear Chat")
        state = gr.State([])

        def clear_history():
            return [], []

        msg.submit(rag_chatbot, [msg, state], [chatbot, state])
        clear.click(fn=clear_history, outputs=[chatbot, state])

        gr.Examples(
            examples=[
                "Where can I get biryani near MVP Colony?",
                "Any dessert places in Siripuram?",
                "Suggest something good under 200",
                "Best North Indian in Vizag?",
                "Cheap pizza place around Waltair Uplands"
            ],
            inputs=[msg]
        )

    with gr.Tab("View Restaurant Data"):
        gr.Markdown("Scraped restaurant data:")
        gr.Dataframe(load_restaurant_data(), interactive=False)

demo.launch()
