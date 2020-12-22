from django.shortcuts import render, redirect, get_list_or_404
from django.urls import reverse_lazy
from django.views import generic
from django.contrib.auth import login, authenticate, get_user_model, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import (LoginView, LogoutView)
from .forms import LoginForm, UserCreateForm, CreateProfile, CreateReview
from .models import User, ProfileModel, ReviewModel, Counter, AnimeModel, AccessReview
from bs4 import BeautifulSoup as bs4
import requests
import matplotlib.pyplot as plt
import numpy as np
from django.http import HttpResponse
import io
import math
# Create your views here.

class Login(LoginView):
    """ログインページ"""
    form_class = LoginForm
    template_name = 'login.html'

class Logout(LogoutView):
    """ログアウトページ"""
    template_name = 'homepage.html'
    # model = ProfileModel

class UserCreate(generic.CreateView):
    form_class = UserCreateForm
    success_url = reverse_lazy('create_profile')
    template_name = 'signup.html'

    def form_valid(self,form):
        response = super().form_valid(form)
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password1')
        user = authenticate(username = username, password = password)
        login(self.request,user)
        return response

class UserDelete(LoginRequiredMixin, generic.View):
    def get(self, *args, **kwargs):
        user = User.objects.get(username = self.request.user.username)
        user.is_active = False
        user.save()
        logout(self.request)
        return render(self.request,'user_delete.html')

def homepage(request):
    return render(request,'homepage.html')

def create_profile(request):
    if request.method == 'POST':
        form = CreateProfile(request.POST)
        Counter.objects.create(username = request.user,genre_counter = '0/0/0/0/0/0/0/0')
        if form.is_valid():
            object = form.save(commit = False)
            object.username = request.user
            object.save()
            return redirect('home')
    else:
        form = CreateProfile
    return render(request,'create_profile.html',{'form' : form})

def home(request):
    review_list = ReviewModel.objects.all().order_by('-post_date')
    profile = ProfileModel.objects.get(username = request.user)
    ############おすすめアニメの表示#################
    counter = Counter.objects.get(username = request.user)
    genre_counter = counter.genre_counter.split('/')
    int_genre_counter = [int(n) for n in genre_counter]
    max_genre = int_genre_counter.index(max(int_genre_counter))
    print(max_genre)
    anime_list = []
    if AnimeModel.objects.exists():
        for animemodel in AnimeModel.objects.all():
            anime_genre = animemodel.anime_genre.split('/')
            print(anime_genre[max_genre])
            if anime_genre[max_genre] == '1':
                anime_list.append(animemodel.anime_title)
        #############ジャンルの一致したアニメを取得######################
        print(anime_list)
        anime_list = AnimeModel.objects.filter(anime_title__in = anime_list)
        print(anime_list)
        #############ジャンルの一致したアニメの平均評価の平均評価########################
        access_review_list = AccessReview.objects.filter(access_name = request.user).filter(review__anime_title__in = anime_list)
        print(access_review_list)
        if access_review_list.exists():
            count = access_review_list.count()
            access_values_sum = [0,0,0,0,0]
            for access_review in access_review_list:
                access_values = access_review.review.evaluation_value.split('/')
                int_access_values = [int(n) for n in access_values]
                access_values_sum = np.array(access_values_sum) + np.array(int_access_values)
            access_values_ave = [n/count for n in access_values_sum]
            ########################################
            ################各アニメの平均評価#########################
            anime_dict = {}
            for anime in anime_list:
                anime_review_list = ReviewModel.objects.filter(anime_title = anime)
                count = anime_review_list.count()
                anime_values_sum = [0,0,0,0,0]
                for review in anime_review_list:
                    anime_values = review.evaluation_value.split('/')
                    int_anime_values = [int(n) for n in anime_values]
                    anime_values_sum = np.array(anime_values_sum) + np.array(int_anime_values)
                anime_values_ave = [n/count for n in anime_values_sum]
                anime_dict[anime.anime_title] = anime_values_ave
            ##################Similarity#############################
            anime_similarity = {}
            for title, values in anime_dict.items():
                value_sub = np.array(access_values_ave) - np.array(values)
                value_sub_sqr = map(lambda x : x**2, value_sub)
                anime_similarity[title] = math.sqrt(sum(value_sub_sqr))
            anime_title = min(anime_similarity,key = anime_similarity.get)
            high_similarity_anime = AnimeModel.objects.get(anime_title = anime_title)
            return render(request,'home.html',{'review_list' : review_list, 'profile' : profile, 'high_similarity_anime' : high_similarity_anime})
    return render(request,'home.html',{'review_list' : review_list, 'profile' : profile})

