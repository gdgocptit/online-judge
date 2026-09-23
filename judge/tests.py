import re
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from judge.models import Judge, Language, Problem, ProblemGroup, Profile, Submission
from judge.views.user import UserList


@override_settings(ALLOWED_HOSTS=['testserver'])
class UserHoverCardTests(TestCase):
    def test_profile_exposes_hover_target_and_exclusive_rank(self):
        profile = Profile.objects.create(user=User.objects.create_user(username='rank-demo'), rating=3250)
        self.assertNotContains(self.client.get(reverse('user_list')), '5P')
        response = self.client.get(reverse('user_page', args=[profile.user.username]))
        self.assertContains(response, '>5P</span>')
        self.assertContains(response, 'data-user-card="/user/rank-demo/card"', count=2)

    def test_public_card_shows_stats_without_private_fields(self):
        profile = Profile.objects.create(
            user=User.objects.create_user(username='go-player', email='private@example.com'),
            username_display_override='<b>Demo</b>', rating=3250,
            performance_points=2468, problem_count=256, notes='private admin note',
        )
        response = self.client.get(reverse('user_hovercard', args=[profile.user.username]))
        self.assertContains(response, '3250 (5P)')
        self.assertNotContains(response, '@go-player')
        self.assertNotContains(response, '3250 · 5P')
        self.assertContains(response, '5 Pro dan')
        self.assertContains(response, '2468')
        self.assertContains(response, '256')
        self.assertContains(response, '&lt;b&gt;Demo&lt;/b&gt;')
        self.assertNotContains(response, 'private@example.com')
        self.assertNotContains(response, 'private admin note')
        profile.rating = None
        profile.save(update_fields=['rating'])
        self.assertContains(self.client.get(reverse('user_hovercard', args=[profile.user.username])), 'Unrated')
        self.assertEqual(self.client.get(reverse('user_hovercard', args=['missing-user'])).status_code, 404)


@override_settings(ALLOWED_HOSTS=['testserver'],
                   CACHES={'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}})
class UserLeaderboardTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        for name, rating, points, problems in [
            ('unrated', None, 9999, 20),
            ('lower-rating', 1200, 900, 90),
            ('fewer-problems', 1600, 200, 2),
            ('tied-first', 1600, 200, 3),
            ('tied-second', 1600, 200, 3),
            ('higher-points', 1600, 300, 1),
            ('higher-rating', 1800, 10, 1),
            ('zero-rating', 0, 5000, 40),
        ]:
            Profile.objects.create(user=User.objects.create_user(username=name), rating=rating,
                                   performance_points=points, problem_count=problems)
        cls.expected = ['higher-rating', 'higher-points', 'tied-first', 'tied-second',
                        'fewer-problems', 'lower-rating', 'zero-rating', 'unrated']

    def test_rating_then_points_then_problems(self):
        response = self.client.get(reverse('user_list'))
        self.assertEqual([user.user.username for user in response.context['page_obj']], self.expected)
        self.assertContains(response, 'class="header rating-column"')
        self.assertContains(response, 'Rating')
        rows = re.findall(r'<tr id="user-([^"]+)"[^>]*>\s*<td>(\d+)</td>', response.content.decode())
        self.assertEqual(rows, list(zip(self.expected, ['1', '2', '3', '3', '5', '6', '7', '8'])))
        response = self.client.get(reverse('user_list'), {'order': '-problem_count'})
        self.assertEqual(response.context['page_obj'][0].user.username, 'lower-rating')

    @patch.object(UserList, 'paginate_by', 2)
    def test_handle_search_targets_sorted_page(self):
        for index, name in enumerate(self.expected):
            with self.subTest(name=name):
                page = index // 2 + 1
                query = f'?page={page}' if page > 1 else ''
                response = self.client.get(reverse('user_ranking_redirect'), {'handle': name})
                self.assertEqual(response.url, f'{reverse("user_list")}{query}#!{name}')


@override_settings(ALLOWED_HOSTS=['testserver'],
                   CACHES={'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}})
class ProblemWorkspaceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.language, _ = Language.objects.update_or_create(
            key='CPP17', defaults={'name': 'C++17', 'ace': 'c_cpp', 'common_name': 'C++'},
        )
        cls.other_language, _ = Language.objects.update_or_create(
            key='PY3', defaults={'name': 'Python 3', 'ace': 'python', 'common_name': 'Python'},
        )
        cls.user = User.objects.create_user(username='workspace-user')
        cls.profile = Profile.objects.create(user=cls.user, language=cls.language)
        cls.problem = Problem.objects.create(
            code='workspace', name='Workspace problem', description='Read the statement here.',
            group=ProblemGroup.objects.create(name='test', full_name='Test'),
            time_limit=1, memory_limit=65536, points=100, is_public=True,
        )
        cls.problem.allowed_languages.add(cls.language)
        cls.judge = Judge.objects.create(name='workspace-judge', auth_key='test-only', online=True)
        cls.judge.problems.add(cls.problem)
        cls.judge.runtimes.add(cls.language, cls.other_language)
        cls.url = reverse('problem_detail', args=[cls.problem.code])
        cls.submit_url = reverse('problem_submit', args=[cls.problem.code])

    def test_guest_sees_statement_and_login(self):
        response = self.client.get(self.url)
        self.assertContains(response, 'Read the statement here.')
        self.assertContains(response, 'Sign in to write and submit your solution.')
        self.assertNotContains(response, 'id="problem_submit"')

    def test_authenticated_workspace_uses_submission_endpoint(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertContains(response, 'class="problem-workspace"')
        self.assertContains(response, f'action="{self.submit_url}"')
        self.assertContains(response, "name='csrfmiddlewaretoken'")
        self.assertEqual(list(response.context['form'].fields['language'].queryset), [self.language])
        self.assertContains(response, 'type="submit"')

    def test_offline_judge_keeps_editor_but_disables_submission(self):
        Judge.objects.filter(pk=self.judge.pk).update(online=False)
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertContains(response, 'id="ace_source"')
        self.assertEqual(list(response.context['editor_languages']), [self.language])
        self.assertContains(response, 'No judge is available for this problem.')
        self.assertFalse(response.context['form'].fields['language'].queryset.exists())

    def test_private_problem_remains_inaccessible(self):
        Problem.objects.filter(pk=self.problem.pk).update(is_public=False)
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(self.url).status_code, 404)

    def test_invalid_language_does_not_create_submission(self):
        self.client.force_login(self.user)
        response = self.client.post(self.submit_url, {'language': self.other_language.pk, 'source': 'print(1)'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('language', response.context['form'].errors)
        self.assertContains(response, 'print(1)')
        self.assertFalse(Submission.objects.exists())

    @patch.object(Submission, 'judge')
    def test_valid_submission_keeps_existing_dispatch(self, dispatch):
        self.client.force_login(self.user)
        response = self.client.post(self.submit_url, {'language': self.language.pk, 'source': 'int main() {}'})
        submission = Submission.objects.get()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('submission_status', args=[submission.pk]))
        self.assertEqual(submission.source.source, 'int main() {}')
        self.assertEqual(submission.problem, self.problem)
        dispatch.assert_called_once_with(force_judge=True, judge_id='')
