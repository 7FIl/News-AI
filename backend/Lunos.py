import requests

kunci = "sk-dc8cdbffcb44c61768ccd612cbe9788f536e391c2163cfdb"

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