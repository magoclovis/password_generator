import tkinter as tk
from tkinter import messagebox, ttk
import sqlite3
import random
import string
from cryptography.fernet import Fernet
import os

# Configuração do Banco de Dados e Criptografia
conn = sqlite3.connect('password_manager.db')
cursor = conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS passwords (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    password TEXT NOT NULL)''')
conn.commit()

# Função para carregar ou gerar uma nova chave de criptografia
def load_or_generate_key():
    if os.path.exists('key.key'):
        with open('key.key', 'rb') as key_file:
            key = key_file.read()
    else:
        key = Fernet.generate_key()
        with open('key.key', 'wb') as key_file:
            key_file.write(key)
    return key

key = load_or_generate_key()
cipher_suite = Fernet(key)

# Função para Gerar Senha
def generate_password(length, use_upper, use_lower, use_numbers, use_special):
    characters = ''
    if use_upper:
        characters += string.ascii_uppercase
    if use_lower:
        characters += string.ascii_lowercase
    if use_numbers:
        characters += string.digits
    if use_special:
        characters += string.punctuation

    return ''.join(random.choice(characters) for _ in range(length))

# Função para Salvar Senha
def save_password(name, password):
    encrypted_password = cipher_suite.encrypt(password.encode()).decode()
    cursor.execute('INSERT INTO passwords (name, password) VALUES (?, ?)', (name, encrypted_password))
    conn.commit()

# Função para Visualizar Senhas
def view_passwords():
    cursor.execute('SELECT id, name, password FROM passwords')
    passwords = cursor.fetchall()
    return passwords

# Função para Deletar Senha
def delete_password(password_id):
    cursor.execute('DELETE FROM passwords WHERE id = ?', (password_id,))
    conn.commit()

# Função para Editar Senha
def edit_password(password_id, new_name, new_password):
    encrypted_password = cipher_suite.encrypt(new_password.encode()).decode()
    cursor.execute('UPDATE passwords SET name = ?, password = ? WHERE id = ?', (new_name, encrypted_password, password_id))
    conn.commit()

# Interface Gráfica
def create_interface():
    def on_generate():
        length = int(length_entry.get())
        use_upper = upper_var.get()
        use_lower = lower_var.get()
        use_numbers = numbers_var.get()
        use_special = special_var.get()

        password = generate_password(length, use_upper, use_lower, use_numbers, use_special)
        password_entry.delete(0, tk.END)
        password_entry.insert(0, password)

    def on_save():
        name = name_entry.get()
        password = password_entry.get()

        if name and password:
            save_password(name, password)
            messagebox.showinfo("Sucesso", "Senha salva com sucesso!")
        else:
            messagebox.showwarning("Erro", "Por favor, preencha todos os campos.")

    def on_view():
        def on_edit():
            selected_item = tree.focus()
            values = tree.item(selected_item, 'values')
            if values:
                password_id = values[0]
                new_name = name_edit_entry.get()
                new_password = password_edit_entry.get()
                if new_name and new_password:
                    edit_password(password_id, new_name, new_password)
                    view_window.destroy()
                    on_view()
                else:
                    messagebox.showwarning("Erro", "Por favor, preencha todos os campos.")

        def on_delete():
            selected_item = tree.focus()
            values = tree.item(selected_item, 'values')
            if values:
                password_id = values[0]
                delete_password(password_id)
                view_window.destroy()
                on_view()

        passwords = view_passwords()

        view_window = tk.Toplevel()
        view_window.title("Senhas Salvas")

        tree = ttk.Treeview(view_window, columns=("ID", "Name", "Password"), show="headings")
        tree.heading("ID", text="ID")
        tree.heading("Name", text="Nome")
        tree.heading("Password", text="Senha")
        tree.column("ID", width=30)
        tree.column("Name", width=150)
        tree.column("Password", width=200)

        for password in passwords:
            password_id, name, encrypted_password = password
            decrypted_password = cipher_suite.decrypt(encrypted_password.encode()).decode()
            tree.insert("", "end", values=(password_id, name, decrypted_password))

        tree.pack()

        tk.Label(view_window, text="Nome (Editar):").pack()
        name_edit_entry = tk.Entry(view_window)
        name_edit_entry.pack()

        tk.Label(view_window, text="Senha (Editar):").pack()
        password_edit_entry = tk.Entry(view_window)
        password_edit_entry.pack()

        tk.Button(view_window, text="Editar Senha", command=on_edit).pack()
        tk.Button(view_window, text="Excluir Senha", command=on_delete).pack()

    # Interface Principal
    root = tk.Tk()
    root.title("Gerenciador de Senhas")

    tk.Label(root, text="Nome (Site/App):").grid(row=0, column=0)
    name_entry = tk.Entry(root)
    name_entry.grid(row=0, column=1)

    tk.Label(root, text="Tamanho da Senha:").grid(row=1, column=0)
    length_entry = tk.Entry(root)
    length_entry.grid(row=1, column=1)

    upper_var = tk.BooleanVar()
    lower_var = tk.BooleanVar()
    numbers_var = tk.BooleanVar()
    special_var = tk.BooleanVar()

    tk.Checkbutton(root, text="Letras Maiúsculas", variable=upper_var).grid(row=2, column=0, sticky="w")
    tk.Checkbutton(root, text="Letras Minúsculas", variable=lower_var).grid(row=3, column=0, sticky="w")
    tk.Checkbutton(root, text="Números", variable=numbers_var).grid(row=4, column=0, sticky="w")
    tk.Checkbutton(root, text="Caracteres Especiais", variable=special_var).grid(row=5, column=0, sticky="w")

    tk.Button(root, text="Gerar Senha", command=on_generate).grid(row=6, column=0)
    password_entry = tk.Entry(root)
    password_entry.grid(row=6, column=1)

    tk.Button(root, text="Salvar Senha", command=on_save).grid(row=7, column=0, columnspan=2)

    tk.Button(root, text="Visualizar Senhas Salvas", command=on_view).grid(row=8, column=0, columnspan=2)

    root.mainloop()

create_interface()

# Fechando a conexão ao fechar o programa
conn.close()
