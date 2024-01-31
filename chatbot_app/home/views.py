import os
import json
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

api_key = os.getenv("OPENAI_API_KEY")

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
    print("palabras de la consulta: ", words)

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
                print("palabras clave relacionadas: ", related_keywords)
                system_message = f"Para más información sobre {word}, visita: {url_mapping[word]}"
                system_messages = f"""
                        Sigue estos pasos para responder a las consultas de los clientes.
                        La consulta del cliente no tiene un formato, puede ser una palabra o frase,\
                        es decir, no es estructurada y puede tener caracteres especiales o emojí.

                        Paso 1: Primero decide si el usuario está \
                        haciendo una pregunta con una palabra en la \
                        lista de palabras clave {related_keywords}.

                        Paso 2: Si la entrada del usuario esta en la lista de palabras claves,\
                        analiza si el usuario hizo alguna suposición, \
                        averigua si la suposición es cierta basada en la \
                        información que hay en {info} \

                        Paso 3: Si el mensaje contiene las palabras \
                        asesoramiento, freelancer, independiente o creador de contenido \
                        has un llamado a la accion ofreciendo los planes que hay en {url_mapping['precios']}.

                        Paso 4: Si el usuario dice que se ha equivocado en la consulta \
                        , corrige cortésmente las \
                        suposiciones incorrectas del cliente si corresponde. \
                        Solo menciona o referencia informacion de {info} \
                        Responde al cliente en un tono amigable.

                        Utiliza el siguiente formato:
                        Respuesta al usuario:<respuesta cortas al cliente tipo Tweets>
                        Vemos que estas interesado en <razonamiento del paso 1>
                        voy a recabar la informacion <razonamiento del paso 2 o del paso 3>

                        """
                user_messages = f"""
                        {message}"""

                messages = [
                        {"role": "system", "content": system_messages},
                        {
                            "role": "user",
                            "content": f"{user_messages}",
                        },
                    ]
                prompt_intent = ""
                    
                for message in messages:
                    prompt_intent += f"{message['role'].title()}: {message['content']}\n"
                # print("prompt del chatbot: ", prompt_intent)
                prompt = f"construye una respuesta basada en {prompt_intent}"
                API_KEY	= os.getenv("OPENAI_API_KEY")
                openai.api_key = "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"
                option_role = messages[1]['role']
                option_content = messages[1]['content']
     
                while not option_content == "exit":
                    response = openai.Completion.create(
                        engine="gpt-3.5-turbo-instruct",
                        prompt=prompt,
                        temperature=1.0,
                        max_tokens=500
                        )
                    response = json.dumps(response, indent=2)
                    data = json.loads(response)
                    text = data['choices'][0]['text']
                    response = text.encode('ascii', 'ignore').decode('ascii')
                    print("respuesta del chatbot: ", response)
                    response = str(response)
                    output = True
                    break
            else:
                #generar un sistema de rol user tipo langchain pero con la base de conocimientos de keywords
                #este conjunto de keywords son el contexto en el que el agente debe entender la entrada
                
                
                prompt = f"construye una respuesta general amable y muy corta al estilo Tweet \
                    tomando como contexto las palabras clave que existen en {keywords} \
                    que sean mas similares a la {word} introducida\
                    por el usuario sin mencionar las palabras clave y terminando con un emoji"
                openai.api_key = "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"
                
                response = openai.Completion.create(
                        engine="gpt-3.5-turbo-instruct",
                        prompt=prompt,
                        temperature=1.0,
                        max_tokens=100
                        )
                response = json.dumps(response, indent=2)
                data = json.loads(response)
                text = data['choices'][0]['text']
                response = text.encode('ascii', 'ignore').decode('ascii')
                print("respuesta del chatbot: ", response)
                response = f'{response}'
                output = True
                break
            
    return Response({'message': response})

