# GraphRAG vs Vector RAG — Comparison Report

**Date**: 2026-06-23 17:06

**Corpus**: 52 chunks from `data/input/`

**GraphRAG LLM**: DeepSeek API (`deepseek-chat`)

**Vector RAG**: Chroma + `BAAI/bge-m3`

**Embedding dim**: 1024

---

## Executive Summary

| # | Type | Expected Best | GraphRAG | VectorRAG | Winner |
|:-:|:-----|:------------:|:--------:|:---------:|:------:|
| 1 | factual | vector | 20.2s (local) | 0.1s | 🏆 VectorRAG |
| 2 | multi_hop | graphrag | 16.1s (local) | 0.1s | 🏆 GraphRAG |
| 3 | multi_hop | graphrag | 18.6s (local) | 0.1s | 🏆 GraphRAG |
| 4 | multi_hop | graphrag | 20.2s (local) | 0.2s | 🏆 GraphRAG |
| 5 | global | graphrag | 30.7s (global) | 0.1s | 🏆 GraphRAG |
| 6 | global | graphrag | 30.6s (global) | 0.0s | 🏆 GraphRAG |
| 7 | summary | graphrag | 32.8s (global) | 0.1s | 🏆 GraphRAG |
| 8 | factual | vector | 13.1s (local) | 0.0s | 🏆 VectorRAG |

**GraphRAG** avg: 22.8s | **VectorRAG** avg: 0.1s

---

## Detailed Results

### 1. What is the Transformer architecture?

- **Type**: `factual` | **Expected best**: `vector`

#### GraphRAG (local, 20.2s)

> # The Transformer Architecture: A Comprehensive Overview

## Foundational Concept and Origin

The Transformer is a modern neural network architecture that fundamentally revolutionized how machines process sequential data. Introduced by Google researchers in the landmark 2017 paper "Attention Is All You Need" at the NeurIPS conference, the Transformer marked a paradigm shift away from previous approaches to sequence modeling [Data: Entities (92, 187); Relationships (403); Sources (15)].

Unlike e

#### Vector RAG (0.1s)

> [Chunk 1, score=0.624] # Transformer (deep learning) In deep learning, the transformer is a family of artificial neural network architectures based on the multi-head attention mechanism, in which text is converted to numerical representations called tokens, and each token is converted into a vector via lookup from a word ...

[Chunk 2, score=0.529] # Vision transformer A vision transformer (ViT) is a transformer designed for computer vision. A ViT decomposes an input image into a series of patch

---

### 2. How are Transformer, BERT, GPT, and LoRA related?

- **Type**: `multi_hop` | **Expected best**: `graphrag`

#### GraphRAG (local, 16.1s)

> # The Relationship Between Transformer, BERT, GPT, and LoRA

## Overview

These four concepts represent a technological lineage in modern AI: the **Transformer** is the foundational architecture, **BERT** and **GPT** are influential models built on that architecture for different purposes, and **LoRA** is an efficient fine-tuning technique designed specifically for such large models. Together, they form a coherent ecosystem spanning foundational research, practical applications, and optimization

#### Vector RAG (0.1s)

> [Chunk 1, score=0.562] # LoRA (machine learning) LoRA (Low-Rank Adaptation) is a parameter-efficient fine-tuning technique for large language models and other deep neural networks. Introduced in 2021 by researchers at Microsoft, LoRA enables adaptation of pre-trained models to specific tasks while requiring significantly ...

[Chunk 2, score=0.542] # BERT (language model) Bidirectional encoder representations from transformers (BERT) is a language model introduced in October 2018 by researchers 

---

### 3. What is the relationship between attention and parameter-efficient fine-tuning?

- **Type**: `multi_hop` | **Expected best**: `graphrag`

#### GraphRAG (local, 18.6s)

> Based solely on the data provided, there is **no direct relationship** between the **Attention Mechanism** and **Parameter-Efficient Fine-tuning (PEFT)**.

The provided information describes these as two separate, fundamental concepts in deep learning without linking them to one another.

### On Attention and Self-Attention

Attention mechanisms are a foundational component of the Transformer architecture. They allow models to dynamically focus on relevant parts of an input sequence, enabling ef

#### Vector RAG (0.1s)

> [Chunk 1, score=0.605] # Attention (machine learning) In machine learning, attention is a method that determines the importance of each component in a sequence relative to the other components in that sequence. In natural language processing, importance is represented by "soft" weights assigned to each word in a sentence....

[Chunk 2, score=0.587] # Fine-tuning (deep learning) In deep learning, fine-tuning is the process of adapting a computational model trained for one task (the upstream task)

---

### 4. How do knowledge distillation and quantization relate?

- **Type**: `multi_hop` | **Expected best**: `graphrag`

#### GraphRAG (local, 20.2s)

