# AI-Interview
Interview Task

All imports used are in the requirements.txt file 

Make the app with FastAPI to make sure async works as well as pydantic schema validation.

Schema classes are defined through pydantic to ensure correctness in output and for a structured output.

Since Ollama was not working I left it as it is, my python interpreter on vscode is not working properly.

To ensure the outputs were structured, we use pydantic for schema validation.

For flutter, it is not 1 to 1 but there should be a similarity within the apps, however my flutter is not working, hence I could not add screenshots.

Ollama should be used since it should be offline and local, meaning it is good for prototyping and easy to use.

To ensure there is no false injection of data into the model, I make sure to trust only the system message or the rule thats set, and anything else should be untrusted.
