import requests

kunci = "sk-33XlE-C9aGoU3M0ZRkMFVkFgYEqENs9PxnO55vzfhBOiOvHstzfYQRHIOTjfyraC"

url = "https://api.unli.dev/v1/chat/completions"
body = {
  "stream": False,
  "model": "unli-auto",
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