> Based solely on the provided data, I can describe the relationship between these two concepts as they are represented in the given tables. However, the information is incomplete for a full comparison.

### Quantization and Vector Compression in FAISS

The data extensively covers **vector quantization**, but in the specific context of the FAISS library, not as a general model compression technique for neural networks. FAISS (Facebook AI Similarity Search) is an open-source library for efficient s

#### Vector RAG (0.2s)

> [Chunk 1, score=0.490] # Question answering Question answering (QA) is a computer science discipline within the fields of information retrieval and natural language processing (NLP) that is concerned with building systems that automatically answer questions that are posed by humans in a natural language. A question-answer...

[Chunk 2, score=0.470] # Knowledge graph In knowledge representation and reasoning, a knowledge graph is a knowledge base that uses a graph-structured data model or topolog

---

### 5. What are the major themes in this knowledge base?

- **Type**: `global` | **Expected best**: `graphrag`

#### GraphRAG (global, 30.7s)

> # Major Themes in the Knowledge Base

This knowledge base encompasses a comprehensive range of interconnected topics spanning artificial intelligence, machine learning, data science, and computational infrastructure. Below is a synthesized overview of the major themes identified.

## Foundational Neural Network Architectures

The knowledge base extensively covers the evolution and fundamentals of neural network architectures. The **Transformer architecture**, introduced in the 2017 paper "Attent

#### Vector RAG (0.1s)

> [Chunk 1, score=0.506] # Knowledge graph In knowledge representation and reasoning, a knowledge graph is a knowledge base that uses a graph-structured data model or topology to represent and operate on data. Knowledge graphs are often used to store interlinked descriptions of entities – objects, events, situations or abst...

[Chunk 2, score=0.465] # Question answering Question answering (QA) is a computer science discipline within the fields of information retrieval and natural language process

---

### 6. What are key research trends in large language models?

- **Type**: `global` | **Expected best**: `graphrag`

#### GraphRAG (global, 30.6s)

> # Key Research Trends in Large Language Models

The field of large language models (LLMs) is experiencing rapid and multifaceted evolution, with several interconnected research trends driving innovation. These trends span foundational architectures, training methodologies, efficiency improvements, alignment techniques, and practical applications.

## Foundational Architectures and Mechanisms

The **Transformer architecture**, introduced by Google in the 2017 paper "Attention Is All You Need," re

#### Vector RAG (0.0s)

> [Chunk 1, score=0.689] # Large language model A large language model (LLM) is a neural network trained on a vast amount of text for natural language processing tasks, especially language generation. LLMs can typically generate, summarize, translate, and analyze text in many contexts, and are a foundational technology behi...

[Chunk 2, score=0.562] # Neural machine translation Neural machine translation (NMT) is an approach to machine translation that uses an artificial neural network to predict

---

### 7. Summarize the evolution from RNNs to Transformers.

- **Type**: `summary` | **Expected best**: `graphrag`

#### GraphRAG (global, 32.8s)

> # The Evolution from Recurrent Neural Networks to Transformers

## The Foundations: Recurrent Neural Networks (RNNs) and Their Limitations

Recurrent Neural Networks (RNNs) were originally designed to capture temporal dependencies in sequential data, using a hidden state that is updated at each time step [Data: Reports (153)]. They maintain internal memory through recurrent connections, allowing past information to influence current outputs, making them foundational for sequence modeling tasks s

#### Vector RAG (0.1s)

> [Chunk 1, score=0.585] # Transformer (deep learning) In deep learning, the transformer is a family of artificial neural network architectures based on the multi-head attention mechanism, in which text is converted to numerical representations called tokens, and each token is converted into a vector via lookup from a word ...

[Chunk 2, score=0.551] # Recurrent neural network In artificial neural networks, recurrent neural networks (RNNs) are designed for processing sequential data, such as text,

---

### 8. What is masked language modeling in BERT?

- **Type**: `factual` | **Expected best**: `vector`

#### GraphRAG (local, 13.1s)

> # Masked Language Modeling in BERT

## Overview of the Technique

Masked language modeling is a self-supervised training objective that BERT (Bidirectional Encoder Representations from Transformers) uses to learn rich, contextual representations of language [Data: Entities (428); Relationships (504)]. In this approach, certain tokens within a sentence are randomly masked or hidden, and the model's task is to predict those masked tokens based on the surrounding context [Data: Sources (18); Entiti

#### Vector RAG (0.0s)

> [Chunk 1, score=0.664] # BERT (language model) Bidirectional encoder representations from transformers (BERT) is a language model introduced in October 2018 by researchers at Google. It learns to represent text as a sequence of vectors using self-supervised learning. It uses the encoder-only transformer architecture. BERT...

[Chunk 2, score=0.577] # Large language model A large language model (LLM) is a neural network trained on a vast amount of text for natural language processing tasks, espec

---

