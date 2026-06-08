import pygame
import sys
import json
import random
import os

# Configurações Iniciais
pygame.init()
LARGURA, ALTURA = 1000, 800
LINHA_LARGURA = 10

COR_FUNDO = (10, 15, 35)
COR_LINHA = (40, 90, 180)
COR_CIRCULO = (0, 220, 255)
COR_X = (255, 70, 140)
COR_X_SUMIR = (255, 170, 210)

COR_TEXTO = (255, 255, 255)
COR_BOTAO = (110, 50, 255)
COR_BOTAO_HOVER = (140, 80, 255)

TAB_X = 230
TAB_Y = 120
CELULA = 180

FONTE_MSG = pygame.font.SysFont("Segoe UI", 36, bold=True)
FONTE_BOTAO = pygame.font.SysFont("Segoe UI", 24, bold=True)

tela = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Jogo da Velha - Interface Moderna")

# Estado do Jogo
tabuleiro = [[0 for _ in range(3)] for _ in range(3)]
pecas_j1 = []
pecas_j2 = []

jogador = 1
jogo_acabou = False

rect_botao = pygame.Rect(
    LARGURA // 2 - 140,
    ALTURA // 2 + 30,
    280,
    60
)

class IAAprendiz:

    def __init__(self):
        self.q_table = {}
        self.alpha = 0.5
        self.gamma = 0.95
        self.epsilon = 0.10
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.997

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
            json.dump(
                {
                    "q_table": self.q_table,
                    "padroes_usuario": self.padroes_usuario,
                    "epsilon": self.epsilon,
                    "total_partidas": self.total_partidas,
                },
                f,
            )

    def registrar_jogada_usuario(self, pos):
        self.sequencia_usuario.append(pos)
        for tamanho in (2, 3):
            if len(self.sequencia_usuario) >= tamanho:
                chave = str(tuple(self.sequencia_usuario[-tamanho:]))
                self.padroes_usuario[chave] = self.padroes_usuario.get(chave, 0) + 1

    def jogada_prevista_do_usuario(self, tab):
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
                    if tab[l][c] == 0 and freq > melhor_freq:
                        melhor_freq = freq
                        melhor_pos = proxima
        if melhor_freq >= 2:
            return melhor_pos
        return None

    def estado_para_string(self, tab):
        return str([row[:] for row in tab])

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


def verificar_vitoria_tab(tab, j):
    for i in range(3):
        if all(tab[i][c] == j for c in range(3)): return True
        if all(tab[r][i] == j for r in range(3)): return True
    if tab[0][0] == j and tab[1][1] == j and tab[2][2] == j: return True
    if tab[0][2] == j and tab[1][1] == j and tab[2][0] == j: return True
    return False


def contar_ameacas(tab, jogador_alvo):
    ameacas = 0
    linhas = []
    for i in range(3):
        linhas.append([tab[i][0], tab[i][1], tab[i][2]])
        linhas.append([tab[0][i], tab[1][i], tab[2][i]])
    linhas.append([tab[0][0], tab[1][1], tab[2][2]])
    linhas.append([tab[0][2], tab[1][1], tab[2][0]])
    for linha in linhas:
        if linha.count(jogador_alvo) == 2 and linha.count(0) == 1:
            ameacas += 1
    return ameacas


def contar_potencial(tab, jogador_alvo):
    pot = 0
    linhas = []
    for i in range(3):
        linhas.append([tab[i][0], tab[i][1], tab[i][2]])
        linhas.append([tab[0][i], tab[1][i], tab[2][i]])
    linhas.append([tab[0][0], tab[1][1], tab[2][2]])
    linhas.append([tab[0][2], tab[1][1], tab[2][0]])
    for linha in linhas:
        if linha.count(jogador_alvo) == 1 and linha.count(0) == 2:
            pot += 1
    return pot


def simular_remocao(tab, pecas_j2_sim):
    tab_novo = [row[:] for row in tab]
    if len(pecas_j2_sim) >= 3:
        r_lin, r_col = pecas_j2_sim[0]
        tab_novo[r_lin][r_col] = 0
    return tab_novo


def avaliar_tab(tab):
    if verificar_vitoria_tab(tab, 2): return 1000
    if verificar_vitoria_tab(tab, 1): return -1000

    score = 0

    score += contar_ameacas(tab, 2) * 50
    score -= contar_ameacas(tab, 1) * 60 
    score += contar_potencial(tab, 2) * 10
    score -= contar_potencial(tab, 1) * 8

    if tab[1][1] == 2: score += 25
    elif tab[1][1] == 1: score -= 20
    for l, c in [(0,0),(0,2),(2,0),(2,2)]:
        if tab[l][c] == 2: score += 10
        elif tab[l][c] == 1: score -= 8

    return score


