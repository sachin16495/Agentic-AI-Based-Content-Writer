import dash
from dash import dcc, html, Input, Output, State, callback
import dash_bootstrap_components as dbc
from langgraph.graph import StateGraph, END
#import lang
import os
from serpapi import GoogleSearch
from langchain.agents import initialize_agent, AgentType
from typing import TypedDict,List
from langchain_core.tools import tool
from langgraph.types import Command, interrupt
from typing import Annotated

from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper
import content_writer_config

os.environ["OPENAI_API_KEY"] = content_writer_config.openai_key


class Content_State(TypedDict):
    topic_name:str
    audiance_type: str
    reference_content :dict={}
    keyword_analaysis: dict={}
    topic_setup :dict= {}
    content:List[str]
    type_audience:str
    goal:str
    feedback:str
    word_count:int
    content_keyword:dict={}

@tool
def wikipedia_search(query: str) -> str:
    """Search Wikipedia and return a short summary for  reference a given query."""
    wiki_wrapper = WikipediaAPIWrapper(top_k_results=1, doc_content_chars_max=5000)
    
    wiki_result = wiki_wrapper.load(query=query)
    wiki_reference="\n\n".join([pg_cont.page_content for pg_cont in wiki_result ])
    return wiki_reference
@tool
def trend_and_topic_extraction(query: str) -> dict:
    '''
    Search the query on google search trend and extract the breakout related topic and high rated keywords
    '''
    params = {"engine": "google_trends","q": query,"data_type": "RELATED_TOPICS","api_key": content_writer_config.serpapi_key}
    search = GoogleSearch(params)
    trend_analytics = search.get_dict()
    topic_setup_dict={}

    rising_keyword={trend_analytics['related_topics']['rising'][i]['topic']['title'].lower():trend_analytics['related_topics']['rising'][i]['value'] for i in range(0,len(trend_analytics['related_topics']['rising']))}
    top_keyword={trend_analytics['related_topics']['top'][i]['topic']['title'].lower():trend_analytics['related_topics']['top'][i]['value'] for i in range(0,len(trend_analytics['related_topics']['top']))}
    
    topic_setup_dict['top_related_topic']=top_keyword
    topic_setup_dict['top_rising_topic']=rising_keyword

    return topic_setup_dict

def feedback_processor(topic_name,content,feedback):
    print("Feedback Node")
    llm = ChatOpenAI(model="o3",max_output_tokens=5000,  model_kwargs={"reasoning": {"effort": "medium"}})
    """Pause after content generation to collect feedback."""
    # Interrupt returns content to external process for feedback
    if feedback!=None:
        prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You are a senior content writer. Write useful and accurante"),
      ("user",
         " For the Topic: {topic_name} with feedback rewrite the content {feedback}" 
         "Don't add irrelevant header"
         "Deliverable: a complete article in markdown format highlighting necessary keywords")])
        chain = prompt | llm | StrOutputParser()
        #cs["feedback"] = feedback
        
        article = chain.invoke({"topic_name":topic_name,"feedback":feedback})
        
        # Once resumed, feedback will be merged into state
        
    return article

def topic_analyser(cs:Content_State):
    topic_setup_dict=trend_and_topic_extraction.invoke(cs['topic_name'])
    
 #    topic_setup_dict={'top_related_topic': {'large language model': '100',
 #  'master of laws': '29',
 #  'artificial intelligence': '16',
 #  'law': '6',
 #  'data': '5',
 #  'application programming interface': '4',
 #  'university': '4',
 #  'github': '3',
 #  'openai': '3',
 #  'retrieval-augmented generation': '3',
 #  'python': '3',
 #  'ollama': '3',
 #  'open source': '3',
 #  'language model': '3',
 #  'llama': '2',
 #  'training': '2',
 #  'hugging face': '2',
 #  'august': '2',
 #  'notebook': '2',
 #  'intelligent agent': '2',
 #  'deepseek': '1',
 #  'notebooklm': '1',
 #  'model context protocol': '1',
 #  'qwen': '1'},
 # 'top_rising_topic': {'deepseek': 'Breakout',
 #  'model context protocol': 'Breakout',
 #  'august': 'Breakout',
 #  'retrieval-augmented generation': '+3,350%',
 #  'notebooklm': '+2,750%',
 #  'qwen': '+2,500%',
 #  'cursor': '+850%',
 #  'intelligent agent': '+850%',
 #  'notebook': '+800%',
 #  'revenue': '+500%',
 #  'ollama': '+180%',
 #  'application programming interface': '+60%'}}
    
    cs['topic_setup']=topic_setup_dict

    return cs

