ENEMY_STATS = {
    "Tank": {
        "color": "Green",
        "force": 200,
        "num_attacks_available": 2,
        "max_health": 400,
    },
    "Artillery": {
        "color": "Brown",
        "force": 500,
        "num_attacks_available": 1,
        "max_health": 50,
    },
    "Infantry": {
        "color": "Blue",
        "force": 100,
        "num_attacks_available": 3,
        "max_health": 100,
    }
}

class Enemy:

    # Inicializa uma nova instância da classe Enemy
    # Recebe como argumento o tipo de inimigo ("Tank", "Artillery" ou "Infantry") e o turno em que spawnou
    def __init__(self, type, spawn_turn, position):
        
        if type not in ENEMY_STATS:
            raise ValueError("Erro: O Inimigo '{}' nao existe.".format(type)) # The character 'é' was here.
            
        stats = ENEMY_STATS[type]
        
        self.type = type
        self.color = stats['color']
        self.force = stats['force']
        self.num_attacks_available = stats['num_attacks_available']
        self.max_health = stats['max_health']
        self.spawn_turn = spawn_turn
        self.current_health = self.max_health
        self.position = position


    # Recebe dano e atualiza a vida atual do inimigo
    # Retorna True se o inimigo for morto (vida atual atinge zero ou menos), False caso contrário
    def receive_damage(self, damage):
        self.current_health -= damage
        if self.current_health <= 0:
            self.current_health = 0
        return self.current_health == 0


    # Verifica se o inimigo ainda está vivo
    # Retorna True se estiver vivo, False caso contrário
    def is_alive(self):
        return self.current_health > 0


    def __str__(self):
        status = "VIVO" if self.is_alive() else "MORTO"
        
        return "[Tipo: {} | Cor: {} | Vida: {}/{} | Forca: {} | Ataques disponiveis: {} | Status: {}]".format(
            self.type, 
            self.color, 
            self.current_health, 
            self.max_health, 
            self.force,
            self.num_attacks_available, 
            status
        )