def minimax(tab, profundidade, maximizando, pecas_j1_sim, pecas_j2_sim, alfa=-float("inf"), beta=float("inf")):
    if verificar_vitoria_tab(tab, 2): return 1000 + profundidade
    if verificar_vitoria_tab(tab, 1): return -1000 - profundidade
    if profundidade == 0:
        return avaliar_tab(tab)

    movimentos = [(l, c) for l in range(3) for c in range(3) if tab[l][c] == 0]
    if not movimentos:
        return avaliar_tab(tab)

    if maximizando:
        melhor = -float("inf")
        for l, c in movimentos:
            tab_sim = simular_remocao(tab, pecas_j2_sim)
            novas_pecas_j2 = pecas_j2_sim[1:] if len(pecas_j2_sim) >= 3 else pecas_j2_sim[:]
            tab_sim[l][c] = 2
            novas_pecas_j2.append((l, c))
            val = minimax(tab_sim, profundidade - 1, False, pecas_j1_sim[:], novas_pecas_j2, alfa, beta)
            melhor = max(melhor, val)
            alfa = max(alfa, melhor)
            if beta <= alfa:
                break
        return melhor
    else:
        melhor = float("inf")
        for l, c in movimentos:
            tab_sim = [row[:] for row in tab]
            novas_pecas_j1 = pecas_j1_sim[:]
            if len(novas_pecas_j1) >= 3:
                r_lin, r_col = novas_pecas_j1.pop(0)
                tab_sim[r_lin][r_col] = 0
            tab_sim[l][c] = 1
            novas_pecas_j1.append((l, c))
            val = minimax(tab_sim, profundidade - 1, True, novas_pecas_j1, pecas_j2_sim[:], alfa, beta)
            melhor = min(melhor, val)
            beta = min(beta, melhor)
            if beta <= alfa:
                break
        return melhor


def detectar_garfo(tab, jogador_alvo):
    garfos = []
    movimentos = [(l, c) for l in range(3) for c in range(3) if tab[l][c] == 0]
    for l, c in movimentos:
        tab[l][c] = jogador_alvo
        if contar_ameacas(tab, jogador_alvo) >= 2:
            garfos.append((l, c))
        tab[l][c] = 0
    return garfos

def verificar_vitoria(j):
    return verificar_vitoria_tab(tabuleiro, j)

def contar_duplas(jogador_alvo):
    return contar_ameacas(tabuleiro, jogador_alvo)


def desenhar_linhas():
    tela.fill(COR_FUNDO)

    sombra = pygame.Rect(TAB_X + 8, TAB_Y + 8, CELULA * 3, CELULA * 3)
    pygame.draw.rect(tela, (0, 0, 0), sombra, border_radius=25)

    board = pygame.Rect(TAB_X, TAB_Y, CELULA * 3, CELULA * 3)
    pygame.draw.rect(tela, (15, 25, 55), board, border_radius=25)

    for i in range(1, 3):
        pygame.draw.line(tela, COR_LINHA, (TAB_X + i * CELULA, TAB_Y), (TAB_X + i * CELULA, TAB_Y + CELULA * 3), 4)
        pygame.draw.line(tela, COR_LINHA, (TAB_X, TAB_Y + i * CELULA), (TAB_X + CELULA * 3, TAB_Y + i * CELULA), 4)

def desenhar_topo():
    pygame.draw.rect(tela, (20, 30, 60), (20, 20, 960, 70), border_radius=15)
    titulo = FONTE_MSG.render("JOGO DA VELHA", True, COR_TEXTO)
    tela.blit(titulo, (40, 30))
    txt = FONTE_BOTAO.render("Você vs IA", True, COR_TEXTO)
    tela.blit(txt, (780, 42))

def desenhar_painel():
    pygame.draw.rect(tela, (20, 30, 60), (800, 120, 170, 220), border_radius=15)
    titulo = FONTE_BOTAO.render("IA Aprendiz", True, COR_TEXTO)
    tela.blit(titulo, (825, 145))
    pygame.draw.line(tela, COR_X, (850, 205), (920, 275), 8)
    pygame.draw.line(tela, COR_X, (920, 205), (850, 275), 8)


