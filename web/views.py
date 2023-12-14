from django.contrib.auth import authenticate, login
from django.contrib.auth import logout
from django.shortcuts import render,get_object_or_404,redirect
from django.db.models import Q
from django.http import Http404
from .models import Movie,Myrating
from django.contrib import messages
from .forms import UserForm
from django.db.models import Case, When
from .recommendation import Myrecommend
import numpy as np 
import pandas as pd
import requests
from django.shortcuts import render
from .models import Movie

# Функция для запроса к API TMDb для поиска фильмов по тексту
def search_movies_by_title(query):
    api_key = 'fc418e4fcf4031275be98156963dc842'  
    url = f'https://api.themoviedb.org/3/search/movie?api_key={api_key}&query={query}'
    
    response = requests.get(url)
    if response.status_code == 200:
        results = response.json()
        return results.get('results', [])  # Возвращает список результатов
    else:
        return None

def recommend(request):
    if not request.user.is_authenticated:
        return redirect("login")
    if not request.user.is_active:
        raise Http404
    
    # Получение количества уникальных пользователей из Myrating
    df = pd.DataFrame(list(Myrating.objects.all().values()))
    nu = df.user_id.unique().shape[0]
    
    # Получение текущего идентификатора пользователя
    current_user_id = request.user.id
    
    # Проверка, если новый пользователь не оценивал ни одного фильма
    if current_user_id > nu:
        movie = Movie.objects.get(id=15)
        q = Myrating(user=request.user, movie=movie, rating=0)
        q.save()

    print("Current user id: ", current_user_id)
    
    # Вызов Myrecommend для получения прогнозов
    prediction_matrix, Ymean = Myrecommend()
    
    # Использование current_user_id в качестве индекса
    my_predictions = prediction_matrix[:, current_user_id - 1] + Ymean.flatten()
    pred_idxs_sorted = np.argsort(my_predictions)
    pred_idxs_sorted[:] = pred_idxs_sorted[::-1]
    pred_idxs_sorted = pred_idxs_sorted + 1
    
    preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(pred_idxs_sorted)])
    movie_list = list(Movie.objects.filter(id__in=pred_idxs_sorted).order_by(preserved)[:10])
    
    return render(request, 'web/recommend.html', {'movie_list': movie_list})



# List view
def index(request):
	movies = Movie.objects.all()
	query  = request.GET.get('q')
	if query:
		movies = Movie.objects.filter(Q(title__icontains=query)).distinct()
		return render(request,'web/list.html',{'movies':movies})
	return render(request,'web/list.html',{'movies':movies})


# detail view
def detail(request,movie_id):
	if not request.user.is_authenticated:
		return redirect("login")
	if not request.user.is_active:
		raise Http404
	movies = get_object_or_404(Movie,id=movie_id)
	#for rating
	if request.method == "POST":
		rate = request.POST['rating']
		ratingObject = Myrating()
		ratingObject.user   = request.user
		ratingObject.movie  = movies
		ratingObject.rating = rate
		ratingObject.save()
		messages.success(request,"Ваш рейтинг отправлен ")
		return redirect("index")
	return render(request,'web/detail.html',{'movies':movies})


# Register user
def signUp(request):
	form =UserForm(request.POST or None)
	if form.is_valid():
		user      = form.save(commit=False)
		username  =	form.cleaned_data['username']
		password  = form.cleaned_data['password']
		user.set_password(password)
		user.save()
		user = authenticate(username=username,password=password)
		if user is not None:
			if user.is_active:
				login(request,user)
				return redirect("index")
	context ={
		'form':form
	}
	return render(request,'web/signUp.html',context)				


# Login User
def Login(request):
	if request.method=="POST":
		username = request.POST['username']
		password = request.POST['password']
		user     = authenticate(username=username,password=password)
		if user is not None:
			if user.is_active:
				login(request,user)
				return redirect("index")
			else:
				return render(request,'web/login.html',{'error_message':'Your account disable'})
		else:
			return render(request,'web/login.html',{'error_message': 'Invalid Login'})
	return render(request,'web/login.html')

def index(request):
    movies = Movie.objects.all()
    query = request.GET.get('q')
    if query:
        # Используйте функцию для поиска фильмов через API
        movies = search_movies_by_title(query)
        return render(request, 'web/list.html', {'movies': movies})
    
    return render(request, 'web/list.html', {'movies': movies})

def detail(request, movie_id):
    movie = Movie.objects.get(id=movie_id)  # Получаем информацию о фильме из базы данных или API
    context = {
        'movie': movie  # Передаем информацию о фильме в шаблон
    }
    return render(request, 'web/detail.html', context)

#Logout user
def Logout(request):
	logout(request)
	return redirect("login")

