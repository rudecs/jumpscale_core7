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

from JumpScale import j
from .EasyDialogWizardServer import WizardActions
from .EasyDialogWizardServer import EasyDialogWizardServer

try:
    import ujson as json
except:
    import json

class EasyDialogWizardForm(object):

    def createForm(self):
        """
        Create new wizard form object

        @return: WizardForm object
        """
        return WizardForm()

class WizardElementBase(object):
    """
    Base class for element objects
    """
    def __init__(self, properties):
        self.__dict__ = properties

class WizardForm(object):
    """
    Helper class which generate form
    """
    def __init__(self):
        self.tabs = WizardList()
        self.activeTab = ''

    def addTab(self, name, text):
        """
        Add new tab to form

        @param name: Unique name for this control
        @param text: Text to be displayed in tab label
        @return: WizardTab object
        """
        wizardtab = WizardTab(name, text)
        self.tabs._addItem(wizardtab)
        return wizardtab

    def removeTab(self, name):
        """
        Remove existing tab from form

        @param name: Unique name for this control
        """
        self.tabs._removeItem(name)

    def loadForm(self, data):
        self.tabs = WizardList()

        if not isinstance(data, dict):
            if isinstance(data, str):
                data = json.loads(data)
            else:
                raise RuntimeError('Unknown data format. Data type: %s, Data: %s' % (type(data), data))

        self.activeTab = data['activeTab']
        for tabData in data['tabs']:
            tab = WizardTab(tabData['name'], tabData['text'])
            self.tabs._addItem(tab)
            for elementData in tabData['elements']:
                element = WizardElementBase(elementData)
                tab.elements._addItem(element)

    def convertToWizardAction(self):
        tabpages = []
        for tab in self.tabs:
            tabDict = {}
            tabDict['control'] = 'tab'
            tabDict['name'] = tab.name
            tabDict['text'] = tab.text
            elements = [element.__dict__ for element in tab.elements]
            tabDict['elements'] = elements
            tabpages.append(tabDict)

        params = {}
        params['control'] = 'form'
        params['tabs'] = tabpages
        params['activeTab'] = self.activeTab
        action = {'action': 'display', 'params': params}
        return action

class WizardList(list):
    """
    Generic Wizard List with name indexer
    """
    def __init__(self):
        self._items = []

    def _addItem(self, item):
        if item.name in self:
            raise KeyError("Item with name '%s' already exists"%item.name)

        self._items.append(item)

    def _getItem(self, key):
        for item in self._items:
            if item.name.lower() == key.lower():
                return item
        raise KeyError("No item defined with name '%s'"%key)

    def _removeItem(self, key):
        for item in self._items:
            if item.name.lower() == key.lower():
                self._items.remove(item)
                return

    def __contains__(self, key):
        for item in self._items:
            if item.name.lower() == key.lower():
                return True
        return False

    def __delitem__(self, key):
        self._removeItem(key)

    def __getitem__(self, key):
        return self._getItem(key)

    def __iter__(self):
        for item in self._items:
            yield item

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return '[%s]'%','.join([item.name for item in self._items])

