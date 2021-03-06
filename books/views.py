from operator import attrgetter
from datetime import datetime

from django.views.generic import CreateView, TemplateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy

from .models import Ticket, Review, UserFollows
from .forms import TicketForm, ReviewForm


class FeedView(LoginRequiredMixin, TemplateView):

    template_name = 'books/feed.html'
    context_object_name = 'feed_items'
    view_type = 'feed'

    def get_feed_items(self):
        tickets = list(Ticket.objects.all())
        reviews = list(Review.objects.all())
        followed_users = [object.followed_user
                          for object in UserFollows.objects.all()
                          if object.user == self.request.user]
        tickets = [ticket for ticket in tickets
                   if (ticket.user in followed_users)
                   or (ticket.user == self.request.user)]
        reviews = [review for review in reviews
                   if ((review.user in followed_users)
                       or (review.user == self.request.user)
                       or (review.ticket.user in followed_users)
                       or (review.ticket.user == self.request.user))]
        feed_items = tickets + reviews
        feed_items.sort(key=attrgetter('time_created'), reverse=True)
        return feed_items

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        feed_items = self.get_feed_items()

        paginator = Paginator(feed_items, 5)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context['page_obj'] = page_obj
        context['rating_range'] = Review.get_rating_range()

        return context


class PostsView(FeedView):

    def get_feed_items(self):
        feed_items = super().get_feed_items()
        feed_items = [feed_item for feed_item in feed_items
                      if feed_item.user == self.request.user]
        return feed_items


class TicketCreateView(LoginRequiredMixin, CreateView):
    model = Ticket
    fields = ['title', 'description', 'image']

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class TicketUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Ticket
    fields = ['title', 'description', 'image']
    template_name_suffix = '_update_form'

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.time_created = datetime.now()
        return super().form_valid(form)

    def test_func(self):
        return self.request.user == self.get_object().user


class TicketDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Ticket
    success_url = reverse_lazy('books:feed')

    def test_func(self):
        return self.request.user == self.get_object().user


@login_required
def add_review(request, id_ticket=None):
    if id_ticket is not None:
        ticket = get_object_or_404(Ticket.objects, pk=id_ticket)
        if ticket.completed:
            return redirect('books:feed')
    else:
        ticket = None
    if request.method == "GET":
        form_review = ReviewForm()
        form_ticket = TicketForm()
        context = {
            'ticket': ticket,
            'form_review': form_review,
            'form_ticket': form_ticket,
        }
        if id_ticket:
            context['id_ticket'] = id_ticket
        return render(request, 'books/review_form.html', context)

    elif request.method == 'POST':
        form_ticket = TicketForm()
        if not ticket:
            ticket_data = {
                'title': request.POST['title'],
                'description': request.POST['description'],
            }
            form_ticket = TicketForm(ticket_data)
            if request.FILES:
                form_ticket.instance.image = request.FILES['image']
            form_ticket.instance.user = request.user

        review_data = {
            'headline': request.POST['headline'],
            'rating': request.POST['rating'],
            'body': request.POST['body'],
        }
        form_review = ReviewForm(review_data)
        form_review.instance.user = request.user

        if (ticket or form_ticket.is_valid()) and form_review.is_valid():
            if ticket:
                ticket.completed = True
                ticket.save()
                form_review.instance.ticket = ticket
            else:
                form_ticket.instance.completed = True
                form_ticket.save()
                form_review.instance.ticket = Ticket.objects.last()
            form_review.save()
            return redirect('books:feed')
        else:
            context = {
                'ticket': ticket,
                'form_review': form_review,
                'form_ticket': form_ticket,
            }
            if id_ticket:
                context['id_ticket'] = id_ticket
            return render(request, 'books/review_form.html', context)


class ReviewUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):

    model = Review
    fields = [
            "headline",
            "rating",
            "body",
        ]
    template_name_suffix = '_update_form'

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.time_created = datetime.now()
        return super().form_valid(form)

    def test_func(self):
        return self.request.user == self.get_object().user


class ReviewDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Review
    success_url = reverse_lazy('books:feed')

    def test_func(self):
        return self.request.user == self.get_object().user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["rating_range"] = Review.get_rating_range()
        return context

    def delete(self, request, *args, **kwargs):
        ticket = self.get_object().ticket
        ticket.completed = False
        ticket.save()
        return super().delete(request, *args, **kwargs)


@login_required
def sub(request):
    follows = []
    followed_by = []
    follow_list = []
    if UserFollows.objects.filter(user=request.user):
        for entry in UserFollows.objects.filter(user=request.user):
            follows.append(entry.followed_user)
    if UserFollows.objects.filter(followed_user=request.user):
        for entry in UserFollows.objects.filter(followed_user=request.user):
            followed_by.append(entry.user)
    follow_list = [user for user in User.objects.all()
                   if user not in follows and user != request.user]
    if request.method == 'GET':
        context = {
            'follow_list': follow_list,
            'follows': follows,
            'followed_by': followed_by,
        }
        return render(request, 'books/sub.html', context)
    if request.method == 'POST':
        if request.POST.get('followed_user'):
            new_followed_user = User.objects.get(
                pk=request.POST['followed_user'])
            new_user = request.user
            new_entry = UserFollows(
                user=new_user, followed_user=new_followed_user)
            new_entry.save()
        elif request.POST.get('delete'):
            UserFollows.objects.get(
                user=request.user,
                followed_user=User.objects.get(id=request.POST['delete']),
                ).delete()
        return redirect('books:sub')
