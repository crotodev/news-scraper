import os
import tkinter as tk
import multiprocessing
import crawl
from article_manager import ArticleManager
import sqlite3


def run_crawl():
    t = multiprocessing.Process(target=crawl.crawl)
    t.start()


class Reader:
    def __init__(self) -> None:
        conn = sqlite3.connect(os.path.join(".", "data", "news.db"), timeout=20)

        self.article_manager = ArticleManager(conn)

        self.articles = {article[0]: article for article in self.article_manager.select_all()}

        self.root = tk.Tk()
        self.root.geometry("800x600")

        self.main_frame = tk.PanedWindow(self.root, orient="horizontal")
        self.main_frame.pack(fill="both", expand=True)

        self.sidebar_frame = tk.Frame(self.main_frame, bg="grey", width=200)
        self.main_frame.add(self.sidebar_frame)

        self.scrollbar = tk.Scrollbar(self.sidebar_frame)
        self.scrollbar.pack(side='right', fill='y')

        self.button_canvas = tk.Canvas(self.sidebar_frame, yscrollcommand=self.scrollbar.set)
        self.button_canvas.pack(side='left', fill='both', expand=True)

        self.scrollbar.config(command=self.button_canvas.yview)

        self.button_frame = tk.Frame(self.button_canvas)
        self.button_canvas.create_window((0,0), window=self.button_frame, anchor='nw')

        self.crawl_button = tk.Button(
            self.sidebar_frame, text="Crawl", command=run_crawl
        )
        self.crawl_button.pack(side="bottom")

        self.refresh_button = tk.Button(
            self.sidebar_frame, text="Refresh", command=self.refresh_articles
        )
        self.refresh_button.pack(side="bottom")

        self.content_frame = tk.Frame(self.main_frame, bg="white")
        self.main_frame.add(self.content_frame)

        self.content_text = tk.Text(self.content_frame)
        self.content_text.pack(fill="both", expand=True)

        self.populate_sidebar()

        self.root.mainloop()

    def populate_sidebar(self) -> None:
        for widget in self.button_frame.winfo_children():
            widget.destroy()

        for id_, article in self.articles.items():
            button = tk.Button(
                self.button_frame,
                text=article[1],
                width=20,
                bg="grey",
                justify="left",
                command=lambda id_=id_: self.show_content(id_),
            )
            button.pack()

        self.button_frame.update_idletasks()
        self.button_canvas.config(scrollregion=self.button_canvas.bbox('all'))

    def refresh_articles(self) -> None:
        self.articles = {article[0]: article for article in self.article_manager.select_all()}
        self.populate_sidebar()

    def show_content(self, id_: int) -> None:
        article = self.articles[id_]
        self.content_text.delete("1.0", tk.END)
        self.content_text.insert(tk.END, article[3])



if __name__ == "__main__":
    Reader()
