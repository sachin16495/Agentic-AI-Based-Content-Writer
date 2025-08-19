# Repo Content- 
**Content_Writing_Agent.ipynb**  
  Jupyter Notebook containing the content writing agent code along with sample outputs.

**Dash_APP_LLM_Content_Writer_Agent.py**  
  Dash-based user interface for interacting with the content writing agent.
  
**README.md**  
  Documentation of the project, setup, and usage details.

**Screen.jpg**  
  Screenshot of the UI screen output with youtube link https://www.youtube.com/watch?v=u0uV6N-T0U8  

**content_writer_structure.png**  
  Graph representation of the agent workflow structure.

# Content Writing Agent

A modular, state-driven system for automated content generation.
The workflow integrates **topic analysis, reference gathering, expert content writing, keyword validation, and feedback refinement**, ensuring accuracy, adaptability, and alignment with user objectives.

---
# Here’s a demonstration of the Content Writing Agent.
[![Watch the demo](https://github.com/sachin16495/Agentic-AI-Based-Content-Writer/blob/main/Screen.jpg)](https://www.youtube.com/watch?v=u0uV6N-T0U8 "Click to play")

## Graph Structure
![alt text](https://github.com/sachin16495/Agentic-AI-Based-Content-Writer/blob/main/content_writer_structure.png)


This is a **LangGraph workflow**  I’ve designed for a **content-writing agent**, and the nodes represent different processing steps. Let’s walk through it step by step:

---

###  Structure Breakdown

1. **`__start__`**

   * Entry point of the graph. Execution begins here.

2. **`topic_analyser`**

   * First node after start.
   * Likely takes in the user’s input (topic, audience, goal, etc.).
   * Decides how to branch out (which type of article to generate).

3. **`reference_article`**

   * Gathers supporting material for the chosen topic.
   * Could involve **retrieving reference documents** (via RAG, web search, or internal dataset).
   * Acts as the “knowledge base entry point” for writers.

---

###  Branching Writers

From `reference_article`, the workflow branches into **four specialized content writers** based on the type of content:

* **`education_content_writer`** → creates content in an educational tone (tutorials, explainers).
* **`marketing_content_writer`** → generates persuasive/marketing-style content (ads, product posts).
* **`social_content_writer`** → produces social-media-optimized content (short, catchy).
* **`technical_content_writer`** → writes technical documentation, guides, research-style text.

> The dotted lines (`education`, `marketing`, etc.) indicate **conditional edges**:
> depending on the topic/goal, the graph routes to the right writer.

---

###  `content_keyword_analysis_report`

* This is the **convergence point** after writing content.
* All writers feed their drafts into this node.
* Purpose:

  * Extract keywords.
  * Analyze  SEO potential, trending terms.
  * Generate a structured report about the produced content.
* Marked with `__interrupt = after`, which means execution pauses for feedback here → you can surface results to the user (like in your Dash app), and optionally resume.

---

###  `feedback_node`

* After keyword analysis, the workflow moves here.
* Could collect user feedback, rating, or allow editing.
* This ensures a **human-in-the-loop** step before finalization.

---

###  `__end__`

* Terminates the workflow.
* Means either content is finalized, or feedback loop is complete.

---



## State Definition

The system state maintains the flow of information across nodes:

* **topic\_name (str)** → User-defined subject of the content.
* **type\_audience (str)** → Target audience (students, professionals, researchers, etc.).
* **reference\_content (dict)** → External reference material (Wikipedia extracts).
* **topic\_setup (dict)** → Preprocessing and contextual details from topic analysis.
* **content (List\[str])** → Generated content sections.
* **goal (str)** → Content objective (`marketing`, `social`, `technical`, `education`).
* **feedback (str)** → Reviewer feedback for refinement.
* **word\_count (int)** → Expected/actual word length.
* **content\_keyword (dict)** → Keyword frequency & alignment report.

---

##  Tool Initialization

### 1. Keyword Trend Analysis Tool (Google SERP API)

* **Input:** Keyword/topic string
* **Process:** Query Google Trends API for related and rising topics
* **Output:** `top_keywords`, `rising_keywords`
* **Use Case:** Ensures generated content matches current audience interest.

### 2. Wikipedia Search Tool

* **Input:** Topic string
* **Process:** Fetch Wikipedia content (max 5000 chars)
* **Output:** Reference text
* **Use Case:** Grounds generated content with factual, external knowledge.

---

##  Topic Analysis

**Function:** `topic_analyser`

* Builds query for Google Trends API
* Extracts:

  * `rising_keywords` (fast-growing popularity)
  * `top_keywords` (high-ranking related topics)
* Updates system state → `topic_setup`

---

##  Research & Reference

**Function:** `reference_article`

* Uses Wikipedia API to fetch article reference
* Adds structured reference to `reference_content` in state

---

##  Expert Content Writers

All expert writers consume:

* `topic_name`, `type_audience`, `word_count`, `reference_content`, and goal

Outputs → Structured Markdown content

### Writers:

* **Technical Content Writer** → Detailed, accurate technical docs/blogs
* **Social Media Content Writer** → Engaging, shareable posts
* **Marketing Content Writer** → Persuasive, product-driven text (scarcity/urgency optional)
* **Education Content Writer** → Structured tutorials, learning modules

---

##  Keyword Analysis

**Function:** `content_keyword_analysis_report`

* Compares generated content vs `rising_keywords` and `top_keywords`
* Tracks alignment in `content_keyword` dictionary

Process:

1. Match rising keywords in content → `dic_rising_keyword`
2. Match trending keywords → `dic_trending_keyword`
3. Store matches in `analysis_keyword`
4. Update system state

---

##  Goal-Oriented Routing

**Function:** `goal_oriented`

* Routes workflow to correct expert writer:

  * `marketing` → `marketing_content_writer`
  * `social` → `social_content_writer`
  * `technical` → `technical_content_writer`
  * `education` → `education_content_writer`

---

##  Feedback Loop

**Function:** `feedback_node`

* Exposes content for review → `interrupt("Please provide feedback")`
* Captures feedback → updates `feedback` in state
* Rewrites content with improvements
* Stores revised output in `content`

---

##  Graph Structure

### Nodes

* `topic_analyser` → Extract trending keywords
* `reference_article` → Fetch Wikipedia references
* `goal_oriented` → Route to expert writer
* `technical_content_writer` / `social_content_writer` / `marketing_content_writer` / `education_content_writer`
* `content_keyword_analysis_report` → Validate keyword alignment
* `feedback_node` → Human-in-the-loop refinement

### Execution Flow

```
Start
  ↓
topic_analyser
  ↓
reference_article
  ↓
goal_oriented ──> [expert writer node]
  ↓
content_keyword_analysis_report
  ↓
feedback_node
  ↺ (iterative refinement)
```

---






