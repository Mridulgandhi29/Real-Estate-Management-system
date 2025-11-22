import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from db import properties_col, transactions_col, client
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime, UTC
import csv
import re
from pymongo.errors import OperationFailure
import subprocess
import sys


def stop_app_py():
    """Stop any running app.py Python processes before starting the UI."""
    try:
        if sys.platform == "win32":
            # Use wmic to find all python processes with app.py in their command line
            try:
                result = subprocess.run(
                    ["wmic", "process", "where", "CommandLine like '%app.py%'", "get", "ProcessId", "/format:list"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                for line in result.stdout.split("\n"):
                    if "ProcessId=" in line:
                        try:
                            pid = int(line.split("=")[1].strip())
                            subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True, timeout=2)
                        except (ValueError, Exception):
                            pass
            except Exception:
                # Fallback: try using psutil if available
                try:
                    import psutil
                    for proc in psutil.process_iter(['pid', 'cmdline']):
                        try:
                            if 'app.py' in ' '.join(proc.info['cmdline'] or []):
                                proc.kill()
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
                except ImportError:
                    pass
    except Exception:
        pass


class SimpleUI(tk.Tk):
    def __init__(self):
        super().__init__()
        # Auto-stop any running app.py before starting the UI
        stop_app_py()
        self.title("Real Estate — Simple UI")
        self.geometry("900x580")

        top = ttk.Frame(self)
        top.pack(fill=tk.X, padx=8, pady=8)

        ttk.Label(top, text="City/Title filter:").pack(side=tk.LEFT)
        self.filter_var = tk.StringVar()
        self.filter_entry = ttk.Entry(top, textvariable=self.filter_var, width=24)
        self.filter_entry.pack(side=tk.LEFT, padx=(6, 4))
        self.filter_entry.bind("<Return>", lambda e: self.apply_filter())
        self.filter_entry.bind("<Escape>", lambda e: self.clear_filter())
        ttk.Button(top, text="Filter", command=self.apply_filter).pack(side=tk.LEFT)
        ttk.Button(top, text="Clear", command=self.clear_filter).pack(side=tk.LEFT, padx=(6, 12))

        ttk.Button(top, text="Create Index", command=self.create_indexes).pack(side=tk.LEFT, padx=4)

        ttk.Button(top, text="Insert", command=self.insert_dialog).pack(side=tk.RIGHT)
        ttk.Button(top, text="Export CSV", command=self.export_csv).pack(side=tk.RIGHT, padx=6)
        ttk.Button(top, text="Refresh", command=self.refresh).pack(side=tk.RIGHT, padx=6)

        # Main area: treeview
        cols = ("_id", "title", "city", "price", "status")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", selectmode="browse")
        for c in cols:
            self.tree.heading(c, text=c)
        self.tree.column("_id", width=160)
        self.tree.column("title", width=260)
        self.tree.column("city", width=120)
        self.tree.column("price", width=90, anchor=tk.E)
        self.tree.column("status", width=100)

        self.tree.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        # Bottom controls
        bot = ttk.Frame(self)
        bot.pack(fill=tk.X, padx=8, pady=6)

        ttk.Label(bot, text="Selected ID:").pack(side=tk.LEFT)
        self.sel_id_var = tk.StringVar()
        ttk.Label(bot, textvariable=self.sel_id_var, foreground="blue", width=30).pack(side=tk.LEFT, padx=(6, 12))

        ttk.Label(bot, text="New price:").pack(side=tk.LEFT)
        self.new_price_var = tk.StringVar()
        ttk.Entry(bot, textvariable=self.new_price_var, width=12).pack(side=tk.LEFT, padx=(6, 8))
        self.update_btn = ttk.Button(bot, text="Update Price", command=self.update_price, state=tk.DISABLED)
        self.update_btn.pack(side=tk.LEFT)

        self.delete_btn = ttk.Button(bot, text="Delete", command=self.delete_property, state=tk.DISABLED)
        self.delete_btn.pack(side=tk.RIGHT)
        self.purchase_btn = ttk.Button(bot, text="Purchase", command=self.purchase_property, state=tk.DISABLED)
        self.purchase_btn.pack(side=tk.RIGHT, padx=6)

        # Status bar at bottom
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN).pack(fill=tk.X, side=tk.BOTTOM)

        # initial load
        self.current_filter = None
        self.load_items()

    def set_status(self, text):
        # small transient status using window title
        self.title(f"Real Estate — Simple UI    {text}")

    def load_items(self, filter_text=None):
        """Load up to 200 items (to keep UI responsive). Case-insensitive partial match on city."""
        self.tree.delete(*self.tree.get_children())
        q = {}
        if filter_text:
            pat = re.escape(filter_text)
            # match either city or title (case-insensitive partial match)
            q = {"$or": [{"city": {"$regex": pat, "$options": "i"}}, {"title": {"$regex": pat, "$options": "i"}}]}
        try:
            docs = list(properties_col.find(q).sort("price", 1).limit(200))
            for d in docs:
                self.tree.insert("", tk.END, values=(str(d.get("_id")), d.get("title"), d.get("city"), d.get("price"), d.get("status")))
            self.current_filter = filter_text
            self.set_status(f"Loaded {len(docs)} items")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load items: {e}")

    def apply_filter(self):
        txt = self.filter_var.get().strip()
        if not txt:
            messagebox.showinfo("Info", "Enter a city to filter")
            return
        self.load_items(filter_text=txt)

    def clear_filter(self):
        self.filter_var.set("")
        self.load_items(filter_text=None)

    def refresh(self):
        """Reload the current items with existing filter."""
        self.load_items(filter_text=self.current_filter)

    def on_select(self, event):
        sel = self.tree.selection()
        if not sel:
            self.sel_id_var.set("")
            self.update_btn.config(state=tk.DISABLED)
            self.delete_btn.config(state=tk.DISABLED)
            self.purchase_btn.config(state=tk.DISABLED)
            return
        vals = self.tree.item(sel[0], "values")
        _id = vals[0]
        self.sel_id_var.set(_id)
        # Enable action buttons when a property is selected
        self.update_btn.config(state=tk.NORMAL)
        self.delete_btn.config(state=tk.NORMAL)
        self.purchase_btn.config(state=tk.NORMAL)

    def insert_dialog(self):
        dlg = tk.Toplevel(self)
        dlg.title("Insert Property")
        dlg.geometry("360x220")
        dlg.transient(self)
        dlg.grab_set()

        ttk.Label(dlg, text="Title:").pack(anchor=tk.W, padx=8, pady=(8, 0))
        title_v = tk.StringVar()
        ttk.Entry(dlg, textvariable=title_v, width=40).pack(padx=8, fill=tk.X)

        ttk.Label(dlg, text="City:").pack(anchor=tk.W, padx=8, pady=(8, 0))
        city_v = tk.StringVar()
        ttk.Entry(dlg, textvariable=city_v, width=40).pack(padx=8, fill=tk.X)

        ttk.Label(dlg, text="Price:").pack(anchor=tk.W, padx=8, pady=(8, 0))
        price_v = tk.StringVar()
        ttk.Entry(dlg, textvariable=price_v, width=40).pack(padx=8, fill=tk.X)

        def do_insert():
            title = title_v.get().strip()
            city = city_v.get().strip()
            price_str = price_v.get().strip()

            if not title or not city or not price_str:
                messagebox.showerror("Error", "Title, city, and price are required")
                return

            try:
                price = int(price_str)
                if price < 0:
                    messagebox.showerror("Error", "Price cannot be negative")
                    return
            except ValueError:
                messagebox.showerror("Error", "Price must be a valid number")
                return

            doc = {
                "title": title,
                "city": city,
                "price": price,
                "status": "available",
                "created_at": datetime.now(UTC)
            }
            try:
                res = properties_col.insert_one(doc)
                messagebox.showinfo("Inserted", f"Inserted id: {res.inserted_id}")
                dlg.destroy()
                self.refresh()
            except Exception as e:
                messagebox.showerror("Error", f"Insert failed: {e}")

        ttk.Button(dlg, text="Insert", command=do_insert).pack(pady=12)

    def update_price(self):
        _id = self.sel_id_var.get().strip()
        if not _id:
            messagebox.showinfo("Info", "Select a property first")
            return
        try:
            newp = int(self.new_price_var.get())
            if newp < 0:
                messagebox.showerror("Error", "Price cannot be negative")
                return
        except ValueError:
            messagebox.showerror("Error", "Enter a valid number for price")
            return
        try:
            obj_id = ObjectId(_id)
        except InvalidId:
            messagebox.showerror("Error", "Invalid property id")
            return
        try:
            r = properties_col.update_one({"_id": obj_id}, {"$set": {"price": newp}})
            messagebox.showinfo("Updated", f"Modified: {r.modified_count}")
            self.new_price_var.set("")  # Clear the input after successful update
            self.refresh()
        except Exception as e:
            messagebox.showerror("Error", f"Update failed: {e}")

    def delete_property(self):
        _id = self.sel_id_var.get().strip()
        if not _id:
            messagebox.showinfo("Info", "Select a property first")
            return
        if not messagebox.askyesno("Confirm", "Delete selected property?"):
            return
        try:
            r = properties_col.delete_one({"_id": ObjectId(_id)})
            messagebox.showinfo("Deleted", f"Deleted count: {r.deleted_count}")
            self.load_items(filter_text=self.current_filter)
        except Exception as e:
            messagebox.showerror("Error", f"Delete failed: {e}")

    def export_csv(self):
        try:
            docs = list(properties_col.find({}))
            if not docs:
                messagebox.showinfo("Info", "No documents to export")
                return
            fieldnames = set()
            rows = []
            for d in docs:
                row = {}
                for k, v in d.items():
                    row[k] = str(v) if k == "_id" else v
                    fieldnames.add(k)
                rows.append(row)
            fieldnames = list(fieldnames)
            path = "properties_export.csv"
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for r in rows:
                    writer.writerow(r)
            messagebox.showinfo("Exported", f"Exported to {path}")
        except Exception as e:
            messagebox.showerror("Error", f"Export failed: {e}")

    def purchase_property(self):
        _id = self.sel_id_var.get().strip()
        if not _id:
            messagebox.showinfo("Info", "Select a property first")
            return
        buyer = simpledialog.askstring("Buyer name", "Enter buyer name:")
        if not buyer:
            return
        try:
            price = int(simpledialog.askstring("Offer price", "Enter offer price:"))
        except Exception:
            messagebox.showerror("Error", "Offer price must be a number")
            return
        try:
            # Try transactional path first
            try:
                with client.start_session() as session:
                    with session.start_transaction():
                        r = properties_col.update_one({"_id": ObjectId(_id), "status": "available"}, {"$set": {"status": "sold"}}, session=session)
                        if r.modified_count == 0:
                            raise Exception("Property not available")
                        transactions_col.insert_one({"property_id": ObjectId(_id), "buyer_name": buyer, "price": price, "date": datetime.now(UTC)}, session=session)
                messagebox.showinfo("Success", "Purchase recorded (transaction)")
                self.load_items(filter_text=self.current_filter)
                return
            except OperationFailure:
                # fallback to non-transactional flow for standalone MongoDB
                pass

            # Non-transactional fallback: perform conditional update then insert
            r = properties_col.update_one({"_id": ObjectId(_id), "status": "available"}, {"$set": {"status": "sold"}})
            if r.modified_count == 0:
                raise Exception("Property not available")
            try:
                transactions_col.insert_one({"property_id": ObjectId(_id), "buyer_name": buyer, "price": price, "date": datetime.now(UTC)})
                messagebox.showinfo("Success", "Purchase recorded (no transactions available on this server)")
            except Exception as ie:
                messagebox.showwarning("Partial Success", f"Property marked sold but failed to record transaction: {ie}")
            self.load_items(filter_text=self.current_filter)
        except Exception as e:
            messagebox.showerror("Transaction failed", f"{e}\n(Transactions require a replica set or Atlas for full atomicity)")

    def create_indexes(self):
        """Create database indexes on city and price for faster queries."""
        try:
            idx_city = properties_col.create_index([("city", 1)])
            idx_price = properties_col.create_index([("price", 1)])
            messagebox.showinfo("Indexes Created", f"Created indexes:\n• city: {idx_city}\n• price: {idx_price}")
            self.set_status("Indexes created successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create indexes: {e}")


if __name__ == "__main__":
    app = SimpleUI()
    app.mainloop()
