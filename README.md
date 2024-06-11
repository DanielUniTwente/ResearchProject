# Conversation agent leveraging VTS for preference gathering during an art exhibition

# Instalation
### Prerequisites
        python 3.9.x
        rasa plus version 3.8.x
        neo4j 
        flask 
        fuzzywuzzy
        dotenv
### Setup
* Rasa

    To set up rasa we will make 2 environmental variable
    1. OPENAI_API_KEY that contains your API key
    2. RASA_PRO_BETA_LLM_INTENT to use the LLM intent classifier(might remove)

* Neo4j

    To setup a connection to a Neo4j DBMS you have to assign three variable in the action.py
    1. URI - to the address your DBMS is hosted
    2. USERNAME - the username with which you will access the database
    3. PASSWORD - the password that allows you access

### Usage
To start rasa run this command in terminal.

    `rasa run`

Additionally you will have to run the rasa custom action server to execute custom actions with this in command in another terminal

    `rasa run actions`

To start the UI run the app.py file and go to the specified address

    



