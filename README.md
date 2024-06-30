# Conversation agent leveraging VTS for opinion forming during an art exhibition

# Instalation
### Prerequisites
        python 3.9.x
        rasa pro/plus version 3.8.x
        openai
        neo4j 
        flask 
        spaCy
        dotenv
### Setup
* Rasa

    To set up rasa make the following environmental variable
    1. OPENAI_API_KEY that contains your API key

* Neo4j

    To setup a connection to a Neo4j DBMS you have to assign three variable in the databaseCredentials.txt file
    1. URI - to the address your DBMS is hosted
    2. USERNAME - the username with which you will access the database
    3. PASSWORD - the password that allows you access

### Usage
To start rasa run this command in terminal.

    rasa run

To run the rasa custom action server, which allows execution of custom actions run this command in a different terminal

    rasa run actions

To start the UI run the app.py file and go to the specified address

    



