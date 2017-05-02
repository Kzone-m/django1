from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect, Http404, HttpResponse
from .models import Comment
from .forms import CommentForm
from django.contrib.contenttypes.models import ContentType

from django.contrib.auth.decorators import login_required


# @login_required(login_url='/login/')    # LOGIN_URL = '/login/'
# @login_required
@login_required(login_url='/login/')
def comment_delete(request, id):
    """This is a method deleting selected parent comment"""
    # obj = get_object_or_404(Comment, id=id)
    try:
        obj = Comment.objects.get(id=id)
    except:
        raise Http404

    if obj.user != request.user:
        """ if request user is not parent comment user, declare 404"""
        # raise Http404
        response = HttpResponse("You do not have permission to view this.")
        response.status_code = 403
        return response

    if request.method == 'POST':
        # print(obj) -> admin
        # print(type(obj)) -> <class 'comments.models.Comment'>
        # print(obj.content_object) -> Test Post for Calculating Reading Time
        # print(type(obj.content_object)) -> <class 'posts.models.Post'>
        # print(obj.content_object.get_absolute_url()) -> /posts/7/
        parent_obj_url = obj.content_object.get_absolute_url()
        obj.delete()
        return HttpResponseRedirect(parent_obj_url)
    context = {
        'object': obj,
    }
    return render(request, 'confirm_delete.html', context)


def comment_thread(request, id):
    """This is a method viewing each comment's detail as view
    and it gives the functionality adding children comment on its parent comment"""
    # obj = get_object_or_404(Comment, id=id)

    try:
        obj = Comment.objects.get(id=id)
    except:
        raise Http404

    if not obj.is_parent:
        """ If this is not parent, which means that the comment requested is one of the children,
        set its parent objects as obj variable. The reason to re-set the variable is to avoid that 
        client request children comment's thread """
        obj = obj.parent

    initial_data = {
        'content_type': obj.content_type,
        'object_id': obj.object_id
    }

    form = CommentForm(request.POST or None, initial=initial_data)

    if form.is_valid():
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
                parent_obj = parent_qs.first()

        new_comment, created = Comment.objects.get_or_create(
                                    user=request.user,
                                    content_type=content_type,
                                    object_id=obj_id,
                                    content=content_data,
                                    parent=parent_obj
                            )
        new_comment.save()
        return HttpResponseRedirect(new_comment.parent.get_absolute_url())

    context = {
        'comment': obj,
        'form': form,
        'title': 'Thread'
    }
    return render(request, 'comment_thread.html', context)


