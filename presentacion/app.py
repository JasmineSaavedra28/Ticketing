import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk
from concurrent.futures import ThreadPoolExecutor

from control.servicios import Servicio
from dominio.modelos import EstadoTicket
from persistencia.database import Database


class HitosApp:
    def __init__(self, root):
        self.root=root
        self.root.title("Hitos | Sistema de Ticketing")
        self.root.geometry("1050x680")
        self.root.minsize(850,550)
        self.db=Database()
        self.servicio=Servicio(self.db)
        self.usuario=None
        self.executor=ThreadPoolExecutor(max_workers=2)
        self._estilos()
        self.mostrar_login()
        self.root.protocol("WM_DELETE_WINDOW",self.cerrar)

    def _estilos(self):
        style=ttk.Style()
        try: style.theme_use("clam")
        except tk.TclError: pass
        style.configure("Title.TLabel",font=("Segoe UI",20,"bold"),foreground="#15324b")
        style.configure("Treeview",rowheight=28)

    def limpiar(self):
        for child in self.root.winfo_children(): child.destroy()

    def mostrar_login(self):
        self.limpiar()
        box=ttk.Frame(self.root,padding=40)
        box.place(relx=.5,rely=.5,anchor="center")
        ttk.Label(box,text="Hitos",style="Title.TLabel").grid(row=0,column=0,columnspan=2,pady=(0,8))
        ttk.Label(box,text="Gestión de atención y soporte técnico").grid(row=1,column=0,columnspan=2,pady=(0,22))
        ttk.Label(box,text="Correo").grid(row=2,column=0,sticky="w",pady=5)
        email=ttk.Entry(box,width=34); email.grid(row=2,column=1,pady=5)
        ttk.Label(box,text="Contraseña").grid(row=3,column=0,sticky="w",pady=5)
        password=ttk.Entry(box,width=34,show="•"); password.grid(row=3,column=1,pady=5)
        ttk.Label(box,text="Demo: admin@hitos.local / admin123",foreground="#607080").grid(row=4,column=0,columnspan=2,pady=12)
        ttk.Label(box,text="Cliente: cliente@hitos.local / cliente123 · Técnico: tecnico@hitos.local / tecnico123",foreground="#607080").grid(row=5,column=0,columnspan=2,pady=4)
        def entrar(event=None):
            u=self.servicio.login(email.get(),password.get())
            if not u: messagebox.showerror("Acceso denegado","Correo o contraseña incorrectos."); return
            self.usuario=u; self.mostrar_principal()
        ttk.Button(box,text="Ingresar",command=entrar).grid(row=6,column=0,columnspan=2,pady=16,sticky="ew")
        password.bind("<Return>",entrar)

    def mostrar_principal(self):
        self.limpiar()
        header=ttk.Frame(self.root,padding=(18,12)); header.pack(fill="x")
        ttk.Label(header,text="Hitos",style="Title.TLabel").pack(side="left")
        ttk.Label(header,text=f"{self.usuario['nombre']} · {self.usuario['rol']}").pack(side="left",padx=20)
        ttk.Button(header,text="Cerrar sesión",command=self.mostrar_login).pack(side="right")
        self.tabs=ttk.Notebook(self.root); self.tabs.pack(fill="both",expand=True,padx=16,pady=8)
        self.tab_tickets=ttk.Frame(self.tabs,padding=12); self.tabs.add(self.tab_tickets,text="Tickets"); self._vista_tickets()
        self.tab_productos=ttk.Frame(self.tabs,padding=12); self.tabs.add(self.tab_productos,text="Productos"); self._vista_productos()
        if self.usuario["rol"]=="Admin":
            self.tab_usuarios=ttk.Frame(self.tabs,padding=12); self.tabs.add(self.tab_usuarios,text="Usuarios"); self._vista_usuarios()
        self.tab_notificaciones=ttk.Frame(self.tabs,padding=12); self.tabs.add(self.tab_notificaciones,text="Notificaciones"); self._vista_notificaciones()

    def _tree(self,parent,columns,headings):
        frame=ttk.Frame(parent); frame.pack(fill="both",expand=True,pady=8)
        tree=ttk.Treeview(frame,columns=columns,show="headings",selectmode="browse")
        for col,title,width in headings:
            tree.heading(col,text=title); tree.column(col,width=width,anchor="w")
        scroll=ttk.Scrollbar(frame,orient="vertical",command=tree.yview); tree.configure(yscrollcommand=scroll.set)
        tree.pack(side="left",fill="both",expand=True); scroll.pack(side="right",fill="y")
        return tree

    def _vista_tickets(self):
        top=ttk.Frame(self.tab_tickets); top.pack(fill="x")
        if self.usuario["rol"] in ("Cliente","Admin"): ttk.Button(top,text="Crear ticket",command=self.crear_ticket).pack(side="left")
        ttk.Button(top,text="Actualizar",command=self.cargar_tickets).pack(side="left",padx=6)
        self.ticket_tree=self._tree(self.tab_tickets,("id","estado","cliente","tecnico","producto","fecha"),[("id","#",55),("estado","Estado",115),("cliente","Cliente",145),("tecnico","Técnico",145),("producto","Producto",180),("fecha","Creado",150)])
        bottom=ttk.Frame(self.tab_tickets); bottom.pack(fill="x")
        ttk.Button(bottom,text="Ver conversación e hitos",command=self.ver_ticket).pack(side="left")
        if self.usuario["rol"] in ("Tecnico","Admin"): ttk.Button(bottom,text="Cambiar estado",command=self.cambiar_estado).pack(side="left",padx=6)
        if self.usuario["rol"] in ("Cliente","Admin"): ttk.Button(bottom,text="Cerrar / reabrir",command=self.cerrar_reabrir).pack(side="left")
        self.cargar_tickets()

    def cargar_tickets(self):
        if not hasattr(self,"ticket_tree") or not self.ticket_tree.winfo_exists(): return
        self.ticket_tree.delete(*self.ticket_tree.get_children())
        for t in self.servicio.tickets.listar(self.usuario["id"],self.usuario["rol"]):
            self.ticket_tree.insert("","end",iid=str(t["id"]),values=(t["id"],t["estado"],t["cliente"],t["tecnico"],t["producto"],t["fecha_creacion"]))

    def ticket_seleccionado(self):
        sel=self.ticket_tree.selection()
        if not sel: messagebox.showinfo("Seleccioná un ticket","Elegí un ticket de la lista primero."); return None
        return int(sel[0])

    def crear_ticket(self):
        win=tk.Toplevel(self.root); win.title("Crear ticket"); win.transient(self.root); win.grab_set()
        body=ttk.Frame(win,padding=20); body.pack(fill="both",expand=True)
        productos=self.servicio.catalogo.productos()
        if not productos: messagebox.showinfo("Sin productos","Primero registrá un producto."); win.destroy(); return
        ttk.Label(body,text="Producto").grid(row=0,column=0,sticky="w",pady=6)
        prod=ttk.Combobox(body,state="readonly",width=42,values=[f"{p['id']} · {p['nombre']} ({p['tipo']})" for p in productos]); prod.grid(row=0,column=1,pady=6); prod.current(0)
        ttk.Label(body,text="Descripción del problema").grid(row=1,column=0,sticky="nw",pady=6)
        desc=tk.Text(body,width=44,height=7); desc.grid(row=1,column=1,pady=6)
        def guardar():
            try:
                ticket_id=self.servicio.crear_ticket(self.usuario["id"],productos[prod.current()]["id"],desc.get("1.0","end").strip())
                messagebox.showinfo("Ticket creado",f"Se creó el ticket #{ticket_id} y se asignó un técnico automáticamente."); win.destroy(); self.cargar_tickets()
            except Exception as e: messagebox.showerror("No se pudo crear",self.servicio.manejar_error(e))
        ttk.Button(body,text="Crear",command=guardar).grid(row=2,column=1,sticky="e",pady=8)

    def ver_ticket(self):
        tid=self.ticket_seleccionado()
        if tid is None:return
        data=self.servicio.tickets.detalle(tid)
        if not data: return
        t,mensajes,hitos=data
        if self.usuario["rol"]!="Admin" and self.usuario["id"] not in (t["cliente_id"],t["tecnico_id"]): messagebox.showerror("Acceso denegado","No tenés acceso a este ticket."); return
        win=tk.Toplevel(self.root); win.title(f"Ticket #{tid} · {t['estado']}"); win.geometry("720x570"); win.transient(self.root)
        body=ttk.Frame(win,padding=14); body.pack(fill="both",expand=True)
        ttk.Label(body,text=f"{t['producto']} · {t['estado']}",font=("Segoe UI",14,"bold")).pack(anchor="w")
        ttk.Label(body,text=f"Cliente: {t['cliente']}    Técnico: {t['tecnico']}    Serie: {t['numero_serie']}").pack(anchor="w",pady=4)
        ttk.Label(body,text=f"Descripción: {t['descripcion']}",wraplength=680).pack(anchor="w",pady=5)
        text=tk.Text(body,state="normal",wrap="word",height=18); text.pack(fill="both",expand=True,pady=8)
        text.insert("end","— Conversación —\n")
        for m in mensajes:text.insert("end",f"[{m['fecha_hora']}] {m['remitente']}: {m['contenido']}\n")
        text.insert("end","\n— Hitos —\n")
        for h in hitos:text.insert("end",f"[{h['fecha_hora']}] {h['tipo_evento']}: {h['detalle']} · {h['realizado_por_nombre']}\n")
        text.configure(state="disabled")
        row=ttk.Frame(body); row.pack(fill="x")
        entry=ttk.Entry(row); entry.pack(side="left",fill="x",expand=True)
        def enviar():
            try:self.servicio.enviar_mensaje(tid,self.usuario,entry.get()); entry.delete(0,"end"); win.destroy(); self.ver_ticket(); self.cargar_tickets()
            except Exception as e: messagebox.showerror("No se pudo enviar",self.servicio.manejar_error(e))
        ttk.Button(row,text="Enviar mensaje",command=enviar).pack(side="left",padx=6)

    def cambiar_estado(self):
        tid=self.ticket_seleccionado()
        if tid is None:return
        win=tk.Toplevel(self.root); win.title("Cambiar estado"); win.transient(self.root); win.grab_set()
        box=ttk.Frame(win,padding=20); box.pack()
        combo=ttk.Combobox(box,state="readonly",values=[s.value for s in EstadoTicket]); combo.pack(pady=8); combo.current(1)
        def guardar():
            try:self.servicio.cambiar_estado(tid,EstadoTicket(combo.get()),self.usuario); win.destroy(); self.cargar_tickets()
            except Exception as e:messagebox.showerror("No se pudo cambiar",self.servicio.manejar_error(e))
        ttk.Button(box,text="Guardar",command=guardar).pack()

    def cerrar_reabrir(self):
        tid=self.ticket_seleccionado()
        if tid is None:return
        t=self.servicio.tickets.buscar(tid)
        estado=EstadoTicket.ABIERTO if t["estado"]==EstadoTicket.CERRADO.value else EstadoTicket.CERRADO
        try:
            self.servicio.cambiar_estado(tid,estado,self.usuario)
            messagebox.showinfo("Ticket actualizado","Se registró el cambio y se notificó a las partes."); self.cargar_tickets()
        except Exception as e:messagebox.showerror("No se pudo actualizar",self.servicio.manejar_error(e))

    def _vista_productos(self):
        bar=ttk.Frame(self.tab_productos); bar.pack(fill="x")
        ttk.Label(bar,text="Filtrar por tipo:").pack(side="left")
        tipos=self.servicio.catalogo.tipos()
        self.tipo_filtro=ttk.Combobox(bar,state="readonly",values=["Todos"]+[t["nombre"] for t in tipos],width=28); self.tipo_filtro.pack(side="left",padx=6); self.tipo_filtro.current(0)
        self.tipo_filtro.bind("<<ComboboxSelected>>",lambda e:self.cargar_productos())
        if self.usuario["rol"]=="Admin":ttk.Button(bar,text="Agregar producto",command=self.crear_producto).pack(side="left",padx=6)
        self.producto_tree=self._tree(self.tab_productos,("nombre","tipo","marca","modelo","serie"),[("nombre","Producto",180),("tipo","Tipo",180),("marca","Marca",140),("modelo","Modelo",140),("serie","N.º de serie",180)])
        self.cargar_productos()

    def cargar_productos(self):
        if not hasattr(self,"producto_tree") or not self.producto_tree.winfo_exists():return
        self.producto_tree.delete(*self.producto_tree.get_children())
        tipos=self.servicio.catalogo.tipos(); elegido=self.tipo_filtro.get()
        tipo_id=next((t["id"] for t in tipos if t["nombre"]==elegido),None)
        for p in self.servicio.catalogo.productos(tipo_id):self.producto_tree.insert("","end",values=(p["nombre"],p["tipo"],p["marca"],p["modelo"],p["numero_serie"]))

    def crear_producto(self):
        win=tk.Toplevel(self.root); win.title("Agregar producto"); win.transient(self.root); win.grab_set()
        body=ttk.Frame(win,padding=20); body.pack()
        tipos=self.servicio.catalogo.tipos(); fields={}
        for i,label in enumerate(("Nombre","Marca","Modelo","Número de serie")):
            ttk.Label(body,text=label).grid(row=i,column=0,sticky="w",pady=5); entry=ttk.Entry(body,width=34); entry.grid(row=i,column=1,pady=5); fields[label]=entry
        ttk.Label(body,text="Tipo").grid(row=4,column=0,sticky="w",pady=5)
        tipo=ttk.Combobox(body,state="readonly",values=[t["nombre"] for t in tipos],width=31); tipo.grid(row=4,column=1,pady=5); tipo.current(0)
        def guardar():
            try:
                self.servicio.crear_producto(fields["Nombre"].get(),fields["Marca"].get(),fields["Modelo"].get(),tipos[tipo.current()]["id"],fields["Número de serie"].get())
                win.destroy(); self.cargar_productos(); messagebox.showinfo("Producto guardado","El producto quedó registrado.")
            except Exception as e:messagebox.showerror("No se pudo guardar",self.servicio.manejar_error(e))
        ttk.Button(body,text="Guardar",command=guardar).grid(row=5,column=1,sticky="e",pady=10)

    def _vista_usuarios(self):
        bar=ttk.Frame(self.tab_usuarios); bar.pack(fill="x")
        ttk.Button(bar,text="Agregar usuario",command=self.crear_usuario).pack(side="left")
        self.usuario_tree=self._tree(self.tab_usuarios,("nombre","email","rol","especialidad"),[("nombre","Nombre",200),("email","Correo",260),("rol","Rol",120),("especialidad","Especialidad",220)])
        self.cargar_usuarios()

    def cargar_usuarios(self):
        if not hasattr(self,"usuario_tree") or not self.usuario_tree.winfo_exists():return
        self.usuario_tree.delete(*self.usuario_tree.get_children())
        for u in self.servicio.usuarios.listar():self.usuario_tree.insert("","end",values=(u["nombre"],u["email"],u["rol"],u["especialidad"] or "—"))

    def crear_usuario(self):
        win=tk.Toplevel(self.root); win.title("Agregar usuario"); win.transient(self.root); win.grab_set()
        body=ttk.Frame(win,padding=20); body.pack()
        nombres=("Nombre","Correo","Contraseña"); fields={}
        for i,label in enumerate(nombres):
            ttk.Label(body,text=label).grid(row=i,column=0,sticky="w",pady=5); entry=ttk.Entry(body,width=32,show="•" if label=="Contraseña" else ""); entry.grid(row=i,column=1,pady=5); fields[label]=entry
        ttk.Label(body,text="Rol").grid(row=3,column=0,sticky="w",pady=5); rol=ttk.Combobox(body,state="readonly",values=["Cliente","Tecnico","Admin"],width=29); rol.grid(row=3,column=1,pady=5); rol.current(0)
        ttk.Label(body,text="Especialidad").grid(row=4,column=0,sticky="w",pady=5); tipos=self.servicio.catalogo.tipos(); especialidad=ttk.Combobox(body,state="readonly",values=[t["nombre"] for t in tipos],width=29); especialidad.grid(row=4,column=1,pady=5); especialidad.current(0)
        def guardar():
            try:
                esp=tipos[especialidad.current()]["id"] if rol.get()=="Tecnico" else None
                self.servicio.crear_usuario(fields["Nombre"].get(),fields["Correo"].get(),fields["Contraseña"].get(),rol.get(),esp)
                win.destroy(); self.cargar_usuarios(); messagebox.showinfo("Usuario creado","El usuario quedó registrado.")
            except Exception as e:messagebox.showerror("No se pudo guardar",self.servicio.manejar_error(e))
        ttk.Button(body,text="Guardar",command=guardar).grid(row=5,column=1,sticky="e",pady=10)

    def _vista_notificaciones(self):
        self.notif_tree=self._tree(self.tab_notificaciones,("id","mensaje","fecha","leida"),[("id","#",55),("mensaje","Notificación",540),("fecha","Fecha",170),("leida","Leída",70)])
        ttk.Button(self.tab_notificaciones,text="Marcar seleccionada como leída",command=self.marcar_leida).pack(anchor="w")
        self.cargar_notificaciones()

    def cargar_notificaciones(self):
        if not hasattr(self,"notif_tree") or not self.notif_tree.winfo_exists():return
        self.notif_tree.delete(*self.notif_tree.get_children())
        for n in self.servicio.notificaciones.listar(self.usuario["id"]):self.notif_tree.insert("","end",iid=str(n["id"]),values=(n["id"],n["mensaje"],n["fecha_hora"],"Sí" if n["leida"] else "No"))

    def marcar_leida(self):
        sel=self.notif_tree.selection()
        if not sel:return
        self.servicio.notificaciones.marcar_leida(int(sel[0]),self.usuario["id"]); self.cargar_notificaciones()

    def cerrar(self):
        self.executor.shutdown(wait=False,cancel_futures=True)
        self.root.destroy()


def iniciar():
    root=tk.Tk(); HitosApp(root); root.mainloop()
