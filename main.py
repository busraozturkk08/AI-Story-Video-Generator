import tkinter as tk 
from tkinter import ttk, messagebox
import sqlite3
import os
from dotenv import load_dotenv
from google import genai
from PIL import Image, ImageTk 
import requests 
from io import BytesIO
from urllib.parse import quote

# .env dosyasındaki değişkenleri yükle
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

class HikayeUygulamasi:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Hikaye & Video Atölyesi")
        # Ekranı yatay ve geniş yapıyoruz
        self.root.geometry("1200x800")
        
        self.temalar = {
            "Bilim Kurgu": {"bg": "#E3F2FD", "fg": "#0D47A1"},
            "Korku": {"bg": "#263238", "fg": "#FF5252"},
            "Macera": {"bg": "#F1F8E9", "fg": "#33691E"},
            "Dram": {"bg": "#F3E5F5", "fg": "#4A148C"},
            "Komedi": {"bg": "#FFFDE7", "fg": "#F57F17"},
            "Varsayılan": {"bg": "#F9F9F9", "fg": "#333333"}
        }
        self.loaded_images = []
        self.veritabani_hazirla()       
        self.arayuz_olustur()
        self.veritabani_listele()
 

    def veritabani_hazirla(self):
        conn = sqlite3.connect('stories.db')
        conn.execute('''CREATE TABLE IF NOT EXISTS stories 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                      title TEXT, 
                      content TEXT,
                      category TEXT)''')
        conn.commit()
        conn.close()

    def arayuz_olustur(self):
        # --- ANA TAŞIYICI (Sol ve Sağ Paneller) ---
        self.ana_frame = tk.Frame(self.root)
        self.ana_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # --- SOL PANEL (Girişler, Hikaye ve Kütüphane) ---
        self.sol_panel = tk.Frame(self.ana_frame, width=500)
        self.sol_panel.pack(side="left", fill="both", expand=True, padx=5)

        tk.Label(self.sol_panel, text="🎭 Hikaye Atölyesi", font=("Arial", 18, "bold")).pack(pady=5)
        
        # Konu Girişi
        frame_giris = tk.Frame(self.sol_panel)
        frame_giris.pack(pady=5, fill="x")
        tk.Label(frame_giris, text="Konu:").pack(side="left")
        self.entry_konu = tk.Entry(frame_giris, font=("Arial", 12))
        self.entry_konu.pack(side="left", padx=10, expand=True, fill="x")
        self.btn_uret = tk.Button(frame_giris, text="✨ Üret", bg="#4CAF50", fg="white", command=self.hikaye_uret)
        self.btn_uret.pack(side="right")

        # Kategori ve Metin Alanı
        self.lbl_kategori = tk.Label(self.sol_panel, text="Tür: -", font=("Arial", 10, "bold"))
        self.lbl_kategori.pack()
        self.text_hikaye = tk.Text(self.sol_panel, height=12, font=("Segoe UI", 11), wrap="word", padx=10, pady=10)
        self.text_hikaye.pack(pady=5, fill="both", expand=True)

        # Kütüphane Bölümü (Sol Alt)
        tk.Label(self.sol_panel, text="📚 Kütüphane", font=("Arial", 10, "bold")).pack(pady=(10,0))
        self.listbox_hikayeler = tk.Listbox(self.sol_panel, height=6)
        self.listbox_hikayeler.pack(pady=5, fill="x")
        self.listbox_hikayeler.bind('<<ListboxSelect>>', self.hikaye_getir)

        # --- SAĞ PANEL (Görseller ve Video) ---
        self.sag_panel = tk.Frame(self.ana_frame, width=650, bg="#f0f0f0")
        self.sag_panel.pack(side="right", fill="both", expand=True, padx=5)

        # Üst Kısım: 4 Görsel (2x2 Izgara)
        tk.Label(self.sag_panel, text="🖼️ Üretilen Görseller (Story 3)", font=("Arial", 12, "bold"), bg="#f0f0f0").pack(pady=5)
        self.frame_gorseller = tk.Frame(self.sag_panel, bg="#f0f0f0")
        self.frame_gorseller.pack()

        self.gorsel_etiketleri = []
        # arayuz_olustur içindeki döngü:
        for r in range(2):
            for c in range(2):
                # width ve height değerlerini sildik, sadece görsel odaklı yaptık
                lbl = tk.Label(self.frame_gorseller, relief="sunken", bg="white") 
                lbl.grid(row=r, column=c, padx=10, pady=10)
                self.gorsel_etiketleri.append(lbl)

        # Alt Kısım: Video Oynatıcı Alanı
        tk.Label(self.sag_panel, text="🎬 Final Video (Story 5, 6, 7)", font=("Arial", 12, "bold"), bg="#f0f0f0").pack(pady=10)
        self.video_alani = tk.Label(self.sag_panel, text="Video Üretildiğinde Burada Oynatılacak", relief="solid", bg="black", fg="white", width=60, height=12)
        self.video_alani.pack(pady=5)
        
        self.btn_video_uret = tk.Button(self.sag_panel, text="🎞️ Videoyu Oluştur", bg="#2196F3", fg="white", font=("Arial", 10, "bold"))
        self.btn_video_uret.pack(pady=5)

    def tema_uygula(self, kategori):
        tema = self.temalar.get(kategori, self.temalar["Varsayılan"])
        self.text_hikaye.config(bg=tema["bg"], fg=tema["fg"])
        self.lbl_kategori.config(text=f"Tür: {kategori}", fg=tema["fg"])

    def hikaye_uret(self):
        konu = self.entry_konu.get()
        if not konu: return

        self.btn_uret.config(text="🤖 Yazılıyor...", state="disabled")
        self.root.update()

        try:
            prompt = (f"Konu: {konu}. Bu konuyla ilgili kısa bir hikaye yaz. "
                      "Yanıtın ŞU FORMATTA OLSUN:\n"
                       "KATEGORİ: [Bilim Kurgu, Macera, Korku, Dram veya Komedi seçeneklerinden biri]\n"
                       "KARAKTER: [Ana karakterin kısa açıklaması]\n"
                       "BAŞLIK: [Hikaye Başlığı]\n"
                       "İÇERİK: [Hikaye Metni]")
            
            response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
            raw_text = response.text

            kategori, baslik, icerik = "Dram", konu, raw_text
            karakter = "main character"
            lines = raw_text.split("\n")
            for line in lines:
                if line.startswith("KATEGORİ:"): kategori = line.replace("KATEGORİ:", "").strip()
                elif line.startswith("KARAKTER:"):karakter = line.replace("KARAKTER:", "").strip()
                elif line.startswith("BAŞLIK:"): baslik = line.replace("BAŞLIK:", "").strip()
            
            if "İÇERİK:" in raw_text:
                icerik = raw_text.split("İÇERİK:")[1].strip()

            self.text_hikaye.delete("1.0", tk.END)
            self.text_hikaye.insert(tk.END, icerik)
            
            self.tema_uygula(kategori)
            self.veritabani_kaydet(baslik, icerik, kategori)
            self.veritabani_listele()
            
            # Hikaye bitince görselleri üretmeye başla
            self.gorselleri_hazirla(icerik,karakter)
            
        except Exception as e:
            messagebox.showerror("Hata", str(e))
        finally:
            self.btn_uret.config(text="✨ Üret", state="normal")

    def gorselleri_hazirla(self, hikaye_metni, karakter):

        cumleler = [c.strip() for c in hikaye_metni.split('.') if c.strip()]

        for i in range(4):
            try:
                self.gorsel_etiketleri[i].config(
                    text=f"Görsel {i+1}\nÜretiliyor...",
                    fg="#2196F3"
                )

                self.root.update()

                sahne = cumleler[i % len(cumleler)]

                # gorselleri_hazirla içindeki döngüde prompt_text kısmını bulun ve şununla değiştirin:

                focus_points = [
                    f"Wide shot of the setting: {sahne}", # 1. Görsel: Genel mekan
                    f"Close up of the character: {karakter}", # 2. Görsel: Karakter detayı
                    f"Important objects and surroundings: {sahne}", # 3. Görsel: Nesneler/Çevre
                    f"Cinematic action scene: {karakter} {sahne}" # 4. Görsel: Aksiyon/Final
                ]

                prompt_text = f"""
                Pixar style 3D render, high resolution.
                {focus_points[i]}
                Vibrant colors, magic atmosphere, masterpiece.
                """
                prompt = quote(prompt_text)
                
                image_url = f"https://image.pollinations.ai/prompt/{prompt}"

                response = requests.get(image_url)

                dosya_yolu = f"outputs/images/gorsel_{i}.png"
                os.makedirs(os.path.dirname(dosya_yolu), exist_ok=True)

                with open(dosya_yolu, "wb") as f:
                    f.write(response.content)

                print("Görsel indirildi:", dosya_yolu) 

                img = Image.open(dosya_yolu)

                print("Image size:", img.size)

                # gorselleri_hazirla içindeki resize satırı:
                img = img.resize((280, 220), Image.Resampling.LANCZOS)

                img_tk = ImageTk.PhotoImage(img)

                lbl = self.gorsel_etiketleri[i]
                lbl.config(image="", text="")

                lbl.config(image=img_tk)

                self.loaded_images.append(img_tk)
                self.gorsel_etiketleri[i].config(image=img_tk, text="")

            except Exception as e:
                print(f"Görsel {i} hatası: {e}")

                self.gorsel_etiketleri[i].config(
                    text=f"Hata!\n{str(e)[:20]}...",
                    fg="red"
                )

            self.root.update_idletasks()
            self.root.after(500)

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
            self.listbox_hikayeler.insert(tk.END, f"[{row[2]}] {row[1]}")
        conn.close()

    def hikaye_getir(self, event):
        selection = self.listbox_hikayeler.curselection()
        if selection:
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