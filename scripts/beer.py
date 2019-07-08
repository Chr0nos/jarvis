import math


def marmite(hauteur, diametre=None, circonference=None):
    """Calcule le littrage d'une cuve selon ses dimentions
    il fout fournir soit diametre soit circonference
    """
    if not diametre and not circonference:
        raise ValueError((diametre, circonference))
    if diametre and circonference:
        raise ValueError('please choose between diametre and circonference')
    if not diametre:
        diametre = circonference / math.pi
    surface = math.pi * pow(diametre, 2) / 4
    return round(hauteur * surface / 1000, 1)


def densite(mesure, temperature):
    """Corrige une mesure de densite prise a une temperature supperieure a 20C
    """
    dens = (0.1963596 * temperature) + \
            (0.002661056 * pow(temperature, 2)) - 5.431719
    return round(mesure + dens, 1)


def toPlato(mesure):
    p = mesure / 1000;
    return round(258.6 * (p - 1) / ((0.88 * p) + 0.12), 1)


def fromPlato(plato):
    d = 1 + (plato / (258.6 - (0.88 * plato)))
    return round(d * 1000, 1)


def fromBrix(brix):
    """Convertis des brix en densitee
    """
    return round((brix / (258.6 - ((brix / 258.2) * 227.1)) + 1) * 1000, 1)



def color(volume_brassin, *args):
    """Chaque argument doit etre un tuple avec (masse_kg, coleur_ebc)
    renvoi la couleur finale de la biere
    le volume_brassin est en littres
    """
    def get_relative_color():
        beer_color = 0;
        for (mass, color) in args:
            beer_color += color * mass
        return 4.23 * beer_color / volume_brassin

    return round(2.9396 * pow(get_relative_color(), 0.6859), 1)

