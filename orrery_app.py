# orrery_app.py (versão atualizada)
import customtkinter
from tkinter import messagebox
from geminiOrreryF_refactored import AstroCLI, CITIES, BODIES, PLANETS_FOR_ASPECTS

# ... (cabeçalho e classe App __init__ como antes, até a seção de botões) ...

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("Orrery Pro")
        self.geometry("1200x800")
        self.astro_logic = AstroCLI()

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.nav_frame = customtkinter.CTkFrame(self, corner_radius=0)
        self.nav_frame.grid(row=0, column=0, sticky="nsew")
        self.nav_frame.grid_rowconfigure(12, weight=1) # Aumentar para dar espaço aos novos botões

        self.nav_label = customtkinter.CTkLabel(self.nav_frame, text="Orrery Pro",
                                                font=customtkinter.CTkFont(size=20, weight="bold"))
        self.nav_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # --- Categoria: Configuração ---
        self.config_label = customtkinter.CTkLabel(self.nav_frame, text="Configuração",
                                                   font=customtkinter.CTkFont(size=12, weight="bold"))
        self.config_label.grid(row=1, column=0, padx=20, pady=(20, 5), sticky="w")
        
        self.btn_city = customtkinter.CTkButton(self.nav_frame, text="Selecionar Cidade", fg_color="black",
                                                command=self.show_city_selection_view)
        self.btn_city.grid(row=2, column=0, padx=20, pady=5, sticky="ew")

        self.btn_date = customtkinter.CTkButton(self.nav_frame, text="Definir Data de Busca", fg_color="black",
                                                command=self.show_set_search_time_view)
        self.btn_date.grid(row=3, column=0, padx=20, pady=5, sticky="ew")

        # --- Categoria: Observação ---
        self.obs_label = customtkinter.CTkLabel(self.nav_frame, text="Observação Imediata",
                                                font=customtkinter.CTkFont(size=12, weight="bold"))
        self.obs_label.grid(row=4, column=0, padx=20, pady=(20, 5), sticky="w")

        self.btn_positions = customtkinter.CTkButton(self.nav_frame, text="Posições dos Astros", fg_color="black",
                                                     command=self.show_positions_view)
        self.btn_positions.grid(row=5, column=0, padx=20, pady=5, sticky="ew")

        # --- Categoria: Eventos Futuros ---
        self.events_label = customtkinter.CTkLabel(self.nav_frame, text="Busca de Eventos",
                                                    font=customtkinter.CTkFont(size=12, weight="bold"))
        self.events_label.grid(row=6, column=0, padx=20, pady=(20, 5), sticky="w")

        self.btn_lunar_apsis = customtkinter.CTkButton(self.nav_frame, text="Ápsides Lunares", fg_color="black",
                                                       command=self.show_lunar_apsis_view)
        self.btn_lunar_apsis.grid(row=7, column=0, padx=20, pady=5, sticky="ew")
        
        # --- BOTÕES NOVOS ---
        self.btn_planet_apsis = customtkinter.CTkButton(self.nav_frame, text="Ápsides Planetários", fg_color="black",
                                                        command=self.show_planet_apsis_view)
        self.btn_planet_apsis.grid(row=8, column=0, padx=20, pady=5, sticky="ew")

        self.btn_moon_nodes = customtkinter.CTkButton(self.nav_frame, text="Nodos Lunares", fg_color="black",
                                                      command=self.show_moon_nodes_view)
        self.btn_moon_nodes.grid(row=9, column=0, padx=20, pady=5, sticky="ew")
        
        self.btn_elongation = customtkinter.CTkButton(self.nav_frame, text="Máxima Elongação", fg_color="black",
                                                      command=self.show_elongation_view)
        self.btn_elongation.grid(row=10, column=0, padx=20, pady=5, sticky="ew")
        
        self.btn_eclipses = customtkinter.CTkButton(self.nav_frame, text="Eclipses", fg_color="black",
                                                       command=self.show_eclipses_view)
        self.btn_eclipses.grid(row=11, column=0, padx=20, pady=5, sticky="ew")
        
        # --- Área de Conteúdo ---
        self.content_frame = customtkinter.CTkFrame(self, corner_radius=10)
        self.content_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        
        self.show_welcome_view()

    # --- Funções de Controle da Interface (clear_content_frame, create_results_textbox, check_city_selected) ---
    # ... (cole aqui as funções da versão anterior) ...
    def clear_content_frame(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def create_results_textbox(self):
        textbox = customtkinter.CTkTextbox(self.content_frame, font=("Courier New", 13), wrap="none")
        textbox.pack(padx=10, pady=10, fill="both", expand=True)
        return textbox

    def check_city_selected(self):
        if not self.astro_logic.observer:
            messagebox.showwarning("Localização Necessária", "Por favor, selecione uma cidade primeiro no menu 'Configuração'.")
            return False
        return True

    # --- "Telas" da Aplicação ---
    # ... (cole aqui as telas da versão anterior: show_welcome_view, show_city_selection_view, etc.) ...
    def show_welcome_view(self):
        self.clear_content_frame()
        customtkinter.CTkLabel(self.content_frame, text="Bem-vindo ao Orrery Pro!\n\nSelecione uma opção no menu à esquerda.",
                               font=customtkinter.CTkFont(size=20)).pack(padx=20, pady=20, expand=True)

    def select_city(self, city_name):
        result, message = self.astro_logic.set_city(city_name)
        if result:
            messagebox.showinfo("Sucesso", message)
            self.show_welcome_view()
        else:
            messagebox.showerror("Erro de Fuso Horário", message)

    def show_city_selection_view(self):
        self.clear_content_frame()
        city_list_frame = customtkinter.CTkScrollableFrame(self.content_frame, label_text="Selecione sua localização")
        city_list_frame.pack(padx=10, pady=10, fill="both", expand=True)
        for name in sorted(CITIES.keys()):
            button = customtkinter.CTkButton(city_list_frame, text=name, fg_color="black", command=lambda n=name: self.select_city(n))
            button.pack(padx=10, pady=5, fill="x")
    
    def show_set_search_time_view(self):
        if not self.check_city_selected(): return
        self.clear_content_frame()
        current_search_str = self.astro_logic.get_search_time_str()
        customtkinter.CTkLabel(self.content_frame, text=f"Data de Início para Buscas\nAtual: {current_search_str}", font=customtkinter.CTkFont(size=16)).pack(pady=(10,5))
        customtkinter.CTkLabel(self.content_frame, text="Digite a nova data (AAAA-MM-DD) ou deixe em branco para 'agora'.").pack(pady=5)
        entry = customtkinter.CTkEntry(self.content_frame, placeholder_text="AAAA-MM-DD")
        entry.pack(pady=5, padx=20, fill="x")
        def set_date():
            result, message = self.astro_logic.set_search_time_from_str(entry.get())
            messagebox.showinfo("Data de Busca", message)
            self.show_welcome_view()
        customtkinter.CTkButton(self.content_frame, text="Definir Data", fg_color="black", command=set_date).pack(pady=10)

    def show_positions_view(self):
        if not self.check_city_selected(): return
        self.clear_content_frame()
        # ... (código da função da versão anterior)
    
    def show_lunar_apsis_view(self):
        if not self.check_city_selected(): return
        self.clear_content_frame()

        customtkinter.CTkLabel(self.content_frame, text="Busca por Ápsides Lunares (Apogeu/Perigeu)", font=customtkinter.CTkFont(size=16)).pack(pady=(10,5))
        textbox = self.create_results_textbox()

        def find_next():
            textbox.insert("end", "\nBuscando próximo evento...\n")
            self.update_idletasks()
            output, error = self.astro_logic.find_next_lunar_apsis()
            textbox.insert("end", output if not error else f"ERRO: {error}")
            textbox.see("end")
        
        button = customtkinter.CTkButton(self.content_frame, text="Buscar Próximo", fg_color="black", command=find_next)
        button.pack(pady=10)
        find_next()

    def show_eclipses_view(self):
        if not self.check_city_selected(): return
        self.clear_content_frame()
        customtkinter.CTkLabel(self.content_frame, text="Busca por Eclipses", font=customtkinter.CTkFont(size=16)).pack(pady=(10,5))
        options_frame = customtkinter.CTkFrame(self.content_frame, fg_color="transparent")
        options_frame.pack(pady=10)
        textbox = self.create_results_textbox()
        def find_eclipse(mode):
            textbox.insert("end", f"\nBuscando próximo eclipse ({mode})...\n")
            self.update_idletasks()
            output, error = self.astro_logic.find_next_eclipse(mode)
            textbox.insert("end", output if not error else f"ERRO: {error}")
            textbox.see("end")
        btn_solar_global = customtkinter.CTkButton(options_frame, text="Solar (Global)", fg_color="black", command=lambda: find_eclipse("solar_global"))
        btn_solar_global.grid(row=0, column=0, padx=5)
        btn_solar_local = customtkinter.CTkButton(options_frame, text="Solar (Local)", fg_color="black", command=lambda: find_eclipse("solar_local"))
        btn_solar_local.grid(row=0, column=1, padx=5)
        btn_lunar = customtkinter.CTkButton(options_frame, text="Lunar", fg_color="black", command=lambda: find_eclipse("lunar"))
        btn_lunar.grid(row=0, column=2, padx=5)

    # --- TELAS NOVAS ---

    def show_planet_apsis_view(self):
        if not self.check_city_selected(): return
        self.clear_content_frame()

        customtkinter.CTkLabel(self.content_frame, text="Busca por Ápsides Planetários (Afélio/Periélio)", font=customtkinter.CTkFont(size=16)).pack(pady=(10,5))
        
        # Frame para os controles de seleção
        controls_frame = customtkinter.CTkFrame(self.content_frame, fg_color="transparent")
        controls_frame.pack(pady=5)
        
        customtkinter.CTkLabel(controls_frame, text="Planeta:").pack(side="left", padx=(0, 5))
        planet_menu = customtkinter.CTkOptionMenu(controls_frame, values=PLANETS_FOR_ASPECTS)
        planet_menu.pack(side="left")

        textbox = self.create_results_textbox()

        def find_next():
            planet_name = planet_menu.get()
            textbox.insert("end", f"\nBuscando para {planet_name}...\n")
            self.update_idletasks()
            output, error = self.astro_logic.find_next_planet_apsis(planet_name)
            textbox.insert("end", output if not error else f"ERRO: {error}")
            textbox.see("end")

        button = customtkinter.CTkButton(self.content_frame, text="Buscar Próximo", fg_color="black", command=find_next)
        button.pack(pady=10)

    def show_moon_nodes_view(self):
        if not self.check_city_selected(): return
        self.clear_content_frame()
        customtkinter.CTkLabel(self.content_frame, text="Busca por Nodos Lunares", font=customtkinter.CTkFont(size=16)).pack(pady=(10,5))
        textbox = self.create_results_textbox()

        def find_next():
            textbox.insert("end", "\nBuscando próximo nodo lunar...\n")
            self.update_idletasks()
            output, error = self.astro_logic.find_next_moon_node()
            textbox.insert("end", output if not error else f"ERRO: {error}")
            textbox.see("end")

        button = customtkinter.CTkButton(self.content_frame, text="Buscar Próximo", fg_color="black", command=find_next)
        button.pack(pady=10)
        find_next()

    def show_elongation_view(self):
        if not self.check_city_selected(): return
        self.clear_content_frame()

        customtkinter.CTkLabel(self.content_frame, text="Busca por Máxima Elongação", font=customtkinter.CTkFont(size=16)).pack(pady=(10,5))
        
        controls_frame = customtkinter.CTkFrame(self.content_frame, fg_color="transparent")
        controls_frame.pack(pady=5)
        
        customtkinter.CTkLabel(controls_frame, text="Planeta:").pack(side="left", padx=(0, 5))
        planet_menu = customtkinter.CTkOptionMenu(controls_frame, values=["Mercury", "Venus"])
        planet_menu.pack(side="left")

        textbox = self.create_results_textbox()

        def find_next():
            planet_name = planet_menu.get()
            textbox.insert("end", f"\nBuscando para {planet_name}...\n")
            self.update_idletasks()
            output, error = self.astro_logic.find_next_elongation(planet_name)
            textbox.insert("end", output if not error else f"ERRO: {error}")
            textbox.see("end")

        button = customtkinter.CTkButton(self.content_frame, text="Buscar Próximo", fg_color="black", command=find_next)
        button.pack(pady=10)

if __name__ == "__main__":
    app = App()
    app.mainloop()