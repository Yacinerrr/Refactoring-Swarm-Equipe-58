def count_down(n):
    """
    Compte à rebours à partir d'un nombre entier positif donné 'n' jusqu'à 1.

    Affiche chaque nombre sur une nouvelle ligne.
    Si 'n' est zéro ou négatif, la fonction n'affiche rien.

    Args:
        n (int): Le nombre entier positif à partir duquel commencer le compte à rebours.
    """
    while n > 0:
        print(n)
        n -= 1