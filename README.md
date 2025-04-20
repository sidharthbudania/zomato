# zomato


This project collects restaurant data from Zomato using Selenium, extracts key information like name, location, cuisine, rating, and contact details, and uploads that data to Pinecone as vector embeddings for semantic search and retrieval.

---

## Requirements

Make sure you have Python installed. Then install all required packages:

```bash
pip install -r requirements.txt
```

Dependencies include:

- selenium
- beautifulsoup4
- pandas
- sentence-transformers
- pinecone-client

## Project Structure

```
.
├── chatbot_ui.py
├── locscraper.py  
├── scraper.py          
├── vector_store.py     
├── restaurant_data.json      
├── restaurant_data.csv       
├── requirements.txt          
└── README.md                 
```


