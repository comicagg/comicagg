from comicagg import *
from comicagg.help.models import *
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404

# Create your views here.
def index(request):
    tickets = None
    if request.user and request.user.is_authenticated():
        tickets = Ticket.objects.filter(owner=request.user).order_by('-date')
    return render(request, 'help/index.html', {'tickets':tickets}, 'help')

def view_faq(request):
    faq = Faq.objects.all()
    return render(request, 'help/faq.html', {'faq':faq}, 'help')

@login_required
def new_ticket(request):
    form = NewTicketForm()
    if request.POST:
        new_data = request.POST
        form = NewTicketForm(new_data)
        if form.is_valid():
            ticket = Ticket(owner=request.user, title=form.cleaned_data['title'], text=form.cleaned_data['text'])
            ticket.save()
            details = {'to':'esu@proyectoanonimo.com', 'from':'Comic Aggregator', 'subject':'[CA] Nuevo ticket', 'message':ticket.title}
            #send_email(details)
            return HttpResponseRedirect(reverse('comicagg.help.views.index'))
    return render(request, 'help/new_ticket.html', {'form':form}, 'help')

@login_required
def view_ticket(request, ticket_id):
    ticket = get_object_or_404(Ticket, pk=ticket_id)
    if request.user != ticket.owner and not request.user.is_staff:
        return HttpResponseRedirect(reverse('comicagg.help.views.index'))
    form = ReplyTicketForm()
    return render(request, 'help/edit_ticket.html', {'form':form, 'ticket':ticket}, 'help')

@login_required
def reply_ticket(request, ticket_id):
    form = ReplyTicketForm()
    if request.POST:
        ticket = get_object_or_404(Ticket, pk=ticket_id)
        if request.user != ticket.owner and not request.user.is_staff:
            return HttpResponseRedirect(reverse('comicagg.help.views.index'))
        new_data = request.POST
        form = ReplyTicketForm(new_data)
        if form.is_valid():
            if request.user.is_staff:
                tm = TicketMessage(ticket=ticket, user=None, text=form.cleaned_data['text'])
            else:
                tm = TicketMessage(ticket=ticket, user=request.user, text=form.cleaned_data['text'])
            tm.save()
            ticket.set_open()
            ticket.save()
            return HttpResponseRedirect(reverse('comicagg.help.views.view_ticket', args=[ticket_id]))
    return render(request, 'help/new_ticket.html', {'form':form}, 'help')

@login_required
def close_ticket(request, ticket_id):
    ticket = get_object_or_404(Ticket, pk=ticket_id)
    if request.user != ticket.owner and not request.user.is_staff:
        return HttpResponseRedirect(reverse('comicagg.help.views.index'))
    ticket.set_close()
    ticket.save()
    return HttpResponseRedirect(reverse('comicagg.help.views.view_ticket', args=[ticket_id]))

@login_required
def open_tickets(request):
    tickets = Ticket.objects.filter(status='O').order_by('-date')
    return render(request, 'admin/open_tickets.html', {'tickets':tickets}, 'help')
