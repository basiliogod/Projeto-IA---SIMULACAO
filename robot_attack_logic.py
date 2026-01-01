from robot_class import ROBOT_ATTACKS, ROBOT_HEALS, Robot
from robot_movement_logic import rotate_perform_action_return
from robot_attacks import sound_attack, touch_attack, crane_attack


# Constantes de Gestão de Energia e Sobrevivência
# Definem os limiares para quando o robot deve entrar em modo de conservação ou cura.
MINIMUM_SURVIVAL_ENERGY = 200  # Energia mínima a manter se a vida estiver baixa.
NORMAL_ENERGY_RESERVE = 300    # Energia a reservar em condições normais.
LOW_HEALTH_THRESHOLD = 350     # Limiar de vida abaixo do qual o robot prioriza a sobrevivência.


# Pesos para o Cálculo de Score de Ataque
# Ajustam a heurística de decisão para escolher o melhor ataque.
EFFICIENCY_MULTIPLIER = 1000   # Multiplicador base para a eficiência (dano/custo).
ELIMINATION_BONUS_FACTOR = 100 # Bónus extra por eliminar um inimigo (multiplicado pela força do inimigo).
OVERKILL_PENALTY_FACTOR = 2    # Penalização por causar muito mais dano do que a vida restante do inimigo.


# Bónus de Prioridade por Tipo de Inimigo
# Incentivam o robot a focar em tipos de inimigos mais perigosos.
ARTILLERY_TYPE_BONUS = 10000   # Bónus para priorizar Artilharia.
TANK_TYPE_BONUS = 5000         # Bónus para priorizar Tanques.



# Calcula o dano potencial que um inimigo pode infligir.
# O dano é proporcional à força do inimigo e à sua percentagem de vida atual.
# Retorna o dano estimado que o inimigo causará. Retorna 0 se o inimigo não existir ou estiver morto.
def calculate_incoming_damage(enemy):
    if not enemy or not enemy.is_alive():
        return 0
    max_hp = enemy.max_health if enemy.max_health > 0 else 1
    percentage_life = enemy.current_health / max_hp
    return enemy.force * percentage_life



# Identifica e filtra os candidatos a alvo para o turno atual.
# Filtra inimigos mortos, slots já atacados neste turno ou slots já agendados para ataque.
# Dá prioridade a inimigos que ainda possuem ataques disponíveis (ameaças ativas).
# Retorna uma lista contendo os candidatos válidos.
def get_target_candidates(enemies_list, robot, temp_slots_attacked):
    all_candidates = []
    for i, enemy in enumerate(enemies_list):
        slot_id = i + 1
        if (enemy and enemy.is_alive() and
                slot_id not in robot.slots_attacked_this_turn and
                slot_id not in temp_slots_attacked):
            all_candidates.append((slot_id, enemy))

    attacking_candidates = [c for c in all_candidates if c[1].num_attacks_available > 0]
    return attacking_candidates if attacking_candidates else all_candidates



# Calcula uma pontuação (score) para um determinado ataque contra um inimigo.
# A pontuação baseia-se na eficiência do dano por custo de energia, bónus por eliminação, 
# penalizações por "overkill" (dano excessivo desnecessário) e prioridade por tipo de inimigo.
# Retorna a pontuação calculada para a ação.
def calculate_attack_score(enemy, atk_name, atk_info):
    current_threat = calculate_incoming_damage(enemy)
    cost = atk_info["cost"]
    damage_dealt = atk_info["damage"]

    predicted_health = max(0, enemy.current_health - damage_dealt)

    max_hp = enemy.max_health if enemy.max_health > 0 else 1
    new_threat = 0
    if predicted_health > 0:
        new_threat = enemy.force * (predicted_health / max_hp)

    damage_prevented = current_threat - new_threat

    efficiency = damage_prevented / (cost + 0.1)
    score = efficiency * EFFICIENCY_MULTIPLIER

    if predicted_health == 0:
        score += enemy.force * ELIMINATION_BONUS_FACTOR
        overkill_damage = damage_dealt - enemy.current_health
        score -= overkill_damage * OVERKILL_PENALTY_FACTOR

    if enemy.type == "Artillery":
        score += ARTILLERY_TYPE_BONUS
    if enemy.type == "Tank":
        score += TANK_TYPE_BONUS

    return score



# Determina a melhor ação de ataque a realizar entre os candidatos disponíveis.
# Itera sobre todos os candidatos e tipos de ataque, verificando se há energia suficiente (respeitando a reserva) e escolhendo a ação com o maior score.
def find_best_action(candidates, temp_energy, energy_reserve):
    best_option = None

    for slot_id, enemy in candidates:
        for atk_name in ["sound", "touch", "crane"]:
            atk_info = ROBOT_ATTACKS[atk_name]
            cost = atk_info["cost"]

            if temp_energy - cost < energy_reserve:
                continue

            score = calculate_attack_score(enemy, atk_name, atk_info)

            if best_option is None or score > best_option["score"]:
                best_option = {
                    "slot_id": slot_id,
                    "enemy": enemy,
                    "attack": atk_name,
                    "score": score,
                    "cost": cost
                }
    return best_option



