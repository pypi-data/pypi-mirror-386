import numpy as np
import matplotlib.pyplot as plt
import sympy as sp

# Função de Ajuste Polinomial
def ajuste_polinomial(valores_x:list, valores_y:list, grau:int):

    # Construção da Matriz de Vandermonde
    matriz_list = []

    for valor in valores_x:
        linha = []
        for i in range(grau + 1):
            linha.append(valor**i)
        matriz_list.append(linha)

    x_matriz = np.array(matriz_list)
    
    # Construção da Matriz dos Valores de y

    y_list = []

    for valor in valores_y:
        y_list.append(valor)

    y_list = np.array(y_list)

    # Construção da Matriz de Parâmetros

    matriz_T = x_matriz.T

    coeficientes_list = np.linalg.solve(matriz_T @ x_matriz, matriz_T @ y_list)

    # Função Polinomial Aproximadora

    x = sp.Symbol("x")
    expr = 0

    for i in range(len(coeficientes_list)):
        expr += coeficientes_list[i]*x**i
    
    print(f"Função Polinomial Aproximadora {expr}")

    # Plotando o Gráfico

    f = sp.lambdify(x, expr, "numpy")
    x_func = np.linspace(min(valores_x), max(valores_x), 200)
    y_func = f(x_func)

    plt.scatter(valores_x, valores_y, color="blue", marker="o", label="Dados Fornecidos")
    plt.plot(x_func, y_func, color="black", linewidth=2, label="Função Aproximadora")

    plt.title("Gráfico dos Dados Fornecidos e da Função Aproximadora")
    plt.xlabel("Eixo x")
    plt.ylabel("Eixo y")
    plt.margins(x=0.1, y=0.1)
    plt.grid(True)
    plt.show()

ajuste_polinomial([0, 1, 2, 3, 4, 5], [2.2, 2.8, 3.6, 4.5, 5.1, 5.9], 2)
