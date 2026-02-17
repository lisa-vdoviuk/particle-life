import random

class InteractionMatrix:
    """Manages the 2D matrix of interaction forces between particle types."""
    def __init__(self, num_types):
        """Initializes a matrix of a given size, filled with zeros."""
        self.num_types = num_types
        self.matrix = []
        for i in range(num_types):
            row = []
            for j in range(num_types):
                row.append(0.0)
            self.matrix.append(row)

    def set_interaction(self, type1, type2, value):
        """Sets the interaction force from type1 to type2."""
        if 0 <= type1 < self.num_types and 0 <= type2 < self.num_types:
            self.matrix[type1][type2] = value

    def get_interaction(self, type1, type2):
        """Gets the interaction force from type1 to type2, returning 0.0 if out of bounds."""
        if 0 <= type1 < self.num_types and 0 <= type2 < self.num_types:
            return self.matrix[type1][type2]
        return 0.0

    def randomize(self):
        """Fills the entire matrix with random values between -1.0 and 1.0."""
        for i in range(self.num_types):
            for j in range(self.num_types):
                self.matrix[i][j] = random.uniform(-1.0, 1.0)


# Console Editor
def console_editor(): # pragma: no cover
    """
    Runs a small text-based tool to edit the matrix.
    Separated from the class so it doesn't run during the actual simulation.
    """
    print("--- Interaction Matrix Editor ---")
    matrix = InteractionMatrix(4)
    matrix.randomize() 

    while True:
        print("\nCurrent Matrix:")
        for row in matrix.matrix:
            print([f"{val:.2f}" for val in row])
        
        print("\nOptions: [s]et value, [r]andomize, [q]uit")
        choice = input("Choice: ").strip().lower()

        if choice == 'q':
            break
        elif choice == 'r':
            matrix.randomize()
            print("Matrix randomized.")
        elif choice == 's':
            try:
                t1 = int(input("Type 1 ID (0-3): "))
                t2 = int(input("Type 2 ID (0-3): "))
                val = float(input("Value (-1.0 to 1.0): "))
                matrix.set_interaction(t1, t2, val)
                print(f"Set relation {t1}->{t2} to {val}")
            except ValueError:
                print("Invalid input! Use numbers.")


if __name__ == "__main__":
    console_editor()