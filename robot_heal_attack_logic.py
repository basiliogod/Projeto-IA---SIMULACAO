from robot_class import ROBOT_ATTACKS, ROBOT_HEALS, Robot, ROBOT_MAX_HEALTH
from robot_movement_logic import rotate_perform_action_return
from robot_attacks import sound_attack, touch_attack, crane_attack

def calculate_incoming_damage(enemy):
    """Calcula o dano baseado na Força * %Vida"""
    if not enemy or not enemy.is_alive():
        return 0
    max_hp = enemy.max_health if enemy.max_health > 0 else 1
    percentage_life = enemy.current_health / max_hp
    return enemy.force * percentage_life

def robot_turn_logic(tank_pair, medium_motor, color_sensor, gyro,
                     us_sensor, spin_speed, forward_speed,
                     robot, enemies_list):

    # ==============================
    # 1. Verificação de Estado Crítico
    # ==============================
    alive_enemies = [e for e in enemies_list if e and e.is_alive()]
    if not alive_enemies:
        print("Vitória! Todos os inimigos eliminados.")
        return

    # CORREÇÃO DO LOOP INFINITO:
    # Nunca permitir que a reserva seja 0. Precisamos de pelo menos 1 de energia 
    # para a recuperação funcionar (assumindo arredondamentos) ou idealmente mais.
    # Se gastarmos tudo, 50% de 0 é 0 e o robot morre de exaustão.
    
    MINIMUM_SURVIVAL_ENERGY = 20 # Nunca baixar disto

    if robot.current_health < 250:
        # Modo Desespero: Mantém apenas o mínimo vital para não "brickar" o robot
        energy_reserve = MINIMUM_SURVIVAL_ENERGY
    else:
        # Modo Normal: Mantém reserva saudável para crescimento exponencial
        energy_reserve = 100 

    temp_energy = robot.energy 
    scheduled_actions = {}
    temp_slots_attacked = set()

    # Se já entramos no turno com 0 de energia (bug anterior), não há nada a fazer
    if robot.energy == 0:
        print("ALERTA CRÍTICO: Energia a 0. O robot entrou em colapso energético.")
        return # Passa o turno e reza para que o jogo tenha base regen (que não tem)

    # ==============================
    # 2. Loop de Decisão
    # ==============================
    while True:
        candidates = []
        for i, enemy in enumerate(enemies_list):
            slot_id = i + 1
            if (enemy and enemy.is_alive() and 
                slot_id not in robot.slots_attacked_this_turn and 
                slot_id not in temp_slots_attacked):
                candidates.append((slot_id, enemy))

        if not candidates:
            break

        best_option = None

        for slot_id, enemy in candidates:
            current_threat = calculate_incoming_damage(enemy)
            
            for atk_name in ["sound", "touch", "crane"]:
                atk_info = ROBOT_ATTACKS[atk_name]
                cost = atk_info["cost"]
                
                # VERIFICAÇÃO DE SEGURANÇA:
                # Se usar este ataque nos deixar com menos que a reserva mínima,
                # NÃO ATACAR. É preferível passar turno e recuperar do que ficar com 0.
                if temp_energy - cost < energy_reserve:
                    continue

                damage_dealt = atk_info["damage"]
                predicted_health = max(0, enemy.current_health - damage_dealt)
                
                # Cálculo de Eficiência (igual ao anterior)
                max_hp = enemy.max_health if enemy.max_health > 0 else 1
                new_threat = 0
                if predicted_health > 0:
                    new_threat = enemy.force * (predicted_health / max_hp)
                
                damage_prevented = current_threat - new_threat
                efficiency = damage_prevented / (cost + 0.1)
                score = efficiency * 1000

                if predicted_health == 0: score += 5000
                if enemy.type == "Artillery": score += 2000

                if best_option is None or score > best_option["score"]:
                    best_option = {
                        "slot_id": slot_id,
                        "enemy": enemy,
                        "attack": atk_name,
                        "score": score,
                        "cost": cost
                    }

        if not best_option:
            # Se não há opções viáveis (seja por falta de alvos ou falta de energia
            # para cobrir a reserva), paramos de agendar ataques.
            break

        # Regista a ação
        target = best_option["enemy"]
        slot = best_option["slot_id"]
        attack_type = best_option["attack"]

        temp_energy -= best_option["cost"]
        temp_slots_attacked.add(slot)

        def create_action_callback(atk_type, s_id, tgt_enemy):
            def callback():
                print(f"Executando {atk_type} no Slot {s_id}...")
                if robot.attack_slot(atk_type, s_id, enemies_list):
                    if atk_type == "sound": sound_attack()
                    elif atk_type == "touch": touch_attack(tank_pair)
                    elif atk_type == "crane": crane_attack(tank_pair, medium_motor, color_sensor)
                    
                    if not tgt_enemy.is_alive():
                        print(f"ALVO ELIMINADO: {tgt_enemy.type}")
            return callback

        scheduled_actions[slot - 1] = create_action_callback(attack_type, slot, target)

    # ==============================
    # 3. Execução Física
    # ==============================
    if scheduled_actions:
        print(f"Energia Inicial: {robot.energy} | Prevista Final: {temp_energy}")
        rotate_perform_action_return(
            tank_pair=tank_pair,
            color_sensor=color_sensor,
            gyro=gyro,
            us_sensor=us_sensor,
            spin_speed=spin_speed,
            forward_speed=forward_speed,
            scheduled_actions=scheduled_actions
        )
    else:
        # Se não atacamos, é porque estamos a poupar energia para não atingir o 0.
        print(f"Poupando energia. Atual: {robot.energy}. Próximo turno: {robot.energy + (robot.energy * 0.5)}")