def profile(request,pk):
    profile = ProfileModel.objects.get(pk = pk)
    review_list = ReviewModel.objects.filter(username = profile.username).order_by('-post_date')
    review_num = ReviewModel.objects.filter(username = profile.username).count()
    if review_list.exists():
        return render(request, 'profile.html', {'profile' : profile, 'review_list' : review_list,'review_num' : review_num})
    else:
        context = '投稿レビューはありません'
        return render(request, 'profile.html',{'profile' : profile, 'context' : context})

def create_review(request):
    if 'search' in request.POST:
        anime_title = request.POST.get('anime_title')
        try:
            anime = AnimeModel.objects.get(anime_title = anime_title)
            return render(request,'create_review.html',{'anime_title' : anime_title})
        except AnimeModel.DoesNotExist:
            AnimeModel.objects.create(anime_title = anime_title)
            context = 'そのアニメに関する投稿はまだないため、入力してください'
            return render(request, 'create_review.html', {'anime_title' : anime_title,'context' : context})
    if 'post' in request.POST:
        form = CreateReview(request.POST)
        if form.is_valid():
            object = form.save(commit = False)
            object.username = request.user
            object.nickname = ProfileModel.objects.get(username = request.user)
            object.anime_title = AnimeModel.objects.get(anime_title = request.POST.get('anime_title'))
            object.evaluation_value = request.POST.get('val1') + '/' + request.POST.get('val2') + '/' + request.POST.get('val3') + '/' + request.POST.get('val4') + '/' + request.POST.get('val5')
            object.evaluation_value_ave = (int(request.POST.get('val1')) + int(request.POST.get('val2')) + int(request.POST.get('val3')) + int(request.POST.get('val4')) + int(request.POST.get('val5')))/5
            object.save()
            #############AnimeModelへのジャンル追加###########
            anime_title = request.POST.get('anime_title')
            animemodel = AnimeModel.objects.get(anime_title = anime_title)
            anime_genre = animemodel.anime_genre.split('/')
            i = int(request.POST.get('anime_genre')) -1
            if anime_genre[i] == '0':
                anime_genre[i] = '1'
                animemodel.anime_genre = '/'.join(anime_genre)
                print(animemodel.anime_genre)
                animemodel.save()
            #############AnimeModelへのジャンル追加###########
            return redirect('home')
    else:
        form = CreateReview
    return render(request,'create_review.html',{'form' : form})

def review_detail(request,pk):
    review = ReviewModel.objects.get(pk = pk)
    profile = ProfileModel.objects.get(username = request.user)
    if review.username != request.user:
    #####################Counter###############################
        counter = Counter.objects.get(username = request.user)
        genre_counter = counter.genre_counter.split('/')
        int_genre_counter = [int(n) for n in genre_counter]
        for i in range(len(genre_counter)):
            print(review.anime_genre)
            if review.anime_genre == str(i + 1):
                int_genre_counter[i] += 1
                print(int_genre_counter[i])
        genre_counter = [str(n) for n in int_genre_counter]
        counter.genre_counter = '/'.join(genre_counter)
        counter.visited_review = review
        counter.save()
        #####################Counter###############################
        #####################AccessReview##########################
    if review.username != request.user:
        AccessReview.objects.create(access_name = request.user, review = review)
    #####################AccessReview##########################
    return render(request, 'review_detail.html', {'review' : review, 'profile' : profile})

def setPlt(values1,values2,label1,label2):
#######各要素の設定#########
    labels = ['シナリオ','作画','音楽','キャラクター','声優']
    angles = np.linspace(0,2*np.pi,len(labels) + 1, endpoint = True)
    rgrids = [0,1,2,3,4,5] 
    rader_values1 = np.concatenate([values1, [values1[0]]])
    rader_values2 = np.concatenate([values2, [values2[0]]])

