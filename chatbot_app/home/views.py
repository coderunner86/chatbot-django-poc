from django.http import HttpResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
import nltk
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords

#scrape_info
import requests
from bs4 import BeautifulSoup

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
    'explain': 'https://www.factcil.com/how-it-works',
    'pricing': 'https://www.factcil.com/pricing',
    'home': 'https://www.factcil.com/',
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

    # Utiliza un enfoque de tipo switch para determinar la respuesta
    for word in words:
        if word in url_mapping:
            info = scrape_info(url_mapping[word])
            response = f"{info}. Para más información sobre {word}, visita: {url_mapping[word]}"
            break

    return Response({'message': response})

