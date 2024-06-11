# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

from typing import Any, Text, Dict, List
from neo4j import GraphDatabase
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import dotenv
import os
import openai

from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from transformers import pipeline

# Load a pre-trained emotion analysis pipeline
URI = "bolt://localhost:7687"
AUTH = ("neo4j", "53ds!6g81ds8nmD_F74982FH89D7ds54gSD")
openai.api_key = os.getenv("OPENAI_API_KEY")
    
class ActionSendToAPI(Action):
    def name(self) -> Text:
        return "action_send_to_api"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # user_input = tracker.latest_message.get('text')
        # print(user_input)
        conversation_history = tracker.events
        active_painting = tracker.get_slot("active_painting")
        stage = tracker.get_slot("stage")
        query= f"""MATCH (p:Paintings)-->(i:Item) WHERE p.name="{active_painting}" RETURN i.name AS name, i.Description AS description"""
        knownObjects = tracker.get_slot("known_objects")
        items=""
        databaseObjects=usefull.callDatabase(query)
        for record in databaseObjects:
            items = items + f"""\nItem: {record['name']}\nDescription: {record['description']}"""
        compare=""  
        if stage == "compare":
            last_active_painting = tracker.get_slot("last_active_painting")
            # favorite_painting = tracker.get_slot("favourite_painting")
            compare = f"The paintings you want the user to compare are {active_painting}, {last_active_painting}."

        instructions = f"""
You are a tour guide trained in Visual Thinking Strategies (VTS). 
You are chatting with a single user who is interested in learning more about the artwork {active_painting}.
Do not describe the artwork, ask open-ended questions to guide the user through it.
If the user tries to talk about another painting , gently guide them back to {active_painting}
You want to do this in 5 stages: observation, describe story, describe author technique, describe feelings and compare.
The current stage is {stage}. Do not go to other stages. Vary the beginnings of your responses.
Here are all the items in the painting: {items}
If the user begins describing objects not in the above list ask them to focus on the items in the painting.
{compare}"""
        messages = usefull.constructPrompt(conversation_history, active_painting, instructions)
        openai_response = usefull.getAPIResponse(messages)
        dispatcher.utter_message(text=openai_response)
        # print(knownObjects)
        if knownObjects is None:
            return [SlotSet('known_objects',  databaseObjects)]
        elif len(knownObjects) < len(databaseObjects)*(30/100):
            return [SlotSet('known_objects',  None)]
        else:
            del messages[0]
            covered_items = usefull.check_chat_for_items(messages[-3:], knownObjects)
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
                    RETURN item[0] AS name, item[1] AS description"""
        materialsAndGenres=""
        databaseObjects=usefull.callDatabase(query)
        for record in databaseObjects:
            materialsAndGenres= materialsAndGenres + f"""\nMaterial: {record['m.name']}\nDescription: {record['m.description']}
Genre: {record['g.name']}\nDescription: {record['g.description']}"""
            
        instructions = f"""
You are a tour guide trained in Visual Thinking Strategies (VTS). 
You are chatting with a single user who is interested in learning more about the artwork {active_painting}.
You want to do this in 5 stages: observation, describe story, describe author technique, describe feelings and compare.
The current stage is {stage}. Do not go to other stages. Ask open-ended questions to guide the user. Vary the beginnings of your responses.
You may describe the techniques if the user is having trouble perceiving or identifying them.
Here are some details genre and materials: {materialsAndGenres}
        """
        print(instructions)
        # Construct the history of conversation
        messages = usefull.constructPrompt(conversation_history, active_painting, instructions)

        # API call
        openai_response = usefull.getAPIResponse(messages)
        print(f"{stage}")

        dispatcher.utter_message(text=openai_response)
        print(materialsAndGenres)
        if materialsAndGenres is None:
            return [SlotSet('known_objects',  databaseObjects)]
        elif len(materialsAndGenres) < len(databaseObjects)*(30/100):
            return [SlotSet('known_objects',  None)]
        else:
            del messages[0]
            covered_items = usefull.check_chat_for_items(messages[-3:], materialsAndGenres)
            return [SlotSet('known_objects', [t for t in materialsAndGenres if t[0] not in covered_items])]
        
class ActionFeelings(Action):
    def name(self) -> Text:
        return "action_feelings_api"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # user_input = tracker.latest_message.get('text')
        conversation_history = tracker.events
        active_painting = tracker.get_slot("active_painting")
        stage = tracker.get_slot("stage")
        instructions = f"""
You are a tour guide trained in Visual Thinking Strategies (VTS). 
You are chatting with a single user who is interested in learning more about the artwork {active_painting}.
You want to do this in 5 stages: observation, describe story, describe author technique, describe feelings and compare.
The current stage is {stage}. Do not go to other stages. Vary the beginnings of your responses.
If the user tries to talk about another painting , gently guide them back to {active_painting}
Do not describe the artwork, prompt the user to give their opinion.
"""
        messages = usefull.constructPrompt(conversation_history, active_painting, instructions)
        openai_response = usefull.getAPIResponse(messages)
        dispatcher.utter_message(text=openai_response)
        return[]

class ActionSendFeelingsToDatabase(Action):
    def name(self) -> Text:
        return "action_send_feelings_to_database"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        feeling = usefull.extract_emotion(tracker.get_slot("current_feeling"))
        query = f"""
                MATCH (n:Paintings) 
                WHERE n.name="{tracker.get_slot("active_painting")}" 
                SET n.feelings= CASE
                    WHEN '{feeling}' IN coalesce(n.feelings, []) THEN n.feelings
                    ELSE n.feelings + '{feeling}'
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
        """
        messages = usefull.constructPrompt(conversation_history, active_painting, instructions)
        print(messages)

        # API call
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
    
    def check_chat_for_items(chat, items, threshold=80):
        for message in chat:
            content = message['content']
            found_items = []
            for name, description in items:
                name_match_score = fuzz.partial_ratio(content.lower(), name.lower())
                # description_match_score = fuzz.partial_ratio(content.lower(), description.lower())
                if name_match_score >= threshold:#or description_match_score>=threshold 
                    found_items.append(name)
        return found_items
    
    def extract_emotion(text):
        predictions = emotion_classifier(text)
        emotions = {pred['label']: pred['score'] for pred in predictions[0]}
        primary_emotion = max(emotions, key=emotions.get)
        return primary_emotion