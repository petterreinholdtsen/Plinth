import cherrypy
from gettext import gettext as _
from plugin_mount import PagePlugin
from modules.auth import require
from forms import Form
import cfg
from privilegedactions import privilegedaction_run

class Privacy(PagePlugin):
    order = 20 # order of running init in PagePlugins
    def __init__(self, *args, **kwargs):
        PagePlugin.__init__(self, *args, **kwargs)
        self.register_page("privacy")
        self.menu = cfg.main_menu.add_item("Privacy", "icon-eye-open", "/privacy", 12)
        self.menu.add_item("General Config", "icon-asterisk", "/privacy/config", 10)
        self.menu.add_item("Ad Blocking", "icon-ban-circle", "/privacy/adblock", 20)
        self.menu.add_item("TOR", "icon-eye-close", "/privacy/TOR", 30)
        self.menu.add_item("HTTPS Everywhere", "icon-lock", "/privacy/https_everywhere", 30)

    @cherrypy.expose
    def index(self):
        #raise cherrypy.InternalRedirect('/privacy/config')
        return self.config()

    @cherrypy.expose
    @require()
    def config(self):
        main="""
        <p>Privacy controls are not yet implemented.  This page is a
        placeholder and a promise: privacy is important enough that it
        is a founding consideration, not an afterthought.</p>
        """
        return self.fill_template(title=_("Privacy Control Panel"), main=main,
sidebar_right=_("""<strong>Statement of Principles</strong><p>When we say your
privacy is important, it's not just an empty pleasantry.  We really
mean it.  Your privacy control panel should give you fine-grained
control over exactly who can access your %(box_name)s and the
information on it.</p>

<p>Your personal information should not leave this box without your
knowledge and direction.  And if companies or government wants this
information, they have to ask <strong>you</strong> for it.  This gives you a
change to refuse and also tells you who wants your data.</p>
""") % {'box_name':cfg.box_name})

    def update_TOR_setup(self, tor_setting):
        if tor_setting in ('disabled', 'encrypted', 'alltcp'):
            privilegedaction_run("tor-setup", [tor_setting])
        else:
            True
        return tor_setting

    @cherrypy.expose
    @require()
    def TOR(self, submitted=False, tor_setting = None, **kwargs):
        checkedinfo = {
            'enable'   : False,
            'relay'    : False,
            'exitnode' : False,
            'dns'      : False,
            }

        if submitted:
            opts = []
            for k in kwargs.keys():
                if 'on' == kwargs[k]:
                    shortk = k.split("tor_").pop()
                    cfg.log.info('found: %s, short %s ' % (k, shortk))
                    checkedinfo[shortk] = True

            for key in checkedinfo.keys():
                if checkedinfo[key]:
                    opts.append(key)
                else:
                    opts.append('no'+key)
            privilegedaction_run("tor-setup", opts)

        output, error = privilegedaction_run("tor-setup", ['status'])
        if error:
            raise Exception("something is wrong: " + error)
        tor_setup = output.split()
        for option in tor_setup:
            checkedinfo[option] = True
        for t in ('disabled', 'encrypted', 'alltcp'):
            if tor_setting == t:
                checkedinfo[t] = True
            else:
                checkedinfo[t] = False
        main = ""
        form = Form(title="Configuration", 
                        action="/privacy/TOR", 
                        name="configure_tor",
                        message='')
        form.checkbox(_("Enable TOR"), name="tor_enable", id="tor_enable", checked=checkedinfo['enable'])
        form.checkbox(_("Relay TOR traffic"), name="tor_relay", id="tor_relay", checked=checkedinfo['relay'])
#        form.checkbox(_("Exit node for TOR traffic"), name="tor_exitnode", id="tor_exitnode", checked=checkedinfo['exitnode'])
        form.checkbox(_("Use TOR for DNS lookup"), name="tor_dns", id="tor_dns", checked=checkedinfo['dns'])
        form.html(_("<p>Should TOR be used by default for those using %s as its http/https web proxy or the default Internet router?</p>") % cfg.product_name)
        form.radiobutton(_('Do not use TOR'),
                         name="tor_setting", value='disabled', checked=checkedinfo['disabled'])
        form.radiobutton(_('Use TOR for encrypted connections like https and ssh'),
                         name="tor_setting", value='encrypted', checked=checkedinfo['encrypted'])
        form.radiobutton(_('Use TOR for all TCP connection'),
                         name="tor_setting", value='alltcp', checked=checkedinfo['alltcp'])
        form.hidden(name="submitted", value="True")
        form.html(_("<p>For web traffic, it is wise to disable javascript when using tor, both to avoid giving the site the chance to look up your location, but also to not allow exit nodes to inject javascript into web pages.</p>"))
        form.submit(_("Update setup"))
        main += form.render()
        return self.fill_template(title=_("TOR"), main=main,
sidebar_right=_("""<strong>The Onion Router</strong>
<p>Warning: Using Tor only make it hard to figure out where you are.
It do not protect the communication.  For this, you need to make sure
an encrypted channel like TCP using SSL/TLS or SSH is used, and ensure
to check the encryption key/certificate of the other end to ensure you
are talking to the correct server.</p>
"""))
