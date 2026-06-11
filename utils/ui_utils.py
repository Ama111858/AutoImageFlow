import tkinter as tk
import customtkinter as ctk

def add_context_menu(widget):
    """
    Adds a standard Cut/Copy/Paste/Select All context menu to a CTkEntry or CTkTextbox.
    """
    menu = tk.Menu(widget, tearoff=0)
    
    # We need to target the underlying tk.Entry or tk.Text
    if isinstance(widget, ctk.CTkEntry):
        target = widget._entry
        
        def select_all():
            target.select_range(0, 'end')
            target.icursor('end')
            
        def clear_all():
            target.delete(0, 'end')
            
    elif isinstance(widget, ctk.CTkTextbox):
        target = widget._textbox
        
        def select_all():
            target.tag_add("sel", "1.0", "end")
            
        def clear_all():
            target.delete("1.0", "end")
    else:
        return

    menu.add_command(label="Cut", command=lambda: target.event_generate("<<Cut>>"))
    menu.add_command(label="Copy", command=lambda: target.event_generate("<<Copy>>"))
    menu.add_command(label="Paste", command=lambda: target.event_generate("<<Paste>>"))
    menu.add_separator()
    menu.add_command(label="Select All", command=select_all)
    menu.add_command(label="Clear", command=clear_all)
    
    def show_menu(event):
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    target.bind("<Button-3>", show_menu)
