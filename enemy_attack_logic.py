# Lógica de ataque dos inimigos contra o robot
# Um inimigo só ataca se o turno atual for maior que o seu turno de spawn
def enemy_attack_phase(robot, enemies_list, current_turn):
    total_damage = 0
    
    for enemy in enemies_list:
        
        if enemy and enemy.is_alive() and current_turn > enemy.spawn_turn and enemy.num_attacks_available > 0:
            enemy_damage = enemy.force * (enemy.current_health / enemy.max_health) # Add 1 to avoid division by zero
            print("O Inimigo '{}', que spawnou no Turno {} no slot {}, atacou o Robot com {} de dano.".format(
                enemy.type, enemy.spawn_turn, enemy.position, enemy_damage
            ))
            total_damage += enemy_damage
            enemy.num_attacks_available -= 1

            if enemy.num_attacks_available == 0:
                print("O Inimigo '{}' acabou os seus ataques".format(enemy.type))
    
    if total_damage > 0:
        robot.receive_damage(total_damage)
    
    