
# ===============================
# Fixed Point Iteration
# ===============================
fixed_point = """
def fixed_point_iteration(f, x_init, epsilon=1e-6, n_iter=100):
    x = x_init
    for iter in range(n_iter):
        x_updated = f(x)
        error = abs(x_updated - x)
        x = x_updated
        if error < epsilon:
            print(f"Converged after {iter + 1} iterations")
            return x_updated
    print("Did not converge within the maximum number of iterations.")
    return None
"""

# ===============================
# Bisection Method
# ===============================
bisection = """
def bisection_method(f, a, b, epsilon=1e-6):
    if f(a) * f(b) >= 0:
        print("You have chosen the wrong interval.")
        return None
    while abs(b - a) > epsilon:
        c = (a + b) / 2
        if f(a) * f(c) <= 0:
            b = c
        else:
            a = c
    print(f"approximate value is: {(a + b) / 2 :.6f}")
    return (a + b) / 2
"""

# ===============================
# Regula Falsi Method
# ===============================
regula_falsi = """
def regula_falsi(f, a, b, epsilon=1e-6):
    if f(a) * f(b) >= 0:
        print("You have chosen the wrong interval.")
        return None
    c = b - (f(b) * (b - a)) / (f(b) - f(a))
    while abs(f(c)) > epsilon:
        if f(a) * f(c) < 0:
            b = c
        else:
            a = c
        c = b - (f(b) * (b - a)) / (f(b) - f(a))
    print(f"Approximate value is: {c:.6f}")
    return c
"""

# ===============================
# Newton-Raphson Method
# ===============================
newton_raphson = """
def newton_raphson(f, df, x0, epsilon=1e-6):
    x = x0
    x_updated = x - f(x) / df(x)
    while abs(x_updated - x) > epsilon or abs(f(x_updated)) > epsilon:
        x = x_updated
        x_updated = x - f(x) / df(x)
    print(f"Approximate value is: {x_updated:.6f}")
    return x_updated
"""

# ===============================
# Secant Method
# ===============================
secant = """
def secant_method(f, x0, x1, epsilon=1e-6):
    x_updated = x1 - f(x1) * (x1 - x0) / (f(x1) - f(x0))
    while abs(x_updated - x1) > epsilon or abs(f(x_updated)) > epsilon:
        x0 = x1
        x1 = x_updated
        x_updated = x1 - f(x1) * (x1 - x0) / (f(x1) - f(x0))
    print(f"Approximate value is: {x_updated:.6f}")
"""

# ===============================
# Row Operations & Linear System Solver
# ===============================
linear = """
def row_swap(matrix, i, j):
    matrix = np.array(matrix)
    matrix[[i, j]] = matrix[[j, i]]
    return matrix

def row_add(matrix, i, j, alpha):
    matrix = np.array(matrix)
    matrix[i] = matrix[i] + alpha * matrix[j]
    return matrix

def row_reduction(matrix):
    matrix = np.array(matrix)
    n = len(matrix)
    for i in range(n):
        if matrix[i][i] == 0:
            for k in range(i+1, n):
                if matrix[k][i] != 0:
                    matrix = row_swap(matrix, i, k)
                    break
        for j in range(i+1, n):
            alpha = -1 * matrix[j][i] / matrix[i][i]
            matrix = row_add(matrix, j, i, alpha)
    return matrix.tolist()

def back_substitution(matrix):
    n = len(matrix)
    x = [0] * n
    for i in range(n-1, -1, -1):
        sum_known = 0
        for j in range(i+1, n):
            sum_known += matrix[i][j] * x[j]
        x[i] = (matrix[i][-1] - sum_known) / matrix[i][i]
    return x

def forward_substitution(matrix):
    n = len(matrix)
    x = [0] * n
    for i in range(n):
        sum_known = 0
        for j in range(i):
            sum_known += matrix[i][j] * x[j]
        x[i] = (matrix[i][-1] - sum_known) / matrix[i][i]
    return x

def solve_linear_system(matrix, triangular=None):
    matrix = np.array(matrix, dtype=float)
    if triangular == "upper":
        return back_substitution(matrix)
    elif triangular == "lower":
        return forward_substitution(matrix)
    else:
        row_reduced = row_reduction(matrix)
        return back_substitution(row_reduced)
"""

# ===============================
# Function to print all code
# ===============================
def full():
    all_codes = [
        fixed_point,
        bisection,
        regula_falsi,
        newton_raphson,
        secant,
        linear
    ]
    for code in all_codes:
        print(code)
        print("\n" + "="*50 + "\n")

# ===============================
# Example usage:
# ===============================
# print_all_numerical_methods()

