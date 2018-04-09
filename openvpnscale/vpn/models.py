from django.db import models
from django.core import validators
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Host(models.Model):
    ipv4 = models.GenericIPAddressField(
        protocol='IPv4',
        primary_key=True
    )
    hostname = models.CharField(
        max_length=50,
        blank=True
    )


class PushOption(models.Model):
    name = models.CharField(
        max_length=20, validators=[
            validators.RegexValidator(r'^[a-z\-]+$')
        ]
    )
    value = models.CharField(max_length=40, blank=True)


class ExtraServerOption(models.Model):
    name = models.CharField(
        max_length=20, validators=[
            validators.RegexValidator(r'^[a-z\-]+$')
        ]
    )
    value = models.CharField(max_length=40, blank=True)


class ExtraClientOption(models.Model):
    name = models.CharField(
        max_length=20, validators=[
            validators.RegexValidator(r'^[a-z\-]+$')
        ]
    )
    value = models.CharField(max_length=40, blank=True)


class ServerConfig(models.Model):
    port = models.IntegerField(
        default=1194,
        validators=[
            validators.MinValueValidator(1),
            validators.MaxValueValidator(65535),
        ], help_text=_('Which local IP address should OpenVPN'
                       'listen on? (optional)')
    )
    protocol = models.CharField(
        default='udp',
        max_length=3,
        choices=[('udp', 'udp'), ('tcp', 'tcp')],
        help_text=_('Which TCP/UDP port should OpenVPN listen on?'
                    'If you want to run multiple OpenVPN instances'
                    'on the same machine, use a different port'
                    'number for each one.  You will need to'
                    'open up this port on your firewall.')
    )
    dev = models.CharField(
        default='tun',
        max_length=5,
        validators=[validators.RegexValidator(r'^(tun|tap)(\d+)?$')],
        help_text=_('"dev tun" will create a routed IP tunnel, '
                    '"dev tap" will create an ethernet tunnel. '
                    'Use "dev tap0" if you are ethernet bridging '
                    'and have precreated a tap0 virtual interface '
                    'and bridged it with your ethernet interface. '
                    'If you want to control access policies '
                    'over the VPN, you must create firewall '
                    'rules for the the TUN/TAP interface. '
                    'On non-Windows systems, you can give '
                    'an explicit unit number, such as tun0. '
                    'On Windows, use "dev-node" for this. '
                    'On most systems, the VPN will not function '
                    'unless you partially or fully disable '
                    'the firewall for the TUN/TAP interface.')
    )
    keep_alive = models.CharField(
        default="10 120",
        verbose_name=_('keep-alive'),
        max_length=10,
        validators=[
            validators.RegexValidator(r"^\d+ \d+$", message=_('Enter a valid keep-alive option.'))
        ], blank=True
    )
    push_options = models.ManyToManyField(
        PushOption, blank=True,
        verbose_name=_('push options'),
        help_text=_('Extra push options, at your risk')
    )
    extra_options = models.ManyToManyField(
        ExtraServerOption, blank=True,
        verbose_name=_('extra options'),
        help_text=_('Extra options, at your risk')
    )

    up = models.BooleanField(default=False, help_text='Is server up?')

    def template_context(self):
        from django.template import Context
        res = dict()
        res['port'] = "port {}".format(self.port)
        res['proto'] = "proto {}".format(self.protocol)
        res['dev'] = "dev {}".format(self.dev)
        res['keepalive'] = "keepalive {}".format(self.keep_alive)
        push = []
        for po in self.push_options.all():
            push.append('push "{0} {1}"'.format(po.name, po.value))
        res['push'] = '\n'.join(push)
        extra = []
        for eo in self.extra_options.all():
            extra.append('{0} {1}'.format(eo.name, eo.value))
        res['extra'] = '\n'.join(extra)
        return Context(res)

    def txt(self):
        from django.template import loader
        template = loader.get_template('ovpn/server.conf')
        return template.render(self.template_context())


class VPNServer(models.Model):
    host = models.ForeignKey(Host, on_delete=models.CASCADE)
    config = models.ForeignKey(ServerConfig, on_delete=models.PROTECT)


class ClientConfig(models.Model):
    remotes = models.ManyToManyField(
        VPNServer, blank=False,
        help_text='Available remotes'
    )
    dev = models.CharField(
        default='tun',
        max_length=5,
        validators=[validators.RegexValidator(r'^(tun|tap)(\d+)?$')],
        help_text=_('TUN/TAP virtual network device ( X can be omitted for a dynamic device.) '
                    'See examples section below for an example on setting up a TUN device. '
                    'You must use either tun devices on both ends of the connection or tap devices on both ends. '
                    'You cannot mix them, as they represent different underlying protocols. '
                    'tun devices encapsulate IPv4 while tap devices encapsulate ethernet')
    )
    inactive = models.IntegerField(
        default=3600,
        help_text=_('(Experimental) Causes OpenVPN to exit after n seconds of inactivity on the TUN/TAP device. '
                    'The time length of inactivity is measured since the last incoming tunnel packet.'),
        blank=True
    )
    keep_alive = models.CharField(
        default="10 900",
        verbose_name=_('keep-alive'),
        max_length=10,
        validators=[
            validators.RegexValidator(r"^\d+ \d+$", message=_('Enter a valid keep-alive option.'))
        ],
        blank=True
    )
    resolve_retry = models.CharField(
        default='60',
        verbose_name=_("resolve-retry"),
        max_length=8,
        validators=[
            validators.RegexValidator(r"^(\d+|infinite)$", message=_('Enter a valid resolv-retry option.'))
        ],
        help_text=_('If hostname resolve fails for remote, retry resolve for n seconds before failing. '
                    'Set n to "infinite" to retry indefinitely. '
                    'By default, resolv-retry infinite is enabled. You can disable by setting n=0.'),
        blank=True
    )

    server_poll_timeout = models.IntegerField(
        default=4,
        verbose_name=_("server poll timeout"),
        validators=[
            validators.MinValueValidator(1),
        ],
        blank=True
    )

    extra_options = models.ManyToManyField(
        ExtraClientOption, blank=True,
        verbose_name=_('extra options'),
        help_text='Extra options, at your risk')

    def template_context(self):
        from django.template import Context
        res = dict()
        res['dev'] = "dev {}".format(self.dev)
        res['inactive'] = "inactive {}".format(self.inactive) if self.inactive is not None else ''
        res['keepalive'] = "keepalive {}".format(self.keep_alive) if self.keep_alive is not None else ''
        res['resolve_retry'] = "resolve-retry {}".format(self.resolve_retry) if self.resolve_retry is not None else ''
        remotes = set()
        for rem in self.remotes.all():
            remotes.add('remote {0} {1} {2}'.format(
                rem.host.ipv4 if rem.host.hostname is None else rem.host.hostname
                , rem.config.port, rem.config.protocol))
        res['remotes'] = '\n'.join(remotes)
        extra = []
        for eo in self.extra_options.all():
            extra.append('{0} {1}'.format(eo.name, eo.value).strip())
        res['extra'] = '\n'.join(extra)
        return Context(res)


class Certificate(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    config = models.ForeignKey(ClientConfig, on_delete=models.PROTECT)
    name = models.CharField(
        max_length=50,
        validators=[validators.validate_slug],
        primary_key=True
    )
    active = models.BooleanField(default=False)
