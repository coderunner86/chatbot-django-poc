import os
import json
from django.http import HttpResponse
from requests_html import HTMLSession

from rest_framework.decorators import api_view
from rest_framework.response import Response
import nltk
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
from dotenv import load_dotenv
#scrape_info
import requests
from bs4 import BeautifulSoup
import textrazor
import openai
# Carga las variables de entorno desde el archivo .env
env_path = os.path.join(".", ".env")
load_dotenv(dotenv_path=env_path)

# Obtiene la clave de API de OpenAI desde las variables de entorno
# openai.api_key = os.getenv("OPENAI_API_KEY")
textrazor.api_key = "f971f680d240076f816fc325b488f1550246be6fed21098d0be8b51e"

def extract_links(url):
    # Importa la clase HTMLSession desde requests_html

    # Crea una sesión HTML
    session = HTMLSession()

    # Haz una solicitud GET a la URL de la página que deseas analizar
    
    response = session.get(url)

    # Obtiene todos los enlaces de la página
    links = response.html.absolute_links

    # Crea una lista de tuplas de enlaces similar a url_mappings
    url_links = [(link, link) for link in links]

    # Imprime la lista de enlaces
    return url_links


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

url_mapping = {
    'explicar': 'https://www.factcil.com/how-it-works',
    'precios': 'https://www.factcil.com/pricing',
    'inicio': 'https://www.factcil.com/', 
    'asesor': 'https://api.whatsapp.com/send/?phone=573012128715&text&type=phone_number&app_absent=0',
}

@api_view(['POST'])
def chatbot(request):
    nltk.download('punkt')
    nltk.download('wordnet')
    nltk.download('stopwords')
    lemmatizer = WordNetLemmatizer()
    stop_words = set(stopwords.words('spanish'))
    links=  extract_links(url_mapping['inicio'])
    tel_link = []

    # Itera sobre los enlaces extraídos
    for link in links:
        if link[0].startswith('tel:'):
            tel_link.append(link[0])
    # print("extacted links:", links)
    # print("telefono:", tel_link)
    
    keyword = lambda link: link.split('/')[-1]

    # Crea el diccionario usando la palabra clave y los enlaces
    abs_url = {}
    for link in links:
        key = keyword(link[0])  # Utiliza el enlace del primer elemento como clave
        value = link[1]  # Utiliza el enlace del segundo elemento como valor
        if key not in abs_url:
            abs_url[key] = [value]  # Si la clave no existe en el diccionario, crea una nueva lista con el valor
        else:
            abs_url[key].append(value)  # Si la clave ya existe en el diccionario, agrega el valor a la lista existente
            
    # Imprime el diccionario resultante
    print("Diccionario de URL mapeadas:")
    for key, value in abs_url.items():
        print(key, ":", value)
    for key in url_mapping:
    # Verifica si la clave ya existe en abs_url
        if key not in abs_url:
            # Si la clave no existe, agrégala con una lista vacía como valor inicial
            abs_url[key] = []
    print("Diccionario actualizado:", abs_url)
    message = request.data['message']
    words = nltk.word_tokenize(message.lower())
    words = [word for word in words if word not in stop_words]
    words = [lemmatizer.lemmatize(word) for word in words]
    print("palabras de la consulta: ", words)
    print("openai api key: ", openai.api_key)
    keywords1 = extract_keywords(url_mapping['explicar'])
    keywords2 = extract_keywords(url_mapping['precios'])
    keywords3 = extract_keywords(url_mapping['inicio'])
    keywords = keywords1 + keywords2 + keywords3

    response = ""
    while True:
        for word in words:
            if word in url_mapping or word in abs_url:
                info = scrape_info(url_mapping[word])
                related_keywords = extract_keywords(url_mapping[word])
                print("palabras clave relacionadas: ", related_keywords)
               
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

                        Paso 5: Adicionalmente al contenido de la respuesta\
                        siempre responderás de manera informativa\
                        es decir, con una respuesta que sea escrita en lenguaje natural.\
                        que trate de identificar si la palabra es escrita en ingles o español\
                        y responder con un enlace a la informacion.

                        Utiliza el siguiente formato:
                        Respuesta al usuario:<respuesta de 300 caracteres>
                        Vemos que estas interesado en <razonamiento del paso 1>
                        voy a recabar la informacion <razonamiento del paso 2 o del paso 3>
                    """
                user_messages = f"{message}"

                messages = [
                    {"role": "system", "content": system_messages},
                    {"role": "user", "content": f"{user_messages}"},
                ]
                prompt_intent = ""
                for message in messages:
                    prompt_intent += f"{message['role'].title()}: {message['content']}\n"

                prompt = f"construye una respuesta basada en {prompt_intent}"
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
                    response = f"{text}. Para una atención personalizada escríbenos al: {tel_link}"

                    return Response({"message": response})
            else:
                prompt = f"construye una respuesta general amable y muy corta e informativa al estilo Tweet \
                    tomando como contexto las palabras clave que existen en {keywords} \
                    que sean más similares a la {word} introducida\
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
                response = f"{text}. Para una atención personalizada escríbenos al: {tel_link}"

                return Response({"message": response})
