import os
from openai import OpenAI

from django.http import HttpResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
import nltk
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords

#scrape_info
import requests
from bs4 import BeautifulSoup

#textrazor analyzer
import textrazor
import openai
openai.api_key = "0rnmuNshQSBUaIQnk3BuT3BlbkFJNWvzDBRwHbCSGz6NEmLP"
# os.getenv("TEXTRAZOR")
textrazor.api_key = "f971f680d240076f816fc325b488f1550246be6fed21098d0be8b51e"
def extract_keywords(url):
    client = textrazor.TextRazor(extractors=["entities", "topics"])
    response = client.analyze_url(url)
    keywords = [entity.id for entity in response.entities()]
    return keywords

def scrape_info(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    textos = [p.get_text().strip() for p in soup.find_all('p')]
    info = ' '.join(textos)
    return info

def index(request):
    return HttpResponse("Hello, Django!")

# initialize the lemmatizer and stopwords
lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))

url_mapping = {
    'explicar': 'https://www.factcil.com/how-it-works',
    'precios': 'https://www.factcil.com/pricing',
    'inicio': 'https://www.factcil.com/',
}

@api_view(['POST'])
def chatbot(request):
    nltk.download('punkt')
    nltk.download('wordnet')
    nltk.download('stopwords')
    lemmatizer = WordNetLemmatizer()
    stop_words = set(stopwords.words('spanish'))

    message = request.data['message']
    words = nltk.word_tokenize(message.lower())
    words = [word for word in words if word not in stop_words]
    words = [lemmatizer.lemmatize(word) for word in words]

    response = 'No estoy seguro de cómo ayudar. ¿Puedes ser más específico?'

    keywords1 = extract_keywords(url_mapping['explicar'])
    keywords2 = extract_keywords(url_mapping['precios'])
    keywords3 = extract_keywords(url_mapping['inicio'])
    #keywords es una lista de listas
    keywords = keywords1 + keywords2 + keywords3
    # Utiliza un enfoque de tipo switch para determinar la respuesta
    for word in words:
        if word in url_mapping:
            info = scrape_info(url_mapping[word])
            related_keywords = extract_keywords(url_mapping[word])
            response = f"{related_keywords}. Para más información sobre {word}, visita: {url_mapping[word]}"
            message = f"construye una respuesta basada en {info} con las palabras clave que existen en {keywords}"
            client = OpenAI(
            # This is the default and can be omitted
            # api_key=os.getenv("OPENAI_API_KEY"),
            api_key="0rnmuNshQSBUaIQnk3BuT3BlbkFJNWvzDBRwHbCSGz6NEmLP",
            )

            response = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": message,
                    }
                ],
                model="gpt-3.5-turbo",
            )
            
            break
        else:
            #generar un sistema de rol user tipo langchain pero con la base de conocimientos de keywords
            #este conjunto de keywords son el contexto en el que el agente debe entender la entrada
            message = f"construye una respuesta general con las palabras clave que existen en {keywords} que sean mas similares a la {word} introducida por el usuario"
            response = openai.Completion.create(
                engine="text-davinci-002",
                prompt=message,
                max_tokens=1000
            ).choices[0].text
            
    return Response({'message': response})

