import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk, simpledialog
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
        ttk.Label(box,text="GestiÃ³n de atenciÃ³n y soporte tÃ©cnico").grid(row=1,column=0,columnspan=2,pady=(0,22))
        ttk.Label(box,text="Correo").grid(row=2,column=0,sticky="w",pady=5)
        email=ttk.Entry(box,width=34); email.grid(row=2,column=1,pady=5)
        ttk.Label(box,text="ContraseÃ±a").grid(row=3,column=0,sticky="w",pady=5)
        password=ttk.Entry(box,width=34,show="â€¢"); password.grid(row=3,column=1,pady=5)
        ttk.Label(box,text="Demo: admin@hitos.local / admin123",foreground="#607080").grid(row=4,column=0,columnspan=2,pady=12)
        ttk.Label(box,text="Cliente: cliente@hitos.local / cliente123 Â· TÃ©cnico: tecnico@hitos.local / tecnico123",foreground="#607080").grid(row=5,column=0,columnspan=2,pady=4)
        def entrar(event=None):
            u=self.servicio.login(email.get(),password.get())
            if not u: messagebox.showerror("Acceso denegado","Correo o contraseÃ±a incorrectos."); return
            self.usuario=u; self.mostrar_principal()
        ttk.Button(box,text="Ingresar",command=entrar).grid(row=6,column=0,columnspan=2,pady=16,sticky="ew")
        password.bind("<Return>",entrar)

    def mostrar_principal(self):
        self.limpiar()
        header=ttk.Frame(self.root,padding=(18,12)); header.pack(fill="x")
        ttk.Label(header,text="Hitos",style="Title.TLabel").pack(side="left")
        ttk.Label(header,text=f"{self.usuario['nombre']} Â· {self.usuario['rol']}").pack(side="left",padx=20)
        ttk.Button(header,text="Cerrar sesiÃ³n",command=self.mostrar_login).pack(side="right")
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
        self.ticket_tree=self._tree(self.tab_tickets,("id","titulo","estado","prioridad","cliente","tecnico","producto","fecha"),[("id","#",45),("titulo","TÃ­tulo",160),("estado","Estado",100),("prioridad","Prioridad",85),("cliente","Cliente",125),("tecnico","TÃ©cnico",125),("producto","Producto",150),("fecha","Creado",140)])
        bottom=ttk.Frame(self.tab_tickets); bottom.pack(fill="x")
        ttk.Button(bottom,text="Ver conversaciÃ³n e hitos",command=self.ver_ticket).pack(side="left")
        if self.usuario["rol"] in ("Tecnico","Admin"): ttk.Button(bottom,text="Cambiar estado",command=self.cambiar_estado).pack(side="left",padx=6)
        if self.usuario["rol"]=="Cliente": ttk.Button(bottom,text="Cerrar / reabrir",command=self.cerrar_reabrir).pack(side="left")
        if self.usuario["rol"]=="Admin":
            ttk.Button(bottom,text="Asignar tÃ©cnico",command=self.asignar_tecnico).pack(side="left",padx=6)
            ttk.Button(bottom,text="Configurar prioridad",command=self.configurar_prioridad).pack(side="left")
        self.cargar_tickets()

    def cargar_tickets(self):
        if not hasattr(self,"ticket_tree") or not self.ticket_tree.winfo_exists(): return
        self.ticket_tree.delete(*self.ticket_tree.get_children())
        for t in self.servicio.ticket_controller.listar(self.usuario["id"],self.usuario["rol"]):
            self.ticket_tree.insert("","end",iid=str(t["id"]),values=(t["id"],t["titulo"],t["estado"],t["prioridad"],t["cliente"],t["tecnico"],t["producto"],t["fecha_creacion"]))

    def ticket_seleccionado(self):
        sel=self.ticket_tree.selection()
        if not sel: messagebox.showinfo("SeleccionÃ¡ un ticket","ElegÃ­ un ticket de la lista primero."); return None
        return int(sel[0])

    def crear_ticket(self):
        win=tk.Toplevel(self.root); win.title("Crear ticket"); win.transient(self.root); win.grab_set()
        body=ttk.Frame(win,padding=20); body.pack(fill="both",expand=True)
        productos=self.servicio.producto_controller.listar()
        if not productos: messagebox.showinfo("Sin productos","Primero registrÃ¡ un producto."); win.destroy(); return
        ttk.Label(body,text="Producto").grid(row=0,column=0,sticky="w",pady=6)
        prod=ttk.Combobox(body,state="readonly",width=42,values=[f"{p['id']} Â· {p['nombre']} ({p['tipo']})" for p in productos]); prod.grid(row=0,column=1,pady=6); prod.current(0)
        ttk.Label(body,text="TÃ­tulo").grid(row=1,column=0,sticky="w",pady=6)
        titulo=ttk.Entry(body,width=45); titulo.grid(row=1,column=1,pady=6)
        ttk.Label(body,text="Prioridad").grid(row=2,column=0,sticky="w",pady=6)
        prioridad=ttk.Combobox(body,state="readonly",values=["Baja","Media","Alta","Urgente"],width=42); prioridad.grid(row=2,column=1,pady=6); prioridad.set("Media")
        if self.usuario["rol"]!="Admin": prioridad.configure(state="disabled")
        ttk.Label(body,text="DescripciÃ³n del problema").grid(row=3,column=0,sticky="nw",pady=6)
        desc=tk.Text(body,width=44,height=7); desc.grid(row=3,column=1,pady=6)
        def guardar():
            try:
                ticket_id=self.servicio.crear_ticket(self.usuario["id"],productos[prod.current()]["id"],desc.get("1.0","end").strip(),titulo.get(),prioridad.get())
                messagebox.showinfo("Ticket creado",f"Se creÃ³ el ticket #{ticket_id} y se asignÃ³ un tÃ©cnico automÃ¡ticamente."); win.destroy(); self.cargar_tickets()
            except Exception as e: messagebox.showerror("No se pudo crear",self.servicio.manejar_error(e))
        ttk.Button(body,text="Crear",command=guardar).grid(row=4,column=1,sticky="e",pady=8)

    def ver_ticket(self):
        tid=self.ticket_seleccionado()
        if tid is None:return
        data=self.servicio.ticket_controller.detalle(tid)
        if not data: return
        t,mensajes,hitos=data
        if self.usuario["rol"]!="Admin" and self.usuario["id"] not in (t["cliente_id"],t["tecnico_id"]): messagebox.showerror("Acceso denegado","No tenÃ©s acceso a este ticket."); return
        win=tk.Toplevel(self.root); win.title(f"Ticket #{tid} Â· {t['estado']}"); win.geometry("720x570"); win.transient(self.root)
        body=ttk.Frame(win,padding=14); body.pack(fill="both",expand=True)
        ttk.Label(body,text=f"{t['titulo']} Â· {t['estado']} Â· Prioridad: {t['prioridad']}",font=("Segoe UI",14,"bold")).pack(anchor="w")
        ttk.Label(body,text=f"Cliente: {t['cliente']}    TÃ©cnico: {t['tecnico']}    Serie: {t['numero_serie']}").pack(anchor="w",pady=4)
        ttk.Label(body,text=f"Producto: {t['producto']} Â· DescripciÃ³n: {t['descripcion']}",wraplength=680).pack(anchor="w",pady=5)
        if t["fecha_cierre"]: ttk.Label(body,text=f"Cerrado: {t['fecha_cierre']}").pack(anchor="w")
        text=tk.Text(body,state="normal",wrap="word",height=18); text.pack(fill="both",expand=True,pady=8)
        text.insert("end","â€” ConversaciÃ³n â€”\n")
        for m in mensajes:text.insert("end",f"[{m['fecha_hora']}] {m['remitente']}: {m['contenido']}\n")
        text.insert("end","\nâ€” Hitos â€”\n")
        for h in hitos:text.insert("end",f"[{h['fecha_hora']}] {h['tipo_evento']}: {h['detalle']} Â· {h['realizado_por_nombre']}\n")
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
        t=self.servicio.ticket_controller.buscar(tid)
        if t["estado"]==EstadoTicket.CERRADO.value:
            consulta=simpledialog.askstring("Reabrir ticket", "IngresÃ¡ la nueva consulta para justificar la reapertura:", parent=self.root)
            if consulta is None:return
            try:
                self.servicio.reabrir_ticket(tid,self.usuario,consulta)
                messagebox.showinfo("Ticket reabierto","El ticket pasÃ³ a En proceso. Se registrÃ³ el mensaje y se notificÃ³ al tÃ©cnico."); self.cargar_tickets()
            except Exception as e:messagebox.showerror("No se pudo reabrir",self.servicio.manejar_error(e))
            return
        estado=EstadoTicket.CERRADO
        try:
            self.servicio.cambiar_estado(tid,estado,self.usuario)
            messagebox.showinfo("Ticket actualizado","Se registrÃ³ el cambio y se notificÃ³ a las partes."); self.cargar_tickets()
        except Exception as e:messagebox.showerror("No se pudo actualizar",self.servicio.manejar_error(e))

    def asignar_tecnico(self):
        tid=self.ticket_seleccionado()
        if tid is None:return
        ticket=self.servicio.ticket_controller.buscar(tid)
        producto=self.servicio.producto_controller.buscar(ticket["producto_id"])
        tecnicos=[u for u in self.servicio.usuarios.listar("Tecnico") if u["activo"] and u["disponible"] and u["especialidad_id"]==producto["tipo_id"]]
        if not tecnicos:messagebox.showinfo("Sin tÃ©cnicos disponibles","No hay tÃ©cnicos activos y disponibles con la especialidad del producto."); return
        seleccion=simpledialog.askstring("Asignar tÃ©cnico","EscribÃ­ el ID de uno de estos tÃ©cnicos:\n"+"\n".join(f"{u['id']}: {u['nombre']}" for u in tecnicos),parent=self.root)
        if seleccion is None:return
        try:
            self.servicio.asignar_ticket(tid,int(seleccion),self.usuario); self.cargar_tickets()
            messagebox.showinfo("Ticket asignado","Se registrÃ³ la asignaciÃ³n y se notificÃ³ al tÃ©cnico.")
        except Exception as e:messagebox.showerror("No se pudo asignar",self.servicio.manejar_error(e))

    def configurar_prioridad(self):
        tid=self.ticket_seleccionado()
        if tid is None:return
        prioridad=simpledialog.askstring("Configurar prioridad","IngresÃ¡: Baja, Media, Alta o Urgente",parent=self.root)
        if prioridad is None:return
        try:
            self.servicio.configurar_prioridad(tid,prioridad.strip().capitalize(),self.usuario); self.cargar_tickets()
            messagebox.showinfo("Prioridad actualizada","La prioridad quedÃ³ registrada.")
        except Exception as e:messagebox.showerror("No se pudo cambiar",self.servicio.manejar_error(e))

    def _vista_productos(self):
        bar=ttk.Frame(self.tab_productos); bar.pack(fill="x")
        ttk.Label(bar,text="Filtrar por tipo:").pack(side="left")
        tipos=self.servicio.producto_controller.tipos()
        self.tipo_filtro=ttk.Combobox(bar,state="readonly",values=["Todos"]+[t["nombre"] for t in tipos],width=28); self.tipo_filtro.pack(side="left",padx=6); self.tipo_filtro.current(0)
        self.tipo_filtro.bind("<<ComboboxSelected>>",lambda e:self.cargar_productos())
        if self.usuario["rol"]=="Admin":
            ttk.Button(bar,text="Agregar producto",command=self.crear_producto).pack(side="left",padx=6)
            ttk.Button(bar,text="Agregar tipo",command=self.crear_tipo_producto).pack(side="left",padx=6)
        self.producto_tree=self._tree(self.tab_productos,("nombre","tipo","marca","modelo","serie"),[("nombre","Producto",180),("tipo","Tipo",180),("marca","Marca",140),("modelo","Modelo",140),("serie","N.Âº de serie",180)])
        self.cargar_productos()

    def cargar_productos(self):
        if not hasattr(self,"producto_tree") or not self.producto_tree.winfo_exists():return
        self.producto_tree.delete(*self.producto_tree.get_children())
        tipos=self.servicio.producto_controller.tipos(); elegido=self.tipo_filtro.get()
        tipo_id=next((t["id"] for t in tipos if t["nombre"]==elegido),None)
        for p in self.servicio.producto_controller.listar(tipo_id):self.producto_tree.insert("","end",values=(p["nombre"],p["tipo"],p["marca"],p["modelo"],p["numero_serie"]))

    def crear_producto(self):
        win=tk.Toplevel(self.root); win.title("Agregar producto"); win.transient(self.root); win.grab_set()
        body=ttk.Frame(win,padding=20); body.pack()
        tipos=self.servicio.producto_controller.tipos(); fields={}
        for i,label in enumerate(("Nombre","Marca","Modelo","NÃºmero de serie","DescripciÃ³n")):
            ttk.Label(body,text=label).grid(row=i,column=0,sticky="w",pady=5); entry=ttk.Entry(body,width=34); entry.grid(row=i,column=1,pady=5); fields[label]=entry
        ttk.Label(body,text="Tipo").grid(row=5,column=0,sticky="w",pady=5)
        tipo=ttk.Combobox(body,state="readonly",values=[t["nombre"] for t in tipos],width=31); tipo.grid(row=5,column=1,pady=5); tipo.current(0)
        def guardar():
            try:
                self.servicio.crear_producto(fields["Nombre"].get(),fields["Marca"].get(),fields["Modelo"].get(),tipos[tipo.current()]["id"],fields["NÃºmero de serie"].get(),fields["DescripciÃ³n"].get())
                win.destroy(); self.cargar_productos(); messagebox.showinfo("Producto guardado","El producto quedÃ³ registrado.")
            except Exception as e:messagebox.showerror("No se pudo guardar",self.servicio.manejar_error(e))
        ttk.Button(body,text="Guardar",command=guardar).grid(row=6,column=1,sticky="e",pady=10)

    def crear_tipo_producto(self):
        nombre=simpledialog.askstring("Nuevo tipo de producto","Nombre del tipo:",parent=self.root)
        if nombre is None:return
        descripcion=simpledialog.askstring("DescripciÃ³n del tipo","DescripciÃ³n:",parent=self.root) or ""
        try:
            self.servicio.crear_tipo_producto(nombre,descripcion,self.usuario)
            messagebox.showinfo("Tipo creado","El tipo de producto quedÃ³ registrado.")
            self.mostrar_principal()
        except Exception as e:messagebox.showerror("No se pudo crear",self.servicio.manejar_error(e))

    def _vista_usuarios(self):
        bar=ttk.Frame(self.tab_usuarios); bar.pack(fill="x")
        ttk.Button(bar,text="Agregar usuario",command=self.crear_usuario).pack(side="left")
        self.usuario_tree=self._tree(self.tab_usuarios,("nombre","email","rol","especialidad"),[("nombre","Nombre",200),("email","Correo",260),("rol","Rol",120),("especialidad","Especialidad",220)])
        self.cargar_usuarios()

    def cargar_usuarios(self):
        if not hasattr(self,"usuario_tree") or not self.usuario_tree.winfo_exists():return
        self.usuario_tree.delete(*self.usuario_tree.get_children())
        for u in self.servicio.usuarios.listar():self.usuario_tree.insert("","end",values=(u["nombre"],u["email"],u["rol"],u["especialidad"] or "â€”"))

    def crear_usuario(self):
        win=tk.Toplevel(self.root); win.title("Agregar usuario"); win.transient(self.root); win.grab_set()
        body=ttk.Frame(win,padding=20); body.pack()
        nombres=("Nombre","Correo","ContraseÃ±a"); fields={}
        for i,label in enumerate(nombres):
            ttk.Label(body,text=label).grid(row=i,column=0,sticky="w",pady=5); entry=ttk.Entry(body,width=32,show="â€¢" if label=="ContraseÃ±a" else ""); entry.grid(row=i,column=1,pady=5); fields[label]=entry
        ttk.Label(body,text="Rol").grid(row=3,column=0,sticky="w",pady=5); rol=ttk.Combobox(body,state="readonly",values=["Cliente","Tecnico","Admin"],width=29); rol.grid(row=3,column=1,pady=5); rol.current(0)
        ttk.Label(body,text="Especialidad").grid(row=4,column=0,sticky="w",pady=5); tipos=self.servicio.producto_controller.tipos(); especialidad=ttk.Combobox(body,state="readonly",values=[t["nombre"] for t in tipos],width=29); especialidad.grid(row=4,column=1,pady=5); especialidad.current(0)
        def guardar():
            try:
                esp=tipos[especialidad.current()]["id"] if rol.get()=="Tecnico" else None
                self.servicio.crear_usuario(fields["Nombre"].get(),fields["Correo"].get(),fields["ContraseÃ±a"].get(),rol.get(),esp)
                win.destroy(); self.cargar_usuarios(); messagebox.showinfo("Usuario creado","El usuario quedÃ³ registrado.")
            except Exception as e:messagebox.showerror("No se pudo guardar",self.servicio.manejar_error(e))
        ttk.Button(body,text="Guardar",command=guardar).grid(row=5,column=1,sticky="e",pady=10)

    def _vista_notificaciones(self):
        self.notif_tree=self._tree(self.tab_notificaciones,("id","mensaje","fecha","leida"),[("id","#",55),("mensaje","NotificaciÃ³n",540),("fecha","Fecha",170),("leida","LeÃ­da",70)])
        ttk.Button(self.tab_notificaciones,text="Marcar seleccionada como leÃ­da",command=self.marcar_leida).pack(anchor="w")
        self.cargar_notificaciones()

    def cargar_notificaciones(self):
        if not hasattr(self,"notif_tree") or not self.notif_tree.winfo_exists():return
        self.notif_tree.delete(*self.notif_tree.get_children())
        for n in self.servicio.notificacion_controller.listar(self.usuario["id"]):self.notif_tree.insert("","end",iid=str(n["id"]),values=(n["id"],n["mensaje"],n["fecha_hora"],"SÃ­" if n["leida"] else "No"))

    def marcar_leida(self):
        sel=self.notif_tree.selection()
        if not sel:return
        self.servicio.notificacion_controller.marcar_leida(int(sel[0]),self.usuario["id"]); self.cargar_notificaciones()

    def cerrar(self):
        self.executor.shutdown(wait=False,cancel_futures=True)
        self.root.destroy()


def iniciar():
    root=tk.Tk(); HitosApp(root); root.mainloop()

