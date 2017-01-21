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
__version__ = "1.0.0"
__maintainer__ = "Noah Meltzer"
__status__ = "Beta"

import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.template
import threading

from MWeb import web


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        loader = tornado.template.Loader(".")
        self.write(loader.load("index.html").generate())


class WSHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        print('Connection opened...')
        message = []
        for d in web.devices:
            message.append("%s: %s" %(d.getTitle(), d.getReadings))
        self.write_message(str(message))
        threading.Timer(1, self.open).start()

    def on_message(self, message):
        self.write_message("The server says %s back at you." 
                %str(message))
        print('Received: %s', str(message))

    def on_close(self):
        print('Connection closed...')


application = tornado.web.Application([
    (r'/ws', WSHandler),
    (r'/', MainHandler),
    (r"/(.*)", tornado.web.StaticFileHandler, {"path": "./resources"})])


if __name__ == "__main__":
    application.listen(9090)
    tornado.ioloop.IOLoop.instance().start()