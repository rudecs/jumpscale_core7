from JumpScale import j
import smtplib
import mimetypes
from email import encoders
from email.message import Message
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

class EmailClient(object):
    def __init__(self):
        cfg = j.core.config.get("mailclient", "main")
        self._server = cfg['server']
        self._port = cfg.get('port', 25)
        self._ssl = cfg.get('ssl', False)
        self._username = cfg.get('login')
        self._password = cfg.get("passwd")
        self._sender = cfg.get("sender", '')

    def __str__(self):
        out="server=%s\n"%(self._server)
        out+="port=%s\n"%(self._port)
        out+="username=%s\n"%(self._username)
        return out

    __repr__=__str__

    def send(self, recipients, sender="", subject="", message="", files=None, mimetype=None):
        """
        @param recipients: Recipients of the message
        @type recipients: mixed, string or list
        @param sender: Sender of the email
        @type sender: string
        @param subject: Subject of the email
        @type subject: string
        @param message: Body of the email
        @type message: string
        @param files: List of paths to files to attach
        @type files: list of strings
        @param mimetype: Type of the body plain, html or None for autodetection
        @type mimetype: string
        """
        if sender=="":
            sender=self._sender 
        if isinstance(recipients, str):
            recipients = [ recipients ]
        server = smtplib.SMTP(self._server, self._port) 
        server.ehlo()
        if self._ssl:
            server.starttls()
        if self._username:
            server.login(self._username, self._password)

        if mimetype is None:
            if '<html>' in message:
                mimetype = 'html'
            else:
                mimetype = 'plain'

        msg = MIMEText(message, mimetype, 'utf-8')
        
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = ','.join(recipients)

        if files:
            txtmsg = msg
            msg = MIMEMultipart()
            msg['Subject'] = subject
            msg['From'] = sender
            msg['To'] = ','.join(recipients)
            msg.attach(txtmsg)
            for fl in files:
                # Guess the content type based on the file's extension.  Encoding
                # will be ignored, although we should check for simple things like
                # gzip'd or compressed files.
                filename = j.system.fs.getBaseName(fl)
                ctype, encoding = mimetypes.guess_type(fl)
                content = j.system.fs.fileGetContents(fl)
                if ctype is None or encoding is not None:
                    # No guess could be made, or the file is encoded (compressed), so
                    # use a generic bag-of-bits type.
                    ctype = 'application/octet-stream'
                maintype, subtype = ctype.split('/', 1)
                if maintype == 'text':
                    attachement = MIMEText(content, _subtype=subtype)
                elif maintype == 'image':
                    attachement = MIMEImage(content, _subtype=subtype)
                elif maintype == 'audio':
                    attachement = MIMEAudio(content, _subtype=subtype)
                else:
                    attachement = MIMEBase(maintype, subtype)
                    attachement.set_payload(content)
                    # Encode the payload using Base64
                    encoders.encode_base64(attachement)
                # Set the filename parameter
                attachement.add_header('Content-Disposition', 'attachment', filename=filename)
                msg.attach(attachement)
        server.sendmail(sender, recipients, msg.as_string())
        server.close()
