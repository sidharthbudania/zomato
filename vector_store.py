import json
import uuid
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer

api_key = "pcsk_74oKf6_AFP3V6cfT1xGabL1zJjUAx6fyK9qjm97as5izv64zj4yzHRmjPAG93FFy4bm7kb"
index_name = "zomato"

model = SentenceTransformer("all-MiniLM-L6-v2")
pc = Pinecone(api_key=api_key, environment="us-east-1")
index = pc.Index(index_name)

with open("restaurant_data.json", "r", encoding="utf-8") as f:
    restaurant_data = json.load(f)

def clean_text(text):
    return text.strip().replace("\n", " ").replace("\r", "").lower()

def process_data_and_upload_to_pinecone(data):
    vectors = []
    for item in data:
        desc = f"{item['names']} located at {item['address']}. Cuisine: {item['cuisine']}. Contact: {item.get('contact', '')}. Timing: {item.get('timing', '')}."
        embedding = model.encode([clean_text(desc)])[0]
        vectors.append({
            "id": str(uuid.uuid4()),
            "values": embedding.tolist(),
            "metadata": {
                "name": item["names"],
                "address": item["address"],
                "cuisine": item["cuisine"],
                "price": item["price for one"],
                "rating": item["ratings"],
                "timing": item.get("timing", ""),
                "contact": item.get("contact", ""),
                "image": item["images"],
                "url": item["links"]
            }
        })

    index.upsert(vectors=vectors)
    print(f"✅ Uploaded {len(vectors)} vectors to Pinecone!")

if __name__ == "__main__":
    process_data_and_upload_to_pinecone(restaurant_data)
