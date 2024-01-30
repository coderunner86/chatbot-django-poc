from django.http import HttpResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
import nltk
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords

def index(request):
    return HttpResponse("Hello, Django!")

# initialize the lemmatizer and stopwords
lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))

url_mapping = {
    'facturacion': 'https://www.factcil.com/facturacion',
    'seguridad_social': 'https://www.factcil.com/seguridad-social',
    'pagos': 'https://www.factcil.com/pagos',
    # Agrega más mapeos según sea necesario
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
            response = f"Para más información sobre {word}, visita: {url_mapping[word]}"
            break

    return Response({'message': response})

    # return the chatbot's response in a JSON format
    return Response({'message': response})