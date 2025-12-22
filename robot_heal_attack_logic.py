from robot_class import ROBOT_ATTACKS, ROBOT_HEALS, Robot, ROBOT_MAX_HEALTH
from robot_movement_logic import rotate_perform_action_return
from robot_attacks import sound_attack, touch_attack, crane_attack
energy_reserve = 100                   #sim


#sim
def teste():
    print( "Teste")
#/sim


# Lógica de cura e de ataque do robot por turno
def robot_turn_logic(tank_pair,medium_motor, color_sensor, gyro, us_sensor,spin_speed, forward_speed, robot, enemies_list):

    # LÓGICA DE CURA
    
    # Vai tentar curar se tiver a vida menor que 500
    if robot.current_health < ((2/3) * ROBOT_MAX_HEALTH ) and not robot.heal_used_this_turn:
        
        # Tenta usar a cura mais forte primeiro
        for heal_type in ["heal3", "heal2", "heal1"]:
            heal_info = ROBOT_HEALS[heal_type]
            if robot.energy >= heal_info["cost"]:
                if robot.heal(heal_type):
                    print("O Robot usou a Cura '{}' (Custo {}EN) e recuperou {} de vida. Vida atual: {:.0f}. Energia restante: {:.0f}.".format(
                        heal_type, heal_info["cost"], heal_info["health_recovered"], robot.current_health, robot.energy
                    ))
                    print("Turno encerrado após cura para poupar energia.")
                    return


    # LÓGICA DE ATAQUE

    # Dicionario para armazenar as acoes planeadas: { indice_linha: callback_funcao }
    scheduled_actions = {}
    temp_energy = robot.energy
    temp_slots_attacked = set()

    # Loop de planeamento: escolhe multiplos alvos enquanto houver energia
    while True:
        
        # 1. Identificar candidatos validos (vivos e nao atacados neste turno)
        candidates = []
        for i, enemy in enumerate(enemies_list):
            slot_id = i + 1
            if enemy and enemy.is_alive() and slot_id not in robot.slots_attacked_this_turn and slot_id not in temp_slots_attacked:
                candidates.append((slot_id, enemy))
        
        if not candidates:
            break

        # 2. Escolher o melhor alvo e ataque
        best_option = None
        
        # Avalia cada candidato
        for slot_id, enemy in candidates:
            attack_to_use = None
            is_kill = False

            # Calcula ameaça real do inimigo (dano potencial)
            enemy_threat = enemy.force * (enemy.current_health / enemy.max_health)

            # Verifica se consegue matar (prioridade ao mais barato que mata)
            if enemy.current_health <= ROBOT_ATTACKS["sound"]["damage"] and temp_energy >= ROBOT_ATTACKS["sound"]["cost"] + energy_reserve:
                attack_to_use = "sound"
                is_kill = True
            elif enemy.current_health <= ROBOT_ATTACKS["touch"]["damage"] and temp_energy >= ROBOT_ATTACKS["touch"]["cost"] + energy_reserve:
                attack_to_use = "touch"
                is_kill = True
            elif enemy.current_health <= ROBOT_ATTACKS["crane"]["damage"] and temp_energy >= ROBOT_ATTACKS["crane"]["cost"] + energy_reserve:
                attack_to_use = "crane"
                is_kill = True

            # Se não mata, escolhe o mais forte possível mantendo reserva
            if not is_kill:
                if temp_energy >= ROBOT_ATTACKS["crane"]["cost"] + energy_reserve:
                    attack_to_use = "crane"
                elif temp_energy >= ROBOT_ATTACKS["touch"]["cost"] + energy_reserve:
                    attack_to_use = "touch"
                elif temp_energy >= ROBOT_ATTACKS["sound"]["cost"] + energy_reserve:
                    attack_to_use = "sound"

            if attack_to_use:
                # Score baseado na ameaça real + bônus se matar
                score = enemy_threat
                if is_kill:
                    score += 10000

                if best_option is None or score > best_option["score"]:
                    best_option = {
                        "slot_id": slot_id,
                        "enemy": enemy,
                        "attack": attack_to_use,
                        "score": score
                    }

        
        if not best_option:
            # Nao consegue atacar mais ninguem
            break
            
        # 3. Adicionar ao planeamento
        target = best_option["enemy"]
        slot = best_option["slot_id"]
        attack = best_option["attack"]
        
        print("Planeamento: Robot vai atacar o Slot {} ({}) com '{}'.".format(slot, target.type, attack))
        
        # Atualiza energia temporaria e slots atacados para a proxima iteracao do loop de planeamento
        temp_energy -= ROBOT_ATTACKS[attack]["cost"]
        temp_slots_attacked.add(slot)

        # Cria a funcao callback que sera executada quando o robot chegar ao slot
        # Usamos uma funcao auxiliar para capturar as variaveis no closure corretamente
        def create_action_callback(atk_type, s_id, tgt_enemy):
            def callback():
                if robot.attack_slot(attack_type=atk_type, slot_id=s_id, enemies=enemies_list):
                    print("O Robot usou o Ataque '{}' (Custo {}EN) no Inimigo {} do Slot {}, deu {} de dano. Energia restante: {:.0f}.".format(
                        atk_type, ROBOT_ATTACKS[atk_type]["cost"], tgt_enemy.type, s_id, ROBOT_ATTACKS[atk_type]["damage"] ,robot.energy
                    ))
                    
                    # Executa o movimento fisico do ataque
                    if atk_type == "sound":
                        sound_attack()
                    elif atk_type == "touch":
                        touch_attack(tank_pair)
                    elif atk_type == "crane":
                        crane_attack(tank_pair, medium_motor, color_sensor)

                    if(not tgt_enemy.is_alive()):
                        print("O inimigo {} morreu.".format(tgt_enemy.type))
            return callback

        scheduled_actions[slot - 1] = create_action_callback(attack, slot, target)

    # 4. Executar todos os ataques planeados numa unica volta
    if scheduled_actions:
        rotate_perform_action_return(tank_pair=tank_pair,
            color_sensor=color_sensor, 
            gyro=gyro,
            us_sensor=us_sensor, 
            spin_speed=spin_speed,
            forward_speed=forward_speed,
            scheduled_actions=scheduled_actions)
    else:
        print("Robot nao tem energia suficiente para atacar nenhum alvo (ou nao existem alvos).")