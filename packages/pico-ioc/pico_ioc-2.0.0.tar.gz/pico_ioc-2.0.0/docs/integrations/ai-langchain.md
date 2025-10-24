# Integration: AI & LangChain

AI applications, especially those built with libraries like LangChain, are classic examples of "dependency injection" without a container.

A typical LangChain application is a complex graph of objects:
* **LLMs** (e.g., `ChatOpenAI`, `ChatAnthropic`), which require API keys.
* **Prompt Templates**, which hold your business logic.
* **Retrievers** (e.g., a `VectorStore` retriever), which require a database.
* **Chains** (e.g., `RetrievalQA`), which tie all the other pieces together.

**Problem:** This often results in hard-coded, monolithic "factory functions" that build your chain. This code is difficult to configure (e.g., swapping `GPT-4` for `Claude`) and very difficult to test (you can't easily mock the LLM).

```python
# The "hard-coded" way
def create_my_app():
    # Hard-coded keys and models
    llm = ChatOpenAI(api_key="sk-...", model="gpt-4")
    embeddings = OpenAIEmbeddings()
    
    # Hard-coded connection
    db = FAISS.load_local("my_index", embeddings)
    retriever = db.as_retriever()
    
    # Hard-coded logic
    prompt = PromptTemplate(template=...)
    
    # The final object
    chain = RetrievalQA.from_llm(llm=llm, retriever=retriever, prompt=prompt)
    return chain
````

**Solution:** You can use `pico-ioc` to manage all these pieces as **configurable components**. This makes your AI application flexible, testable, and clean.

-----

## 1\. The Pattern: Factories for AI Components

The best pattern is to use `@factory` and `@provides` to create "recipes" for each piece of your AI stack. Your services then just ask for the final `Chain` or `Agent`.

Let's refactor the example above.

### Step 1: Configure API Keys

First, use `@configuration` to load your API keys securely from the environment.

```python
# app/config.py
from dataclasses import dataclass
from pico_ioc import configuration

@configuration(prefix="AI_")
@dataclass
class AiConfig:
    OPENAI_API_KEY: str
    ANTHROPIC_API_KEY: str | None = None
```

### Step 2: Create a Factory for LLMs

Next, create a `@factory` that *depends* on the `AiConfig` and *provides* the LLM components.

```python
# app/llms.py
from langchain_openai import ChatOpenAI
from langchain_core.language_models import BaseChatModel
from pico_ioc import component, factory, provides, primary
from .config import AiConfig

@factory
class LlmFactory:
    def __init__(self, config: AiConfig):
        self.config = config

    @provides(BaseChatModel) # Provide the *interface*
    @primary                 # This is the default LLM
    def build_openai_llm(self) -> BaseChatModel:
        return ChatOpenAI(
            api_key=self.config.OPENAI_API_KEY,
            model="gpt-4o"
        )
    
    # You could add other LLMs here
    # @provides(BaseChatModel)
    # @qualifier("claude")
    # def build_claude_llm(self) -> BaseChatModel:
    #    return ChatAnthropic(...)
```

### Step 3: Create a Factory for Your Chain

Now, create another factory that builds your final chain. This factory can simply *inject* the `BaseChatModel` by its type, without knowing *which* LLM it's getting.

```python
# app/chains.py
from pico_ioc import factory, provides
from langchain_core.language_models import BaseChatModel
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

# Assume you also have a 'Retriever' component
@component
class MyRetriever: ... # This could be a factory too

@factory
class ChainFactory:
    
    # This factory injects the default LLM and Retriever
    def __init__(self, llm: BaseChatModel, retriever: MyRetriever):
        self.llm = llm
        self.retriever = retriever

    @provides(PromptTemplate)
    def build_prompt(self) -> PromptTemplate:
        # Logic is cleanly encapsulated
        template_str = "Answer the question: {question}"
        return PromptTemplate.from_template(template_str)

    @provides(RetrievalQA)
    def build_qa_chain(self, prompt: PromptTemplate) -> RetrievalQA:
        # This builds the final chain, using the
        # injected LLM, Retriever, and the prompt
        # from this same factory.
        return RetrievalQA.from_chain_type(
            llm=self.llm,
            retriever=self.retriever,
            chain_type_kwargs={"prompt": prompt}
        )
```

### Step 4: Use the Chain in Your Service

Your final service is now incredibly simple and clean. It's completely decoupled from *how* the chain is built.

```python
# app/services.py
from pico_ioc import component
from langchain.chains import RetrievalQA

@component
class AiService:
    def __init__(self, qa_chain: RetrievalQA):
        self.qa_chain = qa_chain
        
    def ask_question(self, query: str) -> str:
        # We just use the injected chain
        result = self.qa_chain.invoke({"query": query})
        return result["answer"]
```

-----

## 2\. Benefits of This Pattern

1.  **Testability:** Testing `AiService` is now trivial. You can use `init(overrides={...})` to replace the `RetrievalQA` chain with a simple mock that returns a fixed answer.
    ```python
    # tests/test_ai_service.py
    class MockQaChain:
        def invoke(self, _):
            return {"answer": "mocked answer"}

    container = init(
        modules=["app.services"],
        overrides={RetrievalQA: MockQaChain()}
    )

    service = container.get(AiService)
    assert service.ask_question("test") == "mocked answer"
    ```
2.  **Configurability:** Want to swap `GPT-4o` for `Claude 3`? You only change `LlmFactory`. Your `AiService` and `ChainFactory` don't even know a change happened.
3.  **Separation of Concerns:**
      * `config.py` handles **Keys**.
      * `llms.py` handles **Models**.
      * `chains.py` handles **Prompts and Logic**.
      * `services.py` handles **Business Use**.

This pattern is highly recommended for managing the complexity of modern AI applications.

-----

## Next Steps

This concludes the "Integrations" section. You now have patterns for integrating `pico-ioc` with web frameworks and other complex libraries.

The next section, **Cookbook**, provides complete, copy-paste-ready examples of full architectural patterns.

  * **[Cookbook Overview](./cookbook/README.md)**: Explore common architectural patterns.

