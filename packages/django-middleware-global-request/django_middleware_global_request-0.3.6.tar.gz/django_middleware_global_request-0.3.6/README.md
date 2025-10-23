# django-middleware-global-request


Django middleware that keep request instance for every thread.

## Install


```shell
pip install django-middleware-global-request
```
## Note

- It's NOT good to use global request, you should pass the request instance from view to anywhere you want to use it.
- If you use the global request in Model layout, it means when you call the Model method from Django Shell, you get a None request.

## Usage

1. Add django application `django_middleware_global_request` to INSTALLED_APPS in `pro/settings.py`:

    ```python
    INSTALLED_APPS = [
        ...
        'django_middleware_global_request',
        ...
    ]
    ```

2. Add `GlobalRequestMiddleware` to MIDDLEWARE in `pro/settings.py`:


    ```python
    MIDDLEWARE = [
        ...
        'django_middleware_global_request.middleware.GlobalRequestMiddleware',
        ...
    ]
    ```

3. Use `get_request` to get the global request instance from a function in `pro/models.py`:

    ```python
    from django.db import models
    from django.conf import settings
    from django_middleware_global_request import get_request

    class Book(models.Model):
        name = models.CharField(max_length=64)
        author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

        def __str__(self):
            return self.name

        def save(self, *args, **kwargs):
            if not self.author:
                request = get_request()
                if request:
                    self.author = request.user
            return super().save(*args, **kwargs)
    ```

4. Use `with GlobalRequest(xxx): pass` to set the global request to a new value in NON-USER-REQUEST context, e.g. in `management command` context or in `python manage.py shell` context. Out of the `with scope`, the global request instance will be reset to the value when entering into the `with scope`.

    ```python
    import djclick as click
    from django.contrib.auth import get_user_model
    from django_middleware_global_request_example.models import Book
    from django_middleware_global_request import GlobalRequest


    @click.command()
    @click.option("-n", "--number", type=int, default=10)
    def create(number):
        admin = get_user_model().objects.all()[0]
        with GlobalRequest(user=admin):
            for i in range(number):
                book = Book(name="book{idx}".format(idx=i+1))
                book.save()
                print(i, book.name, book.author.username)
    ```

5. Use `GlobalRequestStorage` to set the global request instance for current thread context. The global request instance will all time exists until you changed it by another value.

*example.py*

```
from django.contrib.auth import get_user_model
from django_middleware_global_request_example.models import Book
from django_middleware_global_request import GlobalRequestStorage

b1 = Book(name="b1")
b1.save()
print(b1, b1.author)

admin = get_user_model().objects.get(username="admin")
GlobalRequestStorage().set_user(admin)

b2 = Book(name="b2")
b2.save()
print(b2, b2.author)

b3 = Book(name="b3")
b3.save()
print(b3, b3.author)
```

*example result in python3 manage.py shell context*

```
test@test django-middleware-global-request % python3.9 manage.py shell
Python 3.9.13 (main, Jun  8 2022, 15:40:49) 
Type 'copyright', 'credits' or 'license' for more information
IPython 8.3.0 -- An enhanced Interactive Python. Type '?' for help.

In [1]: import example
b1 None
b2 admin
b3 admin
```

## Test Passed

- python27:~=django1.11.29
- python34:~=django1.11.29
- python34:~=django2.0.13
- python35:~=django1.11.29
- python35:~=django2.0.13
- python35:~=django2.1.15
- python35:~=django2.2.28
- python36:~=django2.0.13
- python36:~=django2.1.15
- python36:~=django2.2.28
- python36:~=django3.0.14
- python36:~=django3.1.14
- python36:~=django3.2.21
- python37:~=django2.0.13
- python37:~=django2.1.15
- python37:~=django2.2.28
- python37:~=django3.0.14
- python37:~=django3.1.14
- python37:~=django3.2.21
- python38:~=django2.0.13
- python38:~=django2.1.15
- python38:~=django2.2.28
- python38:~=django3.0.14
- python38:~=django3.1.14
- python38:~=django3.2.21
- python38:~=django4.0.10
- python38:~=django4.1.11
- python38:~=django4.2.5
- python39:~=django2.0.13
- python39:~=django2.1.15
- python39:~=django2.2.28
- python39:~=django3.0.14
- python39:~=django3.1.14
- python39:~=django3.2.21
- python39:~=django4.0.10
- python39:~=django4.1.11
- python39:~=django4.2.5
- python310:~=django2.1.15
- python310:~=django2.2.28
- python310:~=django3.0.14
- python310:~=django3.1.14
- python310:~=django3.2.21
- python310:~=django4.0.10
- python310:~=django4.1.11
- python310:~=django4.2.5
- python311:~=django2.2.28
- python311:~=django3.0.14
- python311:~=django3.1.14
- python311:~=django3.2.21
- python311:~=django4.0.10
- python311:~=django4.1.11
- python311:~=django4.2.5

## Releases

### v0.1.0

- First release.

### v0.1.1

- Some changes.

### v0.1.2

- Some changes.

### v0.2.0

- Rename the core package from django_global_request to django_middleware_global_request so that it matches with the package name. **Note:** It's NOT backward compatible, all applications that using old name MUST do changes.

### v0.3.0

- Add `GlobalRequest` and `GlobalRequestStorage` to set the global request instance value for NON-USER-REQUEST context.

### v0.3.1

- Add `app_middleware_requires` to module \_\_init\_\_.py to work with `django-app-requires`.

### v0.3.2

- Doc update.

### v0.3.3

- All unit test passed.

### v0.3.4

- Add unit tests for python12 and django-5.0.6.

### v0.3.5

- Fixed a packaging issue that did not exclude 'example.management.commands'.
- Fixed an issue where the `request` instance was not accessible during streaming generation interactions.

### v0.3.6

- Doc update.
