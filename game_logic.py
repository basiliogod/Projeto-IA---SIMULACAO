from tools import playSound


# Verifica se o jogo terminou
# Retorna 'victory' se todos os inimigos foram mortos
# Retorna 'defeat' se o robot morreu
def check_game_status(robot, enemies_list):

    if not robot.is_alive():
        return "defeat"

    victory = True
    for enemy in enemies_list:
        if enemy and enemy.is_alive():
            victory = False
            break

    if victory:
        return "victory"



# Informa do fim de jogo
def handle_game_over(game_status):
    if game_status == "victory":
        playSound("win.wav")
        print("\n\n=======================================")
        print("VITORIA! Todos os inimigos foram mortos!")
        print("========================================")
    elif game_status == "defeat":
        playSound("defeat.wav")
        print("\n\n======================================")
        print("       DERROTA! O Robot morreu!       ")
        print("======================================")
