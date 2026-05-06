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
        self.root.title("AI Hikaye Atölyesi - Koleksiyon")
        self.root.geometry("600x800") # Biraz daha uzun bir ekran iyi olur
        
        self.veritabani_hazirla()
        self.arayuz_olustur()
        self.veritabani_listele()

    def veritabani_hazirla(self):
        conn = sqlite3.connect('stories.db')
        conn.execute('''CREATE TABLE IF NOT EXISTS stories 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                      title TEXT, 
                      content TEXT)''')
        conn.commit()
        conn.close()

    def arayuz_olustur(self):
        # Üst Başlık
        tk.Label(self.root, text="📖 AI Hikaye Atölyesi", font=("Arial", 18, "bold"), fg="#2E7D32").pack(pady=10)
        
        # Giriş Alanı
        frame_giris = tk.Frame(self.root)
        frame_giris.pack(pady=10, padx=20, fill="x")
        
        tk.Label(frame_giris, text="Yeni Hikaye Konusu:", font=("Arial", 10)).pack(side="left")
        self.entry_konu = tk.Entry(frame_giris, font=("Arial", 12))
        self.entry_konu.pack(side="left", padx=10, expand=True, fill="x")
        
        self.btn_uret = tk.Button(frame_giris, text="✍️ Hikaye Üret", command=self.hikaye_uret, bg="#4CAF50", fg="white", font=("Arial", 10, "bold"))
        self.btn_uret.pack(side="right")

        # Hikaye Görüntüleme Alanı
        self.text_hikaye = tk.Text(self.root, height=15, font=("Segoe UI", 11), wrap="word", padx=15, pady=15, bg="#F9F9F9")
        self.text_hikaye.pack(pady=10, padx=20, fill="both", expand=True)

        # Kontrol Butonları (Temizle vb.)
        self.btn_temizle = tk.Button(self.root, text="Ekranı Temizle", command=self.ekrani_temizle, font=("Arial", 9))
        self.btn_temizle.pack(pady=5)

        # Kayıtlı Storyler Listesi
        tk.Label(self.root, text="📚 Hikaye Kütüphanem (Tıklayıp Oku)", font=("Arial", 10, "bold")).pack(pady=(10, 0))
        
        # Listbox ve Scrollbar
        frame_liste = tk.Frame(self.root)
        frame_liste.pack(pady=10, padx=20, fill="both")
        
        self.scrollbar = tk.Scrollbar(frame_liste)
        self.scrollbar.pack(side="right", fill="y")

        self.listbox_hikayeler = tk.Listbox(frame_liste, height=6, font=("Arial", 10), yscrollcommand=self.scrollbar.set)
        self.listbox_hikayeler.pack(side="left", fill="both", expand=True)
        self.scrollbar.config(command=self.listbox_hikayeler.yview)
        
        self.listbox_hikayeler.bind('<<ListboxSelect>>', self.hikaye_getir)

    def ekrani_temizle(self):
        self.entry_konu.delete(0, tk.END)
        self.text_hikaye.delete("1.0", tk.END)

    def hikaye_uret(self):
        konu = self.entry_konu.get()
        if not konu:
            messagebox.showwarning("Uyarı", "Lütfen yeni bir konu girin!")
            return

        self.btn_uret.config(text="🤖 Yazıyor...", state="disabled")
        self.root.update()

        try:
            # AI'ya tam özgürlük veriyoruz
            prompt = (f"'{konu}' konusu üzerine yaratıcı bir hikaye yaz. "
                      "Zamanı, mekanı ve türü tamamen sen seç. "
                      "Hikayenin en başına 'BAŞLIK: [Buraya Başlık]' eklemeyi unutma.")
            
            response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
            tam_metin = response.text

            if "BAŞLIK:" in tam_metin:
                parcalar = tam_metin.split("\n", 1)
                baslik = parcalar[0].replace("BAŞLIK:", "").strip()
                icerik = parcalar[1].strip()
            else:
                baslik = konu[:20] + "..."
                icerik = tam_metin

            # Ekrana yazdır
            self.text_hikaye.delete("1.0", tk.END)
            self.text_hikaye.insert(tk.END, f"🌟 {baslik.upper()} 🌟\n\n{icerik}")

            # Veritabanına yeni story'yi ekle
            self.veritabani_kaydet(baslik, icerik)
            self.veritabani_listele()
            
        except Exception as e:
            messagebox.showerror("Hata", f"Yapay zeka ile bağlantı kurulamadı: {e}")
        finally:
            self.btn_uret.config(text="✍️ Hikaye Üret", state="normal")

    def veritabani_kaydet(self, baslik, icerik):
        conn = sqlite3.connect('stories.db')
        conn.execute('INSERT INTO stories (title, content) VALUES (?, ?)', (baslik, icerik))
        conn.commit()
        conn.close()

    def veritabani_listele(self):
        self.listbox_hikayeler.delete(0, tk.END)
        conn = sqlite3.connect('stories.db')
        cursor = conn.execute('SELECT id, title FROM stories ORDER BY id DESC')
        for row in cursor:
            # Story'leri daha şık listele
            self.listbox_hikayeler.insert(tk.END, f"ID: {row[0]} | {row[1]}")
        conn.close()

    def hikaye_getir(self, event):
        selection = self.listbox_hikayeler.curselection()
        if selection:
            item = self.listbox_hikayeler.get(selection[0])
            # ID kısmını ayıklıyoruz (ID: 5 | Başlık formatından)
            hikaye_id = item.split(" | ")[0].replace("ID: ", "")
            
            conn = sqlite3.connect('stories.db')
            cursor = conn.execute('SELECT title, content FROM stories WHERE id = ?', (hikaye_id,))
            row = cursor.fetchone()
            if row:
                self.text_hikaye.delete("1.0", tk.END)
                self.text_hikaye.insert(tk.END, f"🌟 {row[0].upper()} 🌟\n\n{row[1]}")
            conn.close()

if __name__ == "__main__":
    root = tk.Tk()
    app = HikayeUygulamasi(root)
    root.mainloop()