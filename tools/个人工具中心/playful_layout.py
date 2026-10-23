"""Size tool windows for the current Tk font scaling and visible screen."""
def size_window(window,width,height,min_width,min_height):
    scale=max(1.0,float(window.tk.call('tk','scaling'))/(96/72))
    limit_w=max(400,window.winfo_screenwidth()-80);limit_h=max(400,window.winfo_screenheight()-100)
    width=min(round(width*scale),limit_w);height=min(round(height*scale),limit_h)
    window.geometry(f'{width}x{height}')
    window.minsize(min(round(min_width*scale),width),min(round(min_height*scale),height))
