import os
from hardware import initialize_hardware
from tools import print_initial_setup
from game_logic import check_game_status, handle_game_over
from robot_attack_logic import robot_turn_logic
from enemy_attack_logic import enemy_attack_phase
from initialize_robot_enemies import initialize_robot, initialize_enemies_by_color
from robot_movement_logic import search_enemies
from config import (OBSTACLE_STOP_DISTANCE_CM, OBJECT_SEARCH_DISTANCE_CM, LINE_COLOR_NAME, SPIN_SEARCH_SPEED, SEARCH_TIME_LEFT_S, SEARCH_TIME_RIGHT_S)
from time import sleep


enemies = [None] * 6      # Array global para armazenar os inimigos

# Loop principal do jogo
def run_game_loop(robot, tank_pair, medium_motor, color_sensor, us_sensor, gyro, spin_speed, forward_speed, enemies):
    
    current_turn = 1


    try:
        while True:
            print("\n=== TURNO {} ===\n".format(current_turn))
            if(current_turn != 1):
                # Robot recupera 50% da energia
                # Reset aos ataques feitos e cura do turno anterior
                robot.start_new_turn()
                print("ROBOT RECUPERA 50% DE ENERGIA E DA RESET NOS REGISTOS DE ATAQUES E CURAS DO TURNO ANTERIOR")
                print("Energia do Robot: {:.0f}EN".format(robot.energy))
                
                # Inimigos do turno anterior que o robot não conseguiu matar atacam
                print("FASE DE ATAQUE DOS INIMIGOS")
                enemy_attack_phase(robot, enemies, current_turn)
                print("Vida do Robot: {:.0f}HP".format(robot.current_health))



            # Verifica se o jogo terminou
            game_status = check_game_status(robot, enemies)
            if((current_turn > 6 and game_status == "victory") or game_status == "defeat"):
                handle_game_over(game_status)
                return game_status



            # Faz reconhecimento do ambiente
            enemies_log = search_enemies(
                tank_pair=tank_pair,
                medium_motor=medium_motor, 
                color_sensor=color_sensor, 
                us_sensor=us_sensor, 
                gyro=gyro,
                spin_speed=spin_speed,
                forward_speed=forward_speed,
                enemies=enemies,
                current_turn=current_turn
            )

            # Imprime os resultados do turno
            print("\nResultado do Turno {}: {} \n".format(current_turn, enemies_log))
            
            # Atualiza o array global 'enemies' com novos inimigos encontrados.
            # Não substitui inimigos que já existem.
            new_enemies_list = initialize_enemies_by_color(enemies_log, current_turn,enemies)
            
            for i, new_enemy in enumerate(new_enemies_list):
                if enemies[i] is None and new_enemy is not None:
                    print("Novo inimigo adicionado na Posicao {} do array enemies".format(i))
                    enemies[i] = new_enemy # Adiciona a nova instância
            # Imprime o estado atual do campo de batalha
            print("\n--- Campo de Batalha Atual (Turno {}) ---".format(current_turn))
            for i, enemy in enumerate(enemies):
                if enemy is None:
                    print("Slot {}: Vazio".format(i+1))
                else:
                    print("Slot {}: {}".format(i+1, enemy))

            # Robot utiliza a cura e ataques que pode fazer no turno
            print("\nFASE DE ATAQUE / CURA DO ROBOT")
            robot_turn_logic(
                tank_pair=tank_pair,
                medium_motor=medium_motor, 
                color_sensor=color_sensor, 
                gyro=gyro,
                us_sensor=us_sensor, 
                spin_speed=spin_speed,
                forward_speed=forward_speed,
                robot=robot, 
                enemies_list=enemies)
            
             # Imprime o estado atual do campo de batalha
            print("\n--- Campo de Batalha Apos Ataques (Turno {}) ---".format(current_turn))
            for i, enemy in enumerate(enemies):
                if enemy is None:
                    print("Slot {}: Vazio".format(i+1))
                else:
                    print("Slot {}: {}".format(i+1, enemy))



            game_status = check_game_status(robot, enemies)
            if((current_turn > 6 and game_status == "victory") or game_status == "defeat"):
                handle_game_over(game_status)
                return game_status
            
            # Avança para o próximo turno
            current_turn += 1
            print("-" * 30)

    except KeyboardInterrupt:
        print("\nPrograma interrompido pelo utilizador.")
    except Exception as e:
        print("Erro: {}".format(e))
    finally:
        tank_pair.off()
        medium_motor.off()

def main():

    n = 0
    simulations=500
    wins = 0
    defeats = 0

    while(n<simulations):
        print("A começar simulação {} de {}...".format(n,simulations))
        enemies = [None] * 6    
        tank_pair, medium_motor, color_sensor, us_sensor, gyro_sensor = initialize_hardware()
        
        if tank_pair is not None:
            
            robot = initialize_robot()      # Cria a instância do robot
            print_initial_setup()           # Imprime a tabela do enunciado preenchida 
            # Loop principal do jogo
            status = run_game_loop(
                robot=robot,
                tank_pair=tank_pair,
                medium_motor=medium_motor, 
                color_sensor=color_sensor, 
                us_sensor=us_sensor, 
                gyro=gyro_sensor,
                spin_speed=20,
                forward_speed=-20,
                enemies=enemies
            )

            if(status == "victory"):
                wins+=1
            if(status == "defeat"):
                defeats+=1
            

            # # --- Processar e imprimir o relatório final de inimigos ---
            # print("\n" + "="*40)
            # print("--- RELATORIO FINAL DE INIMIGOS ---")
            # for i, color in enumerate(enemies_log):
            #     position = i + 1
            #     if color == "Empty":
            #         print("Posicao {}: Vazio".format(position)) # O 'ç' em 'Posicao' foi removido para evitar erros de codificacao.
            #     else:
            #         found_enemy = False
            #         # Procura no dicionário importado qual inimigo corresponde à cor
            #         for enemy_type, stats in INIMIGO_STATS.items():
            #             if stats['cor'] == color:
            #                 print("Posicao {}: Encontrado - {}".format(position, enemy_type)) # O 'ç' em 'Posicao' foi removido para evitar erros de codificacao.
            #                 found_enemy = True
            #                 break
            #         if not found_enemy:
            #             # Lida com cores detetadas mas não definidas no dicionário
            #             print("Posicao {}: Inimigo de cor desconhecida ({})".format(position, color)) # O 'ç' em 'Posicao' foi removido para evitar erros de codificacao.
            # print("="*40)
        
        else:
            print("Falha ao inicializar hardware. A sair...")
        n+=1
        
    
    print("O robot ganhou {} vezes".format(wins))
    print("O robot perdeu {} vezes".format(defeats))
    print("Winrate: {}".format(wins/simulations))

if __name__ == "__main__":
    main()