# Fashion Consulting Project

Welcome to the **Fashion Consulting** project! This repository showcases an end-to-end system that:  
- 1. Gathers large-scale clothing data from multiple e-commerce sources,
- 2. Cleans and refines labels for more reliable training,
- 3. Empowers AI models to generate better product descriptions and outfit suggestions(One prompt, multi-part recommendation).


## Tech Stack
**Web & AI Services:** Python, Java, PyTorch, Flask  
**AI api:** gpt-4o, gemini-1.5-Flash  
**Databases:** MySQL, Milvus  
**Tools:** Git, GitHub, Docker, Linux, Markdown  

## Demo

#### Lay Out

![homepage](https://github.com/Hann-Fu/Fashion-Consulting/blob/main/media/homepage.png?raw=true)

![responsepage](https://github.com/Hann-Fu/Fashion-Consulting/blob/main/media/response_page.png?raw=true)


#### Usage

- 1. Enter your daily outfit ideas.
- 2. Choose your gender from the radio buttons.  
- 3. Select your preferred season(s) using the checkboxes (multiple or no selection are allowed).  
- 4. Click the "Submit" button to submit your input.
- 5. Turn to response page, generate the outfit recommendation.
#### Example use case

> **Prompt 1:** A t-shirt printed with genshin impact character, a black cargo pants, and the leather jacket which Jensen Huang always wears

> ![Excited GIF](https://github.com/Hann-Fu/Fashion-Consulting/blob/main/media/9gq0ew.gif?raw=true)

> **Prompt 2:** 一套暖和的，粉色的穿搭。粉色毛茸茸的兔耳朵外套，配一条粉色的时尚运动休闲裤，内搭一个白色T恤印小恐龙图案  
> **English Translation**: A warm and cozy pink outfit: a fluffy pink jacket with bunny ears, paired with trendy pink sporty joggers, and a white T-shirt featuring a small dinosaur print underneath.

> ![Excited GIF](https://github.com/Hann-Fu/Fashion-Consulting/blob/main/media/9gq2wv.gif?raw=true)

> **Prompt 3:** 明日富士山に登る予定なので、North Faceの防風ジャケットと白いインナーTシャツ、そして裏起毛ズボンをください。  
> **English Translation**: I’m planning to climb Mount Fuji tomorrow, so please give me a North Face windproof jacket, a white inner T-shirt, and fleece-lined pants.

> ![Excited GIF](https://github.com/Hann-Fu/Fashion-Consulting/blob/main/media/9gq9q4.gif?raw=true)
## Data Colletion

Source data collected from:

1. **Musinsa**  
   - ~200k fashion items  
   - Labels mostly reliable but sometimes incomplete

2. **Amazon**  
   - ~1M+ clothing items  
   - Labels often noisy, with non-informative descriptions (e.g., “T-shirt could be tagged as ‘umbrella’”)
   - High variety of categories

3. **Additional Kaggle Fraction**  
   - A smaller, well-labeled subset from Kaggle used to **bootstrap** and make classification model.


## Data Process & Baseline Model & Problems
**Main Issues:**  
Because raw e-commerce data can be **noisy** (wrong categories, partial or irrelevant, uninformative descriptions), our cleaning steps include:

### I. Classification

**1. Objective**  
Classify clothing items into appropriate categories (e.g., Tops, Pants, Outerwear) and remove irrelevant items (non-clothing).

---

**2. Model Details**
- **Model Architecture:** DenseNet-121  
- **Loss Function:** Cross-Entropy Loss  
- **Evaluation Metric:** Precision  

---

**3. Datasets**
- **Training Data:** Well-labeled Kaggle Fashion Dataset (100K+ samples)  
- **Evaluation Data:** Musinsa Dataset  

---

**4. Development Environment**
- **Platform:** Google Colab  
- **Framework:** PyTorch  
- **Notebook Tool:** Jupyter  

---

### II. Description Authentation & Baseline Retrieval Prototype

#### Description Authentation
- **Model**: OpenAI CLIP(Contrastive Language-Image Pre-Training)
- **Model Capability**: Project images and descriptions to **embeddings** in a same latent space, and calculate the **similarity score** of image and description pair.
- **Authentation**: Use CLIP processor to make embeddings of our own dataset's image and description pairs, for these similarity score in and below 1st standard deviation, plus description word length < 100, identify as low informative description.

#### Baseline Model
- **Embeddings**: Images and text are converted into embedding vectors using a CLIP processor.
- **Retrieval**: Make embeddings of our dataset then save to a dataframe, execute KNN retrieval for the user's prompt(prompt->embedding->retrieval), matches text to the most similar image or description embeddings.

#### Observations & Issues
- 1. **Performance**: The baseline can make some sense but often fails to meet expectations.  
- 2. **No Evaluation Metric**: Physical criteria (like how “wearable” an item is) are subjective.  
- 3. **Speed**: Processing each query can take ~10s, which is too slow.  
- 4. **Zero-Shot Classification**: Because model'sorigin intention is zero-shot classification for middle has a limited input token size(77); it can’t capture nuanced details in larger prompts.  
- 5. **Specialized Scope**: Model is trained in 2020, and good for more general, simple task.
- 6. **Multi-Type Prompts**: Struggles with prompts referring to multiple items (e.g., tops + pants + outerwear).



## Solution

#### 1 Metrics & Evaluation
- **Approach**: Use OpenAI LLMs (GPT api + function calling) to score recommendation quality.  
- **Flow**:  
  1. Generate synthetic prompts (e.g. 100 variants).  
  2. Produce recommended images.  
  3. Compare with “ground truth.”  
  4. Evaluator model outputs a subjective score.  
  5. Average multiple scores.
  6. Run multiple (e.g. 10) passes then pick the average(eliminate randomness from LLMs).  
---

#### 2 Speed & Persistence
Use **vector database** instead of dataframe for persistence and query.
- **Database**: Switch to Milvus (standalone GPU). Enable  
- **Index**: HNSW(High recall ANN, support dynamic update)
- **Partition** :Partition data to different collections by category for better distribution handling.  
- **Efficiency**: Parallelize queries for high throughput; reduce per-query time from ~10s to ~50ms.

---

#### 3 Prompt Handler
- **Goal**: Analyze user prompts more deeply (beyond simple keywords), able to decompose a single instruction, summarize, speculate the requirements for each part.  
- **Example**: (Women + Summer + A pink outfit with cartoon design.) -> {Tops: Attribute, Pants: Attribute, etc.} 
- **Model**: GPT-4o + Function Calling.

---

#### 4 New Embedding Model: Google Embedding v4
- **Accessability**: Free, ~1500 RPM (requests per minute).  
- **Pros**: Excellent at capturing detailed/rare/up-to-date information.  
- **Cons**: Data will used to improve google's service.

---

#### 5 Description Re-Generation: Google Gemini 1.5 (Beta)
Re-generate description if an item’s description is deemed “low-informative.”
- **Benchmark**: (low similarity score) or (word length < 20) identify as low-informative
- **Model**: Google Gemini-1.5-Flash with function calling
- **Pricing**: Low cost + 300$ free credits for new account

## Authors

Created with by 🌵 [Han Fu](https://github.com/Hann-Fu).  
[![GitHub Badge](https://img.shields.io/badge/-GitHub-181717?style=flat&logo=github&logoColor=white&link=https://github.com/Hann-Fu)](https://github.com/Hann-Fu)  

For more details or meta data for this project. Feel free to get in touch!  
[![Email Badge](https://img.shields.io/badge/-hanfu5799@gmail.com-D14836?style=flat&logo=Gmail&logoColor=white&link=mailto:hanfu5799@gmail.com)](mailto:hanfu5799@gmail.com)

