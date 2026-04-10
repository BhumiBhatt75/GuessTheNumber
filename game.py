import random


# -----------------------------
# VALIDATION HELPERS
# -----------------------------

def is_valid_number(num_str):
    """
    Validates:
    - Must be 4 digits
    - No leading zero
    - No repeated digits
    - No ascending consecutive digits (e.g. 7->8 blocked, 8->7 allowed)
    """

    if len(num_str) != 4:
        return False, "Number must be exactly 4 digits"

    if num_str[0] == '0':
        return False, "Number cannot start with 0"

    if not num_str.isdigit():
        return False, "Number must contain only digits"

    digits = list(map(int, num_str))

    if len(set(digits)) != 4:
        return False, "Digits must not repeat"

    # ascending consecutive only (next - current == 1)
    for i in range(3):
        if digits[i + 1] - digits[i] == 1:
            return False, "Adjacent digits cannot ascend by 1 (e.g. 7→8)"

    return True, "Valid"


# -----------------------------
# CORE GAME LOGIC
# -----------------------------

def check_guess(number, guess):
    """
    Returns:
    [digits exist - X, correctly positioned - Y]
    """

    number = str(number)
    guess = str(guess)

    is_valid, msg = is_valid_number(guess)
    if not is_valid:
        return f"Invalid Guess ❌: {msg}"

    correct = 0
    exist = 0

    for i in range(4):
        if guess[i] == number[i]:
            correct += 1

    for digit in guess:
        if digit in number:
            exist += 1

    return f"[digits exist - {exist}, correctly positioned - {correct}]"


# -----------------------------
# NUMBER GENERATION
# -----------------------------

def generate_number():
    """
    Generates a valid number based on rules.
    """

    while True:
        digits = random.sample(range(1, 10), 4)

        valid = True
        for i in range(3):
            if digits[i + 1] - digits[i] == 1:  # ascending consecutive only
                valid = False
                break

        if valid:
            return "".join(map(str, digits))


# -----------------------------
# TEST CASES
# -----------------------------

def run_tests():
    print("\n--- HAPPY FLOW ---")
    number = "3482"
    print("Number:", number)
    print("Guess 3201 →", check_guess(number, "3201"))
    print("Guess 3482 →", check_guess(number, "3482"))
    print("Guess 4823 →", check_guess(number, "4823"))

    print("\n--- RULE: ascending consecutive blocked, descending allowed ---")
    print("Guess 1476 →", check_guess(number, "1476"))  # 7→6 descending: allowed
    print("Guess 1478 →", check_guess(number, "1478"))  # 7→8 ascending: blocked

    print("\n--- NEGATIVE FLOW (Invalid Inputs) ---")
    print("Guess 1123 →", check_guess(number, "1123"))
    print("Guess 1234 →", check_guess(number, "1234"))
    print("Guess 0123 →", check_guess(number, "0123"))
    print("Guess 12a4 →", check_guess(number, "12a4"))
    print("Guess 123  →", check_guess(number, "123"))

    print("\n--- EDGE CASES ---")
    print("Guess 9999 →", check_guess(number, "9999"))
    print("Guess 8342 →", check_guess(number, "8342"))
    print("Guess 5679 →", check_guess(number, "5679"))


if __name__ == "__main__":
    secret_number = generate_number()
    print("Generated Secret Number (for testing):", secret_number)
    run_tests()
