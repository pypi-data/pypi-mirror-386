import requests
from bs4 import BeautifulSoup
from PIL import Image
import customtkinter as ctk
import tkinter as tk
import os
from pathlib import Path

current_dir = Path(__file__).parent
image_path = current_dir / "data" / "flipline_studio.png"
text_path = current_dir / "data" / "Webjeux_games_names.txt"

ctk.set_appearance_mode("dark")
img = Image.open(image_path)

class gui:
    def __init__(self):
        #going through the sugestion file and appending them all to "suggestions" list
        with open(text_path,"r") as f:
            self.suggestions = [line.strip() for line in f if line.strip()]
            
        #the root, instance choice variable to 0 in default
        #instance choice variable is used in body function to create the download path (default or custom), It's used again in on_type function to pack the enrty if choice is "custom",it's needed to pack the listbox (listbox is above the entry)
        self.root = ctk.CTk()
        self.root.title("WebJeux flash games downloader")
        self.root.geometry("520x640")
        self.root.resizable(False,False)
        self.inst_choice = 0
        #GUI functions calling
        self.user_com()
        self.img_frame()
        self.bottom_labels()
    #function responsible of showing the errors and the success in the bottom
    def bottom_labels(self):
        self.label4 = ctk.CTkLabel(self.root, text='Failed to reach the server. Please check your internet connection', font=ctk.CTkFont("arial black", 12),text_color="#E21F1F")
        self.label5 = ctk.CTkLabel(self.root, text='The game is successfully downloaded', font=ctk.CTkFont("arial black", 12),text_color="#55BD21")
        self.label6 = ctk.CTkLabel(self.root, text='Game not found', font=ctk.CTkFont("arial black", 12),text_color="#E21F1F")
        self.label7 = ctk.CTkLabel(self.root, text='Try typing...', font=ctk.CTkFont("arial black", 12),text_color="#E21F1F")
    #function that handles game name cleaning, path joining, errors showing, and game download
    def body(self):
        #typed name cleaner
        self.un_gm_nm = self.entry1.get()
        self.un_gm_nm = self.un_gm_nm.lower()
        self.un_gm_nm = self.un_gm_nm.replace(" ","-")
        self.game_name = self.un_gm_nm
        print("game name : ",self.game_name)
        #path hadler
        if self.inst_choice:
            self.custom_path = self.entry2.get()
            self.path = os.path.join(self.custom_path, self.game_name)
        else:
            self.path = 'C:\\Users\\HP\\Downloads\\flash games\\'+self.game_name
        #errors handling
        try:    
            r = requests.get("https://www.webjeux.com/jouer/"+self.game_name+".html")
        except requests.exceptions.RequestException:
            print("Failed to reach the server. Please check your internet connection ")
            self.label6.pack_forget()
            self.label5.pack_forget()
            self.label7.pack_forget()
            self.label4.pack(pady=5)
            return
        print("WebJeux status code : ",r.status_code)
        if r.status_code == 404:
            print("Game not found")
            self.label4.pack_forget()
            self.label5.pack_forget()
            self.label7.pack_forget()
            self.label6.pack(pady=5)
            return
        if r.status_code == 403:
            print("Empty entry bar or too many requests (403)")
            self.label4.pack_forget()
            self.label5.pack_forget()
            self.label6.pack_forget()
            self.label7.pack(pady=5)
            return
        #game download
        soup = BeautifulSoup(r.text, "html.parser")
        swfs = soup.find(attrs={"data":True})
        swf = swfs["data"]
        r2 = requests.get(swf)
        print("swf status code : ",r2.status_code)
        headers = r2.headers
        print("Content type : ",headers["Content-Type"])
        with open(self.path+'.swf','wb') as f:
            f.write(r2.content)
            print("Success")
        #packing success message    
        self.label6.pack_forget()
        self.label4.pack_forget()
        self.label7.pack_forget()
        self.label5.pack(pady=5)
        
    #function responsible of updating suggestions while typing game's name
    def on_type(self,event):
        #removing bottom labels
        self.label6.pack_forget()
        self.label4.pack_forget()
        self.label5.pack_forget()
        self.label7.pack_forget()
        #getting the typed text and removing the listbox to update it based on if it is empty or not
        text = self.entry1.get().lower()
        self.listbox.delete(0,tk.END)
        #going through the suggestion list to find matches,if so, it gets inserted to the listbox
        if text:
            for item in self.suggestions:
                if item.lower().startswith(text):
                    self.listbox.insert(tk.END, item)
            #packing the listbox if it's not empty       
            if self.listbox.size()>0:
                self.label2.pack_forget()
                self.dropbox.pack_forget()
                self.entry2.pack_forget()
                self.button1.pack_forget()
                self.listbox.pack(pady=5)
                self.label2.pack(pady=5)
                self.dropbox.pack(pady=5)
                #packing the path entry if checkbow state is 'custom'
                if self.inst_choice==1:
                    self.entry2.pack(pady=5)
                self.button1.pack(pady=5)
                return
        #removing the listbox if it's empty    
        self.listbox.pack_forget()
        
    #function responsible of adding selected suggestion to the entry box   
    def on_select(self,event):
        if self.listbox.curselection():
            self.entry1.delete(0, tk.END)
            self.entry1.insert(0, self.listbox.get(self.listbox.curselection()[0]))
            self.listbox.pack_forget()
            
    #function responsible of the main GUI layout
    def user_com(self):
        self.label1 = ctk.CTkLabel(self.root, text='Welcome to WebJeux flash games.\nEnter game name :',font=ctk.CTkFont("arial black", 15))
        self.label1.pack(pady=15)

        self.entry1 = ctk.CTkEntry(self.root, placeholder_text="Start typing...", width=200)
        self.entry1.pack()

        self.listbox = tk.Listbox(self.root,height=6)

        self.label2 = ctk.CTkLabel(self.root, text='Select download path :\nThe game gonna be saved in flash games folder by default',font=ctk.CTkFont("arial black", 14))
        self.label2.pack(pady=20)

        self.dropbox = ctk.CTkOptionMenu(self.root,command=self.path_fun,text_color_disabled="gray",dropdown_font=("arial black", 12),font=("arial black", 14),button_hover_color='#9A4743',fg_color="#C1554F",button_color='#C1554F',width=200,corner_radius=10, values=["Default","Custom"])
        self.dropbox.pack(pady=5)

        self.entry2 = ctk.CTkEntry(self.root, placeholder_text="Start typing...",width=200)
   
        self.button1 = ctk.CTkButton(self.root,command=self.body, text='Download', corner_radius=15, fg_color='#F7494B',hover_color='#C90E0E',text_color='#171519',border_width=2,width=200,height=50,font=ctk.CTkFont("arial black", 20))
        self.button1.pack(pady=5)

        #detect keyboard keys and calling the function, detect listbox select and calling the function
        self.entry1.bind("<KeyRelease>", self.on_type)
        self.listbox.bind("<<ListboxSelect>>", self.on_select)
        
    #function responsible of adding and removing custom path entry and updating instance choice variable
    def path_fun(self,choice):
        if choice == 'Custom':
            self.label6.pack_forget()
            self.label4.pack_forget()
            self.label5.pack_forget()
            self.label7.pack_forget()
            self.button1.pack_forget()
            self.entry2.pack(pady=5)
            self.button1.pack(pady=5)
            self.inst_choice = 1
            return
        self.label6.pack_forget()
        self.label4.pack_forget()
        self.label5.pack_forget()
        self.label7.pack_forget()
        self.button1.pack_forget()
        self.entry2.pack_forget()
        self.button1.pack(pady=5)
        self.inst_choice = 0
    #function responsible of showing the image at the bottom    
    def img_frame(self):
        self.label3 = ctk.CTkLabel(self.root,text="" ,image=ctk.CTkImage(light_image=img,dark_image=img, size=(200,200)))
        self.label3.pack(side='bottom')

#main loop command        
if __name__ == "__main__":
    app = gui()
    app.root.mainloop()