# Função de callback (closure) para executar a animação física do ataque.
def create_action_callback(robot, enemies_list, tank_pair, medium_motor, color_sensor, atk_type, s_id, tgt_enemy):
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



# Avalia e executa uma cura de emergência se o dano iminente for letal.
# Verifica se o dano total previsto reduzirá a vida do robot a zero ou menos.
# Se sim, procura a cura mais barata que garanta a sobrevivência e a executa.
def handle_emergency_heal(robot, total_incoming_damage):
    if robot.heal_used_this_turn:
        return

    is_lethal = (robot.current_health - total_incoming_damage) <= 0
    
    if is_lethal and total_incoming_damage > 0:
        health_needed = total_incoming_damage - robot.current_health + 1
        print(f"ALERTA: Dano iminente ({total_incoming_damage:.0f}) é letal! "
              f"Vida atual: {robot.current_health:.0f}. Vida necessária: {health_needed:.0f}.")

        best_heal = None
        sorted_heals = sorted(ROBOT_HEALS.items(), key=lambda item: item[1]['cost'])

        for heal_type, heal_info in sorted_heals:

            if heal_info['health_recovered'] >= health_needed:
                if robot.energy - heal_info['cost'] >= 50:
                    best_heal = (heal_type, heal_info)
                    break 

        if best_heal:
            heal_type, heal_info = best_heal
            print(f"A usar a cura de emergência '{heal_type}' "
                  f"(Custo: {heal_info['cost']} EN, Cura: {heal_info['health_recovered']} HP).")
            robot.heal(heal_type)
        else:
            print("NÃO É POSSÍVEL CURAR-SE: Energia insuficiente para evitar a morte completa.")



# Calcula o dano de retaliação dos inimigos sobreviventes e tenta prevenir a morte do robot.
# Soma o dano de todos os inimigos vivos que ainda podem atacar e chama `handle_emergency_heal` se houver dano letal previsto.
def check_and_prevent_death(robot, enemies_list):

    total_post_turn_damage = 0
    
    for enemy in enemies_list:
        if enemy and enemy.is_alive():
            if enemy.num_attacks_available > 0:
                
                max_hp = enemy.max_health if enemy.max_health > 0 else 1
                percentage_life = enemy.current_health / max_hp
                damage = enemy.force * percentage_life
                total_post_turn_damage += damage
    
    if total_post_turn_damage > 0:
        print(f"Dano total previsto dos inimigos: {total_post_turn_damage:.1f}")
        handle_emergency_heal(robot, total_post_turn_damage)
    else:
        print("Nenhum dano iminente (inimigos mortos ou sem ataques).")



# Lógica principal do turno do robot.
# Coordena o planeamento e execução do turno, dividido em:
# Verificação de vitória ou falta de energia.
# Planeamento de ataques (seleção de alvos e gestão de energia).
# Execução da animação de ataque.
# Verificação final para verificar morte iminente.

def robot_turn_logic(tank_pair, medium_motor, color_sensor, gyro,
                      us_sensor, spin_speed, forward_speed,
                      robot, enemies_list):

    if not any(e and e.is_alive() for e in enemies_list):
        print("Todos os inimigos eliminados.")
        return

    energy_reserve = (MINIMUM_SURVIVAL_ENERGY if robot.current_health < LOW_HEALTH_THRESHOLD
                    else NORMAL_ENERGY_RESERVE)

    temp_energy = robot.energy
    scheduled_actions = {}
    temp_slots_attacked = set()

    while True:
        candidates = get_target_candidates(enemies_list, robot, temp_slots_attacked)
        if not candidates:
            break

        best_option = find_best_action(candidates, temp_energy, energy_reserve)
        if not best_option:
            break
        
        slot = best_option["slot_id"]
        attack_type = best_option["attack"]
        target_enemy = best_option["enemy"]
        cost = best_option["cost"]

        temp_energy -= cost
        temp_slots_attacked.add(slot)

        action_callback = create_action_callback(
            robot, enemies_list, tank_pair, medium_motor, color_sensor,
            attack_type, slot, target_enemy
        )
        scheduled_actions[slot - 1] = action_callback

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
        next_turn_energy = robot.energy + (robot.energy * 0.5)
        print(f"A poupar energia. Atual: {robot.energy}. Próximo turno: {next_turn_energy:.0f}")

    check_and_prevent_death(robot, enemies_list)