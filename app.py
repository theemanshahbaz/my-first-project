# ========================= SMART LIBRARY SYSTEM =========================
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta
import csv

# ------------------------- Book Class -------------------------
class Book:
    book_counter = 1000

    def __init__(self, title, author, isbn, category="General",
                 publisher="", year="", copies=1,
                 max_issue_days=15, late_fee_per_day=500):
        self.id = Book.book_counter
        Book.book_counter += 1

        self.title = title
        self.author = author
        self.isbn = isbn
        self.category = category
        self.publisher = publisher
        self.year = year
        self.copies = copies

        self.max_issue_days = max_issue_days
        self.late_fee_per_day = late_fee_per_day

        self.issued_records = []  # [{member_id, issue_date, due_date}]
        self.reservation_queue = []  # [member_id]

    @property
    def available_copies(self):
        return self.copies - len(self.issued_records)

    @property
    def status(self):
        if self.issued_records:
            return f"Issued ({len(self.issued_records)} | {self.available_copies} left)"
        elif self.reservation_queue:
            return f"Reserved ({len(self.reservation_queue)} waiting)"
        return f"Available ({self.available_copies})"

    def issue_book(self, member_id):
        if self.available_copies <= 0:
            if member_id not in self.reservation_queue:
                self.reservation_queue.append(member_id)
                return False, "No copy available. Added to reservation queue."
            return False, "Already in reservation queue."

        issue_date = datetime.now()
        due_date = issue_date + timedelta(days=self.max_issue_days)

        self.issued_records.append({
            "member_id": member_id,
            "issue_date": issue_date,
            "due_date": due_date
        })
        return True, f"Issued successfully. Due: {due_date.strftime('%d-%m-%Y')}"

    def return_book(self, member_id):
        record = next((r for r in self.issued_records if r["member_id"] == member_id), None)
        if not record:
            return False, 0, "This book was not issued to this member."

        overdue_days = (datetime.now() - record["due_date"]).days
        fine = self.late_fee_per_day * overdue_days if overdue_days > 0 else 0

        self.issued_records.remove(record)

        # Auto-issue to next reservation
        if self.reservation_queue and self.available_copies > 0:
            next_member = self.reservation_queue.pop(0)
            self.issue_book(next_member)

        return True, fine, f"Returned. Fine: {fine}"

    def matches(self, query):
        q = query.lower()
        return q in self.title.lower() or q in self.author.lower() or q in self.isbn.lower() or q == str(self.id)

# ------------------------- Library Class -------------------------
class Library:
    def __init__(self):
        self.books = []
        self.members = {}

    # ---------- BOOKS ----------
    def add_book(self, book):
        if any(b.isbn == book.isbn for b in self.books):
            return False, "Duplicate ISBN not allowed."
        self.books.append(book)
        return True, "Book added successfully."

    def delete_book(self, book_id):
        self.books = [b for b in self.books if b.id != book_id]

    def find_book(self, query):
        return next((b for b in self.books if b.matches(query)), None)

    # ---------- MEMBERS ----------
    def add_member(self, mid, data):
        if mid in self.members:
            return False, "Member already exists."
        self.members[mid] = data
        return True, "Member added successfully."

    def delete_member(self, mid):
        if mid in self.members:
            del self.members[mid]

    # ---------- ISSUE / RETURN ----------
    def issue(self, book_query, member_id):
        if member_id not in self.members:
            return "Member not found."

        book = self.find_book(book_query)
        if not book:
            return "Book not found."

        ok, msg = book.issue_book(member_id)
        if ok:
            self.members[member_id]["books"].append(book)
        return msg

    def return_book(self, book_query, member_id):
        book = self.find_book(book_query)
        if not book:
            return "Book not found."

        ok, fine, msg = book.return_book(member_id)
        if ok:
            self.members[member_id]["books"].remove(book)
            self.members[member_id]["total_fines"] += fine
        return msg

    # ---------- DASHBOARD ----------
    def summary(self):
        overdue = sum(
            1 for b in self.books for r in b.issued_records if r["due_date"] < datetime.now()
        )
        return {
            "total_books": sum(b.copies for b in self.books),
            "issued_books": sum(len(b.issued_records) for b in self.books),
            "available_books": sum(b.available_copies for b in self.books),
            "overdue_books": overdue,
            "total_members": len(self.members)
        }

