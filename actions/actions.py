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
        stage = tracker.get_slot("stage")
        query = f"""MATCH (p:Paintings)-->(i:Item) 
                    WHERE p.name="{active_painting}" 
                    OPTIONAL MATCH (c:Content)<--(p)
                    UNWIND [[i.name, coalesce(i.Description, 'No description available')], [c.name, coalesce(c.description, 'No description available')]] AS item
                    WITH item WHERE item[0] IS NOT NULL
                    RETURN DISTINCT item[0] AS name, item[1] AS description
                """
        knownObjects = tracker.get_slot("known_objects") 
        databaseObjects=usefull.callDatabase(query)
        databaseItems=""
        for record in databaseObjects:
            databaseItems = databaseItems + f"""Object: {record['name']} Description: {record['description']}"""
        instructions = f"""
You are a tour guide trained in Visual Thinking Strategies (VTS). 
You are chatting with a single user who is interested in learning more about the artwork {active_painting}.
Do not describe the artwork, ask open-ended questions to guide the user through it.
If it is the beginning of the conversation, ask "What do you see?". 
Comment on and commend their observations. You can give only one description and one question per response. Keep responses short if possible.
If the user wants to talk about a specific item ask a question about it. 
Ensure all of your responses transition smoothly with the latest message in the conversation. Always finish with a question.
If the user tries to talk about another painting , gently guide them back to {active_painting}.
You want to do this in 4 stages. The current stage is {stage}. Vary the beginnings of your responses. Do not say the stage.
Here is a list of items with descriptions of what is in the painting:
{databaseItems}.
If the user mentions an item without describing it, prompt them to describe it.
Do not use the description of items when forming a question about them. Do not talk or make up items that are not in the list.
If the user begins describing objects not in the above list prompt them with one of them.
"""
        messages = usefull.constructPrompt(conversation_history, active_painting, instructions)
        openai_response = usefull.getAPIResponse(messages)
        dispatcher.utter_message(text=openai_response)
        # remove mentioned items from knownObjects
        if knownObjects is None:
            return [SlotSet('known_objects',  databaseObjects)]
        elif len(knownObjects) <= len(databaseObjects)*(50/100):
            return [SlotSet('no_objects',  True), SlotSet('known_objects',  None)]
        else:
            del messages[0]
            covered_items = usefull.check_mentions(messages[-3:], knownObjects)
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
        databaseItems=""
        materialsAndGenres=tracker.get_slot("known_objects")
        databaseObjects=usefull.callDatabase(query)
        for record in databaseObjects:
            databaseItems= databaseItems + f"""Name: {record['name']} Description: {record['description']}"""
        instructions = f"""
You are a tour guide trained in Visual Thinking Strategies (VTS). 
You are chatting with a single user who is interested in learning more about the artwork {active_painting}.
You want to do this in 5 stages. The current stage is {stage}. 
Do not describe the artwork, ask open-ended questions to guide the user through it.
Comment on and commend their observations. You can give only one description and one question per response. Keep responses short if possible.
Ensure all of your responses transition smoothly with the latest message in the conversation. Always finish with a question.
You may describe the techniques if the user is having trouble perceiving or identifying them.
Here are the genres and materials used in the painting: 
{databaseItems}.
Do not talk about items not in the list.
        """
        messages = usefull.constructPrompt(conversation_history, active_painting, instructions)
        openai_response = usefull.getAPIResponse(messages)
        dispatcher.utter_message(text=openai_response)

        # remove mentioned entries from knownObjects
        if materialsAndGenres is None:
            return [SlotSet('known_objects',  databaseObjects)]
        elif len(materialsAndGenres) < len(databaseObjects)*(50/100):
            return [SlotSet('no_objects',  True), SlotSet('known_objects',  None)]
        else:
            del messages[0]
            covered_items = usefull.check_mentions(messages[-3:], databaseObjects)
            return [SlotSet('known_objects', [t for t in databaseObjects if t[0] not in covered_items])]
        
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
                interpretations = interpretations + f" {item}"
        instructions = f"""
You are a tour guide trained in Visual Thinking Strategies (VTS). 
You are chatting with a single user who is interested in learning more about the artwork {active_painting}.
You want to do this in 5 stages. The current stage is {stage}.
You want to make them think about symbolism and meaning. Vary the beginnings of your responses.
Keep responses short if possible. Always finish with a question. Do not ask multiple questions in a single response.
If the user tries to talk about another painting , gently guide them back to {active_painting}.
If the last message in the chat was describing an item, commend their observation and transition to the current stage.
Here is a list of interpreations assosiated with the painting: {interpretations}.
They are not described by the user. You may use one of them as an example.
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
Summarize the conversation regarding the painting {active_painting} in no more than 5 bullet points.
Use the information from the conversation and this description of the artwork:{description} 
Do not ask the user any more questions.
        """
        messages = usefull.constructPrompt(conversation_history, active_painting, instructions)
        openai_response = usefull.getAPIResponse(messages)
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
        query = f"""MATCH (p:Paintings)-->(i:Item) 
                    WHERE p.name="{active_painting}" 
                    OPTIONAL MATCH (c:Content)<--(p)
                    UNWIND [[i.name, coalesce(i.Description, 'No description available')], [c.name, coalesce(c.description, 'No description available')]] AS item
                    WITH item WHERE item[0] IS NOT NULL
                    RETURN DISTINCT item[0] AS name, item[1] AS description
                """
        conversation_history = tracker.events
        databaseObjects=usefull.callDatabase(query)
        query = f"""MATCH (g:Genre)<--(n:Paintings)-[on_MATERIAL]->(m:Material)
                    WHERE n.name = "{active_painting}"
                    UNWIND [[m.name, m.description], [g.name, g.description]] AS item
                    RETURN DISTINCT item[0] AS name, item[1] AS description
                """
        databaseMaterialsAndGenres=usefull.callDatabase(query)
        items=""
        materialsAndGenres=""
        for record in databaseObjects:
            items = items + f""" Object: {record['name']} Description: {record['description']}"""
        for record in databaseMaterialsAndGenres:
            materialsAndGenres = materialsAndGenres + f""" Name: {record['name']} Description: {record['description']}"""
        instructions = f"""
You are a tour guide trained in Visual Thinking Strategies (VTS).
You are chatting with a single user who is interested in learning more about the artwork {active_painting}.
The user is struggling to perceive or identify items in the painting. Help them by describing the item they are asking about.
If the user is asking for your opinion, start the description with "I think" or similar.
Ensure all of your responses transition smoothly with the latest message in the conversation.
If the user tries to talk about another painting , gently guide them back to {active_painting}.
Keep your responses short. Do not ask the user any questions.
Here is a list of items with descriptions:{items}.
Here is a list of genres and materials used in the painting:{materialsAndGenres}.
if the user tries to talk about an item not in the list tell them that is not in the painting and describe one that is.
if the user is not talking about the painting ask them to focus on the painting.
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

    def check_mentions(chat, items, threshold=0.60):
        chat_embeddings = [usefull.embed_text(entry['content'], nlp) for entry in chat]
        item_embeddings = [(name, usefull.embed_text(name, nlp), usefull.embed_text(description, nlp) if description else None) 
                        for name, description in items]
        results = []
        for item_name, name_embedding, desc_embedding in item_embeddings:
            mentioned = False
            for chat_embedding in chat_embeddings:
                name_similarity = 1 - cosine(chat_embedding, name_embedding)
                if name_similarity > threshold:
                    mentioned = True
                    break
                
                if desc_embedding is not None:
                    desc_similarity = 1 - cosine(chat_embedding, desc_embedding)
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
        