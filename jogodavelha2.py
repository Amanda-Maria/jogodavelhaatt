import pygame
import sys
import json
import random
import os

# Configurações Iniciais
pygame.init()
LARGURA, ALTURA = 600, 600
LINHA_LARGURA = 15
COR_FUNDO = (28, 170, 156)
COR_LINHA = (23, 145, 135)
COR_CIRCULO = (255, 215, 0) # Amarelo Ouro
COR_X = (0, 0, 0) # MUDADO: X padrão agora é totalmente preto
COR_X_SUMIR = (180, 195, 190) # MUDADO: X que vai sumir agora é um cinza claro adaptado ao fundo
COR_TEXTO = (255, 255, 255)
COR_BOTAO = (30, 30, 30)
COR_BOTAO_HOVER = (50, 50, 50)

# Fontes
FONTE_MSG = pygame.font.SysFont("Arial", 32, bold=True)
FONTE_BOTAO = pygame.font.SysFont("Arial", 24, bold=True)

tela = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption('Jogo da Velha Infinito')

# Estado do Jogo
tabuleiro = [[0 for _ in range(3)] for _ in range(3)]
pecas_j1 = []
pecas_j2 = []
jogador = 1
jogo_acabou = False
rect_botao = pygame.Rect(LARGURA // 2 - 100, ALTURA // 2 + 20, 200, 50)

class IAAprendiz:

    def __init__(self):
        self.q_table = {}
        self.alpha = 0.5
        self.gamma = 0.95
        self.epsilon = 0.15     
        self.epsilon_min = 0.02
        self.epsilon_decay = 0.995

        self.historico_partida = []
        self.padroes_usuario = {}
        self.sequencia_usuario = []
        self.total_partidas = 0

        self.carregar()

    def carregar(self):
        if os.path.exists("ia_memoria.json"):
            with open("ia_memoria.json", "r") as f:
                dados = json.load(f)
                self.q_table = dados.get("q_table", {})
                self.padroes_usuario = dados.get("padroes_usuario", {})
                self.epsilon = dados.get("epsilon", self.epsilon)
                self.total_partidas = dados.get("total_partidas", 0)

    def salvar(self):
        with open("ia_memoria.json", "w") as f:
            json.dump({
                "q_table": self.q_table,
                "padroes_usuario": self.padroes_usuario,
                "epsilon": self.epsilon,
                "total_partidas": self.total_partidas,
            }, f)

    def registrar_jogada_usuario(self, pos):
        # Guarda a jogada do usuário e incrementa a contagem do padrão.
        self.sequencia_usuario.append(pos)
        # Considera janelas de 2 e 3 jogadas como "padrão"
        for tamanho in (2, 3):
            if len(self.sequencia_usuario) >= tamanho:
                chave = str(tuple(self.sequencia_usuario[-tamanho:]))
                self.padroes_usuario[chave] = self.padroes_usuario.get(chave, 0) + 1

    def jogada_prevista_do_usuario(self, tabuleiro):
        
        # Tenta prever a próxima jogada do usuário com base nos padrões mais frequentes observados. Retorna a posição prevista ou None.
        if len(self.sequencia_usuario) < 1:
            return None

        melhor_pos = None
        melhor_freq = 0

        for tamanho in (2, 1):
            if len(self.sequencia_usuario) < tamanho:
                continue
            prefixo = tuple(self.sequencia_usuario[-tamanho:])
            for chave, freq in self.padroes_usuario.items():
                seq = eval(chave) 
                if seq[:tamanho] == prefixo and len(seq) > tamanho:
                    proxima = seq[tamanho]
                    l, c = proxima
                    if tabuleiro[l][c] == 0 and freq > melhor_freq:
                        melhor_freq = freq
                        melhor_pos = proxima

        if melhor_freq >= 2:
            return melhor_pos
        return None

    def estado_para_string(self, tabuleiro):
        return str([row[:] for row in tabuleiro])

    def movimentos_possiveis(self, tabuleiro):
        return [(l, c) for l in range(3) for c in range(3) if tabuleiro[l][c] == 0]

    def escolher_jogada(self, tabuleiro):
        estado = self.estado_para_string(tabuleiro)
        movimentos = self.movimentos_possiveis(tabuleiro)

        if random.random() < self.epsilon:
            jogada = random.choice(movimentos)
        else:
            melhor_valor = -float("inf")
            melhor_jogada = random.choice(movimentos)
            for mov in movimentos:
                chave = f"{estado}|{mov}"
                valor = self.q_table.get(chave, 0.0)
                if valor > melhor_valor:
                    melhor_valor = valor
                    melhor_jogada = mov
            jogada = melhor_jogada

        self.historico_partida.append((estado, jogada))
        return jogada

    def aprender(self, recompensa_final):

        recompensa = recompensa_final
        for estado, jogada in reversed(self.historico_partida):
            chave = f"{estado}|{jogada}"
            valor_atual = self.q_table.get(chave, 0.0)
            self.q_table[chave] = valor_atual + self.alpha * (recompensa - valor_atual)
            recompensa *= self.gamma

        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
        self.total_partidas += 1

        self.salvar()
        self.historico_partida.clear()
        self.sequencia_usuario.clear()

ia = IAAprendiz()

def desenhar_linhas():
    tela.fill(COR_FUNDO)
    pygame.draw.line(tela, COR_LINHA, (0, 200), (600, 200), LINHA_LARGURA)
    pygame.draw.line(tela, COR_LINHA, (0, 400), (600, 400), LINHA_LARGURA)
    pygame.draw.line(tela, COR_LINHA, (200, 0), (200, 600), LINHA_LARGURA)
    pygame.draw.line(tela, COR_LINHA, (400, 0), (400, 600), LINHA_LARGURA)

def desenhar_figuras():
    for linha in range(3):
        for col in range(3):
            centro_x, centro_y = col * 200 + 100, linha * 200 + 100

            if tabuleiro[linha][col] == 1:
                # Efeito visual: se for a peça que vai sumir, fica mais escura
                cor = (180, 150, 0) if len(pecas_j1) == 3 and (linha, col) == pecas_j1[0] else COR_CIRCULO
                pygame.draw.circle(tela, cor, (centro_x, centro_y), 60, LINHA_LARGURA)
            elif tabuleiro[linha][col] == 2:
                # MUDADO: Lógica de cor do X (Preto padrão vs Cinza para sumir)
                cor = COR_X_SUMIR if len(pecas_j2) == 3 and (linha, col) == pecas_j2[0] else COR_X
                offset = 55
                pygame.draw.line(tela, cor, (centro_x - offset, centro_y + offset), (centro_x + offset, centro_y - offset), LINHA_LARGURA)
                pygame.draw.line(tela, cor, (centro_x - offset, centro_y - offset), (centro_x + offset, centro_y + offset), LINHA_LARGURA)

def verificar_vitoria(j):
    for i in range(3):
        if all(tabuleiro[i][c] == j for c in range(3)): return True
        if all(tabuleiro[r][i] == j for r in range(3)): return True
    if tabuleiro[0][0] == j and tabuleiro[1][1] == j and tabuleiro[2][2] == j: return True
    if tabuleiro[0][2] == j and tabuleiro[1][1] == j and tabuleiro[2][0] == j: return True
    return False

def contar_duplas(jogador_alvo):
    pontos = 0
    linhas = []
    for i in range(3):
        linhas.append([tabuleiro[i][0], tabuleiro[i][1], tabuleiro[i][2]])
        linhas.append([tabuleiro[0][i], tabuleiro[1][i], tabuleiro[2][i]])
    linhas.append([tabuleiro[0][0], tabuleiro[1][1], tabuleiro[2][2]])
    linhas.append([tabuleiro[0][2], tabuleiro[1][1], tabuleiro[2][0]])
    for linha in linhas:
        if linha.count(jogador_alvo) == 2 and linha.count(0) == 1:
            pontos += 1
    return pontos

def exibir_final(mensagem):
    overlay = pygame.Surface((LARGURA, 200))
    overlay.set_alpha(220)
    overlay.fill((0, 0, 0))
    tela.blit(overlay, (0, ALTURA // 2 - 100))
    texto_surf = FONTE_MSG.render(mensagem, True, COR_TEXTO)
    texto_rect = texto_surf.get_rect(center=(LARGURA // 2, ALTURA // 2 - 40))
    tela.blit(texto_surf, texto_rect)
    mouse_pos = pygame.mouse.get_pos()
    cor_atual = COR_BOTAO_HOVER if rect_botao.collidepoint(mouse_pos) else COR_BOTAO
    pygame.draw.rect(tela, cor_atual, rect_botao, border_radius=12)
    texto_btn = FONTE_BOTAO.render("Jogar Novamente", True, COR_TEXTO)
    texto_btn_rect = texto_btn.get_rect(center=rect_botao.center)
    tela.blit(texto_btn, texto_btn_rect)

def reiniciar_jogo():
    global jogador, jogo_acabou, tabuleiro, pecas_j1, pecas_j2
    tabuleiro = [[0 for _ in range(3)] for _ in range(3)]
    pecas_j1, pecas_j2 = [], []
    jogador = 1
    jogo_acabou = False


def jogada_ia():

    movimentos = [(l, c) for l in range(3) for c in range(3) if tabuleiro[l][c] == 0]

    for l, c in movimentos:
        tabuleiro[l][c] = 2
        if verificar_vitoria(2):
            tabuleiro[l][c] = 0
            return (l, c)
        tabuleiro[l][c] = 0

    for l, c in movimentos:
        tabuleiro[l][c] = 1
        if verificar_vitoria(1):
            tabuleiro[l][c] = 0
            return (l, c)
        tabuleiro[l][c] = 0

    prevista = ia.jogada_prevista_do_usuario(tabuleiro)
    if prevista and tabuleiro[prevista[0]][prevista[1]] == 0:
        tabuleiro[prevista[0]][prevista[1]] = 2
        duplas_ganhas = contar_duplas(2)
        tabuleiro[prevista[0]][prevista[1]] = 0
        duplas_ataque_max = max(
            (contar_duplas(2) for l, c in movimentos
             if (tabuleiro.__setitem__(l, tabuleiro[l]) or True)
             ),
            default=0,
        )
        return prevista  

    melhor_score = -float("inf")
    melhor_jogada = random.choice(movimentos)

    estado = ia.estado_para_string(tabuleiro)

    for l, c in movimentos:
        score = 0.0

        if (l, c) == (1, 1):
            score += 30
        elif (l, c) in [(0, 0), (0, 2), (2, 0), (2, 2)]:
            score += 15

        tabuleiro[l][c] = 2
        score += contar_duplas(2) * 20
        score -= contar_duplas(1) * 15
        tabuleiro[l][c] = 0

        chave = f"{estado}|{(l, c)}"
        score += ia.q_table.get(chave, 0.0) * 10

        if score > melhor_score:
            melhor_score = score
            melhor_jogada = (l, c)

    ia.historico_partida.append((estado, melhor_jogada))
    return melhor_jogada

# Loop Principal
while True:
    desenhar_linhas()
    desenhar_figuras()

    if jogo_acabou:
        vencedor = "J1 Ganhou! J2 Perdeu." if verificar_vitoria(1) else "J2 Ganhou! J1 Perdeu."
        exibir_final(vencedor)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            if jogo_acabou:
                if rect_botao.collidepoint(mx, my):
                    reiniciar_jogo()
            else:
                linha, col = my // 200, mx // 200
                if tabuleiro[linha][col] == 0:
                    lista_atual = pecas_j1 if jogador == 1 else pecas_j2

                    if len(lista_atual) == 3:
                        r_lin, r_col = lista_atual.pop(0)
                        tabuleiro[r_lin][r_col] = 0

                    tabuleiro[linha][col] = jogador
                    lista_atual.append((linha, col))

                    ia.registrar_jogada_usuario((linha, col))

                    if verificar_vitoria(jogador):
                        ia.aprender(-100)
                        jogo_acabou = True
                    else:
                        jogador = 2

    if not jogo_acabou and jogador == 2:
        linha, col = jogada_ia()

        if len(pecas_j2) == 3:
            r_lin, r_col = pecas_j2.pop(0)
            tabuleiro[r_lin][r_col] = 0

        tabuleiro[linha][col] = 2
        pecas_j2.append((linha, col))

        if verificar_vitoria(2):
            ia.aprender(100)
            jogo_acabou = True
        else:
            jogador = 1

    pygame.display.update()