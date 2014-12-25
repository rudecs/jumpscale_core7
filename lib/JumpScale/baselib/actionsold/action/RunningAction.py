 
class RunningAction:
    description = ""
    '''Action description

    @type: string
    '''

    resolutionMessage = ""
    '''Action resolution message

    @type: string
    '''

    errorMessage = ""
    '''Action error message

    @type: string
    '''

    show = True
    '''Display action

    @type: bool
    '''

    interrupted = False
    '''Whether the action was interrupted

    @type: bool
    '''

    output = ""
    '''Action output

    @type: string
    '''

    messageLevel = 1
    '''TODO'''
    
    def __init__(self, description, errorMessage, resolutionMessage, show=True, messageLevel=1):
        '''Initialize a new L{RunningAction}

        @param description: Action description
        @type description: string
        @param resolutionMessage: Action resolution message
        @type resolutionMessage: string
        @param show: Display action
        @type show: bool
        @param messageLevel: Message level
        @type messageLevel: number
        '''

        self.description = description
        self.resolutionMessage = resolutionMessage
        self.errorMessage = errorMessage
        self.show = show
        self.messageLevel = messageLevel