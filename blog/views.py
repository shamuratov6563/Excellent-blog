from django.core.mail import send_mail
from django.core.paginator import Paginator, PageNotAnInteger
from django.db.models import Count
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView
from taggit.models import Tag
from .forms import EmailPostForm, CommentForm
from .models import Post


def post_list(request, tag_slug=None):

    object_list = Post.published.all()
    tag = None
    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        object_list = object_list.filter(tags__in=[tag])
    paginator = Paginator(object_list, 3)  # 3 posts in each page
    page = request.GET.get('page')

    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        posts = paginator.page(1)
    return render(request,
                  'blog/post/list.html',
                  {'posts': posts, 'page': page, 'tag': tag}
                  )


# class PostListView(ListView):
#     queryset = Post.published.all()
#     template_name = 'blog/post/list.html'
#     paginate_by = 3
#     context_object_name = 'posts'


def post_detail(request, year, month, day, post):
    post = get_object_or_404(Post, slug=post,
                             status='published',
                             publish__year=year,
                             publish__month=month,
                             publish__day=day)
    comments = post.comments.filter(active=True)
    new_comment = None
    if request.method == "POST":
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            # Create comment but do not save to database
            new_comment = comment_form.save(commit=False)
            new_comment.post = post
            # save the comment to db
            new_comment.save()
    else:
        comment_form = CommentForm()

    # List similar posts
    post_tags_ids = post.tags.values_list('id', flat=True)
    similar_posts = Post.published.filter(tags__in=post_tags_ids).exclude(id=post.id)
    similar_posts = similar_posts.annotate(same_tags=Count('tags')).order_by('same_tags', '-publish')[:4]

    return render(request, 'blog/post/detail.html', {
                                            'post': post,
                                            'comments': comments,
                                            'comment_form': comment_form,
                                            'new_comment': new_comment,
                                            'similar_posts': similar_posts
                                        })


def post_share(request, post_id):
    post = get_object_or_404(Post, id=post_id, status='published')
    sent = False
    if request.method == "POST":
        form = EmailPostForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            post_url = request.build_absolute_uri(post.get_absolute_url())
            subject = f"{cd['name']} recommends you read {post.title}"
            message = f"Read {post.title} at {post_url} \n\n {cd['name']}\'s comments: {cd['comments']}"
            send_mail(subject, message, 'shamuratov6563@gmail.com', [cd['to']])
            sent = True
    else:
        form = EmailPostForm()
    return render(request, 'blog/post/share.html',
                  context={'post': post, 'form': form, 'sent': sent})
