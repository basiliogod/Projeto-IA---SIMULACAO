from robot_class import ROBOT_ATTACKS, ROBOT_HEALS, Robot, ROBOT_MAX_HEALTH
from robot_movement_logic import rotate_perform_action_return
from robot_attacks import sound_attack, touch_attack, crane_attack
energy_reserve = 100                   #sim


#sim
def teste():
    print( "Teste")
#/sim


# Lógica de cura e de ataque do robot por turno
def robot_turn_logic(tank_pair, medium_motor, color_sensor, gyro,
                     us_sensor, spin_speed, forward_speed,
                     robot, enemies_list):

    # ==============================
    # 1️⃣ Análise global
    # ==============================
    alive_enemies = [e for e in enemies_list if e and e.is_alive()]
    threatening_enemies = [e for e in alive_enemies if e.num_attacks_available > 0]

    if not alive_enemies:
        print("Todos os inimigos estão mortos. Fim de jogo.")
        return

    # ==============================
    # 2️⃣ Cura (apenas se houver ameaça)
    # ==============================
    if threatening_enemies:
        if robot.current_health < (2/3) * ROBOT_MAX_HEALTH and not robot.heal_used_this_turn:
            for heal_type in ["heal3", "heal2", "heal1"]:
                heal_info = ROBOT_HEALS[heal_type]
                if robot.energy - heal_info["cost"] >= energy_reserve:
                    if robot.heal(heal_type):
                        print(f"Robot usou {heal_type}.")
                        return

    # ==============================
    # 3️⃣ MODO CLEANUP (ninguém ataca)
    # ==============================
    cleanup_mode = not threatening_enemies

    if cleanup_mode:
        print("Modo cleanup: nenhum inimigo pode atacar. Robot vai acabar o jogo.")

    # ==============================
    # 4️⃣ LÓGICA DE ATAQUE
    # ==============================
    scheduled_actions = {}
    temp_energy = robot.energy
    temp_slots_attacked = set()

    while True:

        candidates = []
        for i, enemy in enumerate(enemies_list):
            slot_id = i + 1
            if (
                enemy and enemy.is_alive()
                and slot_id not in robot.slots_attacked_this_turn
                and slot_id not in temp_slots_attacked
            ):
                candidates.append((slot_id, enemy))

        if not candidates:
            break

        best_option = None

        for slot_id, enemy in candidates:
            attack_to_use = None
            is_kill = False

            # Tentativa de kill primeiro
            for atk in ["sound", "touch", "crane"]:
                atk_info = ROBOT_ATTACKS[atk]
                if (
                    enemy.current_health <= atk_info["damage"]
                    and temp_energy - atk_info["cost"] >= energy_reserve
                ):
                    attack_to_use = atk
                    is_kill = True
                    break

            # Se não mata:
            if not is_kill:
                if cleanup_mode:
                    # Em cleanup, qualquer ataque forte permitido
                    for atk in ["crane", "touch", "sound"]:
                        atk_info = ROBOT_ATTACKS[atk]
                        if temp_energy - atk_info["cost"] >= energy_reserve:
                            attack_to_use = atk
                            break
                else:
                    # Com ameaça, mantém lógica conservadora
                    for atk in ["crane", "touch", "sound"]:
                        atk_info = ROBOT_ATTACKS[atk]
                        if temp_energy - atk_info["cost"] >= energy_reserve:
                            attack_to_use = atk
                            break

            if attack_to_use:
                score = enemy.force * (enemy.current_health / enemy.max_health)
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
            break

        target = best_option["enemy"]
        slot = best_option["slot_id"]
        attack = best_option["attack"]

        temp_energy -= ROBOT_ATTACKS[attack]["cost"]
        temp_slots_attacked.add(slot)

        def create_action_callback(atk_type, s_id, tgt_enemy):
            def callback():
                if robot.attack_slot(atk_type, s_id, enemies_list):
                    if atk_type == "sound":
                        sound_attack()
                    elif atk_type == "touch":
                        touch_attack(tank_pair)
                    elif atk_type == "crane":
                        crane_attack(tank_pair, medium_motor, color_sensor)

                    if not tgt_enemy.is_alive():
                        print(f"Inimigo {tgt_enemy.type} morreu.")
            return callback

        scheduled_actions[slot - 1] = create_action_callback(attack, slot, target)

    # ==============================
    # 5️⃣ Executar
    # ==============================
    if scheduled_actions:
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
        print("Robot não atacou para manter reserva.")
