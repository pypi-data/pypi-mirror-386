.. image:: ../../assets/scrapegraphai_logo.png
   :align: center
   :width: 50%
   :alt: ScrapegraphAI

Overview
========

ScrapeGraphAI is an **open-source** Python library designed to revolutionize **scraping** tools.
In today's data-intensive digital landscape, this library stands out by integrating **Large Language Models** (LLMs)
and modular **graph-based** pipelines to automate the scraping of data from various sources (e.g., websites, local files etc.).

Simply specify the information you need to extract, and ScrapeGraphAI handles the rest, providing a more **flexible** and **low-maintenance** solution compared to traditional scraping tools.

For comprehensive documentation and updates, visit our `website <https://scrapegraphai.com>`_.


Why ScrapegraphAI?
==================

Traditional web scraping tools often rely on fixed patterns or manual configuration to extract data from web pages.
ScrapegraphAI, leveraging the power of LLMs, adapts to changes in website structures, reducing the need for constant developer intervention.
This flexibility ensures that scrapers remain functional even when website layouts change.

We support many LLMs including **GPT, Gemini, Groq, Azure, Hugging Face** etc.
as well as local models which can run on your machine using **Ollama**.

AI Models and Token Limits
==========================

ScrapGraphAI supports a wide range of AI models from various providers. Each model has a specific token limit, which is important to consider when designing your scraping pipelines. Here's an overview of the supported models and their token limits:

OpenAI Models
-------------
- GPT-3.5 Turbo (16,385 tokens)
- GPT-3.5 (4,096 tokens)
- GPT-3.5 Turbo Instruct (4,096 tokens)
- GPT-4 Turbo Preview (128,000 tokens)
- GPT-4 Vision Preview (128,000 tokens)
- GPT-4 (8,192 tokens)
- GPT-4 32k (32,768 tokens)
- GPT-4o (128,000 tokens)
- O1 Preview (128,000 tokens)
- O1 Mini (128,000 tokens)

Azure OpenAI Models
-------------------
- GPT-3.5 Turbo (16,385 tokens)
- GPT-3.5 (4,096 tokens)
- GPT-4 Turbo Preview (128,000 tokens)
- GPT-4 (8,192 tokens)
- GPT-4 32k (32,768 tokens)
- GPT-4o (128,000 tokens)
- O1 Preview (128,000 tokens)
- O1 Mini (128,000 tokens)

Google AI Models
----------------
- Gemini Pro (128,000 tokens)
- Gemini 1.5 Flash (128,000 tokens)
- Gemini 1.5 Pro (128,000 tokens)
- Gemini 1.0 Pro (128,000 tokens)

Anthropic Models
----------------
- Claude Instant (100,000 tokens)
- Claude 2 (9,000 tokens)
- Claude 2.1 (200,000 tokens)
- Claude 3 (200,000 tokens)
- Claude 3.5 (200,000 tokens)
- Claude 3 Opus (200,000 tokens)
- Claude 3 Sonnet (200,000 tokens)
- Claude 3 Haiku (200,000 tokens)

Mistral AI Models
-----------------
- Mistral Large Latest (128,000 tokens)
- Open Mistral Nemo (128,000 tokens)
- Codestral Latest (32,000 tokens)
- Open Mistral 7B (32,000 tokens)
- Open Mixtral 8x7B (32,000 tokens)
- Open Mixtral 8x22B (64,000 tokens)
- Open Codestral Mamba (256,000 tokens)

Ollama Models
-------------
- Command-R (12,800 tokens)
- CodeLlama (16,000 tokens)
- DBRX (32,768 tokens)
- DeepSeek Coder 33B (16,000 tokens)
- Llama2 Series (4,096 tokens)
- Llama3 Series (8,192-128,000 tokens)
- Mistral Models (32,000-128,000 tokens)
- Mixtral 8x22B Instruct (65,536 tokens)
- Phi3 Series (12,800-128,000 tokens)
- Qwen Series (32,000 tokens)

Hugging Face Models
------------------
- Grok-1 (8,192 tokens)
- Meta Llama 3 Series (8,192 tokens)
- Google Gemma Series (8,192 tokens)
- Microsoft Phi Series (2,048-131,072 tokens)
- GPT-2 Series (1,024 tokens)
- DeepSeek V2 Series (131,072 tokens)

