"""
Core package initialization - ensures custom admin site is set up before any admin imports
"""
from django.contrib.admin.sites import AdminSite

class CustomAdminSite(AdminSite):
    login_template = 'registration/login.html'
    login_url = '/login/'

    def admin_view(self, view, cacheable=False):
        # Override to ensure all admin views use our custom login URL
        inner = super().admin_view(view, cacheable)

        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                from django.shortcuts import redirect
                return redirect(f'{self.login_url}?next={request.path}')
            return inner(request, *args, **kwargs)
        return wrapper

# Replace default admin site before any admin imports
from django.contrib import admin
admin.site = CustomAdminSite()
admin.site.site_header = '田小二售后服务平台'
admin.site.site_title = '田小二售后服务平台'
admin.site.index_title = '田小二售后服务平台管理'