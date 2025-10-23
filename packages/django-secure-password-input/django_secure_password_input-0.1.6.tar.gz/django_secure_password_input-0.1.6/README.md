# django-secure-password-input

A simple django application provides function to encrypt password value with rsa public key before form submit and decrypt at the backend.

## Install

```shell
pip install django-secure-password-input
```

## Usage

**pro/settings.py**

```python
INSTALLED_APPS = [
    ...
    'django_secure_password_input',
    ...
]

DJANGO_SECURE_PASSWORD_INPUT_RSA_PRIVATE_KEY = """-----BEGIN RSA PRIVATE KEY-----
......
-----END RSA PRIVATE KEY-----
"""

DJANGO_SECURE_PASSWORD_INPUT_ENCRYPTED_VALUE_PREFIX = "rsa-encrypted:"
```

**Note:**

1. Add your own DJANGO_SECURE_PASSWORD_INPUT_RSA_PRIVATE_KEY and keep it secret. You can generate rsa private key with rsa module in ipython. Copy all things between "BEGIN RSA PRIVATE KEY" and "END RSA PRIVATE KEY" and must include "BEGIN RSA PRIVATE KEY" and "END RSA PRIVATE KEY" lines. It will work if you not provide your own private key, it will use the django_secure_password_input's default private key, and it's not safe for you.

    ```python
    In [1]: import rsa

    In [2]: pk, sk = rsa.newkeys(4096)

    In [3]: print(sk.save_pkcs1().decode())
    -----BEGIN RSA PRIVATE KEY-----
    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
    +H8oSvxWpAB+Kw==
    -----END RSA PRIVATE KEY-----


    In [4]:
    ```

**app/admin.py**

```python
from django.contrib import admin
from django import forms
from django_secure_password_input.fields import DjangoSecurePasswordInput
from .models import Account


class AccountForm(forms.ModelForm):
    password = DjangoSecurePasswordInput()

    class Meta:
        model = Account
        exclude = []

class AccountAdmin(admin.ModelAdmin):
    form = AccountForm
    list_display = ["username", "password"]

admin.site.register(Account, AccountAdmin)
```

**Note:**

1. Create a form, and override password field using type DjangoSecurePasswordInput.

## Release

### v0.1.0

- First release. |

### v0.1.1

-  No depends on django-static-jquery3.

### v0.1.2

- Doc update.
- Add License file. 

### v0.1.3

- Fix problems in django 3.2.x.

### v0.1.4

- Let the end user to choose the package's version.

### v0.1.5

- Doc update.

### v0.1.6

- Doc update.
