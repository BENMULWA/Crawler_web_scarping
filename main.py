from fastapi import FastAPI, HTTPException
from pymongo import MongoClient, DESCENDING

app = FastAPI(title="FX Rates API", version="1.0")

# Mongo connection (same one you use)
client = MongoClient(
    "mongodb+srv://scrapy-selenium:benard9507@cluster0.xad7ngd.mongodb.net/?retryWrites=true&w=majority"
)

db = client["Currency_ratesDB_Crawler"]
collection = db["CrawlerBot_Scraping data"]


@app.get("/fx/latest")
def get_latest_rates():
    doc = collection.find_one(sort=[("_id", DESCENDING)])

    if not doc:
        raise HTTPException(status_code=404, detail="No FX data found")

    doc.pop("_id")  # optional: hide internal id
    return doc


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


@app.get("/fx/run/{run_id}")
def get_run(run_id: str):
    doc = collection.find_one({"_id": run_id})

    if not doc:
        raise HTTPException(status_code=404, detail="Run not found")

    return doc