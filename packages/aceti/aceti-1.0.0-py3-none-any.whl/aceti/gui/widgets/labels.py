import tkinter
import tkinter.font
import tkinter.ttk

def create_label(frame, _text, _variable, relief="raised"):
    a= tkinter.Frame(frame, borderwidth=2, relief=relief, padx=10, pady=2)
    a.pack(side='top', fill='both', expand=True,)
    a.pack_propagate(False)
    tkinter.Label(a, text=_text, font=tkinter.font.Font(weight='bold')).pack(side="left", fill='both', padx=0, pady=2)
    tkinter.Label(a, textvariable=_variable).pack(side="left", fill='both', padx=0, pady=2)
    return a
def create_tittle_label(frame, _text, _size=20):
    a= tkinter.Frame(frame,width=400, height=50, borderwidth=2, relief="raised", padx=50, pady=2)
    a.pack_propagate(False)
    tkinter.Label(a, text=_text, font=tkinter.font.Font(weight='bold', size=_size)).pack(side="left", fill='x', padx=0, pady=2)
    return a
    
def create_labelh(frame, _text, _variable, width=10, _size=14, expand="false", fill="both"):
    a= tkinter.Frame(frame, borderwidth=2, relief="raised", padx=10, pady=10)
    a.pack(side='left', anchor="w", fill=fill, expand=expand)
    tkinter.Label(a, text=_text, font=tkinter.font.Font(weight='bold', size=_size)).pack(side="left", padx=0, pady=2,anchor="e")
    ret=tkinter.Label(a , font=tkinter.font.Font(size=_size-2), textvariable=_variable)
    ret.pack(side="left", padx=0, pady=2,anchor="w")
    return ret

def create_label_with_units(frame, _text, _variable, units):
    a= tkinter.Frame(frame, borderwidth=2, relief="raised", padx=10, pady=10)
    a.pack(side='top', fill='both', expand=True,)
    a.pack_propagate(False)
    tkinter.Label(a, text=_text, font=tkinter.font.Font(weight='bold')).pack(side="left", fill='both', padx=0, pady=5)
    tkinter.Label(a, textvariable=_variable).pack(side="left", fill='both', padx=0, pady=5)
    tkinter.Label(a, text=units).pack(side="left", fill='both', padx=0, pady=5)
    return a

def create_labelh_with_units(frame, _text, _variable, units, _size=14, expand="false", fill = "both"):
    a= tkinter.Frame(frame, borderwidth=2, relief="raised", padx=10, pady=10)
    a.pack(side='left', anchor="w", fill=fill, expand=expand)
    tkinter.Label(a, text=_text, font=tkinter.font.Font(weight='bold', size=_size)).pack(side="left", fill=fill, padx=0, pady=5)
    tkinter.Label(a, textvariable=_variable, font=tkinter.font.Font(size=_size-2)).pack(side="left", fill=fill, padx=0, pady=5)
    tkinter.Label(a, text=units, font=tkinter.font.Font(size=_size-2)).pack(side="left", fill=fill, padx=0, pady=5)
    return a

