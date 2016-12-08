import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.template
import time
import threading

from MWeb import web

class MainHandler(tornado.web.RequestHandler):
  def get(self):
    loader = tornado.template.Loader(".")
    self.write(loader.load("index.html").generate())

class WSHandler(tornado.websocket.WebSocketHandler):
  def open(self):
    print 'connection opened...'
    message = []
    for d in web.devices:
        message.append(str(d.getTitle()+": "+d.getReadings))
    self.write_message(str(message))
    threading.Timer(1, self.open).start()
    #self.write_message("The server says: 'Hello'. Connection was accepted.")

  def on_message(self, message):
    self.write_message("The server says: " + message + " back at you")
    print 'received:', message

  def on_close(self):
    print 'connection closed...'

application = tornado.web.Application([
  (r'/ws', WSHandler),
  (r'/', MainHandler),
  (r"/(.*)", tornado.web.StaticFileHandler, {"path": "./resources"}),
])

if __name__ == "__main__":
  application.listen(9090)
  tornado.ioloop.IOLoop.instance().start()