# MediSearch API Client

<div align="center">
  <h3>Python client for interacting with the <a href="https://medisearch.io/developers">MediSearch API</a></h3>
</div>

## Overview

The **MediSearch API Client** provides a Python interface to the [MediSearch API](https://medisearch.io/developers), enabling developers to integrate MediSearch into their applications. The client supports both synchronous and asynchronous operations, real-time streaming responses, and customizable search parameters.

### Key Features

- **Medical Knowledge**: Access evidence-based medical information from peer-reviewed journals, health guidelines, and trusted sources
- **Synchronous & Asynchronous APIs**: Choose between blocking and non-blocking requests
- **Real-time Streaming**: Get responses as they are generated
- **Customizable Filters**: Refine searches by source type, publication year, and more
- **Multilingual Support**: Interact with the API in multiple languages
- **Conversation Context**: Maintain context across multiple turns of conversation
- **Pro Answers**: Use the [MediSearch Pro](https://medisearch.io/announcements/pro_release) model to generate answers
- **Suggested Followups**: Receive suggested follow-up questions to continue the conversation

## Try It Now

Want to try the MediSearch API Client without any setup? Open our interactive Colab notebook:

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1DpnKm6xMRCZ-00Z4hwbTJjC7rICshm46?usp=sharing)

## Installation

```bash
pip install medisearch-client
```

## Core Concepts

The MediSearch client architecture consists of several key components:

1. **MediSearchClient**: Main client class handling API communication
2. **Settings**: Configuration for language preferences and model selection
3. **Filters**: Criteria for refining search results
4. **ResponseHandler**: Callbacks for processing different response types

The API uses an event-based communication model with the following event types:
- **llm_response**: Text content from the AI
- **articles**: Bibliographic information about source articles
- **followups**: Suggested follow-up questions related to the current query
- **error**: Error conditions with associated error codes

## Authentication

The MediSearch API uses API key authentication:

```python
from medisearch_client import MediSearchClient

# Initialize with your API key
client = MediSearchClient(api_key="your_api_key_here")
```

You can obtain an API key from the [MediSearch Developer Portal](https://medisearch.io/developers).

## Quick Start

```python
from medisearch_client import MediSearchClient

# Initialize client
client = MediSearchClient(api_key="your_api_key")

# Send a query
responses = client.send_message(
    conversation=["What are the symptoms of type 2 diabetes?"],
    conversation_id="diabetes-symptoms-query"
)

# Process responses
for response in responses:
    if response["event"] == "llm_response":
        print("Answer:", response["data"])
    elif response["event"] == "articles":
        print(f"Sources: {len(response['data'])} articles found")
        for i, article in enumerate(response['data'][:3], 1):
            print(f"{i}. {article['title']} ({article.get('year', 'N/A')})")
    elif response["event"] == "followups":
        print("\nSuggested follow-up questions:")
        for i, question in enumerate(response['data'], 1):
            print(f"{i}. {question}")
```

## Basic Usage


### Simple Query Example

```python
from medisearch_client import MediSearchClient

client = MediSearchClient(api_key="your_api_key")

# Send a medical query
responses = client.send_message(
    conversation=["What are the common symptoms of type 2 diabetes?"],
    conversation_id="diabetes-symptoms-query"
)

# Process the responses
for response in responses:
    if response["event"] == "llm_response":
        print("Answer:", response["data"])
    elif response["event"] == "articles":
        print(f"Sources ({len(response['data'])} articles):")
        for i, article in enumerate(response['data'][:3], 1):
            print(f"{i}. {article['title']})
    elif response["event"] == "followups":
        print("\nYou might also want to ask:")
        for question in response["data"]:
            print(f"- {question}")
```

### Parameter Explanation

- **conversation**: List of strings representing the conversation history
- **conversation_id**: Unique identifier for the conversation
- **should_stream_response**: Boolean to enable/disable streaming (default: False)
- **settings**: Optional Settings object for language, model type, and filters
- **response_handler**: Optional ResponseHandler for custom callbacks

## Advanced Usage

### Conversation Management

The `conversation` parameter is a list of strings where user and AI messages alternate, with the user's message always being the last.

**Important**: Always use the same conversation ID for all messages in a single conversation. This maintains both conversation context and article context on the backend, ensuring relevant medical information is preserved across multiple turns.

```python
import uuid
from medisearch_client import MediSearchClient

client = MediSearchClient(api_key="your_api_key")

# Generate a unique UUID for the conversation
conversation_id = str(uuid.uuid4())  # e.g., "f47ac10b-58cc-4372-a567-0e02b2c3d479"
conversation = ["What are the symptoms of type 2 diabetes?"]

# Send the first message
first_responses = client.send_message(
    conversation=conversation,
    conversation_id=conversation_id
)

# Extract the AI's response
ai_response = None
for response in first_responses:
    if response["event"] == "llm_response":
        ai_response = response["data"]

# Follow-up question
if ai_response:
    conversation.append(ai_response)
    conversation.append("How is it diagnosed?")
    
    # Send the follow-up question with the SAME conversation_id
    followup_responses = client.send_message(
        conversation=conversation,
        conversation_id=conversation_id
    )
```

### Streaming Responses

Streaming provides real-time feedback while responses are being generated.

```python
from medisearch_client import MediSearchClient

client = MediSearchClient(api_key="your_api_key")

print("Response: ", end="", flush=True)

# Enable streaming with should_stream_response=True
for response in client.send_message(
    conversation=["What are the treatment options for COVID-19?"],
    conversation_id="covid-treatment-stream",
    should_stream_response=True
):
    if response["event"] == "llm_response":
        # Print each chunk as it arrives
        print(response["data"], end="", flush=True)
    elif response["event"] == "articles":
        print(f"\n\nBased on {len(response['data'])} medical sources")
    elif response["event"] == "followups":
        print("\nSuggested follow-up questions:")
        for question in response["data"]:
            print(f"- {question}")
```

### Asynchronous Operations

For non-blocking operations, use the asynchronous methods.

```python
import asyncio
from medisearch_client import MediSearchClient

async def medical_query():
    client = MediSearchClient(api_key="your_api_key")
    
    # Async request
    responses = await client.send_message_async(
        conversation=["What are the cardiovascular effects of COVID-19?"],
        conversation_id="covid-cardio-async"
    )
    
    # Process responses
    for response in responses:
        if response["event"] == "llm_response":
            print(f"Answer: {response['data'][:100]}...")
        elif response["event"] == "followups":
            print("You might also want to ask about:")
            for question in response["data"]:
                print(f"- {question}")

# Run the async function
asyncio.run(medical_query())
```

#### Async Streaming

```python
import asyncio
from medisearch_client import MediSearchClient

async def stream_response():
    client = MediSearchClient(api_key="your_api_key")
    
    print("Response: ", end="", flush=True)
    
    # Get streaming response asynchronously
    response_stream = await client.send_message_async(
        conversation=["What are the side effects of statins?"],
        conversation_id="statin-side-effects",
        should_stream_response=True
    )
    
    # Process streaming response
    async for response in response_stream:
        if response["event"] == "llm_response":
            print(response["data"], end="", flush=True)
        elif response["event"] == "articles":
            print(f"\n\nBased on {len(response['data'])} medical sources")
        elif response["event"] == "followups":
            print("\nYou might also want to ask:")
            for question in response["data"]:
                print(f"- {question}")

# Run the async streaming function
asyncio.run(stream_response())
```

### Response Handlers

Response handlers provide a way to process different types of responses with custom callbacks.

```python
from medisearch_client import MediSearchClient, ResponseHandler, Settings

client = MediSearchClient(api_key="your_api_key")

# Track the accumulated response
accumulated_response = ""
article_count = 0
followup_questions = []

# Define handler functions
def handle_llm_response(response):
    global accumulated_response
    chunk = response["data"]
    accumulated_response += chunk
    print(chunk, end="", flush=True)

def handle_articles(response):
    global article_count
    articles = response["data"]
    article_count = len(articles)
    print(f"\n\nFound {article_count} relevant medical articles")

def handle_followups(response):
    global followup_questions
    followup_questions = response["data"]
    print("\nSuggested follow-up questions:")
    for i, question in enumerate(followup_questions, 1):
        print(f"{i}. {question}")

def handle_error(response):
    error_code = response["data"]
    print(f"\nError occurred: {error_code}")

# Create response handler
handler = ResponseHandler(
    on_llm_response=handle_llm_response,
    on_articles=handle_articles,
    on_followups=handle_followups,
    on_error=handle_error
)

# Create settings with followup_count to request suggested questions
settings = Settings(followup_count=3)

# Send message with the response handler
client.send_message(
    conversation=["What are recent advances in breast cancer treatment?"],
    conversation_id="breast-cancer-treatment",
    response_handler=handler,
    settings=settings
)
```

### Working with Filters

The `Filters` class allows you to customize search behavior for more targeted results.

```python
from medisearch_client import MediSearchClient, Filters, Settings

client = MediSearchClient(api_key="your_api_key")

# Create filters
filters = Filters(
    # Specify which sources to search
    sources=[
        "scientificArticles",      # Peer-reviewed scientific literature
        "internationalHealthGuidelines"  # Guidelines from health organizations
    ],
    # Limit to recent publications
    year_start=2020,
    year_end=2023,
    # Specific article types
    article_types=[
        "metaAnalysis",   # Meta-analyses
        "clinicalTrials"  # Clinical trials
    ]
)

# Apply filters through settings
settings = Settings(
    language="English",
    filters=filters,
    model_type="pro"  # Use the professional model
)

# Send a message with custom settings
responses = client.send_message(
    conversation=["What are the latest advancements in Alzheimer's treatment?"],
    conversation_id=str(uuid.uuid4()),
    settings=settings
)
```

#### Available Source Types

- `scientificArticles`: Peer-reviewed scientific literature
- `internationalHealthGuidelines`: Guidelines from international health organizations
- `medicineGuidelines`: Guidelines related to drugs
- `healthBlogs`: Content from health blogs
- `books`: Medical textbooks and references

#### Article Types for Scientific Articles

- `metaAnalysis`: Meta-analyses that combine results from multiple studies
- `reviews`: Review articles that summarize current knowledge
- `clinicalTrials`: Reports of clinical trials
- `observationalStudies`: Studies where variables are observed without intervention
- `other`: Other types of scientific articles

#### Year Filtering Options

The year filters allow you to specify the publication date range:

- `year_start`: The earliest publication year to include (e.g., 2018)
- `year_end`: The latest publication year to include (e.g., 2023)

These filters are particularly useful for:
- Finding the most recent research on rapidly evolving topics
- Excluding outdated medical information
- Focusing on specific time periods for historical research

### Language Support

MediSearch supports queries in any language without constraints:

```python
from medisearch_client import MediSearchClient, Settings

client = MediSearchClient(api_key="your_api_key")

# Create language-specific settings
settings = Settings(language="Spanish")

# Send query in Spanish
responses = client.send_message(
    conversation=["¿Cuáles son los síntomas de la diabetes?"],
    conversation_id=str(uuid.uuid4()),
    settings=settings
)
```

The MediSearch API can process queries in any language and will respond in the same language as the query. There are no restrictions on supported languages, making it suitable for global applications.

### Model Selection

MediSearch offers two model types that correspond directly to those available on the MediSearch.io platform:

```python
from medisearch_client import MediSearchClient, Settings

client = MediSearchClient(api_key="your_api_key")

# Use standard model
settings = Settings(model_type="standard")
responses = client.send_message(
    conversation=["What are the treatments for rheumatoid arthritis?"],
    conversation_id=str(uuid.uuid4()),
    settings=settings
)
```

Model options:
- `pro`: Enhanced model with advanced capabilities - identical to the Pro model on medisearch.io
- `standard`: Standard model suitable for most queries (default) - identical to the Standard model on medisearch.io

The Pro model offers more comprehensive answers with deeper medical insights, while the Standard model provides solid medical information for common queries at potentially faster response times.

### Suggested Follow-up Questions

MediSearch can provide suggested follow-up questions based on the current conversation:

```python
from medisearch_client import MediSearchClient, Settings

client = MediSearchClient(api_key="your_api_key")

# Request 3 follow-up question suggestions
settings = Settings(followup_count=3)

responses = client.send_message(
    conversation=["What is type 2 diabetes?"],
    conversation_id="diabetes-info",
    settings=settings
)

# Process the responses
for response in responses:
    if response["event"] == "llm_response":
        print("Answer:", response["data"])
    elif response["event"] == "articles":
        print(f"Sources: {len(response['data'])} articles")
    elif response["event"] == "followups":
        print("\nYou might also want to ask:")
        for i, question in enumerate(response["data"], 1):
            print(f"{i}. {question}")
```

To enable follow-up suggestions:

1. Create a `Settings` object with the `followup_count` parameter set to the desired number of questions
2. The API will return a "followups" event containing a list of suggested questions
3. These questions can be used to guide the conversation or present as options to the user

Follow-up suggestions are useful for:
- Helping users discover related information they might want to know
- Guiding less experienced users through a medical topic
- Creating more interactive conversational experiences

## Response Structure

The MediSearch API returns responses with four main event types:

### LLM Response Event

Contains text content generated by the AI:

```json
{
  "event": "llm_response",
  "data": "Text content from the AI..."
}
```

In streaming mode, multiple `llm_response` events will be received as chunks. In non-streaming mode, you'll receive a list that will contain a single consolidated `llm_response` event.

### Articles Event

Contains bibliographic information about source articles, ordered by citation index (more authoritative sources appear first):

```json
{
  "event": "articles",
  "data": [
    {
      "title": "Article Title",
      "authors": ["Author 1", "Author 2"],
      "year": 2023,
      "url": "https://example.com/article",
      "tldr": "Short summary of the article",
      "journal":"Journal of the article"
    },
    ...
  ]
}
```

The articles are automatically sorted by the model's citation index. 

### Followups Event

Contains suggested follow-up questions related to the current query:

```json
{
  "event": "followups",
  "data": [
    "What are the risk factors for diabetes?",
    "How is type 2 diabetes diagnosed?",
    "What lifestyle changes can help manage diabetes?"
  ]
}
```

This event is only sent when the `followup_count` parameter is specified in the Settings object.

### Error Event

Indicates an error condition with the following structure:

```json
{
  "event": "error",
  "id": "conversation_id",
  "data": "error_code_here"
}
```

The `id` field contains the conversation ID that was used in the request, and the `data` field contains the specific error code.

## Error Handling

The MediSearch API may return error events in various situations:

### Error Event Codes

- `error_not_enough_articles`: Not enough relevant articles found. Try rephrasing the question to be more medical in nature or more specific.
- `error_out_of_tokens`: Conversation exceeded maximum allowed length. Start a new conversation or simplify your query.
- `error_internal`: Internal server error that occurred during processing.
- `error_llm`: Error occurred in the language model processing.

### HTTP Errors

Other errors (like authentication issues, rate limiting, etc.) are returned as standard HTTP errors over SSE, not as error events. These include:

- 403: Unable to query due to authentication issues
- 429: Rate limit exceeded
- 500: General server error

### Error Handling Example

```python
from medisearch_client import MediSearchClient

client = MediSearchClient(api_key="your_api_key")

try:
    responses = client.send_message(
        conversation=["What are the best treatments for seasonal allergies?"],
        conversation_id=str(uuid.uuid4())
    )
    
    for response in responses:
        if response["event"] == "error":
            error_code = response["data"]
            if error_code == "error_not_enough_articles":
                print("Not enough medical articles found. Try a more specific question.")
            elif error_code == "error_out_of_tokens":
                print("Conversation is too long. Please start a new one.")
            elif error_code == "error_internal":
                print("Internal server error occurred. Please try again later.")
            elif error_code == "error_llm":
                print("Language model processing error. Please try rephrasing your question.")
            else:
                print(f"An error occurred: {error_code}")
        elif response["event"] == "llm_response":
            print("Answer:", response["data"])
except Exception as e:
    # Handle HTTP errors here
    print(f"Request failed: {str(e)}")
```

## System Prompts

You can customize the style of responses using system prompts:

```python
from medisearch_client import MediSearchClient, Settings

client = MediSearchClient(api_key="your_api_key")

# Create settings with a system prompt
settings = Settings(
    system_prompt="Provide concise bullet-point responses with medical terminology explained",
    followup_count=3  # Also request follow-up questions
)

# Send a message with the custom response style
responses = client.send_message(
    conversation=["What are the symptoms of type 2 diabetes?"],
    conversation_id="diabetes-symptoms",
    settings=settings
)
```

The system prompt allows you to:
- Adjust the response style and format
- Request specific types of explanations
- Control the level of detail in responses

Example system prompts:
- "Provide very brief, bullet-point responses"
- "Explain all medical terminology in simple terms"
- "Focus on practical advice and treatment options"
- "Include statistical data when available"

## License

MIT License - See LICENSE file for details.

For help or questions, contact us at [founders@medisearch.io](mailto:founders@medisearch.io).

For detailed API documentation, visit [MediSearch API Docs](https://medisearch.io/developers).