import re
from collections import defaultdict
from urllib.parse import urljoin

from ansi2html import Ansi2HTMLConverter
from django.contrib.auth.models import AbstractUser
from django.urls import reverse
from django.utils.html import escape
from django.utils.safestring import mark_safe
from lxml.html import Element

from judge import lxml_tree
from judge.models import Contest, Problem, Profile
from judge.ratings import rating_name
from . import registry

rereference = re.compile(r'\[(r?user):(\w+)\]')


def get_user(username, data):
    if not data:
        element = Element('span', {'class': 'deleted-user'})
        element.text = username
        return element

    rank, rating, is_privileged = data
    element = Element('span', {'class': Profile.get_user_css_class(rank, rating, is_privileged=is_privileged)})
    link = Element('a', {'href': reverse('user_page', args=[username])})
    link.text = username
    element.append(link)
    return element


def get_user_rating(username, data):
    if not data:
        element = Element('span')
        element.text = username
        return element

    rank, rating, is_privileged = data
    element = Element('a', {'class': 'rate-group', 'href': reverse('user_page', args=[username])})
    if rating is not None:
        element.set('title', str(rating_name(rating)))
    user = Element('span', {'class': Profile.get_user_css_class(rank, rating, is_privileged=is_privileged)})
    user.text = username
    element.append(user)
    return element


def get_user_info(usernames):
    return {name: (rank, rating, is_staff or is_superuser) for name, rank, rating, is_staff, is_superuser in
            Profile.objects.filter(user__username__in=usernames)
                   .values_list('user__username', 'display_rank', 'rating', 'user__is_staff', 'user__is_superuser')}


reference_map = {
    'user': (get_user, get_user_info),
    'ruser': (get_user_rating, get_user_info),
}


def process_reference(text):
    # text/tail -> text/tail + elements
    last = 0
    tail = text
    prev = None
    elements = []
    for piece in rereference.finditer(text):
        if prev is None:
            tail = text[last:piece.start()]
        else:
            prev.append(text[last:piece.start()])
        prev = list(piece.groups())
        elements.append(prev)
        last = piece.end()
    if prev is not None:
        prev.append(text[last:])
    return tail, elements


def populate_list(queries, list, element, tail, children):
    if children:
        for elem in children:
            queries[elem[0]].append(elem[1])
        list.append((element, tail, children))


def update_tree(list, results, is_tail=False):
    for element, text, children in list:
        after = []
        for type, name, tail in children:
            child = reference_map[type][0](name, results[type].get(name))
            child.tail = tail
            after.append(child)

        after = iter(reversed(after))
        if is_tail:
            element.tail = text
            link = element.getnext()
            if link is None:
                link = next(after)
                element.getparent().append(link)
        else:
            element.text = text
            link = next(after)
            element.insert(0, link)
        for child in after:
            link.addprevious(child)
            link = child


@registry.filter
def reference(text):
    tree = lxml_tree.fromstring(text)
    texts = []
    tails = []
    queries = defaultdict(list)
    for element in tree.iter():
        if element.text:
            populate_list(queries, texts, element, *process_reference(element.text))
        if element.tail:
            populate_list(queries, tails, element, *process_reference(element.tail))

    results = {type: reference_map[type][1](values) for type, values in queries.items()}
    update_tree(texts, results, is_tail=False)
    update_tree(tails, results, is_tail=True)
    return tree


@registry.filter
def item_title(item):
    if isinstance(item, Problem):
        return item.name
    elif isinstance(item, Contest):
        return item.name
    return '<Unknown>'


@registry.function
def link_user(user):
    if isinstance(user, Profile):
        user, profile = user.user, user
    elif isinstance(user, AbstractUser):
        profile = user.profile
    elif type(user).__name__ == 'ContestRankingProfile':
        user, profile = user.user, user
    else:
        raise ValueError('Expected profile or user, got %s' % (type(user),))
    return mark_safe(f'<span class="{profile.css_class}">'
                     f'<a href="{escape(reverse("user_page", args=[user.username]))}">'
                     f'{escape(profile.display_name)}</a></span>')


@registry.function
@registry.render_with('user/link-list.html')
def link_users(users):
    return {'users': users}


@registry.function
@registry.render_with('runtime-version-fragment.html')
def runtime_versions(versions):
    return {'runtime_versions': versions}


@registry.filter(name='absolutify')
def absolute_links(text, url):
    tree = lxml_tree.fromstring(text)
    for anchor in tree.xpath('.//a'):
        href = anchor.get('href')
        if href:
            anchor.set('href', urljoin(url, href))
    return tree


@registry.function(name='urljoin')
def join(first, second, *rest):
    if not rest:
        return urljoin(first, second)
    return urljoin(urljoin(first, second), *rest)


@registry.filter(name='ansi2html')
def ansi2html(s):
    return mark_safe(Ansi2HTMLConverter(inline=True).convert(s, full=False))
