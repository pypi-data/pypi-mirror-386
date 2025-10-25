"""
Dashboard view for Centrifugo monitoring.
"""

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render


@staff_member_required
def dashboard_view(request):
    """Render the Centrifugo dashboard template."""
    context = {
        'page_title': 'Centrifugo Monitor Dashboard',
    }
    return render(request, 'django_cfg_centrifugo/pages/dashboard.html', context)