#######グラフ作成##########
    fig = plt.figure (facecolor = 'w')
    ax = fig.add_subplot(1,1,1,polar = True)
    ax.plot(angles, rader_values1, color = 'r', label = label1)
    ax.plot(angles, rader_values2, color = 'b', label = label2)
    cm = plt.get_cmap('Reds')
    cm2 = plt.get_cmap('Blues')
    for i in range(6):
        z = i/5
        rader_value3 = [n*z for n in rader_values1]
        rader_value4 = [n*z for n in rader_values2]
        ax.fill(angles, rader_value3, alpha = 0.5, facecolor = cm(z))
        ax.fill(angles, rader_value4, alpha = 0.5, facecolor = cm2(z))
    ax.set_thetagrids(angles[:-1]*180/np.pi,labels,fontname = 'Source Han Code JP')
    ax.set_rgrids([])
    ax.spines['polar'].set_visible(False)
    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)
    
    ax.legend(bbox_to_anchor = (1.05,1.0), loc = 'upper left')

    for grid_value in rgrids:
        grid_values = [grid_value] * (len(labels) + 1)
        ax.plot(angles, grid_values, color = 'gray', linewidth = 0.5)
    
    for t in rgrids:
        ax.text(x = 0,y = t, s = t)

    ax.set_rlim([min(rgrids), max(rgrids)])
    ax.set_title ('評価', fontname = 'Source Han Code JP', pad = 20)
    ax.set_axisbelow(True)
def get_image():
    buf = io.BytesIO()
    plt.savefig(buf,format = 'svg',bbox_inches = 'tight')
    graph = buf.getvalue()
    buf.close()
    return graph

def get_svg2(request,pk):
    ###レビュー者の評価###
    review = ReviewModel.objects.get(pk = pk)
    str_values  = review.evaluation_value.split('/')
    values1 = [int(n) for n in str_values]
    label1 = 'Reviewer_Eval'

    ###全体の平均評価###
    review_list = ReviewModel.objects.filter(anime_title = review.anime_title)
    review_count = review_list.count()
    values2_sum = [0,0,0,0,0]
    for item in review_list:
        str_values = item.evaluation_value.split('/')
        int_values = [int (n) for n in str_values]
        values2_sum = np.array(values2_sum) + np.array(int_values)
    values2 = [n/review_count for n in values2_sum]
    label2 = 'Reviewer_Eval_Ave'
    setPlt(values1,values2,label1,label2)
    svg = get_image()
    plt.cla()
    response = HttpResponse(svg, content_type = 'image/svg+xml')
    return response

def get_svg(request,pk):
    ###########high_similarity_animeの平均評価##################
    anime = AnimeModel.objects.get(pk=pk)
    review_list = ReviewModel.objects.filter(anime_title = anime)
    count = review_list.count()
    review_values_sum = [0,0,0,0,0]
    for review in review_list:
        review_values = review.evaluation_value.split('/')
        int_review_values = [int(n) for n in review_values]
        review_values_sum = np.array(review_values_sum) + np.array(int_review_values)
    values1 = [n/count for n in review_values_sum]
    ###########high_similarity_animeの平均評価##################

    ###########AccessReviewの平均評価###########################
    counter = Counter.objects.get(username = request.user)
    genre_counter = counter.genre_counter.split('/')
    int_genre_counter = [int(n) for n in genre_counter]
    max_genre = int_genre_counter.index(max(int_genre_counter))
    anime_list = []
    if AnimeModel.objects.exists():
        for animemodel in AnimeModel.objects.all():
            anime_genre = animemodel.anime_genre.split('/')
            if anime_genre[max_genre] == '1':
                anime_list.append(animemodel.anime_title)
        #############ジャンルの一致したアニメを取得######################
        anime_list = AnimeModel.objects.filter(anime_title__in = anime_list)
        #############訪問したレビューの平均評価########################
        access_review_list = AccessReview.objects.filter(access_name = request.user).filter(review__anime_title__in = anime_list)
        if access_review_list.exists():
            count = access_review_list.count()
            access_values_sum = [0,0,0,0,0]
            for access_review in access_review_list:
                access_values = access_review.review.evaluation_value.split('/')
                int_access_values = [int(n) for n in access_values]
                access_values_sum = np.array(access_values_sum) + np.array(int_access_values)
            values2 = [n/count for n in access_values_sum]
    label1 = 'Reviwer_ave'
    label2 = 'Access_ave'
    setPlt(values1,values2,label1,label2)
    svg = get_image()
    plt.cla()
    response = HttpResponse(svg, content_type = 'image/svg+xml')
    return response