def reference_article(cs:Content_State):
    query = list(cs['topic_setup']['top_related_topic'].keys())[0]
    #query=query['topic']['title']
    
    wiki_reference=wikipedia_search.invoke(query)
    cs['reference_content']=wiki_reference
    return cs


def technical_content_writer(cs:Content_State):
    print("Technical Content Writer")
    llm = ChatOpenAI(model="o3",max_output_tokens=5000,  model_kwargs={"reasoning": {"effort": "medium"}})
    
    prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are a senior technical content strategist. Write useful and accurante article"),
    ("user",
     " Using list of Topic: {topic} which is relevent to {topic_name} generate a article for Audience: {audience} in {word_count} words \n" 
     "Don't add irrelevant header"
     "Deliverable: a complete article in markdown format highlighting necessary keywords")])
    chain = prompt | llm | StrOutputParser()
    
    article = chain.invoke({
    "topic_name": cs['topic_name'],
    "topic": [tplist for tplist in cs['topic_setup']['top_related_topic'].keys()],
    "audience": cs['type_audience'],
    "reference":cs['reference_content'],
    "word_count":cs['word_count']
    })
    cs['content']=article
    return cs


    


def social_content_writer(cs:Content_State):
    print("Social media Content Writer")
    llm = ChatOpenAI(model="o3",max_output_tokens=5000,  model_kwargs={"reasoning": {"effort": "medium"}})
    
    prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are a senior social media content strategist. Write useful which can produce lots of engagement among audiance"),
  ("user",
     " Using list of Topic: {topic} which is relevent to {topic_name} generate a article for Audience: {audience} in  {word_count} words \n" 
     "Don't add irrelevant header"
     "Deliverable: a complete article in markdown format highlighting necessary keywords")])
    chain = prompt | llm | StrOutputParser()
    
    article = chain.invoke({
    "topic_name": cs['topic_name'],
    "topic": [tplist for tplist in cs['topic_setup']['top_related_topic'].keys()],
    "audience": cs['type_audience'],
    "reference":cs['reference_content'],
    "word_count":cs['word_count']
    })
    cs['content']=article
    return cs


def marketing_content_writer(cs:Content_State):
    print("Marketing Content Writer")
    llm = ChatOpenAI(model="o3",max_output_tokens=5000,  model_kwargs={"reasoning": {"effort": "medium"}})
    
    prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are a senior marketting content writer. Write useful article which can promote the topic if need add scarcity "),
   ("user",
     " Using list of Topic: {topic} which is relevent to {topic_name} generate a article for Audience: {audience} in {word_count} words\n" 
     "Don't add irrelevant header"
     "Deliverable: a complete article in markdown format highlighting necessary keywords")])
    chain = prompt | llm | StrOutputParser()
    
    article = chain.invoke({
    "topic_name": cs['topic_name'],
    "topic": [tplist for tplist in cs['topic_setup']['top_related_topic'].keys()],
    "audience": cs['type_audience'],
    "reference":cs['reference_content'],
    "word_count":cs['word_count']})
    cs['content']=article
    return cs



def education_content_writer(cs:Content_State):
    print("Education Content Writer")
    llm = ChatOpenAI(model="o3",max_output_tokens=5000,  model_kwargs={"reasoning": {"effort": "medium"}})
    
    prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are a senior content strategist and great teacher. Write useful and accurante"),
  ("user",
     " Using list of Topic: {topic} which is relevent to {topic_name} generate a article for Audience: {audience} in {word_count} words\n" 
     "Don't add irrelevant header"
     "Deliverable: a complete article in markdown format highlighting necessary keywords")])
    chain = prompt | llm | StrOutputParser()
    
    article = chain.invoke({
    "topic_name": cs['topic_name'],
    "topic": [tplist for tplist in cs['topic_setup']['top_related_topic'].keys()],
    "audience": cs['type_audience'],
    "reference":cs['reference_content'],
    "word_count":cs['word_count']})
    cs['content']=article
    return cs

