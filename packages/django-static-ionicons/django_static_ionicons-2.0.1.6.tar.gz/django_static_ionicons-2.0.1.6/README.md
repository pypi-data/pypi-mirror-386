# django-static-ionicons


Django application contain ionicons static files


## Install


```
pip install django-static-ionicons
```

## Settings

```
INSTALLED_APPS = [
    ...
    "django_static_ionicons",
    ...
]
```

## Usage

*app/templates/demo.html*

```django
{% load staticfiles %}

<link rel="stylesheet" type="text/css" href="{% static "ionicons/css/ionicons.css" %}">
```

## Releases

### v2.0.1

- First release.

### v2.0.1.1

- Repackage.

### v2.0.1.2

- Add demo page.

### v2.0.1.3

- No depends on django.
- Turn to the package as a pure static wrapper package.

### v2.0.1.4

- Doc update.

### v2.0.1.5

- Doc update.

### v2.0.1.6

- Doc update.