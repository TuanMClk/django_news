from django.shortcuts import render,redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.contrib import messages
import requests
from datetime import datetime
from babel.dates import format_date
from django.contrib.auth.models import User
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

import json
from newsApp import models, forms
def context_data():
    # lấy api thời tiết
    api_key = 'a22ce9d5604fc535a5e7eeed45a581f8'  # Thay YOUR_API_KEY bằng API key của bạn
    city = 'hanoi'
    url = f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&lang=vi&units=metric'
    response = requests.get(url)
    data = response.json()

    #lấy thời gian hiện tại 
    current_date = datetime.now()
    #format định dạng tiếng việt
    formatted_date = format_date(current_date, "EEEE, d MMMM y", locale='vi_VN')
    context = {
        'site_name': 'NewsBox',
        'page' : 'Trang chủ',
        'page_title' : 'News Portal',
        'categories' : models.Category.objects.filter(status = 1).all(),
        'temperature' : data['main']['temp'],
        'current_date' : formatted_date,
        'city' : data['name'],
        'weather_description' : data['weather'][0]['description'],
        'icon_code' : data['weather'][0]['icon'],
        'latest_top_7' :  models.Post.objects.filter(status = 1).order_by('-date_created')[:7]
    }
    return context

# Create your views here.
def home(request):
    context = context_data()
    posts = models.Post.objects.filter(status = 1).order_by('-date_created').all()
    # Lấy ra danh sách các category duy nhất
    unique_categories = models.Post.objects.values_list('category', flat=True).distinct()
    name_categories = models.Post.objects.values_list('category__name', flat=True).distinct()[:2]

    # Lấy ra 2 danh sách bài viết có category ở vị trí đầu và thứ hai
    first_category_posts = models.Post.objects.filter(category=unique_categories[0]).order_by('-date_created')[:5]
    second_category_posts = models.Post.objects.filter(category=unique_categories[1]).order_by('-date_created')[:5]
    context['page'] = 'home'
    context['page_title'] = 'Trang chủ'
    context['latest_top'] = posts[:2]
    context['latest_top_7'] = posts[:7]
    context['latest_bottom'] = posts[2:12]
    context['first_category_posts'] = first_category_posts
    context['second_category_posts'] = second_category_posts
    context['name_categories'] = name_categories
    return render(request, 'home.html', context)
# lấy api thời tiết 
def current_weather(request):
    # lấy api thời tiết
    api_key = 'a22ce9d5604fc535a5e7eeed45a581f8'  # Thay YOUR_API_KEY bằng API key của bạn
    city = 'hanoi'
    url = f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&lang=vi&units=metric'
    response = requests.get(url)
    data = response.json()
    context = context_data()
    context['temperature'] = data['main']['temp']
    context['city'] = data['name']
    context['humidity'] = data['main']['humidity']
    context['wind'] = data['wind']['speed']
    context['weather_description'] = data['weather'][0]['description']
    context['icon_code'] = data['weather'][0]['icon']
    #lấy thời gian hiện tại 
    current_date = datetime.now()
    #format định dạng tiếng việt
    formatted_date = format_date(current_date, "EEEE, d MMMM y", locale='vi_VN')
    context['current_date'] = formatted_date
    return render(request, 'top-navigation.html', context)
#login
def login_user(request):
    logout(request)
    resp = {"status":'failed','msg':''}
    username = ''
    password = ''
    if request.POST:
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                resp['status']='success'
            else:
                resp['msg'] = "Sai tên đăng nhập hoặc mật khẩu"
        else:
            resp['msg'] = "Sai tên đăng nhập hoặc mật khẩu"
    return HttpResponse(json.dumps(resp),content_type='application/json')

#Logout
def logoutuser(request):
    logout(request)
    return redirect('/')


