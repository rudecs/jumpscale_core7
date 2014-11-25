# <License type="Sun Cloud BSD" version="2.2">
#
# Copyright (c) 2005-2009, Sun Microsystems, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or
# without modification, are permitted provided that the following
# conditions are met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#
# 3. Neither the name Sun Microsystems, Inc. nor the names of other
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY SUN MICROSYSTEMS, INC. "AS IS" AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL SUN MICROSYSTEMS, INC. OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY
# OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# </License>

import sys
import os
import functools

try:
    import ujson as json
except:
    import json

from JumpScale import j

from .EasyDialogGeneric import EasyDialogGeneric

def dialogmessage(func):
    @functools.wraps(func)
    def _wrapped(*args, **kwargs):
        value = func(*args, **kwargs)

        if hasattr(j.gui.dialog, 'MessageType'):
            return j.gui.dialog.MessageType(value)
        else:
            return value

    return _wrapped


class EasyDialogWizardServer(EasyDialogGeneric):

    pm_actions = None

    def __init__(self):
        self.pm_actions = WizardActions()

    @dialogmessage
    def message(self,message):
        return self.pm_actions.ShowLabel(message, multiline=True)

    @dialogmessage
    def askFilePath(self,message, startPath):
        #self.pm_actions.ShowLabel(message)
        return self.pm_actions.ShowText("FilePath: ")

    @dialogmessage
    def askDirPath(self,message, startPath):
        self.pm_actions.ShowLabel(message)
        return self.pm_actions.ShowText("FolderPath: ")

    @dialogmessage
    def askString(self,question, defaultValue=None, validator=None):
        return self.pm_actions.ShowText(question, defaultValue=defaultValue, validator=validator)

    @dialogmessage
    def askYesNo(self,question,defaultValue=None):
        values = {True: 'Yes', False: 'No'}
        return self.pm_actions.ShowOptions(question, values, defaultValue)

    @dialogmessage
    def askPassword(self,question, defaultValue=None):
        return self.pm_actions.ShowText(question, defaultValue=defaultValue, password=True)

    @dialogmessage
    def askInteger(self, question,defaultValue=None):
        return self.pm_actions.ShowNumber(question, defaultValue=defaultValue)

    @dialogmessage
    def askIntegers(self, question,defaultValue=None):
        return self.pm_actions.ShowText(question, multiline=False, validator='[0-9,]')

    @dialogmessage
    def askChoice(self, question, choices, defaultValue=None, pageSize = 10, sortChoices=False, sortCallBack=None):
        if not isinstance(choices, dict):
            # choices is not a dict, convert it to a dict
            thechoices = dict.fromkeys(choices)
            for k in list(thechoices.keys()):
                thechoices[k] = k
        else:
            # choices is already a dict, nothing to do
            thechoices = choices

        if len(thechoices) > 4:
            return self.pm_actions.ShowDropDown(question, thechoices, defaultValue)
        else:
            return self.pm_actions.ShowOptions(question, thechoices, defaultValue)

    @dialogmessage
    def askChoiceMultiple(self, question, choices, defaultValue = None, pageSize = 10, sortChoices=False, sortCallBack=None):
        if not isinstance(choices, dict):
            # choices is not a dict, convert it to a dict
            thechoices = dict.fromkeys(choices)
            for k in list(thechoices.keys()):
                thechoices[k] = k
        else:
            # choices is already a dict, nothing to do
            thechoices = choices

        return self.pm_actions.ShowOptionsMultiple(question, thechoices)

    @dialogmessage
    def askMultiline(self, question, defaultValue=None):
        return self.pm_actions.ShowText(question, defaultValue=defaultValue, multiline=True)

    # Specific methods only available in the wizard server
    @dialogmessage
    def askDate(self, question, minValue=None, maxValue=None, selectedValue=None, format='YYYY/MM/DD'):
        return self.pm_actions.ShowDate(question, minValue, maxValue, selectedValue, format)

    @dialogmessage
    def askDateTime(self, question, minValue=None, maxValue=None, selectedValue=None, format='YYYY/MM/DD hh:mm'):
        return self.pm_actions.ShowDateTime(question, minValue, maxValue, selectedValue, format)

    @dialogmessage
    def showProgress(self, minvalue, maxvalue, currentvalue):
        return self.pm_actions.ShowProgress(minvalue, maxvalue, currentvalue)

    @dialogmessage
    def showLogging(self, text):
        return self.pm_actions.ShowLogging(text)

    @dialogmessage
    def navigateTo(self, url):
        return self.pm_actions.NavigateTo(url)
    @dialogmessage
    def askForm(self, form):
        return self.pm_actions.Form(form)
    @dialogmessage
    def clear(self):
        return self.pm_actions.Clear()
    @dialogmessage
    def showMessageBox(self, message, title, msgboxButtons = "OK", msgboxIcon = "Information", defaultButton = "OK"):
        return self.pm_actions.ShowMessageBox(message, title, msgboxButtons, msgboxIcon, defaultButton)

