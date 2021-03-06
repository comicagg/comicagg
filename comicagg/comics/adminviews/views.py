# -*- coding: utf-8 -*-
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.utils.translation import ugettext as _
from comicagg import render
from comicagg.comics.models import Comic, ComicHistory
from comicagg.comics.update import update_comic

@login_required
def admin_update_view(request, comic_id=None):
    """Trigger an an update for a comic.
    If a comic_id is passed as parameter it will update that comic.
    If no comic_id is passed, it will show the list of comics to update.
    """
    if request.user.is_staff:
        context = {}
        # create a dict with the initials of the comics.
        # so {'a':list, 'b':list, ...}
        comic_list = Comic.objects.all().order_by('name')
        comic_dict = dict()
        for c in comic_list:
            l = c.name[0].upper()
            if l in comic_dict.keys():
                comic_dict[l].append(c)
            else:
                comic_dict[l] = [c]
        context['list'] = comic_dict
        if comic_id:
            #if a comic_id is passed, update that comic
            comic = Comic.objects.get(pk=comic_id)
            context['last'] = comic
            context['changed'] = update_comic(comic)
        context['title'] = _('Update comic')
        return render(request, 'admin/update_comic.html', context)
    raise Http404

def admin_reported(request, chids):
    """See the strips reported.
    Present a page with the images of the reported strips.
    """
    if request.user.is_staff:
        context = {}
        chids = chids.split('-')
        chs = dict()
        for chid in chids:
            try:
                ch = ComicHistory.objects.get(pk=int(chid))
            except:
                ch = None
            chs[chid] = ch
        context['chs'] = chs
        return render(request, 'admin/reported.html', context)
    raise Http404
