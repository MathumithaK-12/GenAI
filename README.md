23rd july
Invoking a model (LlaMA) by inferencing using groq api

steps
1. Prompted in ChatGPT to get the code for inferencing using groq

Prompt -
How to Invoke a model in google collab  using groq api

2. create a api key in groq
https://console.groq.com

3. Used the code by embedding the key from groq in Google collab



24th july

Use case preparation
AI support analyst for CMS pack failures

The AI agent should raise a incident based on the user information like order id and container id 

If the cms error response is known the agent will respond with reason and close the log

If the agent is unaware of the error, it should be invoking the email to the team IT with the incident details



Prompt used

Say we are creating a new ai chat agent model for remedy style itsm

Consider a rookie is trying this and want to use open source llms , groq for inferencing and google colab 

Also wanted to create a synthetic data using faker for implementing this

Create a synthetic data with order id container id timestamp and error response from cms including both positive and negative response for around 500 records

Also tell how to train or fine the model which are building now using unsloth

Finally also include a script to invoke a mail to it team when the error reason is not found

Give a detailed step by by step procedure to achieve the end goal


If the user just says they are facing issue with printing
But not given any order id or container 
Will the agent ask for the details

