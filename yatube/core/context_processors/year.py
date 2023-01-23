import datetime


def year(request):
    """Добавляет переменную с текущим годом."""
    return {
        'year': int(
            str(
                datetime.datetime.now()
            )[0:4]
        )
    }
