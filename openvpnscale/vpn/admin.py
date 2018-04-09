from django.contrib import admin
from .models import (
    Host,
    ServerConfig,
    ClientConfig,
    VPNServer,
    Certificate,
    ExtraClientOption,
    ExtraServerOption
)
admin.site.register(Host)
admin.site.register(ServerConfig)
admin.site.register(ClientConfig)
admin.site.register(VPNServer)
admin.site.register(Certificate)
admin.site.register(ExtraClientOption)
admin.site.register(ExtraServerOption)
