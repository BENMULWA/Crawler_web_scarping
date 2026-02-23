from fastapi import FastAPI, HTTPException
from pymongo import MongoClient, DESCENDING
from dotenv import load_dotenv
import os

app = FastAPI(title="FX Rates API", version="1.0")

# Mongo connection to setch the latest FX rates from the database.

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")  
client = MongoClient(MONGO_URI)

db = client["Currency_ratesDB_Crawler"]
collection = db["CrawlerBot_Scraping data"]


# firsst api to fetch all the latest fx rates in the database.
@app.get("/fx_rate/latest")
def get_latest_rates():
    doc = collection.find_one(sort=[("_id", DESCENDING)])

    if not doc:
        raise HTTPException(status_code=404, detail="No FX data found")

    doc.pop("_id")  # optional: hide internal id
    return doc

#2nd api to fetch the latest fx rates for a specific base currency.

@app.get("/fx/latest/{base}")
def get_latest_base(base: str):
    base = base.upper()

    doc = collection.find_one(sort=[("_id", DESCENDING)])
    if not doc or base not in doc:
        raise HTTPException(status_code=404, detail="Currency not found")

    return {
        "base": base,
        "rates": doc[base]
    }

# 3rd api to fetch a specific run of fx rates by its unique id (timestamp-based).
@app.get("/fx/run/{run_id}")
def get_run(run_id: str):
    doc = collection.find_one({"_id": run_id})

    if not doc:
        raise HTTPException(status_code=404, detail="Run not found")

    return doc