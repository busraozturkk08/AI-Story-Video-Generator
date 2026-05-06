import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import os
from dotenv import load_dotenv
from google import genai

# .env dosyasındaki değişkenleri yükle
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

class HikayeUygulamasi:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Hikaye Atölyesi - Görsel & Kategorili")
        self.root.geometry("600x850")
        
        # Tema Renk Sözlüğü (Görselleştirme için)
        self.temalar = {
            "Bilim Kurgu": {"bg": "#E3F2FD", "fg": "#0D47A1"}, # Mavi tonları
            "Korku": {"bg": "#263238", "fg": "#FF5252"},       # Siyah-Kırmızı
            "Macera": {"bg": "#F1F8E9", "fg": "#33691E"},      # Yeşil tonları
            "Dram": {"bg": "#F3E5F5", "fg": "#4A148C"},        # Mor tonları
            "Komedi": {"bg": "#FFFDE7", "fg": "#F57F17"},      # Sarı/Turuncu
            "Varsayılan": {"bg": "#F9F9F9", "fg": "#333333"}
        }

        self.veritabani_hazirla()
        self.arayuz_olustur()
        self.veritabani_listele()

    def veritabani_hazirla(self):
        conn = sqlite3.connect('stories.db')
        # Kategori (category) sütununu ekledik
        conn.execute('''CREATE TABLE IF NOT EXISTS stories 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                      title TEXT, 
                      content TEXT,
                      category TEXT)''')
        conn.commit()
        conn.close()

    def arayuz_olustur(self):
        tk.Label(self.root, text="🎭 Hikaye Atölyesi", font=("Arial", 18, "bold")).pack(pady=10)
        
        frame_giris = tk.Frame(self.root)
        frame_giris.pack(pady=10, padx=20, fill="x")
        
        tk.Label(frame_giris, text="Konu:").pack(side="left")
        self.entry_konu = tk.Entry(frame_giris, font=("Arial", 12))
        self.entry_konu.pack(side="left", padx=10, expand=True, fill="x")
        
        self.btn_uret = tk.Button(frame_giris, text="✨ Üret", command=self.hikaye_uret, bg="#4CAF50", fg="white")
        self.btn_uret.pack(side="right")

        # Kategori Bilgi Etiketi
        self.lbl_kategori = tk.Label(self.root, text="Tür: -", font=("Arial", 10, "bold"))
        self.lbl_kategori.pack()

        self.text_hikaye = tk.Text(self.root, height=15, font=("Segoe UI", 11), wrap="word", padx=15, pady=15)
        self.text_hikaye.pack(pady=10, padx=20, fill="both", expand=True)

        # Liste Bölümü
        tk.Label(self.root, text="📚 Kütüphane", font=("Arial", 10, "bold")).pack()
        self.listbox_hikayeler = tk.Listbox(self.root, height=8)
        self.listbox_hikayeler.pack(pady=10, padx=20, fill="x")
        self.listbox_hikayeler.bind('<<ListboxSelect>>', self.hikaye_getir)

    def tema_uygula(self, kategori):
        # Tür anahtarda yoksa varsayılanı kullan
        tema = self.temalar.get(kategori, self.temalar["Varsayılan"])
        self.text_hikaye.config(bg=tema["bg"], fg=tema["fg"])
        self.lbl_kategori.config(text=f"Tür: {kategori}", fg=tema["fg"])

    def hikaye_uret(self):
        konu = self.entry_konu.get()
        if not konu: return

        self.btn_uret.config(text="🤖 Yazılıyor...", state="disabled")
        self.root.update()

        try:
            # AI'dan artık Kategori de istiyoruz
            prompt = (f"Konu: {konu}. Bu konuyla ilgili bir hikaye yaz. "
                      "Yanıtın ŞU FORMATTA OLSUN:\n"
                      "KATEGORİ: [Bilim Kurgu, Macera, Korku, Dram veya Komedi seçeneklerinden biri]\n"
                      "BAŞLIK: [Hikaye Başlığı]\n"
                      "İÇERİK: [Hikaye Metni]")
            
            response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
            raw_text = response.text

            # Metni parçalama (Hata payını azaltmak için satır satır bakıyoruz)
            kategori, baslik, icerik = "Dram", konu, raw_text
            lines = raw_text.split("\n")
            
            for line in lines:
                if line.startswith("KATEGORİ:"): kategori = line.replace("KATEGORİ:", "").strip()
                elif line.startswith("BAŞLIK:"): baslik = line.replace("BAŞLIK:", "").strip()
            
            if "İÇERİK:" in raw_text:
                icerik = raw_text.split("İÇERİK:")[1].strip()

            self.text_hikaye.delete("1.0", tk.END)
            self.text_hikaye.insert(tk.END, icerik)
            
            # Görselleştirme ve Kayıt
            self.tema_uygula(kategori)
            self.veritabani_kaydet(baslik, icerik, kategori)
            self.veritabani_listele()
            
        except Exception as e:
            messagebox.showerror("Hata", str(e))
        finally:
            self.btn_uret.config(text="✨ Üret", state="normal")

    def veritabani_kaydet(self, baslik, icerik, kategori):
        conn = sqlite3.connect('stories.db')
        conn.execute('INSERT INTO stories (title, content, category) VALUES (?, ?, ?)', (baslik, icerik, kategori))
        conn.commit()
        conn.close()

    def veritabani_listele(self):
        self.listbox_hikayeler.delete(0, tk.END)
        conn = sqlite3.connect('stories.db')
        cursor = conn.execute('SELECT id, title, category FROM stories ORDER BY id DESC')
        for row in cursor:
            # Listede türü de gösteriyoruz
            self.listbox_hikayeler.insert(tk.END, f"[{row[2]}] {row[1]}")
        conn.close()

    def hikaye_getir(self, event):
        selection = self.listbox_hikayeler.curselection()
        if selection:
            item = self.listbox_hikayeler.get(selection[0])
            # Başlığın sonundaki ID'yi bulmak yerine başlık eşleşmesi yapabiliriz
            # Ama en güvenlisi liste indeksinden gitmektir, şimdilik basitleştirelim:
            idx = selection[0]
            conn = sqlite3.connect('stories.db')
            cursor = conn.execute('SELECT title, content, category FROM stories ORDER BY id DESC')
            rows = cursor.fetchall()
            row = rows[idx]
            
            self.text_hikaye.delete("1.0", tk.END)
            self.text_hikaye.insert(tk.END, row[1])
            self.tema_uygula(row[2])
            conn.close()

if __name__ == "__main__":
    root = tk.Tk()
    app = HikayeUygulamasi(root)
    root.mainloop()