def content_keyword_analysis_report(cs:Content_State):
    print("Content Analysis")
    #content,key_analysis_dictionary
    dic_rising_keyword={}
    dic_trending_keyword={}
    analysis_keyword={}
    #dic_input=cs['input']
    for word in cs['topic_setup']['top_rising_topic'].keys():
        if word in cs['content'].replace("*","").lower():
            #print(word,rising_keyword[word])
            dic_rising_keyword[word]=cs['topic_setup']['top_rising_topic'][word]
    for word in cs['topic_setup']['top_related_topic'].keys():
        if word in cs['content'].replace("*","").lower():
            #print(word,trending_keyword[word])
            dic_trending_keyword[word]=cs['topic_setup']['top_related_topic'][word]
    analysis_keyword['rising_keyword']=dic_rising_keyword
    analysis_keyword['trending_keyword']=dic_trending_keyword
    
    #dic_input={"input":{"content":cs['content'],'keyword_analysis':cs['topic_setup']}}
    cs['content_keyword']= analysis_keyword
    return cs
#def reference_content_generation(cs:Content_State):
def goal_oriented(cs: Content_State):
    """ The node will select the next node of the graph"""
    tone = cs.get("goal", "marketing")
    if cs['goal']=="marketing":
        return "marketing"
    elif cs["goal"]=="social":
        return "social_media"
    elif cs["goal"]=="technical":
        return "technical"
    elif cs["goal"]=="education":
        return "education"


def feedback_node(cs: Content_State):
    print("Feedback Node")
    llm = ChatOpenAI(model="o3",max_output_tokens=5000,  model_kwargs={"reasoning": {"effort": "medium"}})
    """Pause after content generation to collect feedback."""
    # Interrupt returns content to external process for feedback
    cs["feedback"] = feedback
    if cs["feedback"]!=None:
        feedback = interrupt("Please provide feedback:")
        prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You are a senior content writer. Write useful and accurante"),
      ("user",
         " For the Topic: {topic_name} with feedback rewrite the content {feedback}" 
         "Don't add irrelevant header"
         "Deliverable: a complete article in markdown format highlighting necessary keywords")])
        chain = prompt | llm | StrOutputParser()
        #cs["feedback"] = feedback
        
        article = chain.invoke({"topic_name": cs['topic_name'],"feedback":cs['feedback']})
        cs['content']=article
        # Once resumed, feedback will be merged into state
        
    return cs
content_writer = StateGraph(Content_State)


content_writer.add_node('topic_analyser',topic_analyser)
content_writer.add_node('reference_article',reference_article)

#builder1.add_node('reference_article',reference_article)

content_writer.add_node('technical_content_writer',technical_content_writer)
content_writer.add_node('social_content_writer',social_content_writer)
content_writer.add_node('marketing_content_writer',marketing_content_writer)
content_writer.add_node('education_content_writer',education_content_writer)
content_writer.add_node("feedback_node", feedback_node)
content_writer.add_node("content_keyword_analysis_report", content_keyword_analysis_report)

#content_writer.add_edge(START,'topic_extraction')
content_writer.add_edge(START,'topic_analyser')
content_writer.add_edge('topic_analyser','reference_article')
#builder1.add_edge('reference_article','content_generation')
#builder1.add_node("tone_condition", lambda builder1: builder1)

#builder1.add_edge("reference_article","tone_condition")
content_writer.add_conditional_edges("reference_article",goal_oriented,
                           {
                               "marketing":"marketing_content_writer",
                               "social_media":"social_content_writer",
                               "technical":"technical_content_writer",
                               "education":"education_content_writer"})


content_writer.add_edge("technical_content_writer", "content_keyword_analysis_report")
content_writer.add_edge("marketing_content_writer", "content_keyword_analysis_report")
content_writer.add_edge("social_content_writer", "content_keyword_analysis_report")
content_writer.add_edge("education_content_writer", "content_keyword_analysis_report")
content_writer.add_edge("content_keyword_analysis_report", "feedback_node")


app=content_writer.compile(interrupt_after=['content_keyword_analysis_report'])

dash_app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

