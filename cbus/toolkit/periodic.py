import asyncio
import queue

class Periodic:
  """   
  class that manages a queue of functions to be called while 
  leaving a interval between two successsive calls 
  """
  queue = []

  def __init__(self,period = 1):
    self.queue = queue.Queue()
    self.period = period
    loop = asyncio.get_event_loop()
    self.task = loop.create_task(self._work())
    
  async def _work(self):
    while True:
      try:
        action = self.queue.get(block=False)
        action()
      except:
        pass
      finally:
        await asyncio.sleep(self.period)

  def enqueue(self,task):
    #talks is a lambda or the name of a function with no argument
      self.queue.put(task)