Bedrock Models
-------------
- Claude 3 Series (200,000 tokens)
- Llama2 & Llama3 Series (4,096-8,192 tokens)
- Mistral Series (32,768 tokens)
- Titan Embed Text (8,000 tokens)
- Cohere Embed (512 tokens)

Fireworks Models
---------------
- Llama V2 7B (4,096 tokens)
- Mixtral 8x7B Instruct (4,096 tokens)
- Llama 3.1 Series (131,072 tokens)
- Mixtral MoE Series (65,536 tokens)

For a complete and up-to-date list of supported models and their token limits, please refer to the API documentation.

Understanding token limits is crucial for optimizing your scraping tasks. Larger token limits allow for processing more text in a single API call, which can be beneficial for scraping lengthy web pages or documents.


Library Diagram
===============

With ScrapegraphAI you can use many already implemented scraping pipelines or create your own.

The diagram below illustrates the high-level architecture of ScrapeGraphAI:

.. image:: ../../assets/project_overview_diagram.png
   :align: center
   :width: 70%
   :alt: ScrapegraphAI Overview

FAQ
===

1. **What is ScrapeGraphAI?**

   ScrapeGraphAI is an open-source python library that uses large language models (LLMs) and graph logic to automate the creation of scraping pipelines for websites and various document types.

2. **How does ScrapeGraphAI differ from traditional scraping tools?**

   Traditional scraping tools rely on fixed patterns and manual configurations, whereas ScrapeGraphAI adapts to website structure changes using LLMs, reducing the need for constant developer intervention.

3. **Which LLMs are supported by ScrapeGraphAI?**

   ScrapeGraphAI supports several LLMs, including GPT, Gemini, Groq, Azure, Hugging Face, and local models that can run on your machine using Ollama.

4. **Can ScrapeGraphAI handle different document formats?**

   Yes, ScrapeGraphAI can scrape information from various document formats such as XML, HTML, JSON, and more.

5. **I get an empty or incorrect output when scraping a website. What should I do?**

   There are several reasons behind this issue, but for most cases, you can try the following:

      - Set the `headless` parameter to `False` in the graph_config. Some javascript-heavy websites might require it.

      - Check your internet connection. Low speed or unstable connection can cause the HTML to not load properly.

      - Try using a proxy server to mask your IP address. Check out the :ref:`Proxy` section for more information on how to configure proxy settings.

      - Use a different LLM model. Some models might perform better on certain websites than others.

      - Set the `verbose` parameter to `True` in the graph_config to see more detailed logs.

      - Visualize the pipeline graphically using :ref:`Burr`.

   If the issue persists, please report it on the GitHub repository.

6. **How does ScrapeGraphAI handle the context window limit of LLMs?**

   By splitting big websites/documents into chunks with overlaps and applying compression techniques to reduce the number of tokens. If multiple chunks are present, we will have multiple answers to the user prompt, and therefore, we merge them together in the last step of the scraping pipeline.

7. **How can I contribute to ScrapeGraphAI?**

   You can contribute to ScrapeGraphAI by submitting bug reports, feature requests, or pull requests on the GitHub repository. Join our `Discord <https://discord.gg/uJN7TYcpNa>`_ community and follow us on social media!

Sponsors
========

.. image:: ../../assets/browserbase_logo.png
   :width: 10%
   :alt: Browserbase
   :target: https://www.browserbase.com/

.. image:: ../../assets/serp_api_logo.png
   :width: 10%
   :alt: Serp API
   :target: https://serpapi.com?utm_source=scrapegraphai

.. image:: ../../assets/transparent_stat.png
   :width: 15%
   :alt: Stat Proxies
   :target: https://dashboard.statproxies.com/?refferal=scrapegraph

.. image:: ../../assets/scrapedo.png
   :width: 11%
   :alt: Scrapedo
   :target: https://scrape.do

.. image:: ../../assets/scrapegraph_logo.png
   :width: 11%
   :alt: ScrapegraphAI
   :target: https://scrapegraphai.com
