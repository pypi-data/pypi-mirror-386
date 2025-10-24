# Copyright (c) 2007-2008 gocept gmbh & co. kg
# See also LICENSE.txt

"""Pagelet support for z3c.form forms."""

import z3c.form.form
import z3c.pagelet.browser
import z3c.pagelet.interfaces
import zope.interface
import z3c.template.interfaces
import zope.component


@zope.interface.implementer(z3c.pagelet.interfaces.IPageletForm)
class Form(z3c.pagelet.browser.BrowserPagelet, z3c.form.form.Form):
    """Pagelet support for z3c.form.form.Form"""

    update = z3c.form.form.Form.update


@zope.interface.implementer(z3c.pagelet.interfaces.IPageletAddForm)
class AddForm(z3c.pagelet.browser.BrowserPagelet, z3c.form.form.AddForm):
    """Pagelet support for z3c.form.form.AddForm"""

    update = z3c.form.form.AddForm.update


@zope.interface.implementer(z3c.pagelet.interfaces.IPageletEditForm)
class EditForm(z3c.pagelet.browser.BrowserPagelet, z3c.form.form.EditForm):
    """Pagelet support for z3c.form.form.EditForm"""

    update = z3c.form.form.EditForm.update
