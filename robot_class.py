ROBOT_MAX_HEALTH = 750
ROBOT_MAX_ENERGY = 500
ENERGY_RECOVERY_PERCENT = 0.5

ROBOT_ATTACKS = {
    "crane" : {
        "damage": 200, 
        "cost": 300
        },
    "touch" : {
        "damage": 100, 
        "cost": 150
        },
    "sound" : {
        "damage": 50, 
        "cost": 50
        }
}

ROBOT_HEALS = {
    "heal1": {
        "health_recovered": 100, 
        "cost": 200
        },
    "heal2": {
        "health_recovered": 200, 
        "cost": 300
        },
    "heal3": {
        "health_recovered": 400, 
        "cost": 400
        }
}


class Robot:

    def __init__(self):
        self.current_health = ROBOT_MAX_HEALTH
        self.energy = ROBOT_MAX_ENERGY
        self.max_health = ROBOT_MAX_HEALTH
        self.heal_used_this_turn = False
        self.slots_attacked_this_turn = set()

    # Rotina de início de truno
    def start_new_turn(self):
        recovered_energy = self.energy * ENERGY_RECOVERY_PERCENT
        self.energy += recovered_energy
        
        if self.energy > ROBOT_MAX_ENERGY:
            self.energy = ROBOT_MAX_ENERGY

        self.heal_used_this_turn = False
        self.slots_attacked_this_turn.clear()

    # Ataca um inimigo num slot específico
    # Retorna True se o ataque for bem-sucedido, False caso contrário
    def attack_slot(self, attack_type, slot_id, enemies):

        # Verifica se o tipo de ataque é válido (crane, touch ou sound)
        if attack_type not in ROBOT_ATTACKS:
            print("Erro: O Ataque '{}' nao existe.".format(attack_type))
            return False

        # Verifica se o slot é válido (entre 1 e 6)
        if not (1 <= slot_id <= 6):
            print("Erro: O Slot {} nao existe.".format(slot_id))
            return False

        # Verifica se o slot já foi atacado neste turno
        if slot_id in self.slots_attacked_this_turn:
            print("Erro: O Slot {} ja foi atacado neste turno.".format(slot_id))
            return False

        # Verifica se existe algum inimigo no slot
        target_enemy = enemies[slot_id - 1]
        if target_enemy is None:
            print("Erro: O Slot {} esta vazio.".format(slot_id))
            return False

        # Obtém os dados do ataque (dano e custo)
        attack = ROBOT_ATTACKS[attack_type]
        cost = attack["cost"]
        damage = attack["damage"]

        # Verifica se o robot tem energia suficiente para fazer o ataque
        if self.energy < cost:
            print("Erro: O Robot nao tem energia suficiente para fazer o Ataque '{}'. Tem um custo de {} e o Robot so tem {} de energia.".format(attack_type, cost, self.energy))
            return False

        # Realiza o ataque  
        self.energy -= cost
        target_enemy.receive_damage(damage)

        # Regista que esse slot já foi atacado neste turno
        self.slots_attacked_this_turn.add(slot_id)
        return True



    # Cura o robot
    # Retorna True se a cura for bem-sucedida, False caso contrário
    def heal(self, heal_type):

        # Verifica se o robot já se curou neste turno
        if self.heal_used_this_turn:
            print("Erro: O Robot ja se curou neste turno.")
            return False

        # Verifica se o tipo de cura é válido (heal1, heal2 ou heal3)
        if heal_type not in ROBOT_HEALS:
            print("Erro: A Cura '{}' nao existe.".format(heal_type))
            return False

        # Obtém os dados da cura (vida recuperada e custo)    
        heal_action = ROBOT_HEALS[heal_type]
        cost = heal_action["cost"]
        health_recovered = heal_action["health_recovered"]

        # Verifica se o robot tem energia suficiente para fazer a cura
        if self.energy < cost:
            print("Erro: O Robot nao tem energia suficiente para fazer a Cura '{}'. Tem um custo de {} e o Robot so tem {} de energia.".format(heal_type, cost, self.energy))
            return False
            
        # Realiza a cura
        self.energy -= cost
        self.current_health += health_recovered
        if self.current_health > self.max_health:
            self.current_health = self.max_health
            
        # Regista que já foi usada uma cura neste turno
        self.heal_used_this_turn = True
        
        return True



    # Recebe dano e atualiza a vida atual do robot
    # Retorna True se o inimigo for morto (vida atual atinge zero ou menos), False caso contrário
    def receive_damage(self, damage):
        self.current_health -= damage
        if self.current_health < 0:
            self.current_health = 0
        
        print("O Robot sofreu {} de dano! Vida restante: {:.0f}/{}".format(
            damage, self.current_health, self.max_health
        ))
        
        return self.current_health == 0



    # Verifica se o robot ainda está vivo
    # Retorna True se estiver vivo, False caso contrário
    def is_alive(self):
        return self.current_health > 0