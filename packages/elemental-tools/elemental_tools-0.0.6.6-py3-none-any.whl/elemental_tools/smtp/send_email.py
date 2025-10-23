import smtplib
from email.mime.text import MIMEText
from elemental_tools.logger import Logger


class SendEmail:

    def __init__(self, login, password, smtp_server, smtp_port, sender=None, destination=None):
        self.sender = sender
        self.destination = destination
        self.login = login
        self.password = password
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port

        self.__logger__ = Logger(app_name=self.__class__.__name__, owner=login).log

    def check_config(self):
        try:
            # Connect to the SMTP server
            _server = smtplib.SMTP(self.smtp_server, int(self.smtp_port))
            _server.starttls()
            self.__logger__("start","Connected to SMTP server")
            try:
                _server.login(self.login, self.password)
                self.__logger__("success", "I just logged in to see in what condition, my condition was him.\n")
            except:
                raise Exception("Your smtp looks fine, maybe the problem is on your login information.")

            return True

        except Exception as e:
            raise Exception(f"Error registering e-mail: {e}")

    def send_email(self, subject, message, destination=None):
        # msg = MIMEText(message, 'plain')
        msg = MIMEText(message, 'html')
        msg['From'] = self.login
        if destination is not None:
            msg['To'] = destination
        else:
            msg['To'] = self.destination
        msg['Subject'] = subject
        try:
            _server = smtplib.SMTP(host=self.smtp_server, port=self.smtp_port)
            _server.starttls()
            self.__logger__("start", "Connected to SMTP server")
            _server.login(self.login, self.password)
            self.__logger__("info", f"Sending the email {self.login, msg['To'], msg.as_string()}")
            _server.sendmail(self.login, msg['To'], msg.as_string())
            self.__logger__("success", "Email Successfully Sent")
            return {'message': "Email Successfully Sent"}

        except Exception as e:
            raise Exception(f"Error sending email: {e}")


