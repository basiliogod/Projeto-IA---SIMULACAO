# Este módulo contém a lógica de decisão para os ataques do robô.
# A função principal, `robot_turn_logic`, avalia os inimigos e decide
# qual ação (ou conjunto de ações) é mais eficiente para maximizar o dano
# prevenido e eliminar ameaças, gerenciando ao mesmo tempo a energia do robô.

from robot_class import ROBOT_ATTACKS, ROBOT_HEALS, Robot
from robot_movement_logic import rotate_perform_action_return
from robot_attacks import sound_attack, touch_attack, crane_attack

# --- Constantes de Lógica de Decisão ---

# Reserva de energia para garantir que o robô não esgote completamente seus recursos.
MINIMUM_SURVIVAL_ENERGY = 20
# Reserva de energia em condições normais para permitir recuperação e ações futuras.
NORMAL_ENERGY_RESERVE = 50
# Vida abaixo da qual o robô entra em "modo desespero", conservando mais energia.
LOW_HEALTH_THRESHOLD = 250

# --- Fatores de Pontuação para Ataques ---
EFFICIENCY_MULTIPLIER = 1000  # Multiplicador para a eficiência do ataque.
ELIMINATION_BONUS_FACTOR = 10  # Bônus por eliminação, multiplicado pela força do inimigo.
OVERKILL_PENALTY_FACTOR = 2  # Penalidade por dano excessivo.

# Bônus de pontuação para priorizar tipos de inimigos específicos.
ARTILLERY_TYPE_BONUS = 4000
TANK_TYPE_BONUS = 1000

# --- Funções Auxiliares ---

def calculate_incoming_damage(enemy):
    """Calcula o dano potencial que um inimigo pode causar."""
    if not enemy or not enemy.is_alive():
        return 0
    max_hp = enemy.max_health if enemy.max_health > 0 else 1
    percentage_life = enemy.current_health / max_hp
    return enemy.force * percentage_life

def _get_target_candidates(enemies_list, robot, temp_slots_attacked):
    """Identifica inimigos que podem ser atacados neste turno."""
    all_candidates = []
    for i, enemy in enumerate(enemies_list):
        slot_id = i + 1
        if (enemy and enemy.is_alive() and
                slot_id not in robot.slots_attacked_this_turn and
                slot_id not in temp_slots_attacked):
            all_candidates.append((slot_id, enemy))

    # Prioriza inimigos que podem atacar no próximo turno.
    attacking_candidates = [c for c in all_candidates if c[1].num_attacks_available > 0]
    return attacking_candidates if attacking_candidates else all_candidates

def _calculate_attack_score(enemy, atk_name, atk_info):
    """Calcula uma pontuação para uma opção de ataque, avaliando sua eficiência."""
    current_threat = calculate_incoming_damage(enemy)
    cost = atk_info["cost"]
    damage_dealt = atk_info["damage"]

    predicted_health = max(0, enemy.current_health - damage_dealt)

    max_hp = enemy.max_health if enemy.max_health > 0 else 1
    new_threat = 0
    if predicted_health > 0:
        new_threat = enemy.force * (predicted_health / max_hp)

    damage_prevented = current_threat - new_threat
    # Adicionado 0.1 para evitar divisão por zero se o custo for 0.
    efficiency = damage_prevented / (cost + 0.1)
    score = efficiency * EFFICIENCY_MULTIPLIER

    # Aplica bônus e penalidades.
    if predicted_health == 0:
        score += enemy.force * ELIMINATION_BONUS_FACTOR
        overkill_damage = damage_dealt - enemy.current_health
        score -= overkill_damage * OVERKILL_PENALTY_FACTOR

    if enemy.type == "Artillery":
        score += ARTILLERY_TYPE_BONUS
    if enemy.type == "Tank":
        score += TANK_TYPE_BONUS

    return score

def _find_best_action(candidates, temp_energy, energy_reserve):
    """Avalia todos os candidatos e ataques para encontrar a melhor ação possível."""
    best_option = None

    for slot_id, enemy in candidates:
        for atk_name in ["sound", "touch", "crane"]:
            atk_info = ROBOT_ATTACKS[atk_name]
            cost = atk_info["cost"]

            if temp_energy - cost < energy_reserve:
                continue

            score = _calculate_attack_score(enemy, atk_name, atk_info)

            if best_option is None or score > best_option["score"]:
                best_option = {
                    "slot_id": slot_id,
                    "enemy": enemy,
                    "attack": atk_name,
                    "score": score,
                    "cost": cost
                }
    return best_option

