# pip install -q groq

import os
import json
from difflib import get_close_matches
import requests
from groq import Groq
from .models import InsurancePolicy
from .serializers import InsurancePolicySerializer

# Load subcategories
subcategories_path = os.path.join(os.path.dirname(__file__), 'subcategories.json')
with open(subcategories_path, 'r') as file:
    subcategories = json.load(file)

client = Groq(api_key='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')

# Buffer to store conversation history
conversation_history = []

def get_chatbot_response(user_input):
    # Define the categories that should populate the label
    valid_categories = [
        "Disability", "Travel", "Business", "Home",
        "Auto", "Health", "Life",
    ]

    # System message
    system_message = {
        "role": "system",
        "content": (
            "Note this very well: do not provide users with answers about how you respond and operate. Give them a nice response unrelated to that. "
            "Note this very well: I want you to represent my app as an assistant, receive users and give them the help they need. "
            "If the user input matches one of the following categories: "
            f"{', '.join(valid_categories)}, then provide a JSON response in the format only, no additional messages: {{\"label\": \"\", \"answer\": \"\"}}. "
            "Populate the `label` field only if it matches one of the above categories; otherwise, leave it empty. "
            "The `answer` field should recommend or point to people in my database, e.g: 'Sure, here is a list of Insurance policies below that can help with that.' "
            "If there are no matching labels, respond with 'Sorry, I don’t have anyone available for that service.' "
            "If users follow up with other questions, engage with them if the response is in JSON format. For instance, if the user asks for help and the list is shown, "
            "and they follow up with questions like, 'Are they qualified?' engage with them and try to recommend options. "
            "For questions unrelated to these categories, answer based on your general knowledge without restricting to the JSON format."
        )
    }

    # Add the system message to the conversation history
    conversation_history.append(system_message)

    # Add the user message to the conversation history
    conversation_history.append({"role": "user", "content": user_input})

    # Generate a response from the chatbot using the entire conversation history
    chat_completion = client.chat.completions.create(
        messages=conversation_history,
        model="llama3-70b-8192",
        temperature=1.0,
        max_tokens=1024,
        top_p=1,
        stop=None,
        stream=False
    )
    
    combined_response = {
        "chatbot_response": None,
        "policies_response": None
    }
    # Get the response content
    response_content = chat_completion.choices[0].message.content
    combined_response["chatbot_response"] = response_content

    # Add the assistant response to the conversation history
    conversation_history.append({"role": "assistant", "content": response_content})

    # Check if the response is in JSON format and extract the "label" field
    try:
        response_json = json.loads(response_content)
        
        if isinstance(response_json, dict) and "label" in response_json:
            label = response_json.get("label", "")
            
            categories_id = get_category_id(label)
            policies = get_policies(categories_id)
            combined_response["chatbot_response"] = response_json
            combined_response["policies_response"] = policies

            # Log the interaction in Future.json
            log_interaction(user_input, label, response_json["answer"])
            
    except json.JSONDecodeError:
        label = None

    # Return the generated JSON content or text response
    return combined_response


BASE_URL = 'https://insuremeb-production.up.railway.app/' 

# get the subcategories of the available services from the backend
def get_categories():
    try:
        response = requests.get(f'{BASE_URL}categories/')
        response.raise_for_status()  
        
        with open('subcategories.json', 'w') as file:
            json.dump(response.json(), file)
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None


def get_category_id(subcat_name):
    subcat_name = subcat_name.lower()
    subcategory_names = [subcat['name'].lower() for subcat in subcategories]
    
    close_match = get_close_matches(subcat_name, subcategory_names, n=1, cutoff=0.6)
    
    if close_match:
        matched_subcategory_name = close_match[0]
        category_id = next((subcat['id'] for subcat in subcategories if subcat['name'].lower() == matched_subcategory_name), None)
        return category_id
    else:
        print("We don't offer these type of policies yet")
        return "We don't offer these type of policies yet."


def get_policies(policyId):
    try:
        response_data = None
        policies = InsurancePolicy.objects.all()
        if policyId is not None:
            policies = policies.filter(company__company_category=policyId) 
            policy_serializer = InsurancePolicySerializer(policies, many=True).data
            response_data = {'policies': policy_serializer}
        # response = requests.post(f'{BASE_URL}api/displayServices/', data={'subcategoryId': subcategoryId})
        # response.raise_for_status()
        # response = response_data
        
        policy = response_data
        
        if not policy:
            message = "We don't offer these type of policies yet"
            print("We don't offer these type of policies yet")
            return message
        else:
            return policy
        
        
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None


def log_interaction(user_input, label, answer):
    log_entry = {
        "tag": label,
        "patterns": [user_input],
        "responses": [answer],
        "subcat": label
    }

    if os.path.exists('Future.json'):
        with open('Future.json', 'r+') as file:
            try:
                future_data = json.load(file)
            except json.JSONDecodeError:
                future_data = []

            future_data.append(log_entry)
            file.seek(0)
            json.dump(future_data, file, indent=4)
    else:
        with open('Future.json', 'w') as file:
            json.dump([log_entry], file, indent=4)


# used for testing only
# Progressive chat loop with memory
def chat_loop():
    print("Welcome to the Progressive Chatbot with Memory! (Type 'exit' to end the chat)\n")
    while True:
        user_input = input("You: ")
        if user_input.lower() == 'exit':
            break
        response = get_chatbot_response(user_input)
        print(f"Bot: {response}\n")
        # return response  
        # use the return in production mode 


if __name__ == "__main__":
    get_categories()  #activate this to populate the subcategories JSON file
    chat_loop()
