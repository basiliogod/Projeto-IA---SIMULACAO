from robot_class import ROBOT_ATTACKS, ROBOT_HEALS, Robot, ROBOT_MAX_HEALTH
from robot_movement_logic import rotate_perform_action_return
from robot_attacks import sound_attack, touch_attack, crane_attack


# Calcula o dano potencial que um inimigo pode causar.
def calculate_incoming_damage(enemy):
    if not enemy or not enemy.is_alive():
        return 0
    max_hp = enemy.max_health if enemy.max_health > 0 else 1
    percentage_life = enemy.current_health / max_hp
    return enemy.force * percentage_life

def robot_turn_logic(tank_pair, medium_motor, color_sensor, gyro,
                     us_sensor, spin_speed, forward_speed,
                     robot, enemies_list):

    # Filtra a lista de inimigos para manter apenas os que estão vivos.
    alive_enemies = [e for e in enemies_list if e and e.is_alive()]
    if not alive_enemies:
        print("Vitória! Todos os inimigos eliminados.")
        return

    MINIMUM_SURVIVAL_ENERGY = 20 # Reserva mínima de energia para evitar que chegue a 0 de energia.

    if robot.current_health < 250:
        # Modo Desespero: Se a vida está baixa, mantém apenas o mínimo para sobreviver.
        energy_reserve = MINIMUM_SURVIVAL_ENERGY
    else:
        # Modo Normal: Mantém uma reserva saudável para permitir recuperação exponencial.
        energy_reserve = 100 

    temp_energy = robot.energy 
    scheduled_actions = {}
    temp_slots_attacked = set() # Conjunto para rastrear os slots já atacados neste turno.

    if robot.energy == 0:
        return

    while True:
        # Identifica todos os inimigos vivos que ainda não foram alvo neste turno.
        all_candidates = []
        for i, enemy in enumerate(enemies_list):
            slot_id = i + 1
            if (enemy and enemy.is_alive() and 
                slot_id not in robot.slots_attacked_this_turn and 
                slot_id not in temp_slots_attacked):
                all_candidates.append((slot_id, enemy))

        # Prioritiza inimigos que podem atacar.
        attacking_candidates = [c for c in all_candidates if c[1].num_attacks_available > 0]

        if attacking_candidates:
            candidates = attacking_candidates
        else:
            candidates = all_candidates

        # Se não há mais candidatos, o loop de decisão termina.
        if not candidates:
            break

        best_option = None

        # Avalia cada inimigo candidato para encontrar a melhor ação.
        for slot_id, enemy in candidates:
            # Calcula a ameaça atual que o inimigo representa.
            current_threat = calculate_incoming_damage(enemy)
            
            # Itera sobre todos os ataques disponíveis para o robô.
            for atk_name in ["sound", "touch", "crane"]:
                atk_info = ROBOT_ATTACKS[atk_name]
                cost = atk_info["cost"]
                
                # Não realiza um ataque se isso reduzir a energia abaixo da reserva mínima.
                if temp_energy - cost < energy_reserve:
                    continue
                
                # Prevê a vida do inimigo após o ataque.
                damage_dealt = atk_info["damage"]
                predicted_health = max(0, enemy.current_health - damage_dealt)
                
                # Recalcula a ameaça que o inimigo representará se sobreviver ao ataque.
                max_hp = enemy.max_health if enemy.max_health > 0 else 1
                new_threat = 0
                if predicted_health > 0:
                    new_threat = enemy.force * (predicted_health / max_hp)
                
                # Calcula a eficiência do ataque: dano prevenido por ponto de energia gasto.
                damage_prevented = current_threat - new_threat
                efficiency = damage_prevented / (cost + 0.1)
                score = efficiency * 1000

                # Adiciona bónus ao score por eliminar um alvo ou atacar inimigos prioritários.
                if predicted_health == 0: score += 5000         # Bónus por eliminação.
                if enemy.type == "Artillery": score += 2000     # Bónus por atacar Artilharia.

                # Se a ação atual for a melhor encontrada até agora, armazena-a.
                if best_option is None or score > best_option["score"]:
                    best_option = {
                        "slot_id": slot_id,
                        "enemy": enemy,
                        "attack": atk_name,
                        "score": score,
                        "cost": cost
                    }

        if not best_option:
            break

        # Regista a melhor ação encontrada.
        target = best_option["enemy"]
        slot = best_option["slot_id"]
        attack_type = best_option["attack"]

        temp_energy -= best_option["cost"]
        temp_slots_attacked.add(slot)

        def create_action_callback(atk_type, s_id, tgt_enemy):
            def callback():
                print(f"Executando {atk_type} no Slot {s_id}...")
                # Tenta executar o ataque.
                if robot.attack_slot(atk_type, s_id, enemies_list):
                    # Se o ataque for bem-sucedido, aciona a animação correspondente.
                    if atk_type == "sound": sound_attack()
                    elif atk_type == "touch": touch_attack(tank_pair)
                    elif atk_type == "crane": crane_attack(tank_pair, medium_motor, color_sensor)
                    
                    # Verifica se o alvo foi eliminado.
                    if not tgt_enemy.is_alive():
                        print(f"ALVO ELIMINADO: {tgt_enemy.type}")
            return callback

        scheduled_actions[slot - 1] = create_action_callback(attack_type, slot, target)

    # Se houver ações agendadas, executa-as.
    if scheduled_actions:
        print(f"Energia Inicial: {robot.energy} | Prevista Final: {temp_energy}")
        # Chama a função que move o robô e executa as ações nos slots corretos.
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
        # Se nenhuma ação foi agendada, o robô está a poupar energia.
        print(f"Poupando energia. Atual: {robot.energy}. Próximo turno: {robot.energy + (robot.energy * 0.5)}")