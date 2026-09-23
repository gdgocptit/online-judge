from types import SimpleNamespace

from django.template.loader import render_to_string
from django.test import SimpleTestCase

from judge.jinja2.rating import get_name, get_rating_class, get_short_name
from judge.ratings import rating_class, rating_name, rating_progress, rating_short_name


class GoRankTests(SimpleTestCase):
    def test_rank_boundaries(self):
        bands = [(0, 10, '30k', '30 kyu', 'rate-kyu')]
        bands += [(11 + 10 * i, 20 + 10 * i, f'{29 - i}k', f'{29 - i} kyu', 'rate-kyu')
                  for i in range(8)]
        bands += [(91, 199, '21k', '21 kyu', 'rate-kyu')]
        bands += [(200 + 100 * i, 299 + 100 * i, f'{20 - i}k', f'{20 - i} kyu', 'rate-kyu')
                  for i in range(20)]
        bands += [(2200 + 100 * i, 2299 + 100 * i, f'{i + 1}d', f'{i + 1} dan', 'rate-dan')
                  for i in range(6)]
        bands += [(2800 + 100 * i, 2899 + 100 * i, f'{i + 1}P', f'{i + 1} Pro dan', 'rate-pro-dan')
                  for i in range(9)]
        for start, end, short, long, css in bands:
            for value in (start, end):
                with self.subTest(value=value):
                    self.assertEqual(rating_short_name(value), short)
                    self.assertEqual(rating_name(value), long)
                    self.assertEqual(rating_class(value), css)
                    self.assertGreaterEqual(rating_progress(value), 0)
                    self.assertLessEqual(rating_progress(value), 1)
        self.assertEqual(rating_short_name(-1), '30k')
        self.assertEqual(rating_progress(-1), 0)
        self.assertEqual(rating_short_name(10000), '9P')
        self.assertEqual(rating_progress(10000), 1)

    def test_rating_display_handles_objects_zero_and_unrated(self):
        for value, short, long in [(0, '30k', '30 kyu'), (100, '21k', '21 kyu'),
                                   (2200, '1d', '1 dan'), (2800, '1P', '1 Pro dan'),
                                   (3600, '9P', '9 Pro dan')]:
            for obj in (value, SimpleNamespace(rating=value)):
                with self.subTest(value=value, obj=obj):
                    html = render_to_string('user/rating.html', {'rating': obj})
                    self.assertIn(f'title="{long}"', html)
                    self.assertIn(f'{value} · {short}', html)
        for obj in (None, SimpleNamespace(rating=None)):
            self.assertEqual(get_short_name(obj), 'Unrated')
            self.assertEqual(get_name(obj), 'Unrated')
            self.assertEqual(get_rating_class(obj), 'rate-none')