def _create_action_callback(robot, enemies_list, tank_pair, medium_motor, color_sensor, atk_type, s_id, tgt_enemy):
    """Cria uma função de callback para executar um ataque agendado."""
    def callback():
        print(f"Executando {atk_type} no Slot {s_id}...")
        if robot.attack_slot(atk_type, s_id, enemies_list):
            # Aciona a animação do ataque correspondente.
            if atk_type == "sound":
                sound_attack()
            elif atk_type == "touch":
                touch_attack(tank_pair)
            elif atk_type == "crane":
                crane_attack(tank_pair, medium_motor, color_sensor)

            if not tgt_enemy.is_alive():
                print(f"ALVO ELIMINADO: {tgt_enemy.type}")
    return callback

# --- Função Principal ---

def robot_turn_logic(tank_pair, medium_motor, color_sensor, gyro,
                     us_sensor, spin_speed, forward_speed,
                     robot, enemies_list):
    """
    Coordena o turno do robô, decidindo as melhores ações de ataque.
    """
    if not any(e and e.is_alive() for e in enemies_list):
        print("Vitória! Todos os inimigos eliminados.")
        return

    if robot.energy == 0:
        print("Robô sem energia. Poupando para o próximo turno.")
        return

    energy_reserve = (MINIMUM_SURVIVAL_ENERGY if robot.current_health < LOW_HEALTH_THRESHOLD
                      else NORMAL_ENERGY_RESERVE)

    temp_energy = robot.energy
    scheduled_actions = {}
    temp_slots_attacked = set()

    while True:
        candidates = _get_target_candidates(enemies_list, robot, temp_slots_attacked)
        if not candidates:
            break

        best_option = _find_best_action(candidates, temp_energy, energy_reserve)
        if not best_option:
            break
        
        # Registra a ação e atualiza o estado temporário.
        slot = best_option["slot_id"]
        attack_type = best_option["attack"]
        target_enemy = best_option["enemy"]
        cost = best_option["cost"]

        temp_energy -= cost
        temp_slots_attacked.add(slot)

        action_callback = _create_action_callback(
            robot, enemies_list, tank_pair, medium_motor, color_sensor,
            attack_type, slot, target_enemy
        )
        scheduled_actions[slot - 1] = action_callback

    # Executa as ações agendadas.
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
        # Informa que o robô está conservando energia.
        next_turn_energy = robot.energy + (robot.energy * 0.5)
        print(f"Poupando energia. Atual: {robot.energy}. Próximo turno: {next_turn_energy:.0f}")



def handle_emergency_heal(robot, total_incoming_damage):
    """
    Verifica se o robô está prestes a sofrer dano letal e, se necessário,
    ativa a cura mais eficiente para sobreviver.
    """
    if robot.heal_used_this_turn:
        return

    is_lethal = robot.current_health - total_incoming_damage <= 0
    if is_lethal and total_incoming_damage > 0:
        health_needed = total_incoming_damage - robot.current_health + 1
        print(f"ALERTA: Dano iminente ({total_incoming_damage:.0f}) é letal! "
              f"Vida atual: {robot.current_health:.0f}. Vida necessária: {health_needed:.0f}.")

        # Encontrar a cura mais barata que salva o robô
        best_heal = None
        # Ordenar curas por custo para encontrar a mais barata primeiro
        sorted_heals = sorted(ROBOT_HEALS.items(), key=lambda item: item[1]['cost'])

        for heal_type, heal_info in sorted_heals:
            if heal_info['health_recovered'] >= health_needed:
                if robot.energy - heal_info['cost'] >= MINIMUM_SURVIVAL_ENERGY:
                    best_heal = (heal_type, heal_info)
                    break # Encontrou a cura mais barata e viável

        if best_heal:
            heal_type, heal_info = best_heal
            print(f"A usar a cura de emergência '{heal_type}' "
                  f"(Custo: {heal_info['cost']} EN, Cura: {heal_info['health_recovered']} HP).")
            robot.heal(heal_type)
        else:
            print("AVISO: Nenhuma cura de emergência eficaz ou acessível disponível. O robô pode ser destruído.")