import requests

def ask_ollama(prompt):
    url = "http://localhost:11434/api/generate"
    data = {
        "model": "llama3",
        "prompt": prompt
    }
    response = requests.post(url, json=data, stream=True)

    answer = ""
    for line in response.iter_lines():
        if line:
            chunk = line.decode("utf-8")
            if '"response":' in chunk:
                part = chunk.split('"response":"')[1].split('"')[0]
                answer += part
    return answer

# Ejemplo de uso
print(ask_ollama("¿Quién fue Alan Turing?"))
