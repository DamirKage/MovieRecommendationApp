import requests
from .models import Movie

def save_movies_from_api_to_db():
    api_key = 'fc418e4fcf4031275be98156963dc842'
    api_url = f'https://api.themoviedb.org/3/discover/movie?api_key={api_key}&language=en-US&sort_by=popularity.desc&include_adult=false&include_video=false&page=1'

    response = requests.get(api_url)
    if response.status_code == 200:
        movies_data = response.json().get('results', [])

        for movie_data in movies_data:
            # Создание объекта модели Movie и сохранение его в базе данных
            movie = Movie.objects.create(
                title=movie_data.get('title'),
                overview=movie_data.get('overview'),
                release_date=movie_data.get('release_date'),
                # Добавьте остальные поля модели здесь
            )
            # Сохранение объекта модели в базе данных
            movie.save()
    else:
        print('Ошибка при получении данных из API')

# Вызов функции для сохранения фильмов в базе данных
save_movies_from_api_to_db()
