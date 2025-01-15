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

## Data Colletion

We source data from:

1. **Musinsa**  
   - ~200k fashion items  
   - Labels mostly reliable but sometimes incomplete

2. **Amazon**  
   - ~1M+ clothing items  
   - Labels often noisy, with non-informative descriptions (e.g., “T-shirt could be tagged as ‘umbrella’”)
   - High variety of categories

3. **Additional Kaggle Fraction**  
   - A smaller, well-labeled subset from Kaggle used to **bootstrap** or cross-check performance.

### Why Multiple Sources?
- Each data source complements the others:
  - **Mushisan** is smaller but typically more accurate.  
  - **Amazon** is huge for coverage and variety but messy labels.  
  - **Kaggle** portion is well-curated and helps us benchmark performance.

## Data Process & Baseline Model

#### I. Partition
Because raw e-commerce data can be **noisy** (wrong categories, partial or irrelevant descriptions), our cleaning steps include:

1. **Partition & Matching**  
   - Map each product to a standardized class set (tops, pants, shoes, etc.).  
   - Discard incomplete or conflicting label fields.

2. **Model: DenseNet (Cross Entropy)**  
   - We use a CNN (e.g., DenseNet) to identify image-level features.  
   - Cross-entropy classification helps filter out mislabeled items.

3. **Manual Spot Checks**  
   - Especially for the Amazon subset, random samples are checked by hand to ensure the model’s reliability.  
   - We “hold out” subsets of Mushisan and Amazon to measure real-world performance.

Overall, this yields a **cleaned** dataset that is far more reliable than raw e-commerce data. Even though some noise remains, it’s significantly reduced.

#### II. Baseline Description Model

- **CLIP** (or similar text–image embedding models) helps measure similarity 
## Demo

Demo interface designed to collect user input for daily outfit suggestions. It features the following elements:

#### Features

- **Text Input**:  
  A text box where users can type their ideas or prompts related to daily outfits.

- **Gender Selection**:  
  Users can select their gender using radio buttons. The options include:  
  - Not Telling  
  - Man  
  - Woman  
  - Else  

- **Season Selection**:  
  Users can specify one or more preferred seasons by checking the following options:  
  - Spring  
  - Summer  
  - Autumn  
  - Winter  

- **Submit Button**:  
  A button to submit the entered information.

#### Usage

- 1. Enter your daily outfit ideas in the provided text box.  
- 2. Choose your gender from the radio buttons (single choice).  
- 3. Select your preferred season(s) using the checkboxes (multiple selections are allowed).  
- 4. Click the "Submit" button to submit your input.

#### Design

The webpage is designed with a minimalistic layout to ensure simplicity and ease of use.

#### Example use case

> **Prompt 1:** A t-shirt printed with genshin impact character, a black cargo pants, and the leather jacket which Jensen Huang always wears

> ![Excited GIF](https://github.com/Hann-Fu/Fashion-Consulting/blob/main/media/9gq0ew.gif?raw=true)

> **Prompt 2:** 一套暖和的，粉色的穿搭。粉色毛茸茸的兔耳朵外套，配一条粉色的时尚运动休闲裤，内搭一个白色T恤印小恐龙图案  
> **English Translation**: A warm and cozy pink outfit: a fluffy pink jacket with bunny ears, paired with trendy pink sporty joggers, and a white T-shirt featuring a small dinosaur print underneath.

> ![Excited GIF](https://github.com/Hann-Fu/Fashion-Consulting/blob/main/media/9gq2wv.gif?raw=true)

> **Prompt 3:** 明日富士山に登る予定なので、North Faceの防風ジャケットと白いインナーTシャツ、そして裏起毛ズボンをください。  
> **English Translation**: I’m planning to climb Mount Fuji tomorrow, so please give me a North Face windproof jacket, a white inner T-shirt, and fleece-lined pants.

> ![Excited GIF](https://github.com/Hann-Fu/Fashion-Consulting/blob/main/media/9gq9q4.gif?raw=true)
## Authors

Created with by 🌵 [Han Fu](https://github.com/Hann-Fu).  
[![GitHub Badge](https://img.shields.io/badge/-GitHub-181717?style=flat&logo=github&logoColor=white&link=https://github.com/Hann-Fu)](https://github.com/Hann-Fu)  

For more details or meta data for this project. Feel free to get in touch!  
[![Email Badge](https://img.shields.io/badge/-hanfu5799@gmail.com-D14836?style=flat&logo=Gmail&logoColor=white&link=mailto:hanfu5799@gmail.com)](mailto:hanfu5799@gmail.com)