def desenhar_figuras():
    for linha in range(3):
        for col in range(3):
            centro_x = TAB_X + col * CELULA + CELULA // 2
            centro_y = TAB_Y + linha * CELULA + CELULA // 2

            if tabuleiro[linha][col] == 1:
                cor = COR_CIRCULO
                if len(pecas_j1) == 3 and (linha, col) == pecas_j1[0]:
                    cor = (0, 140, 170)
                pygame.draw.circle(tela, cor, (centro_x, centro_y), 55, 10)

            elif tabuleiro[linha][col] == 2:
                cor = (COR_X_SUMIR if len(pecas_j2) == 3 and (linha, col) == pecas_j2[0] else COR_X)
                offset = 55
                pygame.draw.line(tela, cor, (centro_x - offset, centro_y - offset), (centro_x + offset, centro_y + offset), 10)
                pygame.draw.line(tela, cor, (centro_x + offset, centro_y - offset), (centro_x - offset, centro_y + offset), 10)


def exibir_final(mensagem):
    overlay = pygame.Surface((LARGURA, ALTURA))
    overlay.set_alpha(180)
    overlay.fill((0, 0, 0))
    tela.blit(overlay, (0, 0))

    card = pygame.Rect(250, 250, 500, 220)
    pygame.draw.rect(tela, (20, 30, 60), card, border_radius=20)

    texto = FONTE_MSG.render(mensagem, True, COR_TEXTO)
    tela.blit(texto, (LARGURA // 2 - texto.get_width() // 2, 300))

    mouse = pygame.mouse.get_pos()
    cor = COR_BOTAO_HOVER if rect_botao.collidepoint(mouse) else COR_BOTAO
    pygame.draw.rect(tela, cor, rect_botao, border_radius=15)

    txt = FONTE_BOTAO.render("Jogar Novamente", True, COR_TEXTO)
    tela.blit(txt, (rect_botao.centerx - txt.get_width() // 2, rect_botao.centery - txt.get_height() // 2))


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
            _registrar_historico((l, c))
            return (l, c)
        tabuleiro[l][c] = 0

    for l, c in movimentos:
        tabuleiro[l][c] = 1
        if verificar_vitoria(1):
            tabuleiro[l][c] = 0
            _registrar_historico((l, c))
            return (l, c)
        tabuleiro[l][c] = 0

    garfos_ia = detectar_garfo(tabuleiro, 2)
    if garfos_ia:
        escolha = garfos_ia[0]
        _registrar_historico(escolha)
        return escolha

    garfos_usuario = detectar_garfo(tabuleiro, 1)
    if len(garfos_usuario) == 1:
        _registrar_historico(garfos_usuario[0])
        return garfos_usuario[0]
    elif len(garfos_usuario) > 1:
        for l, c in movimentos:
            tabuleiro[l][c] = 2
            ameacas = contar_ameacas(tabuleiro, 2)
            tabuleiro[l][c] = 0
            if ameacas >= 1:
                _registrar_historico((l, c))
                return (l, c)

    prevista = ia.jogada_prevista_do_usuario(tabuleiro)
    if prevista and tabuleiro[prevista[0]][prevista[1]] == 0:
        garfos_apos_bloqueio = detectar_garfo(tabuleiro, 1)
        if len(garfos_apos_bloqueio) == 0:
            _registrar_historico(prevista)
            return prevista

    melhor_score = -float("inf")
    melhor_jogada = random.choice(movimentos)
    estado = ia.estado_para_string(tabuleiro)

    for l, c in movimentos:
        tab_sim = simular_remocao(tabuleiro, pecas_j2)
        novas_pecas_j2 = pecas_j2[1:] if len(pecas_j2) >= 3 else pecas_j2[:]
        tab_sim[l][c] = 2
        novas_pecas_j2_sim = novas_pecas_j2 + [(l, c)]

        score = minimax(tab_sim, profundidade=4, maximizando=False,
                        pecas_j1_sim=pecas_j1[:], pecas_j2_sim=novas_pecas_j2_sim)

        chave = f"{estado}|{(l, c)}"
        score += ia.q_table.get(chave, 0.0) * 0.1

        if score > melhor_score:
            melhor_score = score
            melhor_jogada = (l, c)

    _registrar_historico(melhor_jogada)
    return melhor_jogada


def _registrar_historico(jogada):
    """Registra a jogada escolhida no histórico do Q-learning."""
    estado = ia.estado_para_string(tabuleiro)
    ia.historico_partida.append((estado, jogada))

while True:
    desenhar_linhas()
    desenhar_topo()
    desenhar_painel()
    desenhar_figuras()

    if jogo_acabou:
        vencedor = (
            "J1 Ganhou! J2 Perdeu." if verificar_vitoria(1) else "J2 Ganhou! J1 Perdeu."
        )
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
                if (TAB_X <= mx <= TAB_X + CELULA * 3 and TAB_Y <= my <= TAB_Y + CELULA * 3):
                    col = (mx - TAB_X) // CELULA
                    linha = (my - TAB_Y) // CELULA

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