# ------------------------- LOGIN SYSTEM -------------------------
def show_login(root, on_success):
    login_win = tk.Toplevel(root)
    login_win.title("Librarian Login")
    login_win.geometry("400x250")
    login_win.configure(bg="#101820")

    tk.Label(login_win, text="Username:", fg="#00E0FF", bg="#101820").pack(pady=10)
    user_entry = tk.Entry(login_win); user_entry.pack(pady=5)
    tk.Label(login_win, text="Password:", fg="#00E0FF", bg="#101820").pack(pady=10)
    pass_entry = tk.Entry(login_win, show="*"); pass_entry.pack(pady=5)

    def login_action():
        if user_entry.get() == "admin" and pass_entry.get() == "admin123":
            messagebox.showinfo("Login Success", "Welcome Librarian!")
            login_win.destroy()
            on_success()
        else:
            messagebox.showerror("Login Failed", "Invalid Username/Password")

    tk.Button(login_win, text="Login", command=login_action, bg="#00d2ff", fg="#101820", width=15).pack(pady=20)
    login_win.grab_set()
    root.wait_window(login_win)

# ------------------------- GUI APP -------------------------
class LibraryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Library System")
        self.root.geometry("1300x750")
        self.root.configure(bg="#101820")

        self.lib = Library()
        self.load_default_data()

        # Tabs
        self.tabs = ttk.Notebook(root)
        self.tabs.pack(expand=1, fill="both")

        self.dashboard_tab = ttk.Frame(self.tabs)
        self.books_tab = ttk.Frame(self.tabs)
        self.members_tab = ttk.Frame(self.tabs)
        self.issue_tab = ttk.Frame(self.tabs)
        self.report_tab = ttk.Frame(self.tabs)

        self.tabs.add(self.dashboard_tab, text="Dashboard")
        self.tabs.add(self.books_tab, text="Books")
        self.tabs.add(self.members_tab, text="Members")
        self.tabs.add(self.issue_tab, text="Issue / Return")
        self.tabs.add(self.report_tab, text="Reports")

        # Create UI
        self.create_dashboard()
        self.create_books_tab()
        self.create_members_tab()
        self.create_issue_tab()
        self.create_report_tab()
        self.refresh_dashboard()

    # ---------- DEFAULT DATA ----------
    def load_default_data(self):
        self.lib.add_book(Book("Python Programming","John Doe","1111","Programming",copies=3))
        self.lib.add_book(Book("Data Science","Jane Smith","2222","Science",copies=2))
        self.lib.add_member("S001", {
            "name":"Ali","type":"University","department":"CS","uid":"U1001",
            "cnic":"","phone":"","books":[],"total_fines":0
        })
        self.lib.add_member("N001", {
            "name":"Sara","type":"Non-University","department":"","uid":"",
            "cnic":"12345-6789012-3","phone":"03001234567","books":[],"total_fines":0
        })

    # ---------- DASHBOARD ----------
    def create_dashboard(self):
        self.dashboard_lbl = tk.Label(self.dashboard_tab, font=("Segoe UI",18,"bold"), bg="#101820", fg="#00E0FF")
        self.dashboard_lbl.pack(pady=40)

    def refresh_dashboard(self):
        s = self.lib.summary()
        self.dashboard_lbl.config(
            text=(f"📚 Total Books: {s['total_books']}\n"
                  f"📕 Issued: {s['issued_books']}\n"
                  f"📗 Available: {s['available_books']}\n"
                  f"⚠ Overdue: {s['overdue_books']}\n"
                  f"👤 Members: {s['total_members']}"))
        self.root.after(4000, self.refresh_dashboard)

    # ---------- BOOKS TAB ----------
    def create_books_tab(self):
        frame_top = tk.Frame(self.books_tab, bg="#101820")
        frame_top.pack(fill="x", pady=5)

        tk.Label(frame_top, text="Search Book:", fg="#00E0FF", bg="#101820").pack(side="left", padx=5)
        self.book_search_entry = tk.Entry(frame_top)
        self.book_search_entry.pack(side="left", padx=5)
        tk.Button(frame_top, text="Search", command=self.search_books, bg="#00d2ff", fg="#101820").pack(side="left", padx=5)
        tk.Button(frame_top, text="Add Book", command=self.add_book_window, bg="#00d2ff", fg="#101820").pack(side="left", padx=5)

        self.books_tree = ttk.Treeview(self.books_tab, columns=("ID","Title","Author","ISBN","Category","Copies","Available"), show="headings", height=25)
        for c in self.books_tree["columns"]:
            self.books_tree.heading(c, text=c)
            self.books_tree.column(c, width=140, anchor="center")
        self.books_tree.pack(expand=1, fill="both", padx=10)
        self.refresh_books()

    def refresh_books(self):
        self.books_tree.delete(*self.books_tree.get_children())
        for b in self.lib.books:
            self.books_tree.insert("", "end", values=(b.id,b.title,b.author,b.isbn,b.category,b.copies,b.available_copies))

    def search_books(self):
        query = self.book_search_entry.get()
        books = [b for b in self.lib.books if b.matches(query)] if query else self.lib.books
        self.books_tree.delete(*self.books_tree.get_children())
        for b in books:
            self.books_tree.insert("", "end", values=(b.id,b.title,b.author,b.isbn,b.category,b.copies,b.available_copies))

    def add_book_window(self):
        w = tk.Toplevel(self.root)
        w.title("Add Book")
        w.geometry("350x500")
        w.configure(bg="#101820")

        entries = {}
        labels = ["Title","Author","ISBN","Category","Publisher","Year","Copies"]
        for l in labels:
            tk.Label(w,text=l,bg="#101820",fg="white").pack(pady=2)
            entries[l] = tk.Entry(w); entries[l].pack(pady=2)

        def save_book():
            if not entries["Title"].get() or not entries["Author"].get():
                messagebox.showerror("Error","Title and Author required")
                return
            try:
                copies = int(entries["Copies"].get() or 1)
            except:
                copies = 1
            b = Book(
                title=entries["Title"].get(),
                author=entries["Author"].get(),
                isbn=entries["ISBN"].get(),
                category=entries["Category"].get(),
                publisher=entries["Publisher"].get(),
                year=entries["Year"].get(),
                copies=copies
            )
            ok,msg = self.lib.add_book(b)
            messagebox.showinfo("Add Book", msg)
            self.refresh_books()
            w.destroy()

        tk.Button(w,text="Add Book",command=save_book,bg="#00d2ff",fg="#101820").pack(pady=10)

    # ---------- MEMBERS TAB ----------
    def create_members_tab(self):
        frame_top = tk.Frame(self.members_tab, bg="#101820")
        frame_top.pack(fill="x", pady=5)

        tk.Button(frame_top,text="Add Member",command=self.add_member_window,bg="#00d2ff",fg="#101820").pack(side="left", padx=5)
        tk.Label(frame_top,text="Search Member:",fg="#00E0FF",bg="#101820").pack(side="left", padx=5)
        self.member_search_entry = tk.Entry(frame_top)
        self.member_search_entry.pack(side="left", padx=5)
        tk.Button(frame_top,text="Search",command=self.search_members,bg="#00d2ff",fg="#101820").pack(side="left", padx=5)

        self.members_tree = ttk.Treeview(self.members_tab, columns=("ID","Name","Type","Dept","UID","CNIC","Phone","Books","Fine"), show="headings", height=25)
        for c in self.members_tree["columns"]:
            self.members_tree.heading(c,text=c)
            self.members_tree.column(c,width=120, anchor="center")
        self.members_tree.pack(expand=1, fill="both", padx=10)
        self.refresh_members()

    def refresh_members(self):
        self.members_tree.delete(*self.members_tree.get_children())
        for mid,m in self.lib.members.items():
            self.members_tree.insert("", "end", values=(
                mid, m["name"], m["type"], m.get("department",""), m.get("uid",""), m.get("cnic",""), m.get("phone",""), len(m["books"]), m["total_fines"]
            ))

    def search_members(self):
        query = self.member_search_entry.get().lower()
        self.members_tree.delete(*self.members_tree.get_children())
        for mid,m in self.lib.members.items():
            if query in mid.lower() or query in m["name"].lower():
                self.members_tree.insert("", "end", values=(
                    mid, m["name"], m["type"], m.get("department",""), m.get("uid",""), m.get("cnic",""), m.get("phone",""), len(m["books"]), m["total_fines"]
                ))

    def add_member_window(self):
        w = tk.Toplevel(self.root)
        w.title("Add Member")
        w.geometry("350x550")
        w.configure(bg="#101820")

        tk.Label(w,text="Member ID",bg="#101820",fg="white").pack(pady=2)
        mid = tk.Entry(w); mid.pack(pady=2)
        tk.Label(w,text="Name",bg="#101820",fg="white").pack(pady=2)
        name = tk.Entry(w); name.pack(pady=2)

        var = tk.IntVar(value=1)
        def toggle_fields():
            if var.get() == 1:  # University
                dept.config(state="normal")
                uid.config(state="normal")
                cnic.delete(0, tk.END)
                phone.delete(0, tk.END)
                cnic.config(state="disabled")
                phone.config(state="disabled")
            else:  # Non-University
                dept.delete(0, tk.END)
                uid.delete(0, tk.END)
                dept.config(state="disabled")
                uid.config(state="disabled")
                cnic.config(state="normal")
                phone.config(state="normal")

        tk.Radiobutton(w,text="University",variable=var,value=1,bg="#101820",fg="cyan",selectcolor="#101820",command=toggle_fields).pack()
        tk.Radiobutton(w,text="Non-University",variable=var,value=0,bg="#101820",fg="orange",selectcolor="#101820",command=toggle_fields).pack()

        tk.Label(w,text="Department",bg="#101820",fg="white").pack(pady=2)
        dept = tk.Entry(w); dept.pack(pady=2)
        tk.Label(w,text="University ID",bg="#101820",fg="white").pack(pady=2)
        uid = tk.Entry(w); uid.pack(pady=2)
        tk.Label(w,text="CNIC",bg="#101820",fg="white").pack(pady=2)
        cnic = tk.Entry(w); cnic.pack(pady=2)
        tk.Label(w,text="Phone",bg="#101820",fg="white").pack(pady=2)
        phone = tk.Entry(w); phone.pack(pady=2)

        toggle_fields()  # Initialize fields based on default selection

        def save_member():
            member_type = "University" if var.get() == 1 else "Non-University"

            if not mid.get() or not name.get():
                messagebox.showerror("Error", "Member ID and Name required")
                return

            # Special validation
            if member_type == "University":
                if not dept.get() or not uid.get():
                    messagebox.showerror("Error", "University members must have Department and UID")
                    return
            else:  # Non-University
                if not cnic.get() or not phone.get():
                    messagebox.showerror("Error", "Non-University members must have CNIC and Phone")
                    return

            data = {
                "name": name.get(),
                "type": member_type,
                "department": dept.get() if member_type == "University" else "",
                "uid": uid.get() if member_type == "University" else "",
                "cnic": cnic.get() if member_type == "Non-University" else "",
                "phone": phone.get() if member_type == "Non-University" else "",
                "books": [],
                "total_fines": 0
            }
            ok, msg = self.lib.add_member(mid.get(), data)
            messagebox.showinfo("Add Member", msg)
            self.refresh_members()
            w.destroy()

        tk.Button(w,text="Add Member",command=save_member,bg="#00d2ff",fg="#101820").pack(pady=10)

    # ---------- ISSUE / RETURN TAB ----------
    def create_issue_tab(self):
        tk.Label(self.issue_tab,text="Issue / Return Books",font=("Segoe UI",16),fg="#00E0FF",bg="#101820").pack(pady=10)

        frame = tk.Frame(self.issue_tab,bg="#101820"); frame.pack(pady=5)
        tk.Label(frame,text="Member ID:",bg="#101820",fg="white").grid(row=0,column=0,padx=5,pady=5,sticky="e")
        self.issue_member_entry = tk.Entry(frame); self.issue_member_entry.grid(row=0,column=1,padx=5,pady=5)
        tk.Label(frame,text="Book ID / ISBN:",bg="#101820",fg="white").grid(row=1,column=0,padx=5,pady=5,sticky="e")
        self.issue_book_entry = tk.Entry(frame); self.issue_book_entry.grid(row=1,column=1,padx=5,pady=5)

        tk.Button(frame,text="Issue Book",bg="#00d2ff",fg="black",width=15,command=self.issue_book_action).grid(row=2,column=0,pady=10)
        tk.Button(frame,text="Return Book",bg="#ff5500",fg="white",width=15,command=self.return_book_action).grid(row=2,column=1,pady=10)

        tk.Label(self.issue_tab,text="Member's Issued Books:",bg="#101820",fg="#00E0FF",font=("Segoe UI",12)).pack(pady=10)
        self.member_books_tree = ttk.Treeview(self.issue_tab, columns=("Book ID","Title","Due Date","Status"), show="headings", height=8)
        for col in ("Book ID","Title","Due Date","Status"):
            self.member_books_tree.heading(col,text=col)
            self.member_books_tree.column(col,width=150,anchor="center")
        self.member_books_tree.pack(expand=0, fill="x", padx=10)

        tk.Label(self.issue_tab,text="Reservation Queue for Book:",bg="#101820",fg="#00E0FF",font=("Segoe UI",12)).pack(pady=10)
        self.book_reservation_tree = ttk.Treeview(self.issue_tab, columns=("Position","Member ID"), show="headings", height=5)
        for col in ("Position","Member ID"):
            self.book_reservation_tree.heading(col,text=col)
            self.book_reservation_tree.column(col,width=150,anchor="center")
        self.book_reservation_tree.pack(expand=0, fill="x", padx=10)

    def issue_book_action(self):
        member_id = self.issue_member_entry.get().strip()
        book_query = self.issue_book_entry.get().strip()
        if not member_id or not book_query:
            messagebox.showerror("Error","Please provide Member ID and Book ID/ISBN")
            return
        msg = self.lib.issue(book_query, member_id)
        messagebox.showinfo("Issue Book", msg)
        self.refresh_books(); self.refresh_members()
        self.load_member_books(member_id)
        self.load_book_reservation(book_query)

    def return_book_action(self):
        member_id = self.issue_member_entry.get().strip()
        book_query = self.issue_book_entry.get().strip()
        if not member_id or not book_query:
            messagebox.showerror("Error","Please provide Member ID and Book ID/ISBN")
            return
        msg = self.lib.return_book(book_query, member_id)
        messagebox.showinfo("Return Book", msg)
        self.refresh_books(); self.refresh_members()
        self.load_member_books(member_id)
        self.load_book_reservation(book_query)

    def load_member_books(self, member_id):
        self.member_books_tree.delete(*self.member_books_tree.get_children())
        member = self.lib.members.get(member_id)
        if member:
            for b in member["books"]:
                record = next((r for r in b.issued_records if r["member_id"]==member_id), None)
                due_date = record["due_date"].strftime("%d-%m-%Y") if record else ""
                status = "Overdue" if record and datetime.now() > record["due_date"] else "Issued"
                self.member_books_tree.insert("", "end", values=(b.id,b.title,due_date,status))

    def load_book_reservation(self, book_query):
        self.book_reservation_tree.delete(*self.book_reservation_tree.get_children())
        book = self.lib.find_book(book_query)
        if book:
            for idx, mid in enumerate(book.reservation_queue, start=1):
                self.book_reservation_tree.insert("", "end", values=(idx, mid))

    # ---------- REPORT TAB ----------
    def create_report_tab(self):
        tk.Label(self.report_tab,text="Library Reports",font=("Segoe UI",16),fg="#00E0FF",bg="#101820").pack(pady=10)
        self.report_text = tk.Text(self.report_tab,height=25,bg="#1e1e1e",fg="#ffffff")
        self.report_text.pack(expand=1, fill="both", padx=10,pady=10)

        frame_btn = tk.Frame(self.report_tab,bg="#101820"); frame_btn.pack(pady=5)
        tk.Button(frame_btn,text="Refresh Report",bg="#00d2ff",fg="#121212",width=20,command=self.update_report).pack(side="left", padx=5)
        tk.Button(frame_btn,text="Export to CSV",bg="#ff9900",fg="#121212",width=20,command=self.export_report_csv).pack(side="left", padx=5)
        self.update_report()

    def update_report(self):
        self.report_text.delete("1.0", tk.END)
        self.report_text.insert(tk.END,"========== Library Report ==========\n\n")
        for b in self.lib.books:
            self.report_text.insert(tk.END,f"Book ID: {b.id} | {b.title} | Author: {b.author}\n")
            self.report_text.insert(tk.END,f"  Copies: {b.available_copies}/{b.copies} | Status: {b.status}\n")
            if b.issued_records:
                self.report_text.insert(tk.END,"  Issued Records:\n")
                for r in b.issued_records:
                    status = "Overdue" if datetime.now() > r["due_date"] else "On Time"
                    due = r["due_date"].strftime("%d-%m-%Y")
                    self.report_text.insert(tk.END,f"    Member: {r['member_id']} | Due: {due} | Status: {status}\n")
            if b.reservation_queue:
                self.report_text.insert(tk.END,f"  Reservation Queue: {b.reservation_queue}\n")
            self.report_text.insert(tk.END,"\n")
        s = self.lib.summary()
        self.report_text.insert(tk.END,"---------- Summary ----------\n")
        self.report_text.insert(tk.END,f"Total Books: {s['total_books']}\n")
        self.report_text.insert(tk.END,f"Issued Books: {s['issued_books']}\n")
        self.report_text.insert(tk.END,f"Available Books: {s['available_books']}\n")
        self.report_text.insert(tk.END,f"Overdue Books: {s['overdue_books']}\n")
        self.report_text.insert(tk.END,f"Total Members: {s['total_members']}\n")
        self.root.after(5000,self.update_report)

    def export_report_csv(self):
        filename = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files","*.csv")])
        if not filename: return
        with open(filename,"w",newline='',encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Book ID","Title","Author","Copies","Available","Issued To","Reservation Queue"])
            for b in self.lib.books:
                issued_data = []
                for r in b.issued_records:
                    status = "Overdue" if datetime.now() > r["due_date"] else "On Time"
                    due = r["due_date"].strftime("%d-%m-%Y")
                    issued_data.append(f"{r['member_id']} (Due: {due}, {status})")
                res_queue = ", ".join(b.reservation_queue)
                writer.writerow([b.id,b.title,b.author,b.copies,b.available_copies,"; ".join(issued_data),res_queue])
        messagebox.showinfo("Export CSV",f"Report exported successfully to {filename}")

# ------------------------- RUN APP -------------------------
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # Hide main window initially
    root.title("Smart Library System")
    root.geometry("1300x750")  # Default size
    root.resizable(True, True)  # Allow maximize/minimize

    def start_app():
        root.deiconify()  # Show main window after login
        LibraryApp(root)

    show_login(root, start_app)
    root.mainloop()
