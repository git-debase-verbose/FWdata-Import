import os
import tkinter as tk
import tkinter.filedialog as tkfd
import parserFWdata
import traceback
import re
import threading
from tkinter import ttk, Toplevel
from datetime import datetime
from time import sleep
from converter import Converter
from tkinter import messagebox


def on_closing():
    if messagebox.askokcancel("Quit", "Do you want to quit?"):
        root.destroy()

class MainWindow(tk.Frame):
    def __init__(self, root):
        super().__init__(root)
        self.root = root
        self.fwdata = None
        self.flextext = None

        self.frameIntroduction = tk.Frame(root, bg="#F6F2F9")
        self.frameIntroduction.place(relwidth=0.416, relheight=1.0, relx=0, rely=0)
        self.frameFunctions = tk.Frame(root, bg="#F9F3F2")
        self.frameFunctions.place(relwidth=0.584, relheight=0.833, relx=0.416,
                             rely=0)
        self.frameButtons = tk.Frame(root, bg="#F9F2F5")
        self.frameButtons.place(relwidth=0.584, relheight=0.167, relx=0.416, rely=0.833)

        self.style = ttk.Style()
        self.style.configure("BW.TLabel", foreground="black", background="#F9F3F2", justify="left")
        self.style.configure("Custom.TLabel", foreground="black", background="#F6F2F9", justify="left")
        self.style.configure("TButton", padding=5, relief="flat", font=("Georgia", 10))#, background="black", foreground="black")
        #style.map("C.TButton",
        #          foreground=[('pressed', 'red'), ('active', 'blue')],
        #          background=[('pressed', '!disabled', 'black'), ('active', 'white')]
        #          )
        self.style.configure("ResultLabel.TLabel", background="#F9F3F2", foreground="#000000")
        self.infolabel = ttk.Label(self.frameIntroduction,
                                   text="Welcome! This tool helps you to integrate your Toolbox project into a FLEx one or create a new FLEx project using your Toolbox data. For more information on how the tool operates see the documentation.",
                                   style="Custom.TLabel", font=("Georgia", 12) )
        self.infolabel.place(relx=0.02, rely=0.05, relwidth=1.1)
        self.infolabel.bind('<Configure>',
                            lambda e: self.infolabel.config(wraplength=self.frameIntroduction.winfo_width() - 20))
        self.infobutton = ttk.Button(self.frameIntroduction, text="Documentation", command=self.open_secondary_window,
                                     style="C.TButton")
        self.infobutton.place(relx=0.02, rely=0.6, height=30)
        #self.infobutton.bind(
        #    ('<Configure>', lambda e: self.infobutton.config(wraplength=self.frameIntroduction.winfo_width())))
       # self.root.bind("<Configure>", self.update_font_size)

        self.targetlabel = ttk.Label(self.frameFunctions, text="Target language writing system:", style="BW.TLabel", font=("Georgia", 12))
        self.targetlabel.place(relx=0.02, rely=0.05)
        self.targetentry = tk.Entry(self.frameFunctions)
        self.target = tk.StringVar(self.frameFunctions)
        self.target.set("xal-Latn")  # predefined value for testing
        self.targetentry = tk.Entry(self.frameFunctions, textvariable=self.target, font=("Georgia", 10), foreground="blue")
        self.targetentry.place(relx=0.65, rely=0.05)
        self.targetentry["textvariable"] = self.target

        self.glosslabel = ttk.Label(self.frameFunctions, text="Glossing writing system:", style="BW.TLabel", font=("Georgia", 12))
        self.glosslabel.place(relx=0.02, rely=0.2)
        self.glossentry = tk.Entry(self.frameFunctions)
        self.gloss = tk.StringVar(self.frameFunctions)
        self.gloss.set("en")  # predefined value for testing
        self.glossentry = tk.Entry(self.frameFunctions, textvariable=self.target, font=("Georgia", 10), foreground="blue")
        self.glossentry.place(relx=0.65, rely=0.2)
        self.glossentry["textvariable"] = self.gloss

        self.gloss2label = ttk.Label(self.frameFunctions, text="Alternative glossing writing system:",
                                     style="BW.TLabel", font=("Georgia", 12))
        self.gloss2label.place(relx=0.02, rely=0.35)
        self.gloss2entry = tk.Entry(self.frameFunctions)
        self.gloss2 = tk.StringVar(self.frameFunctions)
        self.gloss2.set("ru")  # predefined value for testing
        self.gloss2entry = tk.Entry(self.frameFunctions, textvariable=self.target, font=("Georgia", 10), foreground="blue")
        self.gloss2entry.place(relx=0.65, rely=0.35)
        self.gloss2entry["textvariable"] = self.gloss2

        self.selectfwdata = ttk.Button(self.frameFunctions, text="Select...", command=self.fwdata_selection,
                                       style="C.TButton")
        self.selectfwdata.place(relx=0.65, rely=0.5, height=30)

        self.fwdatanamefield = ttk.Label(self.frameFunctions, text="FLEx Database:", style="BW.TLabel", font=("Georgia", 12))
        self.fwdatanamefield.place(relx=0.02, rely=0.5)
        self.fwdataname = tk.StringVar()
        self.fwdataname_label = ttk.Label(self.frameFunctions, textvariable=self.fwdataname, style="BW.TLabel", font=("Georgia", 10), foreground="red")
        self.fwdataname_label.place(relx=0.45, rely=0.5)

        self.selectflexlabel = ttk.Label(self.frameFunctions, text="Path to flextext:", style="BW.TLabel", font=("Georgia", 12))
        self.selectflexlabel.place(relx=0.02, rely=0.65)
        self.selectflexbutton = ttk.Button(self.frameFunctions, text="Select...", command=self.flextext_selection,
                                           style="C.TButton")
        self.selectflexbutton.place(relx=0.65, rely=0.65, height=30)
        self.flexname = tk.StringVar()
        self.flexname_label = ttk.Label(self.frameFunctions, textvariable=self.flexname, style="BW.TLabel", font=("Georgia", 10), foreground="red")
        self.flexname_label.place(relx=0.45, rely=0.6)

        self.parse_button = ttk.Button(self.frameButtons, text="Parse", command=self.start_parser,
                                       style="C.TButton").place(relx=0.02, rely=0.03, height=30)
        self.convert_button = ttk.Button(self.frameButtons, text="Convert", command=self.start_converter,
                                         style="C.TButton").place(relx=0.65, rely=0.03, height=30)

    def fwdata_selection(self):
        self.fwdata = tkfd.askopenfile(mode='r', title="Select FW Data File",
                                       filetypes=[("FLEx interlinear", ".fwdata")])
        if self.fwdata:
            self.fwdataname.set(os.path.basename(self.fwdata.name))
            self.selectfwdata.place_forget()  # Remove the "Select..." button
            self.changefwdata = ttk.Button(self.frameFunctions, text="Change", command=self.fwdata_selection,
                                           style="C.TButton")
            self.changefwdata.place(relx=0.65, rely=0.6, height=30)
            self.selectflexlabel.place(relx=0.02, rely=0.7)
            self.flexname_label.place(relx=0.45, rely=0.7)
           # self.flexname_label.place(relx=0.3, rely=0.6)
            self.selectflexbutton.place(relx=0.65, rely=0.8, height=30)



    def flextext_selection(self):
        self.flextext = tkfd.askdirectory(title="Select FlexText Folder")
        if self.flextext:
            self.flexname.set(os.path.basename(self.flextext))
            self.selectflexbutton.place_forget()  # Remove the "Select..." button
            self.changeflexbutton = ttk.Button(self.frameFunctions, text="Change", command=self.flextext_selection,
                                               style="C.TButton")
            self.changeflexbutton.place(relx=0.65, rely=0.8, height=30)

    def start_parser(self):
        if not self.fwdata:
            messagebox.showwarning(title="Warning", message="No FWdata selected")
            print("No FWdata selected")
            return
        valuecheck = messagebox.askquestion(title="Information",
                                            message="The values are: " + self.target.get() + ", " + self.gloss.get() + ", " + self.gloss2.get() + ". Proceed with the parsing?")
        if valuecheck == "no":
            return
        print("The values are:", self.target.get(), self.gloss.get(), self.gloss2.get())

        def task_func():
            # with open(self.fwdata.name, 'r', encoding='utf-8-sig') as f:
            parserFWdata.parse(self.fwdata.name, self.target.get(), self.gloss.get(), self.gloss2.get(), app)

        self.show_progress("Parsing", task_func)

    def start_converter(self):
        print("The values are:", self.target.get(), self.gloss.get(), self.gloss2.get())

        def task_func():

            try:
                Converter.__init__(
                    Converter, self.fwdata.name, self.flextext,
                    self.target.get(), self.gloss.get(), self.gloss2.get(),
                    check_guids=False, main_window=app
                )
            except Exception as e:
                error_time = re.sub(r'[ \.\:]', "-", str(datetime.now()))
                errorlogfile = "error-" + error_time + ".log"
                with open(errorlogfile, "w") as logfile:
                    traceback.print_exception(e, file=logfile)
                return errorlogfile

        self.show_progress("Converting", task_func)


    def show_progress(self, title, task_func):
        # self.stop_task = False
        progress_window = Toplevel(self.root, bg="#F9F3F2")
        progress_window.title(title)
        progress_window.geometry("400x100")

        global progress_label
        progress_label = ttk.Label(progress_window, text=f"{title} in progress...", style="BW.TLabel")
        progress_label.pack(pady=10)

        global progress_bar
        progress_bar = ttk.Progressbar(progress_window, orient="horizontal", length=300, mode="indeterminate")
        progress_bar.pack(pady=10)
        progress_bar.start()
        output_label = ttk.Label(progress_window)  # , height=4, wrap='word')
        output_label.pack(pady=10)

        # progress_window.protocol("WM_DELETE_WINDOW", lambda: self.stop_task_execution(progress_window))
        thread = threading.Thread(target=self.run_task, args=(task_func, title, progress_window, progress_bar),
                                  daemon=True)
        thread.start()

    def stop_task_execution(self, progress_window):
        # self.stop_task = True
        progress_window.destroy()
        # self.run_task(task_func, title, progress_window, progress_bar)

    def update_progress(self, label_text, step):
        sleep(0.5)
        global progress_label
        progress_label["text"] = label_text

        global progress_bar
        progress_bar.step(step)
        root.update_idletasks()

    def run_task(self, task_func, title, progress_window, progress_bar):
        progress_window.title(title)
        global run_status
        run_status = task_func()
        if run_status is not None:
            result_text = f"{title} has crashed and burned!\nCheck the logfile at:\n{run_status}"
        else:
            result_text = f"{title} is complete!"
        self.show_result(progress_bar, progress_window, result_text)

        # self.root.after(5000, result_window.destroy)

    def show_result(self, progress_bar, progress_window, result_text):
        progress_bar.stop()
        progress_window.destroy()
        if run_status is not None:
            messagebox.showerror(title="Flextext2FLEx", message=result_text)
        else:
            messagebox.showinfo(title="Flextext2FLEx", message=result_text)

    def open_secondary_window(self):
        secondary_window = tk.Toplevel(self.root)
        secondary_window.title("Documentation")
        secondary_window.config(width=300, height=200)
        secondary_window.focus()

   # def update_font_size(self, event):
      #  new_font_size = max(10, int(event.width / 50))
     #   self.style.configure("TButton", font=("Georgia", new_font_size))
        #self.style.configure("C.TButton", font=("Georgia", new_font_size))
    #    self.style.configure("BW.TLabel", font=("Georgia", new_font_size))
    #    self.style.configure("Custom.TLabel", font=("Georgia", new_font_size))

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Flextext2FLEx")
    root.config(bg="white")
    root.geometry("1000x300")
    root.eval('tk::PlaceWindow . center')
    app = MainWindow(root)
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
