"""Only visible card images, one worker and a bounded thumbnail cache."""
from collections import OrderedDict
import queue,threading

class CardImages:
    def __init__(self,cards,reader):
        self.cards=cards;self.reader=reader;self.cache=OrderedDict();self.events=queue.SimpleQueue();self.active=False;self.timer=None;self.closed=False
        cards.on_visible=self.load;cards.bind('<Destroy>',self.cleanup,add='+')
    def key(self,item):return item.get('icon_key',item['id'])
    def load(self):
        if self.closed:return
        pending=[]
        for key in self.cards.visible_ids():
            item=self.cards.items[key];cache_key=self.key(item)
            if cache_key in self.cache:
                self.cache.move_to_end(cache_key);self.cards.show_image(key,self.cache[cache_key])
            else:pending.append((key,cache_key,dict(item)))
        if not pending or self.active:return
        self.active=True;size=self.cards.icon_size
        def worker():
            for key,cache_key,item in pending:
                if self.closed:break
                try:
                    image=self.reader(item)
                    if image is not None:
                        w,h=image.size;factor=min(size/max(1,w),size/max(1,h));image=image.resize((max(1,round(w*factor)),max(1,round(h*factor))))
                except Exception:image=None
                self.events.put((key,cache_key,image))
            self.events.put(None)
        threading.Thread(target=worker,daemon=True).start();self.timer=self.cards.after(60,self.poll)
    def poll(self):
        self.timer=None
        if self.closed:return
        from PIL import ImageTk
        for _ in range(12):
            try:value=self.events.get_nowait()
            except queue.Empty:break
            if value is None:
                self.active=False;self.load();return
            key,cache_key,image=value;photo=ImageTk.PhotoImage(image,master=self.cards) if image is not None else None
            self.cache[cache_key]=photo;self.cache.move_to_end(cache_key)
            while len(self.cache)>120:self.cache.popitem(last=False)
            item=self.cards.items.get(key)
            if item and key in self.cards.widgets and self.key(item)==cache_key:self.cards.show_image(key,photo)
        self.timer=self.cards.after(60,self.poll)
    def cleanup(self,event):
        if event.widget==self.cards:
            self.closed=True
            if self.timer:self.cards.after_cancel(self.timer);self.timer=None
            self.cache.clear()
