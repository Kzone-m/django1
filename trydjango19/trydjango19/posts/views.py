from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseRedirect, Http404
from .models import Post
from .forms import PostForm    # ユーザーのinput dataを受け取る -> post_create, post_update function
from django.contrib import messages     # 作成した時と、削除した時のメッセージ -> post_create, post_delete
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger    # pagination -> post_list function
import os   # pathの取得
from urllib.parse import quote_plus    # share_string -> post_detail function
from django.utils import timezone   # -> post_list function
from django.db.models import Q  # 検索ボックスに必要なimport -> post_list function

from django.contrib.contenttypes.models import ContentType
from comments.forms import CommentForm
from comments.models import Comment
# from django.contrib.contenttypes.models import ContentType


# ref: http://d.hatena.ne.jp/chlere/20110618/1308369842, http://note.crohaco.net/2014/python-module/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# function based views
def post_create(request):
    # if not request.user.is_staff or not request.user.is_superuser:
    if not request.user.is_staff:
        raise Http404

    form = PostForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.save()
        messages.success(request, 'Successfully Created')
        return HttpResponseRedirect(post.get_absolute_url())
    d = {
        'form': form,
        'title': 'Create',
    }
    return render(request, 'post_form.html', d)


def post_detail(request, id=None):
    post = get_object_or_404(Post, id=id)

    if post.draft or post.publish > timezone.now().date():
        if not request.user.is_staff or not request.user.is_superuser:
            raise Http404

    # share_string = quote_plus(post.content)

    initial_data = {
        'content_type': post.get_content_type,
        'object_id': post.id
    }

    form = CommentForm(request.POST or None, initial=initial_data)

    if form.is_valid() and request.user.is_authenticated():

        # print(type(c_type)), print(c_type) = return -> str : post
        # print(type(content_type)), print(content_type) = return ContentType: post
        c_type = form.cleaned_data.get('content_type')
        content_type = ContentType.objects.get(model=c_type)
        obj_id = form.cleaned_data.get('object_id')
        content_data = form.cleaned_data.get('content')

        parent_obj = None
        try:
            parent_id = int(request.POST.get('parent_id'))
        except:
            parent_id = None

        if parent_id:
            parent_qs = Comment.objects.filter(id=parent_id)
            if parent_qs.exists() and parent_qs.count() == 1:
                parent_obj = parent_qs.first()  # print(type(parent_obj)) => <class 'comments.models.Comment'>

        new_comment, created = Comment.objects.get_or_create(
                                    user=request.user,
                                    content_type=content_type,
                                    object_id=obj_id,
                                    content=content_data,
                                    parent=parent_obj
                            )
        new_comment.save()
        return HttpResponseRedirect(new_comment.content_object.get_absolute_url())

    # content_type = ContentType.objects.get_for_model(Post)
    # obj_id = post.id
    # comments = Comment.objects.filter(content_type=content_type, object_id=obj_id)
    # comments = post.comments -> b/c @property of posts/models.py -> def comments!!!

    comments = Comment.objects.filter_by_instance(post)

    d = {
        'title': 'Detail',
        'post': post,
        # 'share_string': share_string,
        'comments': comments,
        'comment_form': form,
    }
    return render(request, 'post_detail.html', d)


def post_list(request):
    # posts_list = Post.objects.all()  # .order_by('-timestamp') -> 時間の新しい順に取得: modelのMeta Classで設定可能
    # posts_list = Post.objects.filter(draft=False).filter(publish__lte=timezone.now())
    posts_list = Post.objects.active()
    if request.user.is_staff or request.user.is_superuser:
        posts_list = Post.objects.all()

    today = timezone.now().date()

    query = request.GET.get('q')
    if query:
        posts_list = posts_list.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query)
            ).distinct()

    paginator = Paginator(posts_list, 5)    # Show 5 contacts per page
    page = request.GET.get('page')

    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        posts = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        posts = paginator.page(paginator.num_pages)

    d = {
        'title': 'List',
        'posts': posts,
        'today': today,
    }
    return render(request, 'post_list.html', d)


def post_update(request, id=None):
    if not request.user.is_authenticated():
        raise Http404

    post = get_object_or_404(Post, id=id)
    form = PostForm(request.POST or None, request.FILES or None, instance=post)

    if form.is_valid():
        instance = form.save(commit=False)
        instance.user = request.user    # <- this is important validation
        instance.save()
        messages.success(request, 'Item Saved')
        return HttpResponseRedirect(instance.get_absolute_url())

    d = {
        'title': 'Detail',
        'post': post,
        'form': form,
    }
    return render(request, 'post_form.html', d)


def post_delete(request, id=None):
    if not request.user.is_staff or not request.user.is_superuser:
        raise Http404
    post = get_object_or_404(Post, id=id)

    if post.image:
        image = BASE_DIR + post.image.url
        os.remove(image)

    post.delete()
    messages.success(request, 'Successfully Deleted')
    return redirect('posts:list')
