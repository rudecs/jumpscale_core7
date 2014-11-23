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

import sys, os
from datetime import date
#if "--noxp" in sys.argv:
#    import win32gui
#else:
#    import winxpgui as win32gui
#import win32api
#import win32con, winerror
#import struct, array
#import commctrl
#import Queue

from JumpScale import j
from JumpScale.core.Shell import *
#import win32gui
#from win32com.shell import shell, shellcon
import EasyDialogs
from .EasyDialogGeneric import EasyDialogGeneric
from .EasyDialogConsole import EasyDialogConsole

class EasyDialogWin32(EasyDialogGeneric):

    def askFilePath(self,message, startPath):
        filepath=EasyDialogs.AskFileForOpen(message=message)
        return filepath

    def askDirPath(self,message, startPath):
        filepath=EasyDialogs.AskFolder(message=message)
        return filepath

    def askString(self,question, defaultValue=None, validator=None):
        message = '%s%s'%(question, ('[%s]'%defaultValue) if defaultValue else '')
        result = EasyDialogs.AskString(message)
        import re
        if validator:
            if re.match(result, validator):
                if not result and defaultValue:
                    result = defaultValue
        return result

    def askYesNo(self,question, defaultValue = None):
        """
        Default value is not working in the current implementation
        """
        return True if EasyDialogs.AskYesNoCancel(question) > 0 else False

    def askPassword(self,question, defaultValue=None):
        return EasyDialogs.AskPassword(question)

    def message(self,message):
        return EasyDialogs.Message(message)


    def askInteger(self, question, defaultValue = None):
        """
        Asks user the supplied question and prompt for an answer, if none given the default value is used, the response and the default value must be valid integer

        @param question: question to be displayed
        @param defaultValue: if the user did not provide a response this value is used as an answer
        @return: response integer or the default value
        """

        result = self.askString(question, defaultValue)
        if result.isdigit():
            return int(result)
        raise ValueError("Invalid integer value")


    def askChoice(self, question, choices, defaultValue = None, sortChoices=False, sortCallBack=None):
        """
        Ask the user the supplied question and list the choices to choose from, if no response given the default value is used

        @param question: question to be display to the user
        @param choices: list of choices for the user to choose from
        @param defaultValue: the value that will be used if no response given
        @param sortChoices: if True, choices will be sorted before showing them to the user
        @param sortCallBack: A callback function to handle the sorting of the choices (will only be used if sortChoices is set to True)

        @return:  selected choice
        """
        defaultValues = list()

        if defaultValue:
            defaultValues = [value.strip() for value in defaultValue.split(',')]
            #we choose tolerant approach by just filtering out the invalid defaultValues entries, without raising an error
            defaultValues = [value for value in defaultValues if value in choices]

        messageWihDefault = '%s%s'%(question, ('[%s]'%defaultValue) if defaultValue else '')
        message = "%(question)s\n\nMake a selection please: %(choices)s"
        index = 0
        formmattedChoices = ''

        if sortChoices:
            if not sortCallBack:
                choices.sort()
            else:
                sortCallBack(choices)

        for section in choices:
            index += 1
            formmattedChoices = "%s\n   %s: %s" % (formmattedChoices, index, section)
        message = message%{'question':messageWihDefault, 'choices': formmattedChoices}
        result = EasyDialogs.AskString(message)
        if result:
            selections = self._checkSelection(result, choices, False)
            result = choices[selections[0] - 1]
        else:
            if not defaultValues:
                raise ValueError("No/Invalid default value provided, please try again and select Nr")
            result = defaultValues

        return result



    def askChoiceMultiple(self, question, choices, defaultValue = None, sortChoices=False, sortCallBack=None):
        """
        Ask the user the supplied question and list the choices to choose from, if no response given the default value[s] is used

        @param question: question to be display to the user
        @param choices: list of choices for the user to choose from
        @param defaultValue: default value assumed if no user response is given, default value can be a single value or a comma separated list of values
        @param pageSize: max number of choices that can be prompted to the user in a single screen
        @param sortChoices: if True, choices will be sorted before showing them to the user
        @param sortCallBack: A callback function to handle the sorting of the choices (will only be used if sortChoices is set to True)

        @return:  selected choice[s] or default value[s]
        """

        defaultValues = list()

        if defaultValue:
            defaultValues = [value.strip() for value in defaultValue.split(',')]
            #we choose tolerant approach by just filtering out the invalid defaultValues entries, without raising an error
            defaultValues = [value for value in defaultValues if value in choices]

        messageWihDefault = '%s%s'%(question, ('[%s]'%defaultValue) if defaultValue else '')
        message = "%(question)s\n\nMake a selection please: %(choices)s"
        index = 0
        formmattedChoices = ''

        if sortChoices:
            if not sortCallBack:
                choices.sort()
            else:
                sortCallBack(choices)

        for section in choices:
            index += 1
            formmattedChoices = "%s\n   %s: %s" % (formmattedChoices, index, section)
        message = message%{'question':messageWihDefault, 'choices': formmattedChoices}
        result = EasyDialogs.AskString(message)
        if result:
            selections = self._checkSelection(result, choices, True)
            result = [choices[i - 1] for i in selections]
        else:
            if not defaultValues:
                raise ValueError("No/Invalid default value provided, please try again and select Nr")
            result = defaultValues

        return result


    def askDate(self, question, minValue = None, maxValue = None, selectedValue = None, format='%Y/%m/%d'):
        """
        Asks user a question that its answer is a date between minValue and maxValue

        Note: this note my seem out of place, but is is important to note that currently in the EasyDialogConsole implementation only dates with format YYYY/MM/DD are supported

        @param question: question that will be prompted to the user
        @param minValue: optional value for the lower boundary date
        @param maxValue: optional value for the upper boundary date
        @param selectedValue:
        @param  format: the format of the input date
        """
        format = '%Y/%m/%d'
        message  = "Enter a date with format YYYY/MM/DD, where year can be 09 or 2009, day is 2 or 02:"
        result = self.askString(question, selectedValue)
        #@todo validate date is in correct format
        if not result:
            selectedDate = ''
        else:
            yearPrefix = "20"
            if minValue:
                minValueDate = minValue.split('/')
                if len(minValueDate[0]) == 2:
                    minValueDate[0] = "%s%s"%(yearPrefix, minValueDate[0])
                minValue = date(int(minValueDate[0]),int(minValueDate[1]), int(minValueDate[2]))
            if maxValue:
                maxValueDate = maxValue.split('/')
                if len(maxValueDate[0]) == 2:
                    maxValueDate[0] = "%s%s"%(yearPrefix, maxValueDate[0])
                maxValue = date(int(maxValueDate[0]),int(maxValueDate[1]), int(maxValueDate[2]))

            dateValues = result.split('/')
            if len(dateValues[0]) == 2:
                dateValues[0] = "%s%s"%(yearPrefix, dateValues[0])
            selectedDate =  date(int(dateValues[0]),int(dateValues[1]), int(dateValues[2]))

            if minValue and self._compareDates(minValue, selectedDate) > 0:
                raise AttributeError("Provided date [%s] must be greater than min date [%s]"%(selectedDate, minValue))
            if maxValue and self._compareDates(selectedDate, maxValue) > 0 :
                raise AttributeError("Provided date [%s] must be less than max date [%s]"%(selectedDate, maxValue))
        return selectedDate.strftime(format) if selectedDate else selectedDate


    def showProgress(self, minvalue, maxvalue, currentvalue):
        """
        Shows a progress bar according to the given values

        @param minvalue: minVlue of scale
        @param maxvalue: maxvlaue of scale
        @param currentvalue: the current value to show the progress
        """
        bar = EasyDialogs.ProgressBar(maxvalue)
        for i in range(currentvalue):
            bar.inc()
        del bar



    def askIntegers(self, question):
        """
        Asks user the supplied question and prompt for an answer

        @param question: question to be prompted
        @return: response integer
        """

        raise NotImplementedError("Not Supported operation")


    def askMultiline(self, question):
        """
        Asks the user the supplied question, where the answer could be multi-lines

        @param question: the question to be displayed
        """
        raise NotImplementedError("Not Supported operation")


    def showLogging(self, text):
        """
        Shows logging message
        """
        raise NotImplementedError("Not Supported operation")

    def navigateTo(self, url):
        raise NotImplementedError("Not Supported operation")


    def chooseDialogType(self,type):
        """
        supported types today: console,win32,wizardserver
        @param type DialogType enumerator
        """
        raise NotImplementedError("Not Supported operation")


    def _checkSelection(self, selection, choices, multiSelection):
        """
        checks if a selection is a valid selection or not

        @param selection: unprocessed user selection, i.e. single value or comma separated list, or control characters: p|n|previous|next
        @param choices: choices to choose from
        @param multiSelection: whether the more than one selection is allowed or not
        """
        selections = [value.strip() for value in selection.split(',')]
        if not multiSelection:
            selections = selections[:1]

        if selections[0] in EasyDialogConsole._NAVIGATION_CONTROL_FLAGS:
            selections = selections[:1] #ignore the rest of the values, if any
        else:
            try:
                selections = list(map(int, selections)) #convert to int
            except ValueError as ex:
                raise ValueError('Invalid numeric values [%s]'%selections)

            if max(selections) > len(choices) or min(selections) <= 0:
                raise ValueError('Selection out of range')


        return selections



if __name__=='__main__':
    #print EasyDialog().askFilePath()
    print((EasyDialogWin32().askString("something")))