class WizardActions(object):
    """
    Helper class which generates JSON encoded string which represent
    Actions for the Wizard client
    """

    def addParameter(self, params, paramKey, paramValue):
        """
        Adds a parameter to the list of parameters if a value
        is specified.

        @param params:      Dictionary with parameters
        @param paramKey:    Key for the parameter
        @param paramValue:  Value for the parameter

        @return:            Updated dictionary
        """
        if not paramValue in (None, ""):
            params[paramKey] = paramValue
        return params

    def encodeAction(self, action):
        """
        Encodes the wizard action using JSON

        @param action:  Dictionary containing the action for the wizard to execute

        @return:        JSON encoded string of the action
        """
        return json.dumps(action)

    def getClearAction(self):
        """
        Creates a 'clear' action for the wizard which clears all existing
        controls in the wizard.

        @return: A JSON encoded string containing the clear action
        """
        action = {'action': 'clear'}
        return self.encodeAction(action)

    def getDisplayAction(self, params):
        """
        Creates a 'display' action for the wizard which displays a control
        in the wizard.

        @param params:  Dictionary containing the control's parameters

        @return: A JSON encoded string containing the display action
        """
        action = {'action': 'display', 'params': params}
        return self.encodeAction(action)

    def Clear(self):
        """
        Create a clear action.

        @return: A JSON encoded string containing the display action
        """
        return self.getClearAction()

    def ShowLabel(self, text, bold=False, multiline=False):
        """
        Create a display action containing a text label.

        @param text:      Text to display in the label
        @param bold:      Boolean indicating if the text should be displayed in bold
        @param multiline: Boolean indicating if new-lines should be respected

        @return: A JSON encoded string containing the display action
        """
        params = self._showLabel(text, bold, multiline)

        return self.getDisplayAction(params)

    def ShowText(self, text, defaultValue=None, multiline=False, validator=None, password=False):
        """
        Create a display action containing a text input field.

        @param text:          Text to display in the label
        @param defaultValue:  String to pre-populate text field with
        @param multiline:     Boolean indicating if new-lines should be respected
        @param validator:     Regex to which the value should match
        @param password:      Boolean indicating if we have to hide the text

        @return: A JSON encoded string containing the display action
        """
        params = self._showText(text, defaultValue, multiline, validator, password)

        return self.getDisplayAction(params)

    def ShowNumber(self, text, minValue=None, maxValue=None, defaultValue=None):
        """
        Create a display action containing a number input field.

        @param text:          Text to display in the label
        @param minValue:      Minimum value for the number
        @param maxvalue:      Maximum value for the number
        @param defaultValue:  Number to pre-populate number field with

        @return: A JSON encoded string containing the display action
        """
        params = {}

        params = self.addParameter(params, 'control', 'number')
        params = self.addParameter(params, 'text', text)
        params = self.addParameter(params, 'minvalue', minValue)
        params = self.addParameter(params, 'maxvalue', maxValue)
        params = self.addParameter(params, 'defaultvalue', defaultValue)

        return self.getDisplayAction(params)

    def ShowDropDown(self, text, values, selectedValue=None, optional=False):
        """
        Create a display action containing a dropdown box.

        @param text:          Text to display in the label
        @param values:        Dictionary containing key/value pairs to select from
        @param selectedValue: Key of the value which should be selected by default
        @param optional:      Boolean indicating if selection is required

        @return: A JSON encoded string containing the display action
        """
        params = self._showDropDown(text, values, selectedValue, optional)

        return self.getDisplayAction(params)

    def ShowOptions(self, text, values, selectedValue=False, optional=False):
        """
        Create a display action containing a radio buttons.

        @param text:          Text to display in the label
        @param values:        Dictionary containing key/value pairs to select from
        @param selectedValue: Key of the value which should be selected by default
        @param optional:      Boolean indicating if selection is required

        @return: A JSON encoded string containing the display action
        """
        params = {}

        values = [(value, key) for (key, value) in list(values.items())]

        params = self.addParameter(params, 'control', 'option')
        params = self.addParameter(params, 'text', text)
        params = self.addParameter(params, 'values', values)
        params = self.addParameter(params, 'selectedvalue', selectedValue)
        params = self.addParameter(params, 'optional', optional)

        return self.getDisplayAction(params)


    def ShowOptionsMultiple(self, text, values, selectedValue=False, optional=False):
        """
        Create a display action containing checkboxes which enables multi-selects.

        @param text:          Text to display in the label
        @param values:        Dictionary containing key/value pairs to select from
        @param selectedValue: Key of the value which should be selected by default
        @param optional:      Boolean indicating if selection is required

        @return: A JSON encoded string containing the display action
        """
        params = {}

        params = self.addParameter(params, 'control', 'optionmultiple')
        params = self.addParameter(params, 'text', text)
        params = self.addParameter(params, 'values', values)
        params = self.addParameter(params, 'selectedvalue', selectedValue)
        params = self.addParameter(params, 'optional', optional)

        return self.getDisplayAction(params)

    def ShowDateTime(self, text, minValue=None, maxValue=None, selectedValue=None, format='YYYY/MM/DD hh:mm'):
        """
        Create a display action containing a datetime selector.

        @param text:          Text to display in the label
        @param minValue:      Minimum value for the date to select
        @param maxValue:      Maximum value for the date to select
        @param selectedValue: String representation of the date to select by default
        @param format:        String defining format to display date in

        @return: A JSON encoded string containing the display action
        """
        return self.getDisplayAction(self._showDateControl('datetime', text, minValue, maxValue, selectedValue, format))

    def ShowDate(self, text, minValue=None, maxValue=None, selectedValue=None, format='YYYY/MM/DD'):
        """
        Create a display action containing a date selector.

        @param text:          Text to display in the label
        @param minValue:      Minimum value for the date to select
        @param maxValue:      Maximum value for the date to select
        @param selectedValue: String representation of the date to select by default
        @param format:        String defining format to display date in

        @return: A JSON encoded string containing the display action
        """
        return self.getDisplayAction(self._showDateControl('date', text, minValue, maxValue, selectedValue, format))

    def ShowProgress(self, minValue=None, maxValue=None, currentValue=None):
        """
        Create a display action containing a progress bar control with the
        progress of the wizard.

        @param minValue:      Minimum value for the progress bar
        @param maxValue:      Maximum value for the progress bar
        @param currentValue:  Current value for the progress bar

        @return: A JSON encoded string containing the display action
        """
        params = {}

        params = self.addParameter(params, 'control', 'progress')
        params = self.addParameter(params, 'minvalue', minValue)
        params = self.addParameter(params, 'maxvalue', maxValue)
        params = self.addParameter(params, 'value', currentValue)

        return self.getDisplayAction(params)

    def ShowLogging(self, text=None):
        """
        Create a display action containing intermediate information for the
        end user displayed in a logging control.

        @param text: String to add to the log

        @return: A JSON encoded string containing the display action
        """
        params = {}

        params = self.addParameter(params, 'control', 'logging')
        params = self.addParameter(params, 'text', text)

        return self.getDisplayAction(params)

    def ShowMessageBox(self, message, title, msgboxButtons = "OK", msgboxIcon = "Information", defaultButton = "OK"):
        """
        Create a display action containing intermediate information for the
        end user as a message box.

        @param message: message for the messagebox
        @param title: title of the messagebox
        @param msgboxButtons: buttons to show in the messagebox. Possible values are 'OKCancel', 'YesNo', 'YesNoCancel', 'OK'
        @param msgboxIcon: icon to show in the messagebox. Possible values are 'None', 'Error', 'Warning', 'Information', 'Question'
        @param defaultButton: default button for the messagebox. Possible values are 'OK', 'Cancel', 'Yes', 'No'

        @return: A JSON encoded string containing the selected button clicked
        """
        params = {}

        params = self.addParameter(params, 'control', 'messagebox')
        params = self.addParameter(params, 'message', message)
        params = self.addParameter(params, 'title', title)
        params = self.addParameter(params, 'msgboxButtons', msgboxButtons)
        params = self.addParameter(params, 'msgboxIcon', msgboxIcon)
        params = self.addParameter(params, 'defaultButton', defaultButton)

        return self.getDisplayAction(params)

    def NavigateTo(self, url):
        """
        Create a display action with instructions to naviagate to another site/page...

        @param url: Url address to navigate to

        @return: A JSON encoded string containing the display action
        """
        params = {}

        params = self.addParameter(params, 'control', 'navigate')
        params = self.addParameter(params, 'url', url)

        return self.getDisplayAction(params)

    def Form(self, form):
        """
        Create a display action containing a form object

        @param form: WizardForm object

        @return: A JSON encoded string containing the display action
        """
        params = {}
        tabs = [self._showTab(tab.name,tab.text,tab.elements) for tab in form.tabs]

        params = self.addParameter(params, 'control', 'form')
        params = self.addParameter(params, 'activeTab', form.activeTab)
        params = self.addParameter(params, 'tabs', tabs)

        return self.getDisplayAction(params)

    def _showLabel(self, text, bold=False, multiline=False, name=''):
        """
        Create a display action containing a text label.

        @param text:      Text to display in the label
        @param bold:      Boolean indicating if the text should be displayed in bold
        @param multiline: Boolean indicating if new-lines should be respected

        @return: dict
        """
        params = {}
        params = self.addParameter(params, 'name', name or 'label')
        params = self.addParameter(params, 'control', 'label')
        params = self.addParameter(params, 'text', text)
        params = self.addParameter(params, 'bold', bold)
        params = self.addParameter(params, 'multiline', multiline)
        return params

    def _showDropDown(self, text, values, selectedValue=None, name='', message='', status='undefined', trigger=None, callback=None, helpText='', optional=True):
        """
        Create a display action containing a dropdown box.

        @param text:          Text to display in the label
        @param values:        Dictionary containing key/value pairs to select from
        @param value:         Key of the value which should be selected by default
        @param name:          Unique name for the control
        @param message:       Message to use for the tooltip or error message (depending on status)
        @param status:        Current status of this control
        @param trigger:       Event where the control should trigger on
        @param callback:      Method that will be called, if event has been triggerd
        @param helpText:      Information about the usage/functionality of the control
        @param optional:      Boolean indicating if selection is required
        @return: dict
        """
        params = {}
        params = self.addParameter(params, 'control', 'dropdown')
        params = self.addParameter(params, 'text', text)
        params = self.addParameter(params, 'values', values)
        params = self.addParameter(params, 'value', selectedValue)
        params = self.addParameter(params, 'optional', optional)
        params = self.addParameter(params, 'status', status)
        params = self.addParameter(params, 'message', message)
        params = self.addParameter(params, 'name', name or text)
        params = self.addParameter(params, 'callback', callback)
        params = self.addParameter(params, 'trigger', trigger)
        params = self.addParameter(params, 'helpText', helpText)
        return params

    def _showText(self, text, value=None, multiline=False, validator=None, password=False, name='', message='', status='undefined', trigger=None, callback=None, helpText='', optional=True, confirm=False):
        """
        Create a display action containing a text input field.

        @param text:          Text to display in the label
        @param value:         String to pre-populate text field with
        @param multiline:     Boolean indicating if new-lines should be respected
        @param validator:     Regex to which the value should match
        @param password:      Boolean indicating if we have to hide the text
        @param name:          Unique name for the control
        @param message:       Message to use for the tooltip or error message (depending on status)
        @param status:        Current status of this control
        @param trigger:       Event where the control should trigger on
        @param callback:      Method that will be called, if event has been triggerd
        @param helpText:      Information about the usage/functionality of the control
        @param optional:      Define the text field as optional parameter (boolean)
        @return: dict
        """
        params = {}
        params = self.addParameter(params, 'control', 'text')
        params = self.addParameter(params, 'text', text)
        params = self.addParameter(params, 'value', value)
        params = self.addParameter(params, 'multiline', multiline)
        params = self.addParameter(params, 'validator', validator)
        params = self.addParameter(params, 'password', password)
        params = self.addParameter(params, 'status', status)
        params = self.addParameter(params, 'message', message)
        params = self.addParameter(params, 'name', name or text)
        params = self.addParameter(params, 'callback', callback)
        params = self.addParameter(params, 'trigger', trigger)
        params = self.addParameter(params, 'helpText', helpText)
        params = self.addParameter(params, 'optional', optional)
        params = self.addParameter(params, 'confirm', confirm)
        return params

    def _showNumber(self, text, minValue=None, maxValue=None, value=None, name='', message='', status='undefined', trigger=None, callback=None, helpText='', optional=True, stepSize=1):
        """
        Create a display action containing a number input field.

        @param text:          Text to display in the label
        @param minValue:      Minimum value for the number
        @param maxvalue:      Maximum value for the number
        @param value:         Number to pre-populate number field with
        @param name:          Unique name for the control
        @param message:       Message to use for the tooltip or error message (depending on status)
        @param status:        Current status of this control
        @param trigger:       Event where the control should trigger on
        @param callback:      Method that will be called, if event has been triggerd
        @param helpText:      Information about the usage/functionality of the control
        @param optional:      Define the text field as optional parameter (boolean)
        @param stepSize:      Number to increase the steps
        @return: dict
        """
        params = {}

        params = self.addParameter(params, 'control', 'number')
        params = self.addParameter(params, 'text', text)
        params = self.addParameter(params, 'minvalue', minValue)
        params = self.addParameter(params, 'maxvalue', maxValue)
        params = self.addParameter(params, 'value', value)
        params = self.addParameter(params, 'status', status)
        params = self.addParameter(params, 'message', message)
        params = self.addParameter(params, 'name', name or text)
        params = self.addParameter(params, 'callback', callback)
        params = self.addParameter(params, 'trigger', trigger)
        params = self.addParameter(params, 'helpText', helpText)
        params = self.addParameter(params, 'optional', optional)
        params = self.addParameter(params, 'stepsize', stepSize)
        return params

    def _showOptionsMultiple(self, text, values, value=False, name='', message='', status='undefined', trigger=None, callback=None, helpText='', optional=True):
        """
        Create a display action containing checkboxes which enables multi-selects.

        @param text:          Text to display in the label
        @param values:        Dictionary containing key/value pairs to select from
        @param value:         Key of the value which should be selected by default
        @param name:          Unique name for the control
        @param message:       Message to use for the tooltip or error message (depending on status)
        @param status:        Current status of this control
        @param trigger:       Event where the control should trigger on
        @param callback:      Method that will be called, if event has been triggerd
        @param helpText:      Information about the usage/functionality of the control
        @param optional:      Boolean indicating if selection is required
        @return: A JSON encoded string containing the display action
        """
        params = {}

        params = self.addParameter(params, 'control', 'optionmultiple')
        params = self.addParameter(params, 'text', text)
        params = self.addParameter(params, 'values', values)
        params = self.addParameter(params, 'value', value)
        params = self.addParameter(params, 'optional', optional)
        params = self.addParameter(params, 'status', status)
        params = self.addParameter(params, 'message', message)
        params = self.addParameter(params, 'name', name or text)
        params = self.addParameter(params, 'callback', callback)
        params = self.addParameter(params, 'trigger', trigger)
        params = self.addParameter(params, 'helpText', helpText)
        return params

    def _showOptions(self, text, values, selectedValue=0, name='', message='', status='undefined', trigger=None, callback=None, helpText='', optional=True):
        """
        Create a display action containing a radio buttons.

        @param text:          Text to display in the label
        @param values:        Dictionary containing key/value pairs to select from
        @param value:         Key of the value which should be selected by default
        @param name:          Unique name for the control
        @param message:       Message to use for the tooltip or error message (depending on status)
        @param status:        Current status of this control
        @param trigger:       Event where the control should trigger on
        @param callback:      Method that will be called, if event has been triggerd
        @param helpText:      Information about the usage/functionality of the control
        @param optional:      Boolean indicating if selection is required
        @return: dict
        """
        params = {}

        params = self.addParameter(params, 'control', 'option')
        params = self.addParameter(params, 'text', text)
        params = self.addParameter(params, 'values', values)
        params = self.addParameter(params, 'value', selectedValue)
        params = self.addParameter(params, 'optional', optional)
        params = self.addParameter(params, 'status', status)
        params = self.addParameter(params, 'message', message)
        params = self.addParameter(params, 'name', name or text)
        params = self.addParameter(params, 'callback', callback)
        params = self.addParameter(params, 'trigger', trigger)
        params = self.addParameter(params, 'helpText', helpText)
        return params

    def _showDateControl(self, control, text, minValue, maxValue, value, format, name='', message='', status='undefined', trigger=None, callback=None,  helpText='', optional=True):
        """
        Create a display action containing date control.

        @param control:       Date control (date, datetime)
        @param text:          Text to display in the label
        @param minValue:      Minimum value for the number
        @param maxvalue:      Maximum value for the number
        @param value:         Number to pre-populate number field with
        @param format:        Format to display date/datetime
        @param name:          Unique name for the control
        @param message:       Message to use for the tooltip or error message (depending on status)
        @param status:        Current status of this control
        @param trigger:       Event where the control should trigger on
        @param callback:      Method that will be called, if event has been triggerd
        @param helpText:      Information about the usage/functionality of the control
        @param optional:      Boolean indicating if selection is required
        @return: dict
        """
        params = {}

        params = self.addParameter(params, 'control', control)
        params = self.addParameter(params, 'text', text)
        params = self.addParameter(params, 'minvalue', minValue)
        params = self.addParameter(params, 'maxvalue', maxValue)
        params = self.addParameter(params, 'value', value)
        params = self.addParameter(params, 'format', format)
        params = self.addParameter(params, 'status', status)
        params = self.addParameter(params, 'message', message)
        params = self.addParameter(params, 'name', name or text)
        params = self.addParameter(params, 'callback', callback)
        params = self.addParameter(params, 'trigger', trigger)
        params = self.addParameter(params, 'helpText', helpText)
        params = self.addParameter(params, 'optional', optional)
        return params

    def _showTab(self, name, text, elements):
        """
        Create a display action containing a text label.

        @param text:      Text to display in the label
        @param elements:  Elemnts to be displayed on the tab

        @return: dict
        """
        elements = [element.__dict__ for element in elements]

        params = {}
        params = self.addParameter(params, 'control', 'tab')
        params = self.addParameter(params, 'name', name)
        params = self.addParameter(params, 'text', text)
        params = self.addParameter(params, 'elements', elements)
        return params

    def _showButtonControl(self, control, name, label, trigger=None, callback=None, helpText=''):
        """
        Create a display action containing date control.

        @param control:       Date control (date, datetime)
        @param name:          Unique name for the control
        @param label:         Caption displayed in the button
        @param trigger:       Event where the control should trigger on. 'click'
        @param callback:      Method that will be called, if event has been triggered
        @param helpText:      Information about the usage/functionality of the control
        @return: dict
        """
        params = {}

        params = self.addParameter(params, 'control', control)
        params = self.addParameter(params, 'name', name)
        params = self.addParameter(params, 'label', label)
        params = self.addParameter(params, 'callback', callback)
        params = self.addParameter(params, 'trigger', trigger)
        params = self.addParameter(params, 'helpText', helpText)
        return params
