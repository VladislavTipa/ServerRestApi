import tkinter as tk
from tkinter import ttk, messagebox
from db.meta import load_metadata, get_db_schema_info
from db.db_config import get_engine
from sqlalchemy import Table, select, update

class MainGui:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Управление базой студентов")
        self.root.geometry("1200x800")

        self.engine = get_engine()
        self.metadata = load_metadata()
        self.schema_info = get_db_schema_info()

        self.selected_table_name = None
        self.selected_table: Table = None
        self.edit_mode = False
        self.editing_pk = None

        self.setup_layout()
        self.root.mainloop()

    def setup_layout(self):
        self.left_frame = tk.Frame(self.root, width=300)
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

        tk.Label(self.left_frame, text="Таблицы:", font=("Arial", 14)).pack(pady=5)

        self.table_listbox = tk.Listbox(self.left_frame, font=("Arial", 12))
        self.table_listbox.pack(fill=tk.Y, expand=True)
        self.table_listbox.bind("<<ListboxSelect>>", self.on_table_select)

        for table_name in self.schema_info:
            self.table_listbox.insert(tk.END, table_name)

        self.right_frame = tk.Frame(self.root)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.tree_frame = tk.Frame(self.right_frame)
        self.tree_frame.pack(fill=tk.BOTH, expand=True)

        self.tree_scroll_x = tk.Scrollbar(self.tree_frame, orient="horizontal")
        self.tree_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

        self.tree = ttk.Treeview(self.tree_frame, show="headings", xscrollcommand=self.tree_scroll_x.set)
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind("<Double-1>", self.on_row_double_click)

        self.tree_scroll_x.config(command=self.tree.xview)

        self.fields_frame = tk.Frame(self.right_frame)
        self.fields_frame.pack(fill=tk.X)

        self.entry_vars = {}
        self.entry_widgets = {}

        self.button_frame = tk.Frame(self.right_frame)
        self.button_frame.pack(fill=tk.X)

        self.add_button = tk.Button(self.button_frame, text="Добавить", command=self.add_record)
        self.add_button.pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(self.button_frame, text="Удалить", command=self.delete_record).pack(side=tk.LEFT, padx=5, pady=5)

    def on_table_select(self, event):
        selection = self.table_listbox.curselection()
        if not selection:
            return

        self.selected_table_name = self.table_listbox.get(selection[0])
        self.selected_table = self.metadata.tables[self.selected_table_name]
        self.refresh_table_view()
        self.build_form()

    def refresh_table_view(self):
        self.tree.delete(*self.tree.get_children())
        self.tree["columns"] = [col.name for col in self.selected_table.columns]
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150, anchor="center")

        stmt = select(self.selected_table)
        with self.engine.connect() as conn:
            results = conn.execute(stmt).mappings().all()

        for row in results:
            values = [row[col] for col in self.tree["columns"]]
            self.tree.insert("", tk.END, values=values)

    def build_form(self):
        for widget in self.fields_frame.winfo_children():
            widget.destroy()
        self.entry_vars.clear()
        self.entry_widgets.clear()

        fk_map = {
            fk['constrained_columns'][0]: {
                "table": fk['referred_table'],
                "column": fk['referred_columns'][0]
            }
            for fk in self.schema_info[self.selected_table_name]["foreign_keys"]
        }

        for col in self.selected_table.columns:
            if col.primary_key:
                continue

            label = tk.Label(self.fields_frame, text=col.name + ":", anchor="w")
            label.pack(fill=tk.X, padx=5)

            if col.name in fk_map:
                related_table = self.metadata.tables[fk_map[col.name]["table"]]
                display_column = self._guess_display_column(related_table)
                combo = ttk.Combobox(self.fields_frame, state="readonly", font=("Arial", 12))
                with self.engine.connect() as conn:
                    stmt = select(related_table.c[fk_map[col.name]["column"]], related_table.c[display_column])
                    rows = conn.execute(stmt).fetchall()
                display_values = [f"{r[0]}. {r[1]}" for r in rows]
                combo["values"] = display_values
                combo.pack(fill=tk.X, padx=5, pady=2)

                self.entry_vars[col.name] = combo
                self.entry_widgets[col.name] = combo
            else:
                var = tk.StringVar()
                entry = tk.Entry(self.fields_frame, textvariable=var, font=("Arial", 12))
                entry.pack(fill=tk.X, padx=5, pady=2)

                self.entry_vars[col.name] = var
                self.entry_widgets[col.name] = entry

    def on_row_double_click(self, event):
        item = self.tree.focus()
        if not item:
            return

        values = self.tree.item(item, "values")
        columns = self.tree["columns"]
        self.edit_mode = True
        self.editing_pk = values[0]

        for i, col in enumerate(columns):
            if col in self.entry_vars:
                widget = self.entry_widgets[col]
                val = values[i]
                if isinstance(widget, ttk.Combobox):
                    for v in widget["values"]:
                        if v.startswith(f"{val}."):
                            widget.set(v)
                            break
                else:
                    widget.delete(0, tk.END)
                    widget.insert(0, val)

        self.add_button.config(text="Сохранить", command=self.update_record)

    def update_record(self):
        values = {}
        for col_name, widget in self.entry_vars.items():
            if isinstance(widget, ttk.Combobox):
                try:
                    selected = widget.get()
                    values[col_name] = int(selected.split(".")[0])
                except Exception:
                    messagebox.showerror("Ошибка", f"Неверный выбор в поле {col_name}")
                    return
            else:
                val = widget.get().strip()
                values[col_name] = None if val == "" else val

        pk_name = [col.name for col in self.selected_table.columns if col.primary_key][0]
        try:
            with self.engine.connect() as conn:
                with conn.begin():
                    conn.execute(
                        update(self.selected_table)
                        .where(self.selected_table.c[pk_name] == self.editing_pk)
                        .values(**values)
                    )
            self.refresh_table_view()
            self.clear_form()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось обновить запись:\n{e}")

    def clear_form(self):
        for widget in self.entry_widgets.values():
            if isinstance(widget, ttk.Combobox):
                widget.set("")
            else:
                widget.delete(0, tk.END)
        self.edit_mode = False
        self.editing_pk = None
        self.add_button.config(text="Добавить", command=self.add_record)

    def add_record(self):
        values = {}
        for col_name, widget in self.entry_vars.items():
            if isinstance(widget, ttk.Combobox):
                try:
                    selected = widget.get()
                    values[col_name] = int(selected.split(".")[0])
                except Exception:
                    messagebox.showerror("Ошибка", f"Неверный выбор в поле {col_name}")
                    return
            else:
                val = widget.get().strip()
                values[col_name] = None if val == "" else val

        try:
            with self.engine.connect() as conn:
                with conn.begin():
                    conn.execute(self.selected_table.insert().values(**values))
            self.refresh_table_view()
            self.clear_form()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось добавить запись:\n{e}")

    def delete_record(self):
        selected_item = self.tree.focus()
        if not selected_item:
            return

        row = self.tree.item(selected_item, "values")
        pk_name = [col.name for col in self.selected_table.columns if col.primary_key][0]
        pk_value = row[0]

        try:
            with self.engine.connect() as conn:
                conn.execute(
                    self.selected_table.delete().where(
                        self.selected_table.c[pk_name] == pk_value
                    )
                )
            self.refresh_table_view()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось удалить запись:\n{e}")

    def _guess_display_column(self, table):
        priority_names = ['name', 'title', 'fio', 'full_name', 'название', 'ФИО']
        for name in priority_names:
            for col in table.columns:
                if name.lower() in col.name.lower():
                    return col.name
        for col in table.columns:
            if str(col.type).startswith("VARCHAR") or str(col.type).startswith("TEXT"):
                return col.name
        return list(table.columns)[1].name
