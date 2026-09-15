from django import template

register = template.Library()


@register.filter
def cop(value):
    """Formato pesos Colombia: $ 1.234.567"""
    try:
        numero = int(round(float(value)))
    except (TypeError, ValueError):
        return value
    texto = f"{numero:,}".replace(",", ".")
    return f"$ {texto}"
