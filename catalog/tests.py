from datetime import date, timedelta
import uuid

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from catalog.forms import RenewBookForm
from catalog.models import Author, Book, BookInstance, Language


User = get_user_model()


class AuthorModelTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        Author.objects.create(
            first_name='Big',
            last_name='Bob'
        )

    def test_first_name_label(self):
        author = Author.objects.get(id=1)

        field_label = author._meta.get_field(
            'first_name'
        ).verbose_name

        self.assertEqual(field_label, 'first name')

    def test_last_name_label(self):
        author = Author.objects.get(id=1)

        field_label = author._meta.get_field(
            'last_name'
        ).verbose_name

        self.assertEqual(field_label, 'last name')

    def test_date_of_birth_label(self):
        author = Author.objects.get(id=1)

        field_label = author._meta.get_field(
            'date_of_birth'
        ).verbose_name

        self.assertEqual(field_label, 'date of birth')

    def test_date_of_death_label(self):
        author = Author.objects.get(id=1)

        field_label = author._meta.get_field(
            'date_of_death'
        ).verbose_name

        self.assertEqual(field_label, 'Died')

    def test_first_name_max_length(self):
        author = Author.objects.get(id=1)

        max_length = author._meta.get_field(
            'first_name'
        ).max_length

        self.assertEqual(max_length, 100)

    def test_last_name_max_length(self):
        author = Author.objects.get(id=1)

        max_length = author._meta.get_field(
            'last_name'
        ).max_length

        self.assertEqual(max_length, 100)

    def test_object_name_is_last_name_comma_first_name(self):
        author = Author.objects.get(id=1)

        expected_object_name = (
            f'{author.last_name}, {author.first_name}'
        )

        self.assertEqual(
            str(author),
            expected_object_name
        )

    def test_get_absolute_url(self):
        author = Author.objects.get(id=1)

        self.assertEqual(
            author.get_absolute_url(),
            '/catalog/author/1/'
        )


class RenewBookFormTest(TestCase):

    def test_form_date_field_label(self):
        form = RenewBookForm()

        self.assertIsNone(
            form.fields['renewal_date'].label
        )

    def test_form_date_field_help_text(self):
        form = RenewBookForm()

        self.assertEqual(
            form.fields['renewal_date'].help_text,
            'Enter a date between now and 4 weeks (default 3).'
        )

    def test_renewal_date_in_past(self):
        yesterday = date.today() - timedelta(days=1)

        form = RenewBookForm(
            data={
                'renewal_date': yesterday
            }
        )

        self.assertFalse(form.is_valid())

    def test_renewal_date_today(self):
        form = RenewBookForm(
            data={
                'renewal_date': date.today()
            }
        )

        self.assertTrue(form.is_valid())

    def test_renewal_date_four_weeks(self):
        four_weeks = date.today() + timedelta(weeks=4)

        form = RenewBookForm(
            data={
                'renewal_date': four_weeks
            }
        )

        self.assertTrue(form.is_valid())

    def test_renewal_date_too_far_in_future(self):
        future_date = date.today() + timedelta(
            weeks=4,
            days=1
        )

        form = RenewBookForm(
            data={
                'renewal_date': future_date
            }
        )

        self.assertFalse(form.is_valid())

    def test_renewal_date_valid(self):
        valid_date = date.today() + timedelta(days=14)

        form = RenewBookForm(
            data={
                'renewal_date': valid_date
            }
        )

        self.assertTrue(form.is_valid())


class AuthorListViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):

        for author_id in range(13):
            Author.objects.create(
                first_name=f'First {author_id}',
                last_name=f'Last {author_id}'
            )

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get('/catalog/authors/')

        self.assertEqual(
            response.status_code,
            200
        )

    def test_view_url_accessible_by_name(self):
        response = self.client.get(
            reverse('authors')
        )

        self.assertEqual(
            response.status_code,
            200
        )

    def test_view_uses_correct_template(self):
        response = self.client.get(
            reverse('authors')
        )

        self.assertEqual(
            response.template_name,
            ['catalog/author_list.html']
        )

    def test_pagination_is_ten(self):
        response = self.client.get(
            reverse('authors')
        )

        self.assertEqual(
            len(response.context['author_list']),
            10
        )

    def test_lists_all_authors(self):
        response = self.client.get(
            reverse('authors') + '?page=2'
        )

        self.assertEqual(
            len(response.context['author_list']),
            3
        )


class AuthorDetailViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = Author.objects.create(
            first_name='John',
            last_name='Smith'
        )

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get(
            f'/catalog/author/{self.author.id}/'
        )

        self.assertEqual(
            response.status_code,
            200
        )

    def test_view_uses_correct_template(self):
        response = self.client.get(
            self.author.get_absolute_url()
        )

        self.assertEqual(
            response.template_name,
            ['catalog/author_detail.html']
        )

    def test_view_url_accessible_by_name(self):
        response = self.client.get(
            self.author.get_absolute_url()
        )

        self.assertEqual(
            response.status_code,
            200
        )

    def test_object_displayed(self):
        response = self.client.get(
            self.author.get_absolute_url()
        )

        self.assertContains(
            response,
            self.author.first_name
        )

        self.assertContains(
            response,
            self.author.last_name
        )


class LoanedBooksByUserListViewTest(TestCase):

    def setUp(self):

        self.test_user1 = User.objects.create_user(
            username='testuser1',
            password='testpassword123'
        )

        self.test_user2 = User.objects.create_user(
            username='testuser2',
            password='testpassword123'
        )

        self.author = Author.objects.create(
            first_name='Test',
            last_name='Author'
        )

        self.language = Language.objects.create(
            name='English'
        )

        self.book1 = Book.objects.create(
            title='Book One',
            author=self.author,
            summary='Summary one',
            isbn='1234567890123',
            language=self.language
        )

        self.book2 = Book.objects.create(
            title='Book Two',
            author=self.author,
            summary='Summary two',
            isbn='1234567890124',
            language=self.language
        )

        self.book3 = Book.objects.create(
            title='Book Three',
            author=self.author,
            summary='Summary three',
            isbn='1234567890125',
            language=self.language
        )

        self.book_instance1 = BookInstance.objects.create(
            book=self.book1,
            borrower=self.test_user1,
            imprint='Test imprint 1',
            due_back=date.today() + timedelta(days=10),
            status='o'
        )

        self.book_instance2 = BookInstance.objects.create(
            book=self.book2,
            borrower=self.test_user1,
            imprint='Test imprint 2',
            due_back=date.today() + timedelta(days=5),
            status='o'
        )

        self.book_instance3 = BookInstance.objects.create(
            book=self.book3,
            borrower=self.test_user2,
            imprint='Test imprint 3',
            due_back=date.today() + timedelta(days=1),
            status='o'
        )

    def test_redirect_if_not_logged_in(self):

        response = self.client.get(
            reverse('my-borrowed')
        )

        self.assertRedirects(
            response,
            '/accounts/login/?next=/catalog/mybooks/'
        )

    def test_logged_in_uses_correct_template(self):

        self.client.force_login(
            self.test_user1
        )

        response = self.client.get(
            reverse('my-borrowed')
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertTemplateUsed(
            response,
            'catalog/bookinstance_list_borrowed_user.html'
        )

    def test_only_logged_in_users_books_are_shown(self):

        self.client.force_login(
            self.test_user1
        )

        response = self.client.get(
            reverse('my-borrowed')
        )

        self.assertContains(
            response,
            self.book1.title
        )

        self.assertContains(
            response,
            self.book2.title
        )

        self.assertNotContains(
            response,
            self.book3.title
        )

    def test_books_are_ordered_by_due_date(self):

        self.client.force_login(
            self.test_user1
        )

        response = self.client.get(
            reverse('my-borrowed')
        )

        books = response.context['bookinstance_list']

        self.assertEqual(
            books[0],
            self.book_instance2
        )

        self.assertEqual(
            books[1],
            self.book_instance1
        )


class RenewBookLibrarianViewTest(TestCase):

    def setUp(self):

        self.test_user = User.objects.create_user(
            username='librarian',
            password='testpassword123'
        )

        self.normal_user = User.objects.create_user(
            username='normaluser',
            password='testpassword123'
        )

        permission = Permission.objects.get(
            codename='can_mark_returned'
        )

        self.test_user.user_permissions.add(
            permission
        )

        self.author = Author.objects.create(
            first_name='Test',
            last_name='Author'
        )

        self.language = Language.objects.create(
            name='English'
        )

        self.book = Book.objects.create(
            title='Test Book',
            author=self.author,
            summary='Test summary',
            isbn='1234567890999',
            language=self.language
        )

        self.book_instance = BookInstance.objects.create(
            book=self.book,
            borrower=self.normal_user,
            imprint='Test imprint',
            due_back=date.today() + timedelta(days=10),
            status='o'
        )

    def test_redirect_if_not_logged_in(self):

        response = self.client.get(
            reverse(
                'renew-book-librarian',
                kwargs={
                    'pk': self.book_instance.id
                }
            )
        )

        self.assertEqual(
            response.status_code,
            302
        )

    def test_forbidden_for_user_without_permission(self):

        self.client.force_login(
            self.normal_user
        )

        response = self.client.get(
            reverse(
                'renew-book-librarian',
                kwargs={
                    'pk': self.book_instance.id
                }
            )
        )

        self.assertEqual(
            response.status_code,
            403
        )

    def test_librarian_can_access_view(self):

        self.client.force_login(
            self.test_user
        )

        response = self.client.get(
            reverse(
                'renew-book-librarian',
                kwargs={
                    'pk': self.book_instance.id
                }
            )
        )

        self.assertEqual(
            response.status_code,
            200
        )

    def test_correct_template_used(self):

        self.client.force_login(
            self.test_user
        )

        response = self.client.get(
            reverse(
                'renew-book-librarian',
                kwargs={
                    'pk': self.book_instance.id
                }
            )
        )

        self.assertTemplateUsed(
            response,
            'catalog/book_renew_librarian.html'
        )

    def test_initial_renewal_date(self):

        self.client.force_login(
            self.test_user
        )

        response = self.client.get(
            reverse(
                'renew-book-librarian',
                kwargs={
                    'pk': self.book_instance.id
                }
            )
        )

        form = response.context['form']

        expected_date = date.today() + timedelta(weeks=3)

        self.assertEqual(
            form.initial['renewal_date'],
            expected_date
        )

    def test_valid_post_redirects(self):

        self.client.force_login(
            self.test_user
        )

        new_date = date.today() + timedelta(days=14)

        response = self.client.post(
            reverse(
                'renew-book-librarian',
                kwargs={
                    'pk': self.book_instance.id
                }
            ),
            {
                'renewal_date': new_date
            }
        )

        self.assertRedirects(
            response,
            reverse('all-borrowed')
        )

        self.book_instance.refresh_from_db()

        self.assertEqual(
            self.book_instance.due_back,
            new_date
        )

    def test_invalid_past_date(self):

        self.client.force_login(
            self.test_user
        )

        old_date = date.today() - timedelta(days=1)

        response = self.client.post(
            reverse(
                'renew-book-librarian',
                kwargs={
                    'pk': self.book_instance.id
                }
            ),
            {
                'renewal_date': old_date
            }
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertFormError(
            response.context['form'],
            'renewal_date',
            'Invalid date - renewal in past'
        )

    def test_invalid_future_date(self):

        self.client.force_login(
            self.test_user
        )

        future_date = date.today() + timedelta(
            weeks=4,
            days=1
        )

        response = self.client.post(
            reverse(
                'renew-book-librarian',
                kwargs={
                    'pk': self.book_instance.id
                }
            ),
            {
                'renewal_date': future_date
            }
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertFormError(
            response.context['form'],
            'renewal_date',
            'Invalid date - renewal more than 4 weeks ahead'
        )

    def test_404_for_invalid_book_instance(self):

        self.client.force_login(
            self.test_user
        )

        invalid_uuid = uuid.uuid4()

        response = self.client.get(
            reverse(
                'renew-book-librarian',
                kwargs={
                    'pk': invalid_uuid
                }
            )
        )

        self.assertEqual(
            response.status_code,
            404
        )