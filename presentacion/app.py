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
        self.root.title("Sistema de Ticketing")
        self.root.geometry("1100x720")
        self.root.minsize(580,520)
        self.db=Database()
        self.servicio=Servicio(self.db)
        self.usuario=None
        self.executor=ThreadPoolExecutor(max_workers=2)
        self._estilos()
        self.mostrar_login()
        self.root.protocol("WM_DELETE_WINDOW",self.cerrar)
        self.root.bind("<Configure>",self._ajustar_diseno,add="+")

    def _estilos(self):
        style=ttk.Style()
        try: style.theme_use("clam")
        except tk.TclError: pass
        self.root.configure(bg="#f5f6f8")
        style.configure(".",font=("Segoe UI",10),background="#f5f6f8",foreground="#344054")
        style.configure("TFrame",background="#f5f6f8")
        style.configure("Card.TFrame",background="#ffffff")
        style.configure("Title.TLabel",font=("Segoe UI",20,"bold"),foreground="#202b3c",background="#ffffff")
        style.configure("Brand.TLabel",font=("Segoe UI",16,"bold"),foreground="#243449",background="#ffffff")
        style.configure("Subtitle.TLabel",font=("Segoe UI",10),foreground="#7a8798",background="#ffffff")
        style.configure("Section.TLabel",font=("Segoe UI",17,"bold"),foreground="#253247",background="#f5f6f8")
        style.configure("Count.TLabel",font=("Segoe UI",9,"bold"),foreground="#536982",background="#eaf0f5",padding=(10,5))
        style.configure("TButton",padding=(12,8),background="#e9edf2",foreground="#344054",borderwidth=0)
        style.map("TButton",background=[("active","#dce3eb"),("disabled","#edf0f3")])
        style.configure("Primary.TButton",padding=(14,9),background="#527d78",foreground="white",font=("Segoe UI",10,"bold"))
        style.map("Primary.TButton",background=[("active","#426b66")],foreground=[("active","white")])
        style.configure("Nav.TButton",anchor="w",padding=(14,11),background="#ffffff",foreground="#596678",font=("Segoe UI",10))
        style.map("Nav.TButton",background=[("active","#f0f3f6")],foreground=[("active","#26364b")])
        style.configure("NavSelected.TButton",anchor="w",padding=(14,11),background="#eaf1f0",foreground="#3e6d67",font=("Segoe UI",10,"bold"))
        style.map("NavSelected.TButton",background=[("active","#e1ebea")])
        style.configure("Treeview",rowheight=36,background="#ffffff",fieldbackground="#ffffff",foreground="#344054",font=("Segoe UI",10),borderwidth=0)
        style.configure("Treeview.Heading",padding=(10,10),background="#f0f3f6",foreground="#536174",font=("Segoe UI",9,"bold"),relief="flat")
        style.map("Treeview",background=[("selected","#e4eeec")],foreground=[("selected","#263f3b")])
        style.layout("Slim.Vertical.TScrollbar",[("Vertical.Scrollbar.trough",{"sticky":"ns","children":[("Vertical.Scrollbar.thumb",{"expand":"1","sticky":"nswe"})]})])
        style.layout("Slim.Horizontal.TScrollbar",[("Horizontal.Scrollbar.trough",{"sticky":"we","children":[("Horizontal.Scrollbar.thumb",{"expand":"1","sticky":"nswe"})]})])
        style.configure("Slim.Vertical.TScrollbar",background="#c5d0ce",troughcolor="#edf1f0",bordercolor="#edf1f0",darkcolor="#c5d0ce",lightcolor="#c5d0ce",borderwidth=0,arrowsize=0,width=8)
        style.configure("Slim.Horizontal.TScrollbar",background="#c5d0ce",troughcolor="#edf1f0",bordercolor="#edf1f0",darkcolor="#c5d0ce",lightcolor="#c5d0ce",borderwidth=0,arrowsize=0,width=8)
        style.map("Slim.Vertical.TScrollbar",background=[("active","#9fadaa"),("pressed","#82918e")])
        style.map("Slim.Horizontal.TScrollbar",background=[("active","#9fadaa"),("pressed","#82918e")])
        style.configure("TEntry",padding=8)
        style.configure("TCombobox",padding=7)

    def limpiar(self):
        for child in self.root.winfo_children(): child.destroy()

    def mostrar_login(self):
        self._vista_principal_activa=False
        self.limpiar()
        box=ttk.Frame(self.root,padding=38,style="Card.TFrame",relief="solid",borderwidth=1)
        box.place(relx=.5,rely=.5,anchor="center")
        ttk.Label(box,text="Sistema de Ticketing",style="Title.TLabel").grid(row=0,column=0,columnspan=2,pady=(0,8))
        ttk.Label(box,text="Gestión de atención y soporte técnico",style="Subtitle.TLabel").grid(row=1,column=0,columnspan=2,pady=(0,22))
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
        ttk.Button(box,text="Ingresar",style="Primary.TButton",command=entrar).grid(row=6,column=0,columnspan=2,pady=16,sticky="ew")
        password.bind("<Return>",entrar)

    def mostrar_principal(self):
        self.limpiar()
        self._vista_principal_activa=True
        header=ttk.Frame(self.root,padding=(24,14),style="Card.TFrame"); header.pack(fill="x")
        ttk.Label(header,text="Sistema de Ticketing",style="Brand.TLabel").pack(side="left")
        ttk.Label(header,text="Atención y soporte técnico",style="Subtitle.TLabel").pack(side="left",padx=16)
        ttk.Button(header,text="Cerrar sesión",command=self.mostrar_login).pack(side="right")

        self.shell=ttk.Frame(self.root); self.shell.pack(fill="both",expand=True,padx=18,pady=18)
        self.sidebar=ttk.Frame(self.shell,style="Card.TFrame",padding=(12,16)); self.sidebar.pack(side="left",fill="y",padx=(0,16))
        self.menu_label=ttk.Label(self.sidebar,text="MENÚ",style="Subtitle.TLabel"); self.menu_label.pack(anchor="w",padx=10,pady=(2,12))
        self.nav_container=ttk.Frame(self.sidebar,style="Card.TFrame"); self.nav_container.pack(fill="x")
        self.content=ttk.Frame(self.shell); self.content.pack(side="left",fill="both",expand=True)
        self.vistas={}
        self.nav_buttons={}
        nav_items=[("tickets","Tickets"),("productos","Productos")]
        self.tab_tickets=ttk.Frame(self.content,padding=18); self.vistas["tickets"]=self.tab_tickets; self._vista_tickets()
        self.tab_productos=ttk.Frame(self.content,padding=18); self.vistas["productos"]=self.tab_productos; self._vista_productos()
        if self.usuario["rol"]=="Admin":
            nav_items.append(("admin","Administración"))
            self.tab_admin=ttk.Frame(self.content,padding=22); self.vistas["admin"]=self.tab_admin; self._vista_admin()
            nav_items.append(("usuarios","Usuarios"))
            self.tab_usuarios=ttk.Frame(self.content,padding=18); self.vistas["usuarios"]=self.tab_usuarios; self._vista_usuarios()
        nav_items.append(("notificaciones","Notificaciones"))
        self.tab_notificaciones=ttk.Frame(self.content,padding=18); self.vistas["notificaciones"]=self.tab_notificaciones; self._vista_notificaciones()
        for key,label in nav_items:
            button=ttk.Button(self.nav_container,text=label,style="Nav.TButton",command=lambda k=key:self.mostrar_vista(k))
            button.pack(fill="x",pady=3); self.nav_buttons[key]=button
        self.profile=ttk.Frame(self.sidebar,style="Card.TFrame")
        ttk.Separator(self.profile).pack(fill="x",pady=14)
        ttk.Label(self.profile,text=self.usuario["nombre"],font=("Segoe UI",10,"bold"),background="#ffffff",foreground="#344054",wraplength=160).pack(anchor="w",padx=10)
        ttk.Label(self.profile,text=self.usuario["rol"],style="Subtitle.TLabel").pack(anchor="w",padx=10,pady=(3,0))
        self.profile.pack(fill="x")
        vista_inicial="admin" if self.usuario["rol"]=="Admin" else "tickets"
        self.mostrar_vista(vista_inicial)
        self.root.after_idle(self._ajustar_diseno)

    def _ajustar_diseno(self,event=None):
        if not getattr(self,"_vista_principal_activa",False) or not hasattr(self,"shell"):return
        compacto=self.root.winfo_width()<820
        self.sidebar.pack_forget(); self.content.pack_forget()
        if compacto:
            self.shell.pack_configure(padx=8,pady=8)
            self.sidebar.pack(side="top",fill="x",pady=(0,8))
            self.content.pack(side="top",fill="both",expand=True)
            self.menu_label.pack_forget(); self.profile.pack_forget()
            for button in self.nav_buttons.values():button.pack_forget()
            for button in self.nav_buttons.values():button.pack(side="left",fill="x",expand=True,padx=2,pady=0)
            for vista in self.vistas.values():vista.configure(padding=10)
        else:
            self.shell.pack_configure(padx=18,pady=18)
            self.sidebar.pack(side="left",fill="y",padx=(0,16))
            self.content.pack(side="left",fill="both",expand=True)
            self.menu_label.pack(anchor="w",padx=10,pady=(2,12),before=self.nav_container)
            self.profile.pack(fill="x")
            for button in self.nav_buttons.values():button.pack_forget()
            for button in self.nav_buttons.values():button.pack(fill="x",pady=3)
            for vista in self.vistas.values():vista.configure(padding=18)

    def mostrar_vista(self,nombre):
        for vista in self.vistas.values():vista.pack_forget()
        self.vistas[nombre].pack(fill="both",expand=True)
        for key,button in self.nav_buttons.items():button.configure(style="NavSelected.TButton" if key==nombre else "Nav.TButton")

    def _tree(self,parent,columns,headings):
        frame=ttk.Frame(parent,style="Card.TFrame",padding=1); frame.pack(fill="both",expand=True,pady=12)
        tree=ttk.Treeview(frame,columns=columns,show="headings",selectmode="browse")
        for col,title,width in headings:
            tree.heading(col,text=title); tree.column(col,width=width,minwidth=65,anchor="w",stretch=False)
        scroll=ttk.Scrollbar(frame,orient="vertical",command=tree.yview,style="Slim.Vertical.TScrollbar")
        hscroll=ttk.Scrollbar(frame,orient="horizontal",command=tree.xview,style="Slim.Horizontal.TScrollbar")
        tree.configure(yscrollcommand=scroll.set,xscrollcommand=hscroll.set)
        tree.tag_configure("odd",background="#f8fafc")
        frame.grid_rowconfigure(0,weight=1); frame.grid_columnconfigure(0,weight=1)
        tree.grid(row=0,column=0,sticky="nsew",padx=1,pady=1)
        scroll.grid(row=0,column=1,sticky="ns")
        hscroll.grid(row=1,column=0,sticky="ew")
        def mostrar_barra_horizontal(_event=None):
            ancho_columnas=sum(int(tree.column(col,"width")) for col in columns)
            if tree.winfo_width() < ancho_columnas:hscroll.grid()
            else:hscroll.grid_remove()
        tree.bind("<Configure>",mostrar_barra_horizontal,add="+")
        tree.after_idle(mostrar_barra_horizontal)
        return tree

    def _titulo_vista(self,parent,titulo,descripcion):
        ttk.Label(parent,text=titulo,style="Section.TLabel").pack(anchor="w",pady=(0,3))
        ttk.Label(parent,text=descripcion,style="Subtitle.TLabel").pack(anchor="w",pady=(0,16))

    def _vista_tickets(self):
        self._titulo_vista(self.tab_tickets,"Tickets","Consultá, buscá y gestioná los casos de soporte.")
        top=ttk.Frame(self.tab_tickets); top.pack(fill="x")
        if self.usuario["rol"] in ("Cliente","Admin"): ttk.Button(top,text="+ Crear ticket",style="Primary.TButton",command=self.crear_ticket).pack(side="left")
        ttk.Label(top,text="Buscar").pack(side="left",padx=(16,6))
        self.ticket_busqueda=tk.StringVar()
        busqueda=ttk.Entry(top,textvariable=self.ticket_busqueda,width=28); busqueda.pack(side="left")
        busqueda.insert(0,"")
        busqueda.bind("<KeyRelease>",lambda _e:self._filtrar_tickets())
        ttk.Label(top,text="Estado").pack(side="left",padx=(12,6))
        self.ticket_estado_filtro=ttk.Combobox(top,state="readonly",values=["Todos"]+[s.value for s in EstadoTicket],width=16)
        self.ticket_estado_filtro.pack(side="left"); self.ticket_estado_filtro.current(0)
        self.ticket_estado_filtro.bind("<<ComboboxSelected>>",lambda _e:self._filtrar_tickets())
        ttk.Button(top,text="Actualizar",command=self.cargar_tickets).pack(side="right")
        self.ticket_count=ttk.Label(self.tab_tickets,text="",style="Count.TLabel"); self.ticket_count.pack(anchor="e",pady=(10,0))
        self.ticket_tree=self._tree(self.tab_tickets,("id","titulo","estado","prioridad","cliente","tecnico","producto","fecha"),[("id","#",45),("titulo","Título",160),("estado","Estado",100),("prioridad","Prioridad",85),("cliente","Cliente",125),("tecnico","Técnico",125),("producto","Producto",150),("fecha","Creado",140)])
        self.ticket_tree.bind("<Double-1>",lambda _e:self.ver_ticket())
        bottom=ttk.Frame(self.tab_tickets); bottom.pack(fill="x")
        ttk.Button(bottom,text="Ver conversación e historial de actividad",command=self.ver_ticket).pack(side="left")
        if self.usuario["rol"] in ("Tecnico","Admin"): ttk.Button(bottom,text="Cambiar estado",command=self.cambiar_estado).pack(side="left",padx=6)
        if self.usuario["rol"]=="Cliente": ttk.Button(bottom,text="Cerrar / reabrir",command=self.cerrar_reabrir).pack(side="left")
        if self.usuario["rol"]=="Admin":
            ttk.Button(bottom,text="Asignar técnico",command=self.asignar_tecnico).pack(side="left",padx=6)
            ttk.Button(bottom,text="Configurar prioridad",command=self.configurar_prioridad).pack(side="left")
        self.cargar_tickets()

    def cargar_tickets(self):
        if not hasattr(self,"ticket_tree") or not self.ticket_tree.winfo_exists(): return
        self._tickets_cache=self.servicio.ticket_controller.listar(self.usuario["id"],self.usuario["rol"])
        self._filtrar_tickets()

    def _filtrar_tickets(self):
        if not hasattr(self,"ticket_tree") or not self.ticket_tree.winfo_exists():return
        self.ticket_tree.delete(*self.ticket_tree.get_children())
        consulta=self.ticket_busqueda.get().strip().casefold() if hasattr(self,"ticket_busqueda") else ""
        estado=self.ticket_estado_filtro.get() if hasattr(self,"ticket_estado_filtro") else "Todos"
        tickets=[t for t in getattr(self,"_tickets_cache",[]) if (estado=="Todos" or t["estado"]==estado) and (not consulta or consulta in " ".join(str(v) for v in t.values()).casefold())]
        for t in tickets:
            self.ticket_tree.insert("","end",iid=str(t["id"]),values=(t["id"],t["titulo"],t["estado"],t["prioridad"],t["cliente"],t["tecnico"],t["producto"],t["fecha_creacion"]))
        if hasattr(self,"ticket_count") and self.ticket_count.winfo_exists():
            self.ticket_count.configure(text=f"{len(tickets)} de {len(getattr(self,'_tickets_cache',[]))} tickets")

    def ticket_seleccionado(self):
        sel=self.ticket_tree.selection()
        if not sel: messagebox.showinfo("Seleccioná un ticket","Elegí un ticket de la lista primero."); return None
        return int(sel[0])

    def crear_ticket(self):
        win=tk.Toplevel(self.root); win.title("Crear ticket"); win.transient(self.root); win.grab_set()
        body=ttk.Frame(win,padding=20); body.pack(fill="both",expand=True)
        productos=self.servicio.producto_controller.listar()
        if not productos: messagebox.showinfo("Sin productos","Primero registrá un producto."); win.destroy(); return
        ttk.Label(body,text="Producto").grid(row=0,column=0,sticky="w",pady=6)
        prod=ttk.Combobox(body,state="readonly",width=42,values=[f"{p['id']} · {p['nombre']} ({p['tipo']})" for p in productos]); prod.grid(row=0,column=1,pady=6); prod.current(0)
        ttk.Label(body,text="Título").grid(row=1,column=0,sticky="w",pady=6)
        titulo=ttk.Entry(body,width=45); titulo.grid(row=1,column=1,pady=6)
        ttk.Label(body,text="Prioridad").grid(row=2,column=0,sticky="w",pady=6)
        prioridad=ttk.Combobox(body,state="readonly",values=["Baja","Media","Alta","Urgente"],width=42); prioridad.grid(row=2,column=1,pady=6); prioridad.set("Media")
        if self.usuario["rol"]!="Admin": prioridad.configure(state="disabled")
        ttk.Label(body,text="Descripción del problema").grid(row=3,column=0,sticky="nw",pady=6)
        desc=tk.Text(body,width=44,height=7); desc.grid(row=3,column=1,pady=6)
        def guardar():
            try:
                ticket_id=self.servicio.crear_ticket(self.usuario["id"],productos[prod.current()]["id"],desc.get("1.0","end").strip(),titulo.get(),prioridad.get())
                messagebox.showinfo("Ticket creado",f"Se creó el ticket #{ticket_id} y se asignó un técnico automáticamente."); win.destroy(); self.cargar_tickets()
            except Exception as e: messagebox.showerror("No se pudo crear",self.servicio.manejar_error(e))
        ttk.Button(body,text="Crear",command=guardar).grid(row=4,column=1,sticky="e",pady=8)

    def ver_ticket(self):
        tid=self.ticket_seleccionado()
        if tid is None:return
        data=self.servicio.ticket_controller.detalle(tid)
        if not data: return
        t,mensajes,hitos=data
        if self.usuario["rol"]!="Admin" and self.usuario["id"] not in (t["cliente_id"],t["tecnico_id"]): messagebox.showerror("Acceso denegado","No tenés acceso a este ticket."); return
        win=tk.Toplevel(self.root); win.title(f"Ticket #{tid} · {t['estado']}"); win.geometry("720x570"); win.transient(self.root)
        body=ttk.Frame(win,padding=14); body.pack(fill="both",expand=True)
        ttk.Label(body,text=f"{t['titulo']} · {t['estado']} · Prioridad: {t['prioridad']}",font=("Segoe UI",14,"bold")).pack(anchor="w")
        ttk.Label(body,text=f"Cliente: {t['cliente']}    Técnico: {t['tecnico']}    Serie: {t['numero_serie']}").pack(anchor="w",pady=4)
        ttk.Label(body,text=f"Producto: {t['producto']} · Descripción: {t['descripcion']}",wraplength=680).pack(anchor="w",pady=5)
        if t["fecha_cierre"]: ttk.Label(body,text=f"Cerrado: {t['fecha_cierre']}").pack(anchor="w")
        text=tk.Text(body,state="normal",wrap="word",height=18); text.pack(fill="both",expand=True,pady=8)
        text.insert("end","— Conversación —\n")
        for m in mensajes:text.insert("end",f"[{m['fecha_hora']}] {m['remitente']}: {m['contenido']}\n")
        text.insert("end","\n— Historial de actividad —\n")
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
        t=self.servicio.ticket_controller.buscar(tid)
        if t["estado"]==EstadoTicket.CERRADO.value:
            consulta=simpledialog.askstring("Reabrir ticket", "Ingresá la nueva consulta para justificar la reapertura:", parent=self.root)
            if consulta is None:return
            try:
                self.servicio.reabrir_ticket(tid,self.usuario,consulta)
                messagebox.showinfo("Ticket reabierto","El ticket pasó a En proceso. Se registró el mensaje y se notificó al técnico."); self.cargar_tickets()
            except Exception as e:messagebox.showerror("No se pudo reabrir",self.servicio.manejar_error(e))
            return
        estado=EstadoTicket.CERRADO
        try:
            self.servicio.cambiar_estado(tid,estado,self.usuario)
            messagebox.showinfo("Ticket actualizado","Se registró el cambio y se notificó a las partes."); self.cargar_tickets()
        except Exception as e:messagebox.showerror("No se pudo actualizar",self.servicio.manejar_error(e))

    def asignar_tecnico(self):
        tid=self.ticket_seleccionado()
        if tid is None:return
        ticket=self.servicio.ticket_controller.buscar(tid)
        producto=self.servicio.producto_controller.buscar(ticket["producto_id"])
        tecnicos=[u for u in self.servicio.usuarios.listar("Tecnico") if u["activo"] and u["disponible"] and u["especialidad_id"]==producto["tipo_id"]]
        if not tecnicos:messagebox.showinfo("Sin técnicos disponibles","No hay técnicos activos y disponibles con la especialidad del producto."); return
        seleccion=simpledialog.askstring("Asignar técnico","Escribí el ID de uno de estos técnicos:\n"+"\n".join(f"{u['id']}: {u['nombre']}" for u in tecnicos),parent=self.root)
        if seleccion is None:return
        try:
            self.servicio.asignar_ticket(tid,int(seleccion),self.usuario); self.cargar_tickets()
            messagebox.showinfo("Ticket asignado","Se registró la asignación y se notificó al técnico.")
        except Exception as e:messagebox.showerror("No se pudo asignar",self.servicio.manejar_error(e))

    def configurar_prioridad(self):
        tid=self.ticket_seleccionado()
        if tid is None:return
        prioridad=simpledialog.askstring("Configurar prioridad","Ingresá: Baja, Media, Alta o Urgente",parent=self.root)
        if prioridad is None:return
        try:
            self.servicio.configurar_prioridad(tid,prioridad.strip().capitalize(),self.usuario); self.cargar_tickets()
            messagebox.showinfo("Prioridad actualizada","La prioridad quedó registrada.")
        except Exception as e:messagebox.showerror("No se pudo cambiar",self.servicio.manejar_error(e))

    def _vista_productos(self):
        self._titulo_vista(self.tab_productos,"Productos","Administrá el catálogo y encontrá rápidamente un producto.")
        bar=ttk.Frame(self.tab_productos); bar.pack(fill="x")
        ttk.Label(bar,text="Buscar").pack(side="left")
        self.producto_busqueda=tk.StringVar()
        busqueda=ttk.Entry(bar,textvariable=self.producto_busqueda,width=26); busqueda.pack(side="left",padx=(6,14))
        busqueda.bind("<KeyRelease>",lambda _e:self.cargar_productos())
        ttk.Label(bar,text="Filtrar por tipo:").pack(side="left")
        tipos=self.servicio.producto_controller.tipos()
        self.tipo_filtro=ttk.Combobox(bar,state="readonly",values=["Todos"]+[t["nombre"] for t in tipos],width=28); self.tipo_filtro.pack(side="left",padx=6); self.tipo_filtro.current(0)
        self.tipo_filtro.bind("<<ComboboxSelected>>",lambda e:self.cargar_productos())
        if self.usuario["rol"]=="Admin":
            ttk.Button(bar,text="Agregar producto",command=self.crear_producto).pack(side="left",padx=6)
            ttk.Button(bar,text="Agregar tipo",command=self.crear_tipo_producto).pack(side="left",padx=6)
        self.producto_count=ttk.Label(self.tab_productos,text="",style="Count.TLabel"); self.producto_count.pack(anchor="e",pady=(10,0))
        self.producto_tree=self._tree(self.tab_productos,("nombre","tipo","marca","modelo","serie"),[("nombre","Producto",180),("tipo","Tipo",180),("marca","Marca",140),("modelo","Modelo",140),("serie","N.º de serie",180)])
        self.cargar_productos()

    def cargar_productos(self):
        if not hasattr(self,"producto_tree") or not self.producto_tree.winfo_exists():return
        self.producto_tree.delete(*self.producto_tree.get_children())
        tipos=self.servicio.producto_controller.tipos(); elegido=self.tipo_filtro.get()
        tipo_id=next((t["id"] for t in tipos if t["nombre"]==elegido),None)
        productos=self.servicio.producto_controller.listar(tipo_id)
        consulta=self.producto_busqueda.get().strip().casefold() if hasattr(self,"producto_busqueda") else ""
        productos=[p for p in productos if not consulta or consulta in " ".join(str(v) for v in p.values()).casefold()]
        for p in productos:self.producto_tree.insert("","end",values=(p["nombre"],p["tipo"],p["marca"],p["modelo"],p["numero_serie"]))
        if hasattr(self,"producto_count") and self.producto_count.winfo_exists():self.producto_count.configure(text=f"{len(productos)} productos")

    def crear_producto(self):
        win=tk.Toplevel(self.root); win.title("Agregar producto"); win.transient(self.root); win.grab_set()
        body=ttk.Frame(win,padding=20); body.pack()
        tipos=self.servicio.producto_controller.tipos(); fields={}
        for i,label in enumerate(("Nombre","Marca","Modelo","Número de serie","Descripción")):
            ttk.Label(body,text=label).grid(row=i,column=0,sticky="w",pady=5); entry=ttk.Entry(body,width=34); entry.grid(row=i,column=1,pady=5); fields[label]=entry
        ttk.Label(body,text="Tipo").grid(row=5,column=0,sticky="w",pady=5)
        tipo=ttk.Combobox(body,state="readonly",values=[t["nombre"] for t in tipos],width=31); tipo.grid(row=5,column=1,pady=5); tipo.current(0)
        def guardar():
            try:
                self.servicio.crear_producto(fields["Nombre"].get(),fields["Marca"].get(),fields["Modelo"].get(),tipos[tipo.current()]["id"],fields["Número de serie"].get(),fields["Descripción"].get())
                win.destroy(); self.cargar_productos(); messagebox.showinfo("Producto guardado","El producto quedó registrado.")
            except Exception as e:messagebox.showerror("No se pudo guardar",self.servicio.manejar_error(e))
        ttk.Button(body,text="Guardar",command=guardar).grid(row=6,column=1,sticky="e",pady=10)

    def crear_tipo_producto(self):
        nombre=simpledialog.askstring("Nuevo tipo de producto","Nombre del tipo:",parent=self.root)
        if nombre is None:return
        descripcion=simpledialog.askstring("Descripción del tipo","Descripción:",parent=self.root) or ""
        try:
            self.servicio.crear_tipo_producto(nombre,descripcion,self.usuario)
            messagebox.showinfo("Tipo creado","El tipo de producto quedó registrado.")
            self.mostrar_principal()
        except Exception as e:messagebox.showerror("No se pudo crear",self.servicio.manejar_error(e))

    def _vista_usuarios(self):
        self._titulo_vista(self.tab_usuarios,"Usuarios","Cuentas, roles y especialidades técnicas.")
        bar=ttk.Frame(self.tab_usuarios); bar.pack(fill="x")
        ttk.Button(bar,text="Agregar usuario",command=self.crear_usuario).pack(side="left")
        self.usuario_tree=self._tree(self.tab_usuarios,("nombre","email","rol","especialidad"),[("nombre","Nombre",200),("email","Correo",260),("rol","Rol",120),("especialidad","Especialidad",220)])
        self.cargar_usuarios()

    def _vista_admin(self):
        self._titulo_vista(self.tab_admin,"Panel de administración","Accesos rápidos a las herramientas de gestión.")
        opciones=(
            ("Usuarios","Creá cuentas y consultá roles y especialidades.","Gestionar usuarios","usuarios"),
            ("Productos","Administrá productos y tipos del catálogo.","Gestionar productos","productos"),
            ("Tickets","Revisá asignaciones y configurá prioridades.","Gestionar tickets","tickets"),
        )
        for titulo,descripcion,accion,vista in opciones:
            tarjeta=ttk.Frame(self.tab_admin,style="Card.TFrame",padding=(18,14))
            tarjeta.pack(fill="x",pady=7)
            detalle=ttk.Frame(tarjeta,style="Card.TFrame"); detalle.pack(side="left",fill="x",expand=True)
            ttk.Label(detalle,text=titulo,font=("Segoe UI",11,"bold"),background="#ffffff",foreground="#344054").pack(anchor="w")
            ttk.Label(detalle,text=descripcion,style="Subtitle.TLabel").pack(anchor="w",pady=(4,0))
            ttk.Button(tarjeta,text=accion,command=lambda destino=vista:self.mostrar_vista(destino)).pack(side="right",padx=(14,0))

    def cargar_usuarios(self):
        if not hasattr(self,"usuario_tree") or not self.usuario_tree.winfo_exists():return
        self.usuario_tree.delete(*self.usuario_tree.get_children())
        for u in self.servicio.usuarios.listar():
            especialidad=getattr(u,"especialidad_nombre","") or "—"
            self.usuario_tree.insert("","end",values=(u["nombre"],u["email"],u["rol"],especialidad))

    def crear_usuario(self):
        win=tk.Toplevel(self.root); win.title("Agregar usuario"); win.transient(self.root); win.grab_set()
        body=ttk.Frame(win,padding=20); body.pack()
        nombres=("Nombre","Correo","Contraseña"); fields={}
        for i,label in enumerate(nombres):
            ttk.Label(body,text=label).grid(row=i,column=0,sticky="w",pady=5); entry=ttk.Entry(body,width=32,show="•" if label=="Contraseña" else ""); entry.grid(row=i,column=1,pady=5); fields[label]=entry
        ttk.Label(body,text="Rol").grid(row=3,column=0,sticky="w",pady=5); rol=ttk.Combobox(body,state="readonly",values=["Cliente","Tecnico","Admin"],width=29); rol.grid(row=3,column=1,pady=5); rol.current(0)
        ttk.Label(body,text="Especialidad").grid(row=4,column=0,sticky="w",pady=5); tipos=self.servicio.producto_controller.tipos(); especialidad=ttk.Combobox(body,state="readonly",values=[t["nombre"] for t in tipos],width=29); especialidad.grid(row=4,column=1,pady=5); especialidad.current(0)
        def guardar():
            try:
                esp=tipos[especialidad.current()]["id"] if rol.get()=="Tecnico" else None
                self.servicio.crear_usuario(fields["Nombre"].get(),fields["Correo"].get(),fields["Contraseña"].get(),rol.get(),esp)
                win.destroy(); self.cargar_usuarios(); messagebox.showinfo("Usuario creado","El usuario quedó registrado.")
            except Exception as e:messagebox.showerror("No se pudo guardar",self.servicio.manejar_error(e))
        ttk.Button(body,text="Guardar",command=guardar).grid(row=5,column=1,sticky="e",pady=10)

    def _vista_notificaciones(self):
        self._titulo_vista(self.tab_notificaciones,"Notificaciones","Novedades relacionadas con tus tickets.")
        self.notif_tree=self._tree(self.tab_notificaciones,("id","mensaje","fecha","leida"),[("id","#",55),("mensaje","Notificación",540),("fecha","Fecha",170),("leida","Leída",70)])
        ttk.Button(self.tab_notificaciones,text="Marcar seleccionada como leída",command=self.marcar_leida).pack(anchor="w")
        self.cargar_notificaciones()

    def cargar_notificaciones(self):
        if not hasattr(self,"notif_tree") or not self.notif_tree.winfo_exists():return
        self.notif_tree.delete(*self.notif_tree.get_children())
        for n in self.servicio.notificacion_controller.listar(self.usuario["id"]):self.notif_tree.insert("","end",iid=str(n["id"]),values=(n["id"],n["mensaje"],n["fecha_hora"],"Sí" if n["leida"] else "No"))

    def marcar_leida(self):
        sel=self.notif_tree.selection()
        if not sel:return
        self.servicio.notificacion_controller.marcar_leida(int(sel[0]),self.usuario["id"]); self.cargar_notificaciones()

    def cerrar(self):
        self.executor.shutdown(wait=False,cancel_futures=True)
        self.root.destroy()


def iniciar():
    root=tk.Tk(); HitosApp(root); root.mainloop()