@login_required
def update_profile(request):
    context = context_data()
    context['page_title'] = 'Update Profile'
    user = User.objects.get(id = request.user.id)
    if not request.method == 'POST':
        form = forms.UpdateProfile(instance=user)
        context['form'] = form
    else:
        form = forms.UpdateProfile(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Đã cập nhật hồ sơ")
            return redirect("profile-page")
        else:
            context['form'] = form
            
    return render(request, 'update_profile.html',context)


@login_required
def update_password(request):
    context = context_data()
    context['page_title'] = "Update Password"
    if request.method == 'POST':
        form = forms.UpdatePasswords(user = request.user, data= request.POST)
        if form.is_valid():
            form.save()
            messages.success(request,"Your Account Password has been updated successfully")
            update_session_auth_hash(request, form.user)
            return redirect("profile-page")
        else:
            context['form'] = form
    else:
        form = forms.UpdatePasswords(request.POST)
        context['form'] = form
    return render(request,'update_password.html',context)

@login_required
def profile(request):
    context = context_data()
    context['page'] = 'profile'
    context['page_title'] = "Profile"
    return render(request,'profile.html', context)

@login_required
def manage_post(request, pk = None):
    context = context_data()
    if not pk is None:
        context['page']='edit_post'
        context['page_title']='Edit Post'
        context['post']=models.Post.objects.get(id=pk)
    else:
        context['page']='new_post'
        context['page_title']='New Post'
        context['post']={}

    return render(request, 'manage_post.html',context)

@login_required
def save_post(request):
    resp={'status':'failed', 'msg':'','id':None}
    if request.method == 'POST':
        if request.POST['id'] == '':
            form = forms.savePost(request.POST, request.FILES)
        else:
            post = models.Post.objects.get(id=request.POST['id'])
            form = forms.savePost(request.POST, request.FILES, instance= post)
    
        if form.is_valid():
            form.save()
            if request.POST['id'] == '':
                postID = models.Post.objects.all().last().id
            else:
                postID = request.POST['id']
            resp['id'] = postID
            resp['status'] = 'success'
            messages.success(request, "Thêm bài viết thành công.")
        else:
            for field in form:
                for error in field.errors:
                    if not resp['msg'] == '':
                        resp['msg'] += str('<br />')
                    resp['msg'] += str(f"[{field.label}] {error}")

    else:
        resp['msg'] = "Request has no data sent."
    return HttpResponse(json.dumps(resp), content_type="application/json")


def view_post(request, pk=None):
    context = context_data()
    post = models.Post.objects.get(id = pk)
    context['page'] = 'post'
    context['page_title'] = post.title
    print(post.category_id)
    context['post'] = post
    related_posts = models.Post.objects.filter(status=1, category=post.category).exclude(id=pk).order_by('-date_created')[:10]
    context['related_posts'] = related_posts
    context['latest'] = models.Post.objects.exclude(id=pk).filter(status = 1).order_by('-date_created').all()[:10]
    context['comments'] = models.Comment.objects.filter(post=post).all()
    context['actions'] = False
    if request.user.is_superuser or request.user.id == post.user.id:
        context['actions'] = True
    return render(request, 'single_post.html', context)

def save_comment(request):
    resp={'status':'failed', 'msg':'','id':None}
    if request.method == 'POST':
        if request.POST['id'] == '':
            form = forms.saveComment(request.POST)
        else:
            comment = models.Comment.objects.get(id=request.POST['id'])
            form = forms.saveComment(request.POST, instance= comment)
    
        if form.is_valid():
            form.save()
            if request.POST['id'] == '':
                commentID = models.Post.objects.all().last().id
            else:
                commentID = request.POST['id']
            resp['id'] = commentID
            resp['status'] = 'success'
            messages.success(request, "Comment has been saved successfully.")
        else:
            for field in form:
                for error in field.errors:
                    if not resp['msg'] == '':
                        resp['msg'] += str('<br />')
                    resp['msg'] += str(f"[{field.label}] {error}")

    else:
        resp['msg'] = "Request has no data sent."
    return HttpResponse(json.dumps(resp), content_type="application/json")

@login_required
def list_posts(request):
    context = context_data()
    context['page'] = 'all_post'
    context['page_title'] = 'All Posts'
    
    if request.user.is_superuser:
        post_list = models.Post.objects.order_by('-date_created').all()
    else:
        post_list = models.Post.objects.filter(user=request.user).all()
    
    # Phân trang
    paginator = Paginator(post_list, 10)  # Số lượng bài viết trên mỗi trang
    page = request.GET.get('page')
    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        # Nếu page không phải số nguyên, trả về trang đầu tiên
        posts = paginator.page(1)
    except EmptyPage:
        # Nếu page ngoài phạm vi, trả về trang cuối cùng
        posts = paginator.page(paginator.num_pages)

    context['posts'] = posts
    context['latest'] = models.Post.objects.filter(status=1).order_by('-date_created').all()[:10]

    return render(request, 'posts.html', context)


def category_posts(request, pk=None):
    context = context_data()
    
    if pk is None:
        messages.error(request, "File not Found")
        return redirect('home-page')
    
    try:
        category = models.Category.objects.get(id=pk)
    except models.Category.DoesNotExist:
        messages.error(request, "Category not found")
        return redirect('home-page')

    context['category'] = category
    context['page'] = 'category_post'
    context['page_title'] = f'{category.name} Posts'

    # Lấy danh sách bài viết của danh mục
    post_list = models.Post.objects.filter(status=1, category=category).order_by('-date_created')

    # Phân trang
    paginator = Paginator(post_list, 10)  # 10 bài viết mỗi trang
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context['posts'] = page_obj
    context['latest'] = models.Post.objects.filter(status=1).order_by('-date_created')[:10]

    return render(request, 'category.html', context)

@login_required
def delete_post(request, pk = None):
    resp = {'status':'failed', 'msg':''}
    if pk is None:
        resp['msg'] = 'Post ID is Invalid'
        return HttpResponse(json.dumps(resp), content_type="application/json")
    try:
        post = models.Post.objects.get(id=pk)
        post.delete()
        messages.success(request, "Post has been deleted successfully.")
        resp['status'] = 'success'
    except:
        resp['msg'] = 'Post ID is Invalid'
    
    return HttpResponse(json.dumps(resp), content_type="application/json")


@login_required
def delete_comment(request, pk = None):
    resp = {'status':'failed', 'msg':''}
    if pk is None:
        resp['msg'] = 'Comment ID is Invalid'
        return HttpResponse(json.dumps(resp), content_type="application/json")
    try:
        comment = models.Comment.objects.get(id=pk)
        comment.delete()
        messages.success(request, "Comment has been deleted successfully.")
        resp['status'] = 'success'
    except:
        resp['msg'] = 'Comment ID is Invalid'
    
    return HttpResponse(json.dumps(resp), content_type="application/json")

