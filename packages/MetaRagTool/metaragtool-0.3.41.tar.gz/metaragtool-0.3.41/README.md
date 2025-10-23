# MetaRagTool 🚀 ⚠️ EXPERIMENTAL

![Experimental](https://img.shields.io/badge/Status-Experimental-orange)
![Development](https://img.shields.io/badge/Stage-Research-red)
[![PyPI version](https://badge.fury.io/py/MetaRagTool.svg)](https://badge.fury.io/py/MetaRagTool)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/14g-lmMIeElvd8yfGN_vmeCnG4GDds2Xe?usp=sharing)

> **⚠️ EXPERIMENTAL SOFTWARE WARNING**  
> This is experimental research software. features may be unstable, and breaking changes can occur. Use in production environments **is not recommended**. Please report issues and provide feedback to help improve the framework.


**MetaRagTool** is a powerful and flexible Python framework for building, experimenting with, and evaluating Retrieval-Augmented Generation (RAG) systems. It is designed with a unique hierarchical document structure that enables advanced, context-aware retrieval techniques not easily achievable in other frameworks.

Whether you're building a simple question-answering bot or conducting research on novel RAG strategies, MetaRagTool provides the building blocks you need.






[![PyPI version](https://badge.fury.io/py/MetaRagTool.svg)](https://badge.fury.io/py/MetaRagTool)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/14g-lmMIeElvd8yfGN_vmeCnG4GDds2Xe?usp=sharing)



## 🔑 Key Features

*   **Easy to use yet RAG Pipelines:** from raw text to generated answers in a few lines of code.
*   **Hierarchical Document Structure:** Intelligently parses documents into linked paragraphs and sentences for superior context awareness.
*   **Flexible Components:** Easily integrates with `sentence-transformers`, Google `Gemini`, `OpenAI` models or implement your own components.
*   **Multiple Interaction Modes:**
    *   `retrieve()`: Fetch relevant chunks of text.
    *   `ask()`: Standard RAG flow, retrieve then generate an answer.
    *   `ask(useTool=True)`: LLM uses the retriever as a tool, deciding when and what to search for.
*   **Better Chunking:** Choose from various strategies like `SENTENCE_MERGER`, `PARAGRAPH`, or `RECURSIVE`.
*   **Advanced RAG Techniques:**
    *   **Smart Neighbors:** Intelligently include adjacent chunks if they improve relevance to the query.
    *   **Parent Paragraph Replacement:** Retrieve a small chunk but provide its entire parent paragraph to the LLM for richer context.
    *   **Enriched Embeddings:** Steer a chunk's embedding using its neighbors or parent paragraph for better semantic representation.
    *   **Reranking:** Use powerful cross-encoders to re-rank initial retrieval results for higher precision.
*   **Built-in Evaluation Suite:** A comprehensive framework (`MetaRagTool.Evaluations`) to benchmark different configurations, encoders, and retrieval strategies on standard datasets.
*   **Interactive Demo UI:** Includes a Gradio application (`MetaRagTool.Apps`) for hands-on testing and visualization of chunking and retrieval.


## ⚙️ Installation

Get started by installing the package using pip:

```bash
pip install MetaRagTool
```


## ⚡ Quick Start: Your First RAG Query

> **Try it in your browser!** The following quick start guide is available as a Colab Notebook.
> 
> [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/14g-lmMIeElvd8yfGN_vmeCnG4GDds2Xe?usp=sharing)

This example shows the absolute minimum to get a RAG system running and answer a question.

```python
import MetaRagTool
from MetaRagTool import MetaRAG, Gemini, SentenceTransformerEncoder

# Initialize MetaRAG
rag = MetaRAG(encoder_model=SentenceTransformerEncoder('sentence-transformers/LaBSE'),
              llm=Gemini(api_key="YOUR_GEMINI_API_KEY"))

# Add Your Data (Corpus)
rag.add_corpus([
    "The Eiffel Tower is a wrought-iron lattice tower on the Champ de Mars in Paris, France.",
    "It is named after the engineer Gustave Eiffel, whose company designed and built the tower.",
    "Constructed from 1887 to 1889 as the entrance arch for the 1889 World's Fair.",
    "The tower is 330 metres (1,083 ft) tall, about the same height as an 81-storey building.",
    "The tower has three levels for visitors, with restaurants on the first and second levels."
])

# Perform RAG Query
response = rag.ask("How tall is the Eiffel Tower?")

# Alternatively, you can retrieve chunks separately without any LLM processing:
# retrieved_chunks = rag.retrieve(query, top_k=10) # Get top 10 relevant chunks
```

## 📖 Usage Examples



### 1. Setup & Initialization

First, import the necessary classes and set up your encoder and LLM.

```python
import MetaRagTool
from MetaRagTool import MetaRAG, Gemini, SentenceTransformerEncoder

# --- Configuration ---
# 1. Provide your API key (get a free key from ai.dev)
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"

# 2. Choose an Encoder Model from Hugging Face or local path
encoder = SentenceTransformerEncoder('intfloat/multilingual-e5-small')

# 3. Choose an LLM
llm = Gemini(api_key=GEMINI_API_KEY)

# --- Initialize MetaRAG ---
rag = MetaRAG(encoder_model=encoder, llm=llm)

# --- Prepare Your Data (Corpus) ---
# This is a list of documents. Each string can be a page, an article, or a large text block.
contexts = [
    "The Eiffel Tower is a wrought-iron lattice tower on the Champ de Mars in Paris, France.",
    "It is named after the engineer Gustave Eiffel, whose company designed and built the tower.",
    "Constructed from 1887 to 1889 as the entrance arch for the 1889 World's Fair.",
    "The tower is 330 metres (1,083 ft) tall, about the same height as an 81-storey building.",
    "The tower has three levels for visitors, with restaurants on the first and second levels."
]

# This single command processes, chunks, embeds, and indexes your data.
rag.add_corpus(contexts)
```

### 2. Basic Retrieval (`rag.retrieve`)

If you only need the relevant text chunks without a generated answer:

```python
query = "How tall is the Eiffel Tower?"
retrieved_chunks = rag.retrieve(query=query, top_k=2)

print(retrieved_chunks)
# Expected Output:
# ['The tower is 330 metres (1,083 ft) tall, about the same height as an 81-storey building.',
#  'The Eiffel Tower is a wrought-iron lattice tower on the Champ de Mars in Paris, France.']
```

### 3. Standard RAG (`rag.ask`)

Retrieve relevant chunks and pass them to the LLM to synthesize a final answer.

```python
query = "How tall is the Eiffel Tower?"
response = rag.ask(query)

print(f"Answer:\n{response}")
# Expected Output:
# The Eiffel Tower is 330 metres (1,083 ft) tall.
```

### 4. Advanced RAG with `apply_best_config()`

Unleash the full power of MetaRagTool with a single command. The `apply_best_config()` method enables a combination of proven techniques for superior performance.

```python
from MetaRagTool.Encoders import CrossEncoderReranker
from MetaRagTool.RAG import ChunkingMethod

# Re-initialize MetaRAG to apply new settings before adding a corpus
advanced_rag = MetaRAG(encoder_model=encoder, llm=llm)

# Apply a pre-configured set of powerful techniques
advanced_rag.apply_best_config(text_has_proper_paragraphing=True)

# What does apply_best_config() do? It's a shortcut for:
# reranker_model = CrossEncoderReranker('cross-encoder/mmarco-mMiniLMv2-L12-H384-v1')
# advanced_rag.splitting_method = ChunkingMethod.SENTENCE_MERGER
# advanced_rag.rerank = True
# advanced_rag.reranker_model = reranker_model
# advanced_rag.replace_retrieved_chunks_with_parent_paragraph = True
# advanced_rag.add_neighbor_chunks_smart = True
# advanced_rag.use_neighbor_embeddings = True
# advanced_rag.use_parentParagraph_embeddings = True
# advanced_rag.embedding_steering_influence_factor = 0.2

# Now, add the corpus and ask the question
advanced_rag.add_corpus(contexts)
response = advanced_rag.ask("How tall is the Eiffel Tower?")
```

### 5. Tool-Based RAG (`rag.ask(useTool=True)`)

Give control to the LLM. It will receive the `retrieve` function as a tool and can decide for itself when to search for information to answer a complex query.

```python
query = "Tell me about the history and height of the Eiffel Tower."

# Let the LLM use the retrieval tool as needed
tool_answer = advanced_rag.ask(query, useTool=True)

print(f"Tool-Based Answer:\n{tool_answer}")

# Note: The LLM might make one or more calls to the retrieval tool behind the scenes.
# You can inspect rag.llm.messages_history to see the full interaction.
```

### 6. Working with PDFs

MetaRagTool includes helpers to read PDF files directly into your corpus.

```python
from MetaRagTool.Utils import read_pdf

# Let's assume you have two PDF files in your directory
pdf_files = ["./document1.pdf", "./document2.pdf"]
pdf_contexts = []
for pdf_path in pdf_files:
    # Set ignore_line_breaks=True if your PDF has many unwanted line breaks within sentences
    pdf_contexts.append(read_pdf(pdf_path, ignore_line_breaks=False))
    print(f"Read content from {pdf_path}")

# Add the PDF content to a new RAG instance
pdf_rag = MetaRAG(encoder_model=encoder, llm=llm)
pdf_rag.add_corpus(pdf_contexts)

# Now you can retrieve or ask questions based on your PDFs
retrieved_chunks = pdf_rag.retrieve(query='What are the key RAG benchmarks?', top_k=3)
print(retrieved_chunks)
```



## 🧩 Core Components

*   **`MetaRAG`**: The main orchestrator managing the entire pipeline from data ingestion to answer generation.
*   **Encoders (`MetaRagTool.Encoders`)**: Converts text into vector embeddings. `SentenceTransformerEncoder` is the primary implementation.
*   **LLMs (`MetaRagTool.LLM`)**: Interfaces with Large Language Models. Includes `Gemini`, `OpenaiGpt`, and a `JudgeLLM` for evaluations.
*   **Chunking (`MetaRagTool.RAG.Chunkers`)**: Defines strategies for splitting documents. `ChunkingMethod` is an Enum with options like `SENTENCE_MERGER`, `PARAGRAPH`, and `RECURSIVE`.
*   **Document Structures (`MetaRagTool.RAG.DocumentStructs`)**: The `MRDocument`, `MRParagraph`, and `MRSentence` classes that form the hierarchical backbone of the library.
*   **Utilities (`MetaRagTool.Utils`)**: Helper functions for loading data (`DataLoader`), reading PDFs (`read_pdf`), and managing configurations (`MetaRagConfig`).
*   **Evaluations (`MetaRagTool.Evaluations`)**: A powerful suite for assessing RAG performance, measuring retrieval accuracy, and running end-to-end quality tests.




## 🔧 Configuration & Customization

You can customize the `MetaRAG` behavior during initialization:

```python
from MetaRagTool.RAG import ChunkingMethod

rag = MetaRAG(
    encoder_model=encoder,
    llm=llm,

    # --- Chunking ---
    splitting_method=ChunkingMethod.SENTENCE_MERGER, # Strategy
    chunk_size=90,           # Target token count per chunk

    # --- Advanced Retrieval ---
    advanced_rag.rerank = True, # Enable reranking with a cross-encoder
    advanced_rag.reranker_model = reranker_model, # Set your reranker model
    
        # --- Context Expansion ---
    add_neighbor_chunks_smart=True, # Intelligently add adjacent chunks if relevant
    replace_retrieved_chunks_with_parent_paragraph=True, # Retrieve the whole paragraph instead of just the chunk
    
        # --- Embedding Enrichment ---
    use_neighbor_embeddings=False, # Factor in neighbor embeddings (experimental)
    use_parentParagraph_embeddings=False, # Factor in paragraph embeddings (experimental)
    embedding_steering_influence_factor=0.35, # Weight for neighbor/parent embeddings
    
    
    # --- Utilities ---
    log_chunking_report =True, # Print chunking statistics after adding corpus
)

```

Refer to the `MetaRAG` class definition (`MetaRagTool/RAG/MetaRAG.py`) for all available parameters.



## 🚀 Launch the Gradio UI

Explore MetaRAG's features interactively with the built-in Gradio application.

**🌐 Try it online:** The Gradio app is live and running at [https://huggingface.co/spaces/codersan/MetaRAG](https://huggingface.co/spaces/codersan/MetaRAG)

**Or run locally:**

```python
from MetaRagTool.Apps import GradioApps

# Make sure API keys are set, e.g., via environment variables
# os.environ["GEMINI_API_KEY"] = "YOUR_GEMINI_KEY"

GradioApps.load_app()
```

This will launch a web UI with tabs for:
*   **Chunk and Encode:** Visualize how different chunking strategies split your text.
*   **Retriever:** Test retrieval performance with various settings.
*   **Full RAG:** Get end-to-end answers from the LLM.
*   **Full Tool RAG:** Test the RAG-as-a-Tool functionality.
*   **Chunk Only:** A lightweight chunking visualizer.




## 📈 Research & Background

This library is the official implementation of the research paper: "MetaRAG: A Hierarchical and Context-Aware Framework for Retrieval-Augmented Generation."

We provide a comprehensive evaluation suite in the MetaRagTool.Evaluations module to benchmark different RAG configurations. The framework was tested on standard long-document QA datasets like NQ, HotpotQA, and SciFact, as well as the custom-built WikiFaQA dataset for multilingual evaluation.

## Paper Implementation

The experiments used in the MetaRAG paper can be found [here](https://github.com/ali7919/MetaRagTool/tree/master/code):
- Main notebook containing  experiment from the paper, including:
  - Chunking methods comparison (sentence merging, paragraph, recursive, sentence-based)
  - MetaRAG techniques evaluation (neighbor chunks, paragraph replacement, embedding enrichment, reranking)
  - Comparison with other RAG frameworks (LangChain, LlamaIndex)
  - Multi-dataset evaluation (Natural Questions, HotpotQA, SciFact)


### Citing MetaRAG

If you use MetaRAG in your research, please cite our paper:
```bibtex
@article{mobarekati2024metarag,
  title={MetaRAG: A Hierarchical and Context-Aware Framework for Retrieval-Augmented Generation},
  author={Ali Mobarekati and Ali Mohades},
  journal={arXiv preprint},
  year={2025},
  url={}
}
```


## 🤝 Contributing

Contributions are welcome! If you have a feature request, bug report, or pull request, please feel free to open an issue or submit a PR.
## 📜 License

This project is licensed under the [MIT License](LICENSE).