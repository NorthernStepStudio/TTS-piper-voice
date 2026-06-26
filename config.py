VOICES = [
    {"id": "en-US-AvaNeural",         "name": "Ava",         "gender": "Female", "style": "Natural, warm"},
    {"id": "en-US-EmmaNeural",        "name": "Emma",        "gender": "Female", "style": "Natural, friendly"},
    {"id": "en-US-JennyNeural",       "name": "Jenny",       "gender": "Female", "style": "Conversational"},
    {"id": "en-US-AriaNeural",        "name": "Aria",        "gender": "Female", "style": "Expressive"},
    {"id": "en-US-MichelleNeural",    "name": "Michelle",    "gender": "Female", "style": "Clear, professional"},
    {"id": "en-US-AndrewNeural",      "name": "Andrew",      "gender": "Male",   "style": "Natural, warm"},
    {"id": "en-US-BrianNeural",       "name": "Brian",       "gender": "Male",   "style": "Natural, friendly"},
    {"id": "en-US-ChristopherNeural", "name": "Christopher", "gender": "Male",   "style": "Deep, professional"},
    {"id": "en-US-EricNeural",        "name": "Eric",        "gender": "Male",   "style": "Clear, confident"},
    {"id": "en-US-GuyNeural",         "name": "Guy",         "gender": "Male",   "style": "Expressive"},
    {"id": "en-US-RogerNeural",       "name": "Roger",       "gender": "Male",   "style": "Calm, articulate"},
]

VALID_VOICE_IDS = {v["id"] for v in VOICES}
VALID_FORMATS   = {"mp3", "wav"}
MAX_CHARS       = 5000
DEFAULT_VOICE   = "en-US-AvaNeural"
DEFAULT_FORMAT  = "mp3"