class WizardTab(object):
    """
    Helper class which generate tab structure
    """
    def __init__(self, name, text):
        self.pm_actions = WizardActions()
        self.elements = WizardList()
        self.name = name
        self.text = text

    def message(self, name, text, bold=False, multiline=False):
        """
        Create a display action containing label.

        @param name:          Unique name for the control
        @param text:          Text to display in the label
        @param bold:          Define if the font should be bold
        @param multiline:     Use multiline label
        """
        label = WizardElementBase(self.pm_actions._showLabel(text, bold, multiline, name=name))
        self.elements._addItem(label)

    def addText(self, name, text, value=None, multiline=False, validator=None, message='', status='', trigger=None, callback=None, helpText='', optional=True):
        """
        Create a display action containing textbox control.

        @param name:          Unique name for the control
        @param text:          Text to display in the label
        @param value:         Text to pre-populate textbox field with
        @param multiline:     Use multiline label
        @param validator:     Define validator to restrict text input
        @param message:       Message to use for the tooltip or error message (depending on status)
        @param status:        Current status of this control
        @param trigger:       Event where the control should trigger on
        @param callback:      Method that will be called, if event has been triggered
        @param helpText:      Information about the usage/functionality of the control
        @param optional:      Define the text field as optional parameter (boolean)
        """
        text = WizardElementBase(self.pm_actions._showText(text, value, multiline, validator, False, name, message, status, trigger, callback, helpText, optional))
        self.elements._addItem(text)

    def addMultiline(self, name, text, value=None, validator=None, message='', status='', trigger=None, callback=None, helpText='', optional=True):
        """
        Create a display action containing multiline textbox control.

        @param name:          Unique name for the control
        @param text:          Text to display in the label
        @param value:         Text to pre-populate textbox field with
        @param validator:     Define validator to restrict text input
        @param message:       Message to use for the tooltip or error message (depending on status)
        @param status:        Current status of this control
        @param trigger:       Event where the control should trigger on
        @param callback:      Method that will be called, if event has been triggered
        @param helpText:      Information about the usage/functionality of the control
        @param optional:      Define the text field as optional parameter (boolean)
        """
        text = WizardElementBase(self.pm_actions._showText(text, value, True, validator, False, name, message, status, trigger, callback, helpText, optional))
        self.elements._addItem(text)

    def addPassword(self, name, text, value=None, message='', status='', trigger=None, callback=None, helpText='', optional=True, confirm=False):
        """
        Create a display action containing password textbox control.

        @param name:          Unique name for the control
        @param text:          Text to display in the label
        @param value:         Number to pre-populate textbox field with
        @param message:       Message to use for the tooltip or error message (depending on status)
        @param status:        Current status of this control
        @param trigger:       Event where the control should trigger on
        @param callback:      Method that will be called, if event has been triggered
        @param helpText:      Information about the usage/functionality of the control
        @param optional:      Define the password field as optional parameter (boolean)
        """
        password = WizardElementBase(self.pm_actions._showText(text, value, name=name, password=True, message=message, status=status, trigger=trigger, callback=callback, helpText=helpText, optional=optional, confirm=confirm))
        self.elements._addItem(password)

    def addFilepath(self, name, value=None, validator=None, message='', status='', trigger=None, callback=None, helpText='', optional=True):
        """
        Create a display action containing filepath control.

        @param name:          Unique name for the control
        @param value:         Number to pre-populate textbox field with
        @param validator:     Define validator to restrict text input
        @param message:       Message to use for the tooltip or error message (depending on status)
        @param status:        Current status of this control
        @param trigger:       Event where the control should trigger on
        @param callback:      Method that will be called, if event has been triggered
        @param helpText:      Information about the usage/functionality of the control
        @param optional:      Define the filepath field as optional parameter (boolean)
        """
        filepath = WizardElementBase(self.pm_actions._showText('Filepath: ', value, False, validator, False, name, message, status, trigger, callback, helpText, optional))
        self.elements._addItem(filepath)

    def addDirPath(self, name, value=None, validator=None, message='', status='', trigger=None, callback=None, helpText='', optional=True):
        """
        Create a display action containing filedir control.

        @param name:          Unique name for the control
        @param value:         Number to pre-populate textbox field with
        @param validator:     Define validator to restrict text input
        @param message:       Message to use for the tooltip or error message (depending on status)
        @param status:        Current status of this control
        @param trigger:       Event where the control should trigger on
        @param callback:      Method that will be called, if event has been triggered
        @param helpText:      Information about the usage/functionality of the control
        @param optional:      Define the dirpath field as optional parameter (boolean)
        """
        dirpath = WizardElementBase(self.pm_actions._showText('Folderpath: ', value, False, validator, False, name, message, status, trigger, callback, helpText, optional))
        self.elements._addItem(dirpath)

    def addInteger(self, name, text, minValue=None, maxValue=None, value=None, message='', status='', trigger=None, callback=None, helpText='', optional=True, stepSize=1):
        """
        Create a display action containing integer selector control.

        @param name:          Unique name for the control
        @param text:          Text to display in the label
        @param minValue:      Minimum value for the number
        @param maxvalue:      Maximum value for the number
        @param value:         Number to pre-populate textbox field with
        @param message:       Message to use for the tooltip or error message (depending on status)
        @param status:        Current status of this control
        @param trigger:       Event where the control should trigger on
        @param callback:      Method that will be called, if event has been triggered
        @param helpText:      Information about the usage/functionality of the control
        @param optional:      Define the integer field as optional parameter (boolean)
        @param stepSize:      Number to increase the steps
        """
        number = WizardElementBase(self.pm_actions._showNumber(text, str(minValue) if minValue != None else minValue, maxValue, value, name, message, status, trigger, callback, helpText, optional, stepSize))
        self.elements._addItem(number)

    def addIntegers(self, name, question, value=None, message='', status='', trigger=None, callback=None, helpText='', optional=True):
        """
        Create a display action containing integers selector control.

        @param name:          Unique name for the control
        @param question:      Question to display in the label
        @param value:         Numbers to pre-populate textbox field with
        @param message:       Message to use for the tooltip or error message (depending on status)
        @param status:        Current status of this control
        @param trigger:       Event where the control should trigger on
        @param callback:      Method that will be called, if event has been triggered
        @param helpText:      Information about the usage/functionality of the control
        @param optional:      Define the integers field as optional parameter (boolean)
        """
        integers = WizardElementBase(self.pm_actions._showText(question, value, name=name, message=message, status=status, validator='[0-9,]', trigger=trigger, callback=callback, helpText=helpText, optional=optional))
        self.elements._addItem(integers)

    def addChoice(self, name, text, values, selectedValue=0, message='', status='', trigger=None, callback=None, helpText='', optional=True):
        """
        Create a display action containing item selector control.

        @param name:          Unique name for the control
        @param text:          Text to display in the label
        @param values:        Items to select out (dictionary)
        @param selectedValue: Index of the item to select
        @param message:       Message to use for the tooltip or error message (depending on status)
        @param status:        Current status of this control
        @param trigger:       Event where the control should trigger on
        @param callback:      Method that will be called, if event has been triggered
        @param helpText:      Information about the usage/functionality of the control
        @param optional:      Define the choice field as optional parameter (boolean)
        """

        if len(values) > 4:
            options = WizardElementBase(self.pm_actions._showDropDown(text, values, selectedValue, name, message, status, trigger, callback, helpText, optional))
        else:
            options = WizardElementBase(self.pm_actions._showOptions(text, values, selectedValue, name, message, status, trigger, callback, helpText, optional))
        self.elements._addItem(options)

    def addChoiceMultiple(self, name, text, values, selectedValue=0, message='', status='', trigger=None, callback=None, helpText='', optional=True):
        """
        Create a display action containing multi items selector control.

        @param name:          Unique name for the control
        @param text:          Text to display in the label
        @param values:        Items to select out (dictionary)
        @param selectedValue: Index of the item to select
        @param message:       Message to use for the tooltip or error message (depending on status)
        @param status:        Current status of this control\
        @param trigger:       Event where the control should trigger on
        @param callback:      Method that will be called, if event has been triggered
        @param helpText:      Information about the usage/functionality of the control
        @param optional:      Boolean indicating if selection is required
        """

        options = WizardElementBase(self.pm_actions._showOptionsMultiple(text, values, selectedValue, name, message, status, trigger, callback, helpText, optional))

        self.elements._addItem(options)

    def addDropDown(self, name, text, values, selectedValue=0, message='', status='', trigger=None, callback=None, helpText='', optional=True):
        """
        Create a display action containing multi items dropdown control.

        @param name:          Unique name for the control
        @param text:          Text to display in the label
        @param values:        Items to select out (dictionary)
        @param selectedValue: Index of the item to select
        @param message:       Message to use for the tooltip or error message (depending on status)
        @param status:        Current status of this control\
        @param trigger:       Event where the control should trigger on
        @param callback:      Method that will be called, if event has been triggered
        @param helpText:      Information about the usage/functionality of the control

        """

        options = WizardElementBase(self.pm_actions._showDropDown(text, values, selectedValue, name, message, status, trigger, callback, helpText, optional))
        self.elements._addItem(options)

    def addYesNo(self, name, question, selectedValue=None, message='', status='', trigger=None, callback=None, helpText='', optional=True):
        """
        Create a display action containing yes/no control.

        @param name:          Unique name for the control
        @param question:      Question to display in the label
        @param selectedValue: Index of the item to select
        @param message:       Message to use for the tooltip or error message (depending on status)
        @param status:        Current status of this control
        @param trigger:       Event where the control should trigger on
        @param callback:      Method that will be called, if event has been triggered
        @param helpText:      Information about the usage/functionality of the control
        @param optional:      Boolean indicating if selection is required
        """
        values = {True: 'Yes', False: 'No'}
        options = WizardElementBase(self.pm_actions._showOptions(question, values, selectedValue, name=name, message=message, status=status, trigger=trigger, callback=callback, helpText=helpText, optional=optional))
        self.elements._addItem(options)

    def addDate(self, name, question, minValue=None, maxValue=None, selectedValue=None, format='YYYY/MM/DD', message='', status='', trigger=None, callback=None, helpText='', optional=True):
        """
        Create a display action containing date control.

        @param name:          Unique name for the control
        @param question:      Question to display in the label
        @param minValue:      Minimum value for the date
        @param maxvalue:      Maximum value for the date
        @param selectedValue: Default date
        @param format:        Format to display date
        @param message:       Message to use for the tooltip or error message (depending on status)
        @param status:        Current status of this control
        @param trigger:       Event where the control should trigger on
        @param callback:      Method that will be called, if event has been triggered
        @param helpText:      Information about the usage/functionality of the control
        @param optional:      Boolean indicating if selection is required
        """
        date = WizardElementBase(self.pm_actions._showDateControl('date', question, minValue, maxValue, selectedValue, format, name, message, status, trigger, callback, helpText, optional))
        self.elements._addItem(date)

    def addDateTime(self, name, question, minValue=None, maxValue=None, selectedValue=None, format='YYYY/MM/DD hh:mm', message='', status='', trigger=None, callback=None, helpText='', optional=True):
        """
        Create a display action containing datetime control.

        @param name:          Unique name for the control
        @param question:      Question to display in the label
        @param minValue:      Minimum value for the date
        @param maxvalue:      Maximum value for the date
        @param selectedValue: Default datetime
        @param format:        Format to display datetime
        @param message:       Message to use for the tooltip or error message (depending on status)
        @param status:        Current status of this control
        @param trigger:       Event where the control should trigger on
        @param callback:      Method that will be called, if event has been triggered
        @param helpText:      Information about the usage/functionality of the control
        @param optional:      Boolean indicating if selection is required
        """
        datetime = WizardElementBase(self.pm_actions._showDateControl('datetime', question, minValue, maxValue, selectedValue, format, name, message, status, trigger, callback, helpText, optional))
        self.elements._addItem(datetime)

    def addButton(self, name, label, trigger=None, callback=None, helpText=''):
        """
        Create a display action containing button control.

        @param name:          Unique name for the control
        @param label:         Caption displayed in the button
        @param trigger:       Event where the control should trigger on. 'click'
        @param callback:      Method that will be called, if event has been triggered
        @param helpText:      Information about the usage/functionality of the control
        """
        button = WizardElementBase(self.pm_actions._showButtonControl('button', name, label, trigger, callback, helpText))
        self.elements._addItem(button)

    def removeElement(self, name):
        """
        Remove existing tab from form

        @param name: Unique name for this control
        """
        self.elements._removeItem(name)
