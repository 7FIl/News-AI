import requests
import os
from dotenv import load_dotenv

load_dotenv()

kunci = os.getenv("LUNOS_API_KEY")

url = "https://api.lunos.tech/v1/chat/completions"
body = {
  "stream": False,
  "model": "google/gemma-3-27b-it",
  "temperature": 0.1,
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "do you understand indonesian language input?"
        }
      ]
    }
  ]
}
response = requests.request("POST", url, json = body, headers = {
  "Content-Type": "application/json",
  "Authorization": f'Bearer {kunci}'
})

print(response.text)