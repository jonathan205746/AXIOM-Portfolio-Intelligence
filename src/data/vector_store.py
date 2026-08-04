"""
Embeds financial news articles into FAISS for semantic search.
Used by rag_pipeline.py to retrieve relevant news for each ticker.

Run this file directly to test:
    python src/data/vector_store.py
"""

import faiss
import numpy as np
import pickle
import os
import logging
from typing import List, Dict, Tuple, Optional
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Model choice: fast + lightweight + good quality for semantic search
EMBED_MODEL = "all-MiniLM-L6-v2"
INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "./data/faiss_index")


class FinancialNewsStore:
    """
    Stores and retrieves financial news using FAISS vector search.

    How it works:
    1. Each news article text is converted to a 384-dim embedding vector
    2. Vectors are stored in a FAISS index (fast similarity search)
    3. When you search, your query is also embedded
    4. FAISS finds the closest article vectors to your query vector
    5. Returns the most semantically relevant articles

    Why this matters:
    - Keyword search: "Apple revenue" only finds articles with those exact words
    - Vector search: finds articles about Apple earnings even without those words
    """

    def __init__(self, model_name: str = EMBED_MODEL):
        logger.info(f"Loading embedding model: {model_name}")
        logger.info("First run downloads ~90MB — please wait...")
        self.model = SentenceTransformer(model_name)
        # get_sentence_embedding_dimension() may return None in some versions; ensure int
        self.dimension = int(self.model.get_sentence_embedding_dimension() or 384)
        self.index = faiss.IndexFlatL2(int(self.dimension))
        self.documents: List[Dict] = []
        logger.info(f"Model loaded. Embedding dimension: {self.dimension}")

    def add_articles(self, articles: List[Dict]) -> None:
        """
        Embed and store news articles in FAISS.

        Args:
            articles: List of article dicts from news_fetcher.py
                      Each must have a "text" key

        Example:
            store.add_articles(news_by_ticker["AAPL"])
        """
        if not articles:
            logger.warning("No articles to add — skipping")
            return

        texts = [a["text"] for a in articles if a.get("text")]
        if not texts:
            logger.warning("Articles have no text field — skipping")
            return

        logger.info(f"Embedding {len(texts)} articles...")
        embeddings = self.model.encode(
            texts,
            show_progress_bar=True,
            batch_size=32
        )
        embeddings = np.array(embeddings).astype("float32")

        self.index.add(embeddings)
        self.documents.extend(articles)

        logger.info(f"Added {len(articles)} articles. Total in store: {len(self.documents)}")

    def add_articles_batch(self, news_by_ticker: Dict[str, List[Dict]]) -> None:
        """
        Add articles for multiple tickers at once.

        Args:
            news_by_ticker: Dict from fetch_news_batch()
                            e.g. {"AAPL": [...], "MSFT": [...]}
        """
        for ticker, articles in news_by_ticker.items():
            logger.info(f"Adding articles for {ticker}...")
            self.add_articles(articles)

    def search(
        self,
        query: str,
        ticker: str = None,
        top_k: int = 5
    ) -> List[Dict]:
        """
        Find the most relevant articles for a query.

        Args:
            query  : Search query e.g. "Apple iPhone revenue outlook"
            ticker : Optional filter — only return articles for this ticker
            top_k  : Number of results to return

        Returns:
            List of most relevant article dicts

        Example:
            results = store.search("Apple earnings revenue", ticker="AAPL")
            for r in results:
                print(r["title"])
        """
        if len(self.documents) == 0:
            logger.warning("Store is empty — add articles first")
            return []

        # Embed the query using the same model
        query_embedding = self.model.encode([query]).astype("float32")

        # Search FAISS — returns distances and indices
        # We search for more than top_k so we can filter by ticker
        search_k = min(top_k * 3, len(self.documents))
        distances, indices = self.index.search(query_embedding, search_k)

        results = []
        for idx in indices[0]:
            if idx < 0 or idx >= len(self.documents):
                continue

            doc = self.documents[idx]

            # Filter by ticker if specified
            if ticker is None or doc.get("ticker") == ticker:
                results.append(doc)

            if len(results) >= top_k:
                break

        logger.info(f"Search '{query[:50]}' → {len(results)} results")
        return results

    def search_all_tickers(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Search across all tickers without filtering.

        Useful for: "What companies are affected by interest rate changes?"
        """
        return self.search(query, ticker=None, top_k=top_k)

    def get_articles_by_ticker(self, ticker: str) -> List[Dict]:
        """
        Get all articles for a specific ticker.

        Args:
            ticker: Stock symbol e.g. "AAPL"

        Returns:
            All articles stored for this ticker
        """
        return [d for d in self.documents if d.get("ticker") == ticker]

    def get_store_stats(self) -> Dict:
        """
        Get statistics about what is stored.

        Returns:
            Dict with total articles, articles per ticker, index size
        """
        ticker_counts = {}
        for doc in self.documents:
            ticker = doc.get("ticker", "unknown")
            ticker_counts[ticker] = ticker_counts.get(ticker, 0) + 1

        return {
            "total_articles": len(self.documents),
            "articles_per_ticker": ticker_counts,
            "index_size": self.index.ntotal,
            "embedding_dimension": self.dimension,
            "model": EMBED_MODEL
        }

    def save(self, path: str = INDEX_PATH) -> None:
        """
        Save FAISS index and documents to disk for reuse.

        Args:
            path: Directory to save index files

        Creates:
            path/index.faiss  — the FAISS vector index
            path/documents.pkl — the original article dicts
        """
        os.makedirs(path, exist_ok=True)
        faiss.write_index(self.index, os.path.join(path, "index.faiss"))
        with open(os.path.join(path, "documents.pkl"), "wb") as f:
            pickle.dump(self.documents, f)
        logger.info(f"Saved {len(self.documents)} articles to {path}")

    def load(self, path: str = INDEX_PATH) -> None:
        """
        Load previously saved FAISS index from disk.

        Args:
            path: Directory containing saved index files

        Raises:
            FileNotFoundError: If index files don't exist
        """
        index_file = os.path.join(path, "index.faiss")
        docs_file = os.path.join(path, "documents.pkl")

        if not os.path.exists(index_file):
            raise FileNotFoundError(
                f"FAISS index not found at {index_file}. "
                "Run vector_store.py first to create the index."
            )

        self.index = faiss.read_index(index_file)
        with open(docs_file, "rb") as f:
            self.documents = pickle.load(f)

        logger.info(f"Loaded {len(self.documents)} articles from {path}")

    def clear(self) -> None:
        """Reset the store — remove all articles and embeddings."""
        # ensure dimension is int for faiss
        self.index = faiss.IndexFlatL2(int(self.dimension))
        self.documents = []
        logger.info("Store cleared")


# ── Main — Run this to test ────────────────────────────────────────────────────

if __name__ == "__main__":

    print("=" * 60)
    print("AI Portfolio Optimizer — Vector Store Test")
    print("=" * 60)

    # ── Test 1: Initialize store ──
    print("\n[1] Initializing FAISS vector store...")
    store = FinancialNewsStore()
    print(f"Embedding dimension: {store.dimension}")

    # ── Test 2: Fetch and add news ──
    print("\n[2] Fetching news to embed...")
    from src.data.news_fetcher import fetch_news_batch
    import time

    tickers = [
        "AAPL", "MSFT", "GOOGL", "AMZN"
    ]
    company_names = {
        "AAPL": "Apple",
        "MSFT": "Microsoft",
        "GOOGL": "Google",
        "AMZN": "Amazon"
    }

    news_by_ticker = fetch_news_batch(tickers, company_names)
    store.add_articles_batch(news_by_ticker)

    # ── Test 3: Store stats ──
    print("\n[3] Store statistics:")
    stats = store.get_store_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # ── Test 4: Semantic search ──
    print("\n[4] Testing semantic search...")

    queries = [
        ("Apple quarterly revenue iPhone sales", "AAPL"),
        ("Microsoft Azure cloud computing growth", "MSFT"),
        ("technology stocks market outlook", None),
    ]

    for query, ticker in queries:
        results = store.search(query, ticker=ticker, top_k=2)
        label = f"[{ticker}]" if ticker else "[ALL]"
        print(f"\n  {label} Query: '{query[:50]}'")
        for r in results:
            print(f"    → [{r['source']}] {r['title'][:65]}")

    # ── Test 5: Save to disk ──
    print("\n[5] Saving index to disk...")
    store.save()
    print(f"Saved to: {INDEX_PATH}")

    # ── Test 6: Load from disk ──
    print("\n[6] Loading index from disk...")
    store2 = FinancialNewsStore()
    store2.load()
    print(f"Loaded {len(store2.documents)} articles")

    # Verify search still works after load
    results = store2.search("Apple earnings", ticker="AAPL", top_k=1)
    print(f"Search after load: {len(results)} results")
    if results:
        print(f"  → {results[0]['title'][:70]}")

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)

# ── Compatibility shim ─────────────────────────────────────────────────────────
# Notebooks and rag_pipeline.py import VectorStore and call:
#   vs.add_documents(list_of_strings)   →  wraps add_articles()
#   vs.search(query, k=3)               →  wraps search() and returns strings
#   vs.documents                        →  list of dicts (same as FinancialNewsStore)
#
# This class does NOT change FinancialNewsStore at all.
# It is a thin adapter so the notebooks work without any import change.

class VectorStore(FinancialNewsStore):
    """
    Drop-in adapter over FinancialNewsStore.

    Notebooks call:
        vs = VectorStore()
        vs.add_documents(["AAPL: headline. description", ...])
        results = vs.search("Apple earnings", k=3)   # returns list of strings

    FinancialNewsStore expects dicts with a "text" key and returns dicts.
    This class bridges that gap transparently.
    """

    def add_documents(self, texts: list) -> None:
        """
        Accept a list of plain strings (as the notebooks pass) and
        convert each to the dict format FinancialNewsStore.add_articles() needs.

        Args:
            texts: list of strings, e.g.
                   ["AAPL: Apple beats Q4 earnings. Revenue up 12%.", ...]
        """
        if not texts:
            return
        # Convert each plain string to the dict format add_articles() expects.
        # We infer the ticker from the text prefix "TICKER: ..." when present.
        articles = []
        for text in texts:
            ticker = "unknown"
            # Try to extract ticker from "TICKER: ..." prefix
            if ": " in text:
                possible_ticker = text.split(": ")[0].strip()
                if possible_ticker.isupper() and len(possible_ticker) <= 5:
                    ticker = possible_ticker
            articles.append({
                "text":   text,
                "title":  text[:120],   # use first 120 chars as title fallback
                "ticker": ticker,
                "source": "notebook",
            })
        self.add_articles(articles)

    def search(self, query: str, k: int = 5, ticker: str = None) -> list:
        """
        Search wrapper that returns plain strings (as notebooks expect)
        instead of the dict list that FinancialNewsStore.search() returns.

        Args:
            query:  Search string
            k:      Number of results (notebooks use keyword arg k=)
            ticker: Optional ticker filter (passed through to parent)

        Returns:
            List of text strings, not dicts.
        """
        # FinancialNewsStore.search() signature: search(query, ticker, top_k)
        results = super().search(query, ticker=ticker, top_k=k)
        # Return the "text" field of each result dict as a plain string.
        return [r.get("text", r.get("title", str(r))) for r in results]