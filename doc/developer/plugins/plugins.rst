.. highlight:: python
   :linenothreshold: 5

.. _`pluginsetup`:

Creating a plugin
=================

You can extend pretalx with custom Python code using the official plugin API.
Think of every plugin as an independent Django application living in its own
python package installed like any other python module.

The communication between pretalx and the plugins happens using Django’s
`signal dispatcher`_ feature. The core modules of pretalx expose signals which
you can read about on the next pages.

To create a new plugin, create a new python package which must be a valid
`Django application`_ and must contain plugin meta-data, as described below.
You will need some boilerplate for every plugin to get started. To save your
time, we created a `cookiecutter`_ template that you can use like this::

   (env)$ pip install cookiecutter
   (env)$ cookiecutter https://github.com/pretalx/pretalx-plugin-cookiecutter

This will ask you some questions and then create a project folder for your plugin.
Afterwards install your plugin into pretalx:

   (env)$ cd pretalx-pluginname
   (env)$ python -m pip install -e .

If you already had it running, you’ll now have to restart your pretalx dev-server
for it to recognize the new plugin.

About this Documentation
------------------------

The following pages go into detail about the types of plugins
supported. While these instructions don’t assume that you know a lot about
pretalx, they do assume that you have prior knowledge about Django (e.g. its
view layer, how its ORM works, topics covered in the Django tutorial.).

Plugin meta-data
----------------

The plugin meta-data lives inside a ``PretalxPluginMeta`` class inside your
configuration class. The meta-data class must define the following attributes:

.. rst-class:: rest-resource-table

================== ==================== ===========================================================
Attribute          Type                 Description
================== ==================== ===========================================================
name               string               The human-readable name of your plugin
author             string               Your name
version            string               A human-readable version code of your plugin
description        string               A more verbose description of what your plugin does.
category           string               A category for your plugin, used to group it in the plugin list.
                                        Supported categories are ``FEATURE``, ``INTEGRATION``, ``CUSTOMIZATION``,
                                        ``EXPORTER``, ``RECORDING``, ``LANGUAGE``, ``OTHER`` (default).
================== ==================== ===========================================================

A working example would be::

    from django.apps import AppConfig
    from django.utils.translation import ugettext_lazy as _


    class FacebookApp(AppConfig):
        name = "pretalx_facebook"
        verbose_name = _("Facebook")

        class PretalxPluginMeta:
            name = _("Facebook")
            author = _("the pretalx team")
            version = "1.0.0"
            visible = True
            restricted = False
            description = _("This plugin allows you to post talks to facebook.")
            category = "INTEGRATION"


    default_app_config = "pretalx_facebook.FacebookApp"

Plugin registration
-------------------

Somehow, pretalx needs to know that your plugin exists at all. For this purpose, we
make use of the `entry point`_ feature of setuptools. To register a plugin that lives
in a separate python package, your ``pyproject.toml`` should contain something like this::


    [project.entry-points."pretalx.plugin"]
    pretalx_facebook = "pretalx_facebook:PretalxPluginMeta"


This will automatically make pretalx discover this plugin as soon as you have
installed it e.g.  through ``pip``. During development, you can run ``pip
install -e .`` inside your plugin source directory to make it discoverable.

Signals
-------

pretalx defines signals which your plugin can listen for. We will go into the
details of the different signals in the following pages. We suggest that you
put your signal receivers into a ``signals`` submodule of your plugin. You
should extend your ``AppConfig`` (see above) by the following method to make
your receivers available::

    class PaypalApp(AppConfig):

        def ready(self):
            from . import signals  # noqa

You can optionally specify code that you want to execute when the organiser
activates your plugin for an event in the ``installed`` method, and code to
execute upon removal in the ``uninstalled`` method::

    class PaypalApp(AppConfig):

        def installed(self, event):
            pass  # Your code here

        def uninstalled(self, event):
            pass  # Your code here

The ``AppConfig`` class may also implement the method ``is_available(event)``
which checks if a plugin is available for a specific event. If not, it will not
be shown on the plugin list for that event, and cannot be enabled.

Views
-----

Your plugin may define custom views. If you put an ``urls`` submodule into your
plugin module, pretalx will automatically import it and include it into the root
URL configuration with the namespace ``plugins:<label>:``, where ``<label>`` is
your Django application label.

.. note:: We recommend that non-backend-URLs start with a /p/ to avoid collisions
   with event names.

.. WARNING:: If you define custom URLs and views, you are on your own
   with checking that the calling user has logged in, has appropriate permissions,
   and more. We plan on providing native support for this in a later version.

Configuration
-------------

Occasionally, your plugin may need system-level configuration that doesn’t need
its own API. In this case, you can ask users to provide this configuration via
their ``pretalx.cfg`` file. Ask them to put their configuration in a section
with the title ``[plugin:your_plugin_name]``, which pretalx will then provide
in ``settings.PLUGIN_SETTINGS[your_plugin_name]``, like this::

   [plugin:pretalx_soap]
   endpoint=https://example.com
   api_key=123456

Which you can use in your code like this::

   from django.conf import settings
   assert settings.PLUGIN_SETTINGS["pretalx_soap"]["endpoint"] == "https://example.com"

.. versionadded:: 1.1
   The ``PLUGIN_SETTINGS`` configuration was added in pretalx 1.1.

.. _Django application: https://docs.djangoproject.com/en/dev/ref/applications/
.. _signal dispatcher: https://docs.djangoproject.com/en/dev/topics/signals/
.. _namespace packages: http://legacy.python.org/dev/peps/pep-0420/
.. _entry point: https://setuptools.pypa.io/en/latest/pkg_resources.html#locating-plugins
.. _cookiecutter: https://cookiecutter.readthedocs.io/en/latest/
