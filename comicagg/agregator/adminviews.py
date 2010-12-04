# -*- coding: utf-8 -*-
from comicagg import render
from comicagg.agregator.models import Comic, ComicHistory
from comicagg.agregator.check import check_comic
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.utils.translation import ugettext as _

@login_required
def admin_check(request, comic_id=None):
    context = {}
    if request.user.is_staff:
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
            comic = Comic.objects.get(pk=comic_id)
            context['last'] = comic
            context['changed'] = check_comic(comic)
        context['title'] = _('Update comic')
        return render(request, 'admin/check.html', context)
    raise Http404

def admin_reported(request, chids):
    context = {}
    if request.user.is_staff:
        chids = chids.split('-')
        chs = dict()
        for chid in chids:
            try:
                ch = ComicHistory.objects.get(pk=int(chid))
            except:
                ch = None
            chs[chid]= ch
        context['chs'] = chs
        return render(request, 'admin/reported.html', context)
    raise Http404