dash_app.layout = dbc.Container([
    html.H1("Agentic Content Writer", className="mb-4 text-center"),
    
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Input Parameters", className="card-title"),
                    dbc.Input(id="topic-input", placeholder="Enter topic name", type="text"),
                    
                    html.Label("Content Goal", className="mt-3"),
                    dcc.Dropdown(
                        id="goal-dropdown",
                        options=[
                            {'label': 'Technical Writer', 'value': 'technical'},
                            {'label': 'Social Media Writer', 'value': 'social'},
                            {'label': 'Education Content', 'value': 'education'},
                            {'label': 'Marketing Content', 'value': 'marketing'}
                        ],
                        placeholder="Select content goal"
                    ),
                    
                    html.Label("Target Audience", className="mt-3"),
                    dbc.Input(id="audience-input", placeholder="e.g. Developers, Students", type="text"),
                    
                    html.Label(f"Word Count: 200", id="word-count-label", className="mt-3"),
                    dcc.Slider(
                        id="word-count-slider",
                        min=50,
                        max=500,
                        step=50,
                        value=200,
                        marks={i: str(i) for i in range(50, 501, 50)}
                    ),
                    
                    dbc.Button("Generate Content", id="generate-btn", color="primary", className="mt-4 w-100"),
                    html.H5("Feedback:"),
                    dbc.Input(id="feedback-input", placeholder="Enter feedback", type="text"),
                    dbc.Button("Submit", id="feedback-btn", color="primary", className="mt-4 w-100"),
                    
                ])
            ])
        ], md=4),
        dbc.Col([
            dbc.Tabs([
                dbc.Tab(
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("Generated Content", className="card-title mb-4"),
                            dcc.Loading(
                                id="loading-content",
                                type="circle",
                                children=html.Div(id="output-content", className="mt-3", 
                                                style={'whiteSpace': 'pre-line'})
                            )
                        ])
                    ]), 
                    label="Content"
                ),
                dbc.Tab(
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("Keyword Analysis", className="card-title mb-4"),
                            dbc.Row([
                                dbc.Col([
                                    html.H5("Rising Keywords", className="text-center mb-3"),
                                    html.Div(id="rising-keywords-table")
                                ], md=6),
                                dbc.Col([
                                    html.H5("Top Keywords", className="text-center mb-3"),
                                    html.Div(id="top-keywords-table")
                                ], md=6)
                            ])
                        ])
                    ]), 
                    label="Keyword Analysis"
                )
        

        
    ])])])
], fluid=True)

@callback(
    Output("word-count-label", "children"),
    Input("word-count-slider", "value")
)
def update_word_count_label(value):
    return f"Word Count: {value}"

@callback(
    Output("output-content", "children"),
    Output("rising-keywords-table", "children"),
    Output("top-keywords-table", "children"),
    Input("generate-btn", "n_clicks"),
    
    State("topic-input", "value"),
    
    State("goal-dropdown", "value"),
    State("audience-input", "value"),
    State("word-count-slider", "value"),
    prevent_initial_call=True
)
    
def generate_content(n_clicks, topic, goal, audience, word_count):
    if not all([topic, goal, audience]):
        return "Please fill all input fields!"
    
    # Create initial state
    state = {
        "topic_name": topic,
        "goal": goal,
        "type_audience": audience,
        "word_count": word_count
    }
    
    # Execute the graph
    try:
        for output in app.stream(state):
            for key, value in output.items():
                state.update(value)
        rising_keywords=state['content_keyword']['rising_keyword']
        trending_keywords=state['content_keyword']['trending_keyword']
        rising_rows = []
        if rising_keywords:
            for keyword, value in state['content_keyword']['rising_keyword'].items():
                rising_rows.append(
                    html.Tr([
                        html.Td(keyword),
                        html.Td(value)
                    ])
                )
        rising_table = dbc.Table(
            [html.Thead(html.Tr([html.Th("Keyword"), html.Th("Score")]))] +
            [html.Tbody(rising_rows)],
            bordered=True, hover=True, responsive=True
        ) if rising_keywords else html.P("No rising keywords found", className="text-muted")
        
        # Top keywords table
        top_rows = []
        #cs
        if trending_keywords:
            for keyword, value in state['content_keyword']['trending_keyword'].items():
                top_rows.append(
                    html.Tr([
                        html.Td(keyword),
                        html.Td(value+"%")
                    ])
                )
        top_table = dbc.Table(
            [html.Thead(html.Tr([html.Th("Keyword"), html.Th("Score")]))] +
            [html.Tbody(top_rows)],
            bordered=True, hover=True, responsive=True
        ) if trending_keywords else html.P("No top keywords found", className="text-muted")


        
        # Format output
        return html.Div([
            html.H4("Final Content:"),
            dcc.Markdown(state.get("content", "No content generated")),
            html.P(),
            html.Hr(),
            #html.P(state.get("keywords", "No keywords")),
            
        ]),rising_rows,top_rows
            
    
    except Exception as e:
        return f"Error generating content: {str(e)}"

if __name__ == "__main__":
    dash_app.run(debug=True,port=8083)
