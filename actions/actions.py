# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

from typing import Any, Coroutine, Text, Dict, List
from neo4j import GraphDatabase
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
from rasa_sdk.events import Restarted
import dotenv
import os
import openai
from rasa_sdk.types import DomainDict
import spacy
from scipy.spatial.distance import cosine

nlp = spacy.load('en_core_web_md')
# Load a pre-trained emotion analysis pipeline
load_status = dotenv.load_dotenv("actions/databaseCredentials.txt")
if load_status is False:
    raise RuntimeError('Environment variables not loaded.')

URI = os.getenv("NEO4J_URI")
AUTH = (os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
openai.api_key = os.getenv("OPENAI_API_KEY")

class ActionSendToAPI(Action):
    def name(self) -> Text:
        return "action_send_to_api"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        conversation_history = tracker.events
        active_painting = tracker.get_slot("active_painting")
        print(active_painting)
        stage = tracker.get_slot("stage")
        query = f"""MATCH (c:Content)<--(p:Paintings)-->(i:Item) 
                    WHERE p.name="{active_painting}" 
                    UNWIND [[i.name, i.Description], [c.name, c.description]] AS item
                    RETURN DISTINCT item[0] AS name, item[1] AS description"""
        knownObjects = tracker.get_slot("known_objects")
        items=""
        compare="" 
        databaseObjects=usefull.callDatabase(query)
        # if stage == "observation" or stage == "describe story":
        items="In the painting there are one person and some items. Here is a list of them that the user has not yet mentioned:"
        for record in databaseObjects:
            items = items + f"""\nItem: {record['name']}\nDescription: {record['description']}"""
        items = items + "\nDo not talk or make up items that are not in the list.\nIf the user begins describing objects not in the above list prompt them with one of them.\nIf the user is struggling to perceive or identify an item, you may describe it."
        instructions = f"""
You are a tour guide trained in Visual Thinking Strategies (VTS). 
You are chatting with a single user who is interested in learning more about the artwork {active_painting}.
Do not describe the artwork, ask open-ended questions to guide the user through it.
If it is the beginning of the conversation, ask "What do you see?". 
Comment on and commend their observations.Ask one question at a time and keep your responses short if possible. Always finish with a question.
If the user tries to talk about another painting , gently guide them back to {active_painting}
You want to do this in 4 stages. The current stage is {stage}. Vary the beginnings of your responses. Do not say the stage.
{items}
Try to describe items in the painting before using them in questions.
{compare}
"""
        messages = usefull.constructPrompt(conversation_history, active_painting, instructions)
        openai_response = usefull.getAPIResponse(messages)
        dispatcher.utter_message(text=openai_response)
        print(stage)
        # remove mentioned items from knownObjects
        if knownObjects is None:
            return [SlotSet('known_objects',  databaseObjects)]
        elif len(knownObjects) <= len(databaseObjects)*(50/100):
            print("we should transition to the next stage")
            return [SlotSet('no_objects',  True), SlotSet('known_objects',  None)]
        else:
            del messages[0]
            covered_items = usefull.check_mentions(messages[-3:], knownObjects)
            print([t for t in knownObjects if t[0] not in covered_items])
            return [SlotSet('known_objects', [t for t in knownObjects if t[0] not in covered_items])]  

class ActionAuthorTechnique(Action):    
    def name(self) -> Text:
        return "action_author_technique_api"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # user_input = tracker.latest_message.get('text')
        conversation_history = tracker.events
        active_painting = tracker.get_slot("active_painting")
        stage = tracker.get_slot("stage")
        
        query = f"""MATCH (g:Genre)<--(n:Paintings)-[on_MATERIAL]->(m:Material)
                    WHERE n.name = "{active_painting}"
                    UNWIND [[m.name, m.description], [g.name, g.description]] AS item
                    RETURN DISTINCT item[0] AS name, item[1] AS description"""
        materialsAndGenres=""
        knownObjects=usefull.callDatabase(query)
        for record in knownObjects:
            materialsAndGenres= materialsAndGenres + f"""\nItem: {record['name']}\nDescription: {record['description']}"""
            
        instructions = f"""
You are a tour guide trained in Visual Thinking Strategies (VTS). 
You are chatting with a single user who is interested in learning more about the artwork {active_painting}.
You want to do this in 5 stages. The current stage is {stage}. 
Ask open-ended questions to guide the user. Comment on and commend their observations. Vary the beginnings of your responses. 
Ask one question at a time and keep your responses short if possible.
If the last message in the chat was describing an item, commend their observation and transition to the current stage.
You may describe the techniques if the user is having trouble perceiving or identifying them.
Here are some details on genre and materials that the user has not yet mentioned: {materialsAndGenres}
Do not talk about items not in the list.
        """
        messages = usefull.constructPrompt(conversation_history, active_painting, instructions)
        openai_response = usefull.getAPIResponse(messages)
        print(f"{stage}")
        dispatcher.utter_message(text=openai_response)

        # remove mentioned entries from knownObjects
        if materialsAndGenres is None:
            return [SlotSet('known_objects',  knownObjects)]
        elif len(materialsAndGenres) < len(knownObjects)*(50/100):
            return [SlotSet('no_objects',  True), SlotSet('known_objects',  None)]
        else:
            del messages[0]
            covered_items = usefull.check_mentions(messages[-3:], knownObjects)
            return [SlotSet('known_objects', [t for t in knownObjects if t[0] not in covered_items])]
        
class ActionInterpretation(Action):
    def name(self) -> Text:
        return "action_interpretation_api"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # user_input = tracker.latest_message.get('text')
        conversation_history = tracker.events
        active_painting = tracker.get_slot("active_painting")
        stage = tracker.get_slot("stage")   
        database_inter=usefull.get_interpretations(active_painting)
        interpretations = ""
        if database_inter is not None:
            for item in database_inter:
                interpretations = interpretations + f"\n{item}"
        instructions = f"""
You are a tour guide trained in Visual Thinking Strategies (VTS). 
You are chatting with a single user who is interested in learning more about the artwork {active_painting}.
You want to do this in 5 stages. The current stage is {stage}. Vary the beginnings of your responses.
If the user tries to talk about another painting , gently guide them back to {active_painting}
If the last message in the chat was describing an item, commend their observation and transition to the current stage.
Here is a list of interpreations assosiated with the painting: {interpretations} 
They are not described by the user. You may use one of them as an example if the user is struggling.
"""
        
        messages = usefull.constructPrompt(conversation_history, active_painting, instructions)
        openai_response = usefull.getAPIResponse(messages)
        dispatcher.utter_message(text=openai_response)
        return[]

class ActionSendInterpretationToDB(Action):
    def name(self) -> Text:
        return "action_send_interpretation_to_database"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        interpretation = tracker.get_slot("current_interpretation")
        query = f"""
                MATCH (n:Paintings) 
                WHERE n.name="{tracker.get_slot("active_painting")}" 
                SET n.interpretations= CASE
                    WHEN '{interpretation}' IN coalesce(n.feelings, []) THEN n.feelings
                    ELSE coalesce(n.feelings, []) + '{interpretation}'
                END
                """
        usefull.callDatabase(query)
        return []
    
class ActionSummarize(Action):
    def name(self) -> Text:
        return "action_summarize"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # user_input = tracker.latest_message.get('text')
        conversation_history = tracker.events
        active_painting = tracker.get_slot("active_painting")
        query = f"""MATCH (n:Paintings) WHERE n.name="{active_painting}" RETURN n.exhibit"""
        description = usefull.callDatabase(query)[0].data()["n.exhibit"]
        instructions = f"""
You are a tour guide trained in Visual Thinking Strategies (VTS). 
You are chatting with a single user who is interested in learning more about the artwork {active_painting}.
Summarize the conversation regarding the painting {active_painting} in no more than 5 bullet points.
Use the information from the conversation and this description of the artwork:{description} 
Do not ask the user any more questions.
        """
        messages = usefull.constructPrompt(conversation_history, active_painting, instructions)
        openai_response = usefull.getAPIResponse(messages)
        print(openai_response)
        dispatcher.utter_message(text=openai_response)
        return [] 
    
class ActionResetConversation(Action):
    def name(self) -> Text:
        return "action_reset_conversation"
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        return [Restarted()]

class ActionResetKnownObjects(Action):
    def name(self) -> Text:
        return "action_reset_known_objects"
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        return [SlotSet('known_objects',  None)]
    
class ActionGiveDescription(Action):
    def name(self) -> Text:
        return "action_give_description"
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        active_painting = tracker.get_slot("active_painting")
        query = f"""MATCH (c:Content)<--(p:Paintings)-->(i:Item) 
                    WHERE p.name="{active_painting}" 
                    UNWIND [[i.name, i.Description], [c.name, c.description]] AS item
                    RETURN DISTINCT item[0] AS name, item[1] AS description"""
        conversation_history = tracker.events
        databaseObjects=usefull.callDatabase(query)
        items=""
        for record in databaseObjects:
            items = items + f"""\nItem: {record['name']}\nDescription: {record['description']}"""
        instructions = f"""
You are a tour guide trained in Visual Thinking Strategies (VTS).
You are chatting with a single user who is interested in learning more about the artwork {active_painting}.
The user is struggling to perceive or identify items in the painting. Help them by describing the item they are asking about.
Keep your responses short. Do not ask the user any questions.
Here is a list of items with descriptions:{items}
"""
        messages = usefull.constructPrompt(conversation_history, active_painting, instructions)
        openai_response = usefull.getAPIResponse(messages)
        dispatcher.utter_message(text=openai_response)
        return []

class usefull():
    def constructPrompt(conversation_history, active_painting, instructions):
        current_painting = None
        messages = [{"role": "system", "content": instructions}]
        for event in conversation_history:
            if event.get("event") == "slot" and event.get("name") == "active_painting":
                current_painting = event.get("value")
            if current_painting == active_painting:
                if event.get("event") == "user":
                    messages.append({"role": "user", "content": event.get("text")})
                elif event.get("event") == "bot":
                    messages.append({"role": "assistant", "content": event.get("text")})
        return messages
    
    def callDatabase(query):
        with GraphDatabase.driver(URI, auth=AUTH) as driver:
            driver.verify_connectivity()
            records, summary, keys = driver.execute_query(
                query,
                database_="neo4j",
            )
        return records
    
    def getAPIResponse(messages):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=150,
                n=1,
                stop=None,
                temperature=0.9,
            )
            openai_response = response['choices'][0]['message']['content'].strip()
        except Exception as e:
            openai_response = f"Sorry, I encountered an error: {str(e)}"
        return openai_response
    
    def embed_text(text, nlp_model):
        doc = nlp_model(text)
        return doc.vector

    def check_mentions(chat, items, threshold=0.65):
    # Embed chat
        chat_embeddings = [usefull.embed_text(entry['content'], nlp) for entry in chat]
        
        # Embed item names and descriptions separately
        item_embeddings = [(name, usefull.embed_text(name, nlp), usefull.embed_text(description, nlp) if description else None) 
                        for name, description in items]
        
        results = []
        for item_name, name_embedding, desc_embedding in item_embeddings:
            mentioned = False
            for chat_embedding in chat_embeddings:
                # Check similarity with item name
                name_similarity = 1 - cosine(chat_embedding, name_embedding)
                # print(f"Similarity for item name '{item_name}': {name_similarity}")
                if name_similarity > threshold:
                    mentioned = True
                    break
                
                # Check similarity with item description if it exists
                if desc_embedding is not None:
                    desc_similarity = 1 - cosine(chat_embedding, desc_embedding)
                    # print(f"Similarity for item description of '{item_name}': {desc_similarity}")
                    if desc_similarity > threshold:
                        mentioned = True
                        break

            if mentioned:
                results.append(item_name)
        
        return results
    
    # def extract_emotion(text):
    #     predictions = emotion_classifier(text)
    #     emotions = {pred['label']: pred['score'] for pred in predictions[0]}
    #     primary_emotion = max(emotions, key=emotions.get)
    #     return primary_emotion
    
    def get_interpretations(panting):
        query = f"""
                MATCH (n:Paintings) 
                WHERE n.name="{panting}" 
                RETURN n.interpretation
                """
        return usefull.callDatabase(query)[0].data()["n.interpretation"]
        