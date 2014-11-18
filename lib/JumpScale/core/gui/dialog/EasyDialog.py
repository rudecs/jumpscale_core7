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

from JumpScale import j

from .DialogType import DialogType
from .EasyDialogConsole import EasyDialogConsole

class EasyDialog():
    def __init__(self):
      self.easyDialog=EasyDialogConsole()
    def pm_setDialogHandler(self):
        if j.system.platformtype.isWindows():
            self.chooseDialogType(DialogType.WIN32)
        else:
            self.chooseDialogType(None)

    def chooseDialogType(self,type):
        """
        supported types today: console,win32,wizardserver
        @param type DialogType enumerator
        """
        self.type=type
        self.easyDialog=EasyDialogConsole()
        if self.type==DialogType.WIZARDSERVER:
            from .EasyDialogWizardServer import EasyDialogWizardServer
            self.easyDialog=EasyDialogWizardServer()
        if self.type==DialogType.WIN32 and j.system.platformtype.isWindows():
            try:
                import EasyDialogs
                easyDialogsInstalled = True
            except ImportError:
                easyDialogsInstalled = False  # EasyDialog is not installed, fall back to Console.
            if easyDialogsInstalled:
                from .EasyDialogWin32 import EasyDialogWin32
                self.easyDialog=EasyDialogWin32()

    def message(self, message):
        """
        prints the given message to the screen

        @param message: message to print
        """

        return self.easyDialog.message(message)

    def askFilePath(self,message, startPath = None):
        """
        Prompts for a selection of a file path starting from startPath if given and '/' if not

        @param message: message that would be displayed to the user above the selection menu
        @param startPath: base dir of the navigation tree
        @return: path to the file selected
        """

        filepath=self.easyDialog.askFilePath(message, startPath)
        if not j.system.fs.exists(filepath):
            raise RuntimeError ("Could not find selected file path %s." % filepath)
        return filepath

    def askDirPath(self,message, startPath = None):
        """
        Prompts for a selection of a file path starting from startPath if given and '/' if not

        @param message: message that would be displayed to the user above the selection menu
        @param startPath: base dir of the navigation tree
        @return: path to the directory selected
        """

        filepath=self.easyDialog.askDirPath(message, startPath)
        if not j.system.fs.exists(filepath):
            raise RuntimeError ("Could not find selected folder path %s." % filepath)
        return filepath

    def askString(self,question, defaultValue = None, validator=None):
        """
        Asks the user the supplied question and prompt for an answer, if none given the default value is used
        @param question: question to be displayed
        @param defaultValue: if the user did not provide a response this value is used as an answer
        @param validator: regex validation value
        @return: response string or the default value
        """

        return self.easyDialog.askString(question, defaultValue, validator)

    def askYesNo(self,question, defaultValue = None):
        """
        Asks user the supplied question and prompt for an answer, if none given the default value is used, the response and the default value one of the values [y|Y|yes|Yes..n|N|No..]

        Note:For the EasyDialogConol implementation, currently the default value effect is ignored since it would require changing the jumpscale vapp
        @param question: question to be prompted
        @param defaultValue: if the user did not provide a response this value is used as an answer
        @return: response answer or the default value
        """

        return self.easyDialog.askYesNo(question, defaultValue)

    def askPassword(self, question, confirm=True, regex=None, retry=-1, defaultValue=None):
        """
        Asks the supplied question and prompts for password

        @param question: question to be displayed
        @return: response string
        """
        return self.easyDialog.askPassword(question, confirm, regex, retry, defaultValue)

    def askInteger(self, question, defaultValue = None):
        """
        Asks user the supplied question and prompt for an answer, if none given the default value is used, the response and the default value must be valid integer

        @param question: question to be displayed
        @param defaultValue: if the user did not provide a response this value is used as an answer
        @return: response integer or the default value
        """

        return self.easyDialog.askInteger(question, defaultValue)


    def askIntegers(self, question):
        """
        Asks user the supplied question and prompt for an answer

        @param question: question to be prompted
        @return: response integer
        """

        return self.easyDialog.askIntegers(question)

    def askChoice(self, question, choices, defaultValue = None, pageSize = 10, sortChoices=False, sortCallBack=None):
        """
        Ask the user the supplied question and list the choices to choose from, if no response given the default value is used

        @param question: question to be display to the user
        @param choices: list of choices for the user to choose from
        @param defaultValue: the value that will be used if no response given
        @param pageSize: max number of choices that can be prompted to the user in a single screen
        @param sortChoices: if True, choices will be sorted before showing them to the user
        @param sortCallBack: A callback function to handle the sorting of the choices (will only be used if sortChoices is set to True)

        @return:  selected choice
        """

        return self.easyDialog.askChoice(question, choices, defaultValue, pageSize, sortChoices, sortCallBack)

    def askChoiceMultiple(self, question, choices, defaultValue = None, pageSize = 10, sortChoices=False, sortCallBack=None):
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

        return self.easyDialog.askChoiceMultiple(question, choices, defaultValue, pageSize, sortChoices, sortCallBack)

    def askMultiline(self, question, defaultValue=None):
        """
        Asks the user the supplied question, where the answer could be multi-lines

        @param question: the question to be displayed
        """
        return self.easyDialog.askMultiline(question, defaultValue=defaultValue)

    # Specific methods only available in the wizard server
    def askDate(self, question, minValue = None, maxValue = None, selectedValue = None, format = 'YYYY/MM/DD'):
        """
        Asks user a question that its answer is a date between minValue and maxValue

        Note: this note my seem out of place, but is is important to note that currently in the EasyDialogConsole implementation only dates with format YYYY/MM/DD are supported

        @param question: question that will be prompted to the user
        @param minValue: optional value for the lower boundary date
        @param maxValue: optional value for the upper boundary date
        @param selectedValue:
        @param  format: the format of the input date
        """
        return self.easyDialog.askDate(question, minValue, maxValue, selectedValue, format)


    def askDateTime(self, question, minValue = None, maxValue = None, selectedValue = None, format = 'YYYY/MM/DD hh:mm'):
        """
        Asks user a question that its answer is a datetime between minValue and maxValue

        Note: this note my seem out of place, but is is important to note that currently in the EasyDialogConsole implementation only dates with format YYYY/MM/DD are supported

        @param question: question that will be prompted to the user
        @param minValue: optional value for the lower boundary date
        @param maxValue: optional value for the upper boundary date
        @param selectedValue:
        @param  format: the format of the input date
        """
        return self.easyDialog.askDateTime(question, minValue, maxValue, selectedValue, format)

    def showProgress(self, minvalue, maxvalue, currentvalue):
        """
        Shows a progress bar according to the given values

        @param minvalue: minVlue of scale
        @param maxvalue: maxvlaue of scale
        @param currentvalue: the current value to show the progress
        """
        return self.easyDialog.showProgress(minvalue, maxvalue, currentvalue)

    def showLogging(self, text):
        """
        Shows logging message
        """
        return self.easyDialog.showLogging(text)

    def navigateTo(self, url):
        return self.easyDialog.navigateTo(url)
    
    def askForm(self, form):
        return self.easyDialog.askForm(form)
    
    def clear(self):
        return self.easyDialog.clear()

    def showMessageBox(self, message, title, msgboxButtons = "OK", msgboxIcon = "Information", defaultButton = "OK"):
        """
        Shows a large message box

        @param message: message for the messagebox
        @param title: title of the messagebox
        @param msgboxButtons: buttons to show in the messagebox. Possible values are 'OKCancel', 'YesNo', 'YesNoCancel', 'OK'
        @param msgboxIcon: icon to show in the messagebox. Possible values are 'None', 'Error', 'Warning', 'Information', 'Question'
        @param defaultButton: default button for the messagebox. Possible values are 'OK', 'Cancel', 'Yes', 'No'
        
        @return: A JSON encoded string containing the selected button clicked
        """
        return self.easyDialog.showMessageBox(message, title, msgboxButtons, msgboxIcon, defaultButton)


    

if __name__=='__main__':
    #print EasyDialog().askFilePath()
    print(EasyDialog().askString("something"))
