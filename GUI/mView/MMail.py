# Copyright (C) 2016 Noah Meltzer
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

__author__ = "Noah Meltzer"
__copyright__ = "Copyright 2016, McDermott Group"
__license__ = "GPL"
__version__ = "1.0.2"
__maintainer__ = "Noah Meltzer"
__status__ = "Beta"

import smtplib
from email.mime.text import MIMEText


class MMail:
    """Very simple email client."""

    def __init__(self, To, From, Subject, Body):
        msg = MIMEText(Body)
        msg['Subject'] = Subject
        msg['From'] = From
        msg['To'] = To
        smtpObj = smtplib.SMTP('smtp.gmail.com')
        # Say hello to the email server.
        smtpObj.ehlo()
        # Initialize TLS security.
        smtpObj.starttls()
        if To:
            smtpObj.login('physics.labrad@gmail.com', 'mcdermott')
            # Send the email.
            smtpObj.sendmail('physics.labrad@gmail.com', To.split(','),
                             msg.as_string())
            print("Successfully sent mail.")
        smtpObj.quit()
