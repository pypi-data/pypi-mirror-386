# MOSS - Minimal On-Device Semantic Search

`inferedge-moss` enables **private, on-device semantic search** in your Python applications with cloud storage capabilities.

Built for developers who want **instant, memory-efficient, privacy-first AI features** with seamless cloud integration.

## ✨ Features

- ⚡ **On-Device Vector Search** - Sub-millisecond retrieval with zero network latency
- 🔍 **Semantic Search & Hybrid Search** - Beyond keyword matching
- ☁️ **Cloud Storage Integration** - Automatic index synchronization with cloud storage
- 📦 **Multi-Index Support** - Manage multiple isolated search spaces
- 🛡️ **Privacy-First by Design** - Computation happens locally, only indexes sync to cloud
- 🚀 **High-Performance Rust Core** - Built on optimized Rust bindings for maximum speed

## 📦 Installation

```bash
pip install inferedge-moss
```

## 🚀 Quick Start

```python
import asyncio
from inferedge_moss import MossClient, DocumentInfo

async def main():
    # Initialize search client with project credentials
    client = MossClient("your-project-id", "your-project-key")

    # Prepare documents to index
    documents = [
        DocumentInfo(
            id="doc1",
            text="How do I track my order? You can track your order by logging into your account.",
            metadata={"category": "shipping"}
        ),
        DocumentInfo(
            id="doc2", 
            text="What is your return policy? We offer a 30-day return policy for most items.",
            metadata={"category": "returns"}
        ),
        DocumentInfo(
            id="doc3",
            text="How can I change my shipping address? Contact our customer service team.",
            metadata={"category": "support"}
        )
    ]

    # Create an index with documents (syncs to cloud)
    index_name = "faqs"
    await client.create_index(index_name, documents, "moss-minilm")
    print("Index created and synced to cloud!")

    # Load the index (from cloud or local cache)
    await client.load_index(index_name)

    # Search the index
    result = await client.query(
        index_name,
        "How do I return a damaged product?",
        3  # top 3 results
    )

    # Display results
    print(f"Query: {result.query}")
    for doc in result.docs:
        print(f"Score: {doc.score:.4f}")
        print(f"ID: {doc.id}")
        print(f"Text: {doc.text}")
        print("---")

asyncio.run(main())
```

## 🔥 Example Use Cases

- Smart knowledge base search with cloud backup
- Realtime Voice AI agents with persistent indexes
- Personal note-taking search with sync across devices
- Private in-app AI features with cloud storage
- Local semantic search in edge devices with cloud fallback

## Available Models

- `moss-minilm`: Lightweight model optimized for speed and efficiency
- `moss-mediumlm`: Balanced model offering higher accuracy with reasonable performance

## 🔧 Getting Started

### Prerequisites

- Python 3.8 or higher
- Valid InferEdge project credentials

### Environment Setup

1. **Install the package:**

```bash
pip install inferedge-moss
```

2. **Get your credentials:**

Sign up at [InferEdge Platform](https://platform.inferedge.dev) to get your `project_id` and `project_key`.

3. **Set up environment variables (optional):**

```bash
export MOSS_PROJECT_ID="your-project-id"
export MOSS_PROJECT_KEY="your-project-key"
```

### Basic Usage

```python
import asyncio
from inferedge_moss import MossClient, DocumentInfo

async def main():
    # Initialize client
    client = MossClient("your-project-id", "your-project-key")
    
    # Create and populate an index
    documents = [
        DocumentInfo(id="1", text="Python is a programming language"),
        DocumentInfo(id="2", text="Machine learning with Python is popular"),
    ]
    
    await client.create_index("my-docs", documents, "moss-minilm")
    await client.load_index("my-docs")
    
    # Search
    results = await client.query("my-docs", "programming language")
    for doc in results.docs:
        print(f"{doc.id}: {doc.text} (score: {doc.score:.3f})")

asyncio.run(main())
```

## 📚 API Reference

### MossClient

#### `MossClient(project_id: str, project_key: str)`

Initialize the client with your InferEdge project credentials.

#### `create_index(index_name: str, docs: List[DocumentInfo], model_id: str) -> bool`

Create a new search index with documents. The index is automatically synced to cloud storage.

#### `load_index(index_name: str) -> str`

Load an index from cloud storage or local cache for querying.

#### `query(index_name: str, query: str, top_k: int = 5) -> SearchResult`

Search for similar documents using semantic similarity.

#### `add_docs(index_name: str, docs: List[DocumentInfo]) -> Dict[str, int]`

Add new documents to an existing index.

#### `list_indexes() -> List[IndexInfo]`

Get all available indexes in your project.

## 📄 License

This package is licensed under the [PolyForm Shield License 1.0.0](./LICENSE).

- ✅ Free for testing, evaluation, internal use, and modifications.
- ❌ Not permitted for production or competing commercial use.
- 📩 For commercial licenses, contact: <contact@inferedge.dev>

## 📬 Contact

For support, commercial licensing, or partnership inquiries, contact us: [contact@inferedge.dev](mailto:contact@inferedge.dev)
