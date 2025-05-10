import streamlit as st
import pyttsx3
import speech_recognition as sr
import re
import uuid

# Streamlit page configuration
st.set_page_config(page_title="🏡 Smart Home Chatbot", layout="centered")

# Custom CSS for chat interface
st.markdown("""
    <style>
    .user-message {
        background-color: #e6f3ff;
        color: #333;
        border-radius: 10px;
        padding: 10px;
        margin: 5px 10px;
        max-width: 80%;
        float: left;
        clear: both;
        font-size: 15px;
        display: flex;
        align-items: center;
        word-wrap: break-word;
    }
    .assistant-message {
        background-color: #FF8C00;
        color: #fff;
        border-radius: 10px;
        padding: 10px;
        margin: 5px 10px;
        max-width: 80%;
        float: right;
        clear: both;
        font-size: 15px;
        display: flex;
        align-items: center;
        word-wrap: break-word;
    }
    .icon {
        margin-right: 8px;
        font-size: 18px;
    }
    .chat-container {
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# Simulated device states
device_states = {
    "light": {"state": "off", "location": None},
    "tv": {"state": "off", "location": None},
    "thermostat": {"temperature": 22, "location": None},
    "fan": {"state": "off", "location": None},
    "door_lock": {"state": "locked", "location": None},
    "blinds": {"state": "closed", "location": None},
    "speaker": {"state": "off", "playing": None, "location": None},
    "oven": {"state": "off", "temperature": 0, "location": None},
    "vacuum": {"state": "off", "location": None},
    "garage_door": {"state": "closed", "location": None},
    "sprinkler": {"state": "off", "location": None},
    "humidifier": {"state": "off", "level": 50, "location": None},
    "coffee_maker": {"state": "off", "location": None},
    "security_camera": {"state": "off", "location": None}
}

# Expanded sample recipes with YouTube links
recipes = {
    "pasta": {
        "steps": [
            "Boil a pot of water with a pinch of salt.",
            "Add pasta and cook for 8-10 minutes until al dente.",
            "Drain the pasta, reserving 1 cup of pasta water.",
            "Mix with your favorite sauce (e.g., marinara or pesto).",
            "Serve hot with grated Parmesan cheese."
        ],
        "youtube_urls": [
            "https://youtu.be/UfvrcHzv4TQ?feature=shared"
        ]
    },
    "chicken": {
        "steps": [
            "Preheat oven to 375°F (190°C).",
            "Season chicken breasts with salt, pepper, and olive oil.",
            "Place chicken in a baking dish and bake for 25-30 minutes.",
            "Check internal temperature reaches 165°F (74°C).",
            "Let rest for 5 minutes before serving."
        ],
        "youtube_urls": [
            "https://youtu.be/O5MvIQidUVA?feature=shared"
            
        ]
    },
    "pizza": {
        "steps": [
            "Preheat oven to 450°F (230°C).",
            "Roll out pizza dough on a floured surface.",
            "Spread tomato sauce, add cheese, and desired toppings.",
            "Bake for 10-12 minutes until crust is golden.",
            "Slice and serve hot."
        ],
        "youtube_urls": [
            "https://youtu.be/twVKZ5nskto?feature=shared"
            
        ]
    },
    "salad": {
        "steps": [
            "Wash and chop lettuce, tomatoes, cucumbers, and red onions.",
            "Toss vegetables in a large bowl.",
            "Add olive oil, balsamic vinegar, salt, and pepper to taste.",
            "Top with croutons or nuts if desired.",
            "Serve fresh."
        ],
        "youtube_urls": [
            "https://youtu.be/fK6ED8jUvs4?feature=shared"
        ]
    },
    "cake": {
        "steps": [
            "Preheat oven to 350°F (175°C).",
            "Mix flour, sugar, baking powder, eggs, butter, and vanilla extract.",
            "Pour batter into a greased cake pan.",
            "Bake for 25-30 minutes until a toothpick comes out clean.",
            "Let cool and decorate with frosting."
        ],
        "youtube_urls": [
            "https://youtu.be/qtlhdIfojmc?feature=shared"
        ]
    },
    "soup": {
        "steps": [
            "Chop onions, carrots, and celery.",
            "Sauté vegetables in a pot with olive oil.",
            "Add broth, tomatoes, and spices; simmer for 20 minutes.",
            "Add noodles or beans if desired.",
            "Serve hot with bread."
        ],
        "youtube_urls": [
            "https://youtu.be/rdzr91gvNU0?feature=shared"
        ]
    }
}

# Text-to-speech function
def speak(text):
    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', 150)
        engine.setProperty('volume', 1)
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        st.warning(f"Text-to-speech failed: {str(e)}")

# Function to parse and handle commands, including 30 home-related questions
def handle_command(user_input):
    user_input = user_input.lower().strip()

    # Patterns for commands and questions
    patterns = [
        (r"hi|hello", "greeting", "Hello! How can I assist with your smart home or cooking?"),
        (r"thank you", "greeting", "Have a great day!"),
        (r"turn (on|off) the (light|tv|fan|speaker|oven|vacuum|humidifier|coffee_maker|security_camera)(?: in the (\w+))?", "device_toggle", None),
        (r"set the temperature to (\d+)(?: degrees)?(?: in the (\w+))?", "set_temperature", None),
        (r"turn (on|off) the (\w+ light)", "specific_light_toggle", None),
        (r"(lock|unlock) the (door|door_lock)(?: in the (\w+))?", "door_lock", None),
        (r"(open|close) the (blinds|garage_door)(?: in the (\w+))?", "open_close_device", None),
        (r"play (\w+) on the (speaker)(?: in the (\w+))?", "play_music", None),
        (r"set the oven to (\d+)(?: degrees)?(?: in the (\w+))?", "set_oven", None),
        (r"start the (vacuum)(?: in the (\w+))?", "start_vacuum", None),
        (r"turn (on|off) the (sprinkler)(?: in the (\w+))?", "sprinkler_control", None),
        (r"set the humidifier to (\d+)(?: percent)?(?: in the (\w+))?", "set_humidifier", None),
        (r"make coffee(?: in the (\w+))?", "make_coffee", None),
        (r"is the (light|tv|fan|speaker|oven|vacuum|humidifier|coffee_maker|door_lock|blinds|garage_door|sprinkler|security_camera)(?: in the (\w+))? (on|off|locked|unlocked|open|closed|playing)?", "status_check", None),
        (r"what is the temperature(?: in the (\w+))?", "temperature_check", None),
        (r"what is the humidity(?: in the (\w+))?", "humidity_check", None),
        (r"what is the oven temperature(?: in the (\w+))?", "oven_temp_check", None),
        (r"finally thank you", "farewell", "You're welcome! Have a great day!"),
        (r"(?:make|cook) (\w+)(?: in the (\w+))?", "cook_dish", None),
        (r"what recipes can you provide", "list_recipes", None),
        (r"how many devices can you control", "device_count", f"I can control {len(device_states)} devices: light, TV, thermostat, fan, door lock, blinds, speaker, oven, vacuum, garage door, sprinkler, humidifier, coffee maker, and security camera."),
        (r"can you turn on all lights", "all_lights_on", "All lights have been turned on."),
        (r"can you turn off all devices", "all_devices_off", "All devices have been turned off."),
        (r"what is the status of my home", "home_status", None),
        (r"can you set the home to night mode", "night_mode", "Night mode activated: lights dimmed, blinds closed, and security camera on."),
        (r"can you set the home to morning mode", "morning_mode", "Morning mode activated: blinds opened, coffee maker started, and lights turned on."),
        (r"what rooms are supported", "room_list", "I support commands for any room you specify, like living room, bedroom, kitchen, or garden. Just include the room in your command!"),
        (r"can you help me save energy", "energy_saving", "To save energy, turn off unused lights, set the thermostat to 20-22°C, and use the fan instead of air conditioning."),
        (r"what should i cook for dinner", "dinner_suggestion", "How about making pasta? Say 'make pasta' for a recipe and video tutorials!"),
        (r"can you check if the house is secure", "security_check", None),
        (r"how do i use the voice feature", "voice_help", "Click 'Speak Now' in the voice section, say your command clearly, and I’ll respond. Try 'turn on the light' or 'make pizza'!"),
        (r"what can you do", "capabilities", "I can control home devices (like lights, thermostat, or oven), check statuses, provide recipes with video tutorials, and respond to voice or text commands.")
    ]

    for pattern, action, response in patterns:
        match = re.match(pattern, user_input)
        if match:
            if action == "greeting" or action == "farewell" or action == "device_count" or action == "all_lights_on" or action == "all_devices_off" or action == "night_mode" or action == "morning_mode" or action == "room_list" or action == "energy_saving" or action == "dinner_suggestion" or action == "voice_help" or action == "capabilities":
                if action == "all_lights_on":
                    device_states["light"]["state"] = "on"
                elif action == "all_devices_off":
                    for device in device_states:
                        device_states[device]["state"] = "off"
                        if device == "thermostat":
                            device_states[device]["temperature"] = 22
                        elif device == "oven":
                            device_states[device]["temperature"] = 0
                        elif device == "humidifier":
                            device_states[device]["level"] = 50
                        elif device == "speaker":
                            device_states[device]["playing"] = None
                elif action == "night_mode":
                    device_states["light"]["state"] = "off"
                    device_states["blinds"]["state"] = "closed"
                    device_states["security_camera"]["state"] = "on"
                elif action == "morning_mode":
                    device_states["blinds"]["state"] = "open"
                    device_states["coffee_maker"]["state"] = "on"
                    device_states["light"]["state"] = "on"
                return response
            elif action == "device_toggle":
                state, device, location = match.groups()
                if device in device_states:
                    device_states[device]["state"] = state
                    if location:
                        device_states[device]["location"] = location
                        return f"The {device} in the {location} has been turned {state}."
                    return f"The {device} has been turned {state}."
            elif action == "set_temperature":
                temp, location = match.groups()
                temp = int(temp)
                if 10 <= temp <= 30:
                    device_states["thermostat"]["temperature"] = temp
                    if location:
                        device_states["thermostat"]["location"] = location
                        return f"The temperature in the {location} has been set to {temp} degrees."
                    return f"The temperature has been set to {temp} degrees."
                return "Please choose a temperature between 10 and 30 degrees."
            elif action == "specific_light_toggle":
                state, location = match.groups()
                device_states["light"]["state"] = state
                device_states["light"]["location"] = location
                return f"The {location} light has been turned {state}."
            elif action == "door_lock":
                state, _, location = match.groups()
                device_states["door_lock"]["state"] = state
                if location:
                    device_states["door_lock"]["location"] = location
                    return f"The door in the {location} has been {state}."
                return f"The door has been {state}."
            elif action == "open_close_device":
                state, device, location = match.groups()
                device_states[device]["state"] = state
                if location:
                    device_states[device]["location"] = location
                    return f"The {device} in the {location} has been {state}."
                return f"The {device} has been {state}."
            elif action == "play_music":
                music, device, location = match.groups()
                device_states["speaker"]["state"] = "on"
                device_states["speaker"]["playing"] = music
                if location:
                    device_states["speaker"]["location"] = location
                    return f"Playing {music} on the speaker in the {location}."
                return f"Playing {music} on the speaker."
            elif action == "set_oven":
                temp, location = match.groups()
                temp = int(temp)
                if 100 <= temp <= 250:
                    device_states["oven"]["state"] = "on"
                    device_states["oven"]["temperature"] = temp
                    if location:
                        device_states["oven"]["location"] = location
                        return f"The oven in the {location} has been set to {temp} degrees."
                    return f"The oven has been set to {temp} degrees."
                return "Please choose an oven temperature between 100 and 250 degrees."
            elif action == "start_vacuum":
                device, location = match.groups()
                device_states["vacuum"]["state"] = "on"
                if location:
                    device_states["vacuum"]["location"] = location
                    return f"The vacuum in the {location} has been started."
                return f"The vacuum has been started."
            elif action == "sprinkler_control":
                state, device, location = match.groups()
                device_states["sprinkler"]["state"] = state
                if location:
                    device_states["sprinkler"]["location"] = location
                    return f"The sprinkler in the {location} has been turned {state}."
                return f"The sprinkler has been turned {state}."
            elif action == "set_humidifier":
                level, location = match.groups()
                level = int(level)
                if 30 <= level <= 70:
                    device_states["humidifier"]["state"] = "on"
                    device_states["humidifier"]["level"] = level
                    if location:
                        device_states["humidifier"]["location"] = location
                        return f"The humidifier in the {location} has been set to {level}%."
                    return f"The humidifier has been set to {level}%."
                return "Please choose a humidity level between 30 and 70%."
            elif action == "make_coffee":
                location = match.groups()[0]
                device_states["coffee_maker"]["state"] = "on"
                if location:
                    device_states["coffee_maker"]["location"] = location
                    return f"The coffee maker in the {location} is brewing coffee."
                return f"The coffee maker is brewing coffee."
            elif action == "status_check":
                device, location, queried_state = match.groups()
                if device in device_states:
                    current_state = device_states[device]["state"]
                    loc = device_states[device].get("location", None)
                    if device == "speaker" and queried_state == "playing":
                        playing = device_states["speaker"].get("playing", None)
                        if location and location != loc:
                            return f"No {device} in the {location} found."
                        return f"The speaker is {'playing ' + playing if playing else 'not playing'}."
                    if location and location != loc:
                        return f"No {device} in the {location} found."
                    return f"The {device}{' in the ' + loc if loc else ''} is {current_state}."
            elif action == "temperature_check":
                location = match.groups()[0]
                temp = device_states["thermostat"]["temperature"]
                loc = device_states["thermostat"].get("location", None)
                if location and location != loc:
                    return f"No thermostat in the {location} found."
                return f"The temperature{' in the ' + loc if loc else ''} is {temp} degrees."
            elif action == "humidity_check":
                location = match.groups()[0]
                level = device_states["humidifier"]["level"]
                loc = device_states["humidifier"].get("location", None)
                if location and location != loc:
                    return f"No humidifier in the {location} found."
                return f"The humidity{' in the ' + loc if loc else ''} is {level}%."
            elif action == "oven_temp_check":
                location = match.groups()[0]
                temp = device_states["oven"]["temperature"]
                loc = device_states["oven"].get("location", None)
                if location and location != loc:
                    return f"No oven in the {location} found."
                return f"The oven{' in the ' + loc if loc else ''} is set to {temp} degrees."
            elif action == "cook_dish":
                dish, location = match.groups()
                if dish in recipes:
                    steps = "\n\n".join(f"{i+1}. {step}" for i, step in enumerate(recipes[dish]["steps"]))
                    response = f"### Recipe for {dish.capitalize()}\n\n{steps}\n\n*Watch these YouTube videos for guidance:*"
                    return response
                return f"Sorry, I don’t have a recipe for {dish}. Try 'make pasta', 'cook chicken', 'make pizza', 'make salad', 'make cake', or 'make soup'!"
            elif action == "list_recipes":
                recipe_list = ", ".join(recipes.keys())
                return f"I can provide recipes for: {recipe_list}. Try saying 'make [recipe]' for details and YouTube tutorials!"
            elif action == "home_status":
                status = []
                for device, info in device_states.items():
                    loc = info.get("location", None)
                    if device == "thermostat":
                        status.append(f"{device}{' in ' + loc if loc else ''}: {info['temperature']}°C")
                    elif device == "oven":
                        status.append(f"{device}{' in ' + loc if loc else ''}: {info['temperature']}°C, {info['state']}")
                    elif device == "humidifier":
                        status.append(f"{device}{' in ' + loc if loc else ''}: {info['level']}%, {info['state']}")
                    elif device == "speaker":
                        playing = info.get("playing", None)
                        status.append(f"{device}{' in ' + loc if loc else ''}: {info['state']}, {'playing ' + playing if playing else 'not playing'}")
                    else:
                        status.append(f"{device}{' in ' + loc if loc else ''}: {info['state']}")
                return "Home status:\n" + "\n".join(status)
            elif action == "security_check":
                door = device_states["door_lock"]["state"]
                camera = device_states["security_camera"]["state"]
                door_loc = device_states["door_lock"].get("location", None)
                camera_loc = device_states["security_camera"].get("location", None)
                return f"Security check: Door{' in ' + door_loc if door_loc else ''} is {door}, Security camera{' in ' + camera_loc if camera_loc else ''} is {camera}."

    # Stop the chatbot for unrecognized commands
    return "Invalid command. Please try a valid home-related command."

# Function to get response
def get_assistant_response(user_input):
    try:
        return handle_command(user_input)
    except Exception as e:
        return f"Error processing command: {str(e)}. Invalid command. Please try a valid home-related command."

# Streamlit app
st.title("🤖 Smart Home Chatbot with Voice")

# Clear chat history button
if st.button("Clear Chat History"):
    st.session_state.messages = []
    st.success("Chat history cleared!")

# Manage chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
st.markdown('<div class="chat-container">', unsafe_allow_html=True)
for msg in st.session_state.messages:
    if msg[0] == "user":
        st.markdown(f'<div class="user-message"><span class="icon">👤</span>{msg[1]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="assistant-message"><span class="icon">🤖</span>{msg[1]}</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)


# Text input section
user_input = st.chat_input("Ask me anything about your home or recipes...")

if user_input:
    st.session_state.messages.append(("user", user_input))
    st.markdown(f'<div class="user-message"><span class="icon">👤</span>{user_input}</div>', unsafe_allow_html=True)
    with st.spinner("Processing..."):
        reply = get_assistant_response(user_input)
    st.session_state.messages.append(("assistant", reply))
    st.markdown(f'<div class="assistant-message"><span class="icon">🤖</span>{reply}</div>', unsafe_allow_html=True)
    # Display YouTube videos for cooking commands
    match = re.match(r"(?:make|cook) (\w+)(?: in the (\w+))?", user_input.lower().strip())
    if match and match.group(1) in recipes:
        st.markdown("*YouTube Tutorials:*")
        for url in recipes[match.group(1)]["youtube_urls"]:
            st.video(url)
    speak(reply)