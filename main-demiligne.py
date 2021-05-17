#!/usr/bin/env python
# -*- coding: utf-8 -*

# Fichier: Main (+ les fonctions...)
# Version: 0.9

# == IMPORTS ==

import imageio
import subprocess as sp
import numpy as np
from timecode import Timecode

import TimecodeP as tc

import ServeurDate as date

import ChoixFichier as cf  # Programme qui choisi le fichier a analyser.
# import ChoixRatioListe as cr
# import ChoixFramerateListe as cfr
# import ChoixResolutionListe as cre
import ChoixTC as ctc  # Programme qui choisi l'interval a analyser
import Rapport as r
import sys
from PIL import Image

# == VALEURS ==

# Si on peut utiliser le programme
licence = None

# Se connecte pour voir si on depasse la limite d'utilisation du programme:
if int(date.Aujourdhui()) <= 20211225:
    print("Licence OK")
    licence = True
else:
    print("Licence depassee/!\\")
    licence = False

# == Declaration variables: ==
ratio = None

starttc = None
starttc_frame = 0
endtc_frame = None

# Définit à quelle ligne commence l'image utile (en fonction de son ratio).
y_debut_haut = None  # 1ère ligne utile vers le haut.
y_debut_bas = None  # 1ère ligne utile vers le bas.

# Définit à quelle colonne commence l'image utile (en fonction de son ratio).
x_debut_gauche = None
x_debut_droite = None

framerate = None

option_afficher = ""  # Valeur du ratio.

# Liste des erreurs: tc in | tc out | erreur | option
list_tc_in = np.array([])
list_tc_out = np.array([])
liste_option = np.array([])
list_erreur = np.array([])

# Coefficient appliqué à certains chiffre. Les calcules sont basé sur de la HD, donc souvent, x2 pour de l'UHD (calcule en ligne et non intégralité image).
coefficient_resolution = 1

# Fichier pour rapport:
file = None

# Numéro d'erreur
num_erreur = 0


# == FONCTIONS ==


# Donne le TC actuel à l'aide d'un nombre d'image et sur base d'un tc de depard:
def TcActuel(numImage, framerate=24):
    tc1 = Timecode(framerate, starttc)
    if numImage > 0:
        # Comme le résultat est toujours une image en trop, j'enleve ce qu'il faut: :)
        tc2 = Timecode(framerate, tc.frames_to_timecode((numImage - 1), framerate))
        tc3 = tc1 + tc2
        return tc3
    else:
        return tc1


# Met a jour la liste des erreurs pour ecrire dans le rapport:
def UpdateListeProbleme(numImage):
    global list_tc_in, list_tc_out, list_erreur, liste_option, num_erreur

    # Parcoure la liste des problemes, si tc out discontinu, alors on ecrit dans le rapport.
    for i in range(0, np.size(list_tc_in)):
        if i < np.size(list_tc_in) and list_tc_out[i] != (numImage - 1):
            num_erreur = num_erreur + 1
            print(str(num_erreur) + " / " + str(list_tc_in[i]) + " : update liste, on ajoute une erreur!")
            # On ecrit dans le rapport l'erreur:

            # La notion de temps en timecode
            # r.setRapport(str(TcActuel(list_tc_in[i], framerate)) + " a " + str(TcActuel(list_tc_out[i], framerate)) + ": " + str(list_erreur[i]) + "\n")
            # La notion de temps en image
            # r.setRapport(str(int(list_tc_in[i])) + " a " + str(int(list_tc_out[i])) + ": " + str(list_erreur[i]) + "\n")
            r.addProbleme(str(int(list_tc_in[i])), str(int(list_tc_out[i])), str(list_erreur[i]), str(liste_option[i]))

            # On supprime de la liste l'erreur:
            list_tc_in = np.delete(list_tc_in, i)
            list_tc_out = np.delete(list_tc_out, i)
            list_erreur = np.delete(list_erreur, i)
            liste_option = np.delete(liste_option, i)
            # On doit stagner dans les listes si on supprime un element.
            i -= 1


# Quand on doit reporter un probleme dans le rapport:
def Probleme(message, option, numImage):
    global list_tc_in, list_tc_out, list_erreur, liste_option

    # Si c'est une nouvelle erreur:
    new = True

    # Si l'erreur est dans la liste:
    for i in range(0, np.size(list_tc_in, 0)):
        if list_erreur[i] == message:
            list_tc_out[i] = numImage  # Met a jour le tc out
            new = False

    # Sinon, on ajoute le probleme a la liste:
    if new:
        # Dans append, on spécifie le tableau à qui on ajoute une valeur.
        list_tc_in = np.append(list_tc_in, numImage)
        list_tc_out = np.append(list_tc_out, numImage)
        liste_option = np.append(liste_option, option)
        list_erreur = np.append(list_erreur, message)


# Timecode du fichier analyse:
def StartTimeCodeFile(fichier):
    global starttc
    command = ["ffmpeg.exe", '-i', fichier, '-']
    pipe = sp.Popen(command, stdout=sp.PIPE, stderr=sp.PIPE)
    pipe.stdout.readline()
    pipe.terminate()
    infos = pipe.stderr.read()
    tc = ""
    for i in range(18, 29):
        tc += infos[(infos.find("timecode") + i)]
    starttc = tc
    return tc


# On definit le ratio et on prepare les matrices d'analyse de l'image:
def setRatio(ratio_tmp, resolution_tmp):
    global ratio, coefficient_resolution

    global y_debut_haut, y_debut_bas, x_debut_gauche, x_debut_droite

    ratio = ratio_tmp

    # Ligne utile en 2.00 1920x1080
    if ratio == "2.40":
        y_debut_haut = 140
        y_debut_bas = 939

        x_debut_gauche = 0
        x_debut_droite = 1919

    # Ligne utile en 2.39 1920x1080
    elif ratio == "2.39":
        if resolution_tmp == "1920x1080":
            y_debut_haut = 138
            y_debut_bas = 941

            x_debut_gauche = 0
            x_debut_droite = 1919
        # Pour l'instant, car UHD:
        else:
            y_debut_haut = 277
            y_debut_bas = 1883

            x_debut_gauche = 0
            x_debut_droite = 3839

            # l'UHD a un coefficien x2:
            coefficient_resolution = 2

    # Ligne utile en 2.00 1920x1080
    elif ratio == "2.35":
        y_debut_haut = 131
        y_debut_bas = 948

        x_debut_gauche = 0
        x_debut_droite = 1919

    # Ligne utile en 2.00 1920x1080
    elif ratio == "2.00":
        y_debut_haut = 60
        y_debut_bas = 1019

        x_debut_gauche = 0
        x_debut_droite = 1919

    # Ligne utile en 1.85 1920x1080
    elif ratio == "1.85":
        y_debut_haut = 21
        y_debut_bas = 1058

        x_debut_gauche = 0
        x_debut_droite = 1919

    # Ligne utile en 1.77 1920x1080
    elif ratio == "1.77":
        y_debut_haut = 0
        y_debut_bas = 1079

        x_debut_gauche = 0
        x_debut_droite = 1919

    # Ligne utile en 1.77 1920x1080
    elif ratio == "1.33":
        y_debut_haut = 0
        y_debut_bas = 1079

        x_debut_gauche = 240
        x_debut_droite = 1679

    else:
        print("Erreur: Ratio inconnu!!!")


delta_high = 255.0 * 0.05  # Le delta maximum qu'il peut y avoir entre les plus hautes valeurs (en 8bit).
delta = 0.21  # Delta qu'on tolère pour la moyenne.
delta_min = 1 - delta  # Delta min
delta_max = 1 + delta  # Delta max


# Affichage automatisé:
def setOption(ligne_utile_sum, ligne_avant_sum, ligne_utile_min, ligne_avant_min, ligne_utile_mean, ligne_avant_mean,
              ligne_utile_max, ligne_avant_max):
    global option_afficher

    if ligne_utile_sum != 0:
        calcule = (100.0 / ligne_avant_sum) * ligne_utile_sum
    else:
        calcule = 0

    option_afficher = "(ratio: " + str(ligne_utile_sum) + " [~" + str(ligne_utile_mean) + ", -" + str(
        ligne_utile_min) + ", +" + str(ligne_utile_max) + "] / " + str(ligne_avant_sum) + " [~" + str(
        ligne_avant_mean) + ", -" + str(ligne_avant_min) + ", +" + str(ligne_avant_max) + "]): " + str(calcule) + "%"


# Commun entre les différents défauts:
def DemiLigne(ligne_utile, ligne_avant):
    global delta_high, delta_min, delta_max, coefficient_resolution
    # Les sommes:
    ligne_utile_sum = ligne_utile.sum()
    ligne_avant_sum = ligne_avant.sum()

    # Les max:
    ligne_utile_max = ligne_utile.max()
    ligne_avant_max = ligne_avant.max()

    # La ligne limite (des blankinkgs) ne doit pas avoir un delta plus grande que 19% pour la moyenne.
    # La ligne limite avec les blankings ne doit pas avoir un delta plus grand que 18% pour les valeurs maximale.
    if (ligne_avant_max * delta_max > ligne_utile_max > ligne_avant_max * delta_min) or (
            ligne_avant_sum * delta_max > ligne_utile_sum > ligne_avant_sum * delta_min):
        return True

    # Le "else" permet de faire les préparations pour les autres calcules:
    else:
        # Les moyennes:
        ligne_utile_mean = ligne_utile.mean()
        ligne_avant_mean = ligne_avant.mean()

        # Si les deux vallent zéro, on ne compte pas d'erreur (cela serait possiblement un défaut de blanking mais pas de demi-ligne).
        # Si les valeurs (2 lignes) sont vraiment faible (100 = FHD, dû à la compression), on ne compte pas comme un défaut. C'est noir...
        # Si les deux lignes ont pour valeur maximal 1 (= image noire avec défaut de compression), alors c'est bon, il n'y a pas de souci.
        # Si inférieur à 100 et que la moyenne est égale à moins d'un 1% près (0,95%), alors c'est bon!
        if (ligne_utile_sum < 100 * coefficient_resolution and ligne_avant_sum < 100 * coefficient_resolution) and (
                (ligne_utile_max <= 1 and ligne_avant_max <= 1) or (
                ligne_avant_mean - 0.0095 <= ligne_utile_mean <= ligne_avant_mean + 0.0095)):
            return True

        # Le "else" permet de faire les préparations pour les autres calcules:
        else:
            # Les min:
            ligne_utile_min = ligne_utile.min()
            ligne_avant_min = ligne_avant.min()

            # Cas où les lignes sont dans le noir et la compression est mal faite (cas: Le Milieu De L'Horizon):
            if (ligne_utile_sum < ligne_utile.size and ligne_avant_sum < ligne_utile.size) and (
                    ligne_utile_min == 0 and ligne_avant_min == 0) and (
                    ligne_utile_mean < 0.35 and ligne_avant_mean < 0.35) and (
                    ligne_utile_max < 20 and ligne_avant_max < 20) and (ligne_avant_max / ligne_utile_max < 1.5):
                return True

            # Si après toute ces vérifs ce n'est toujours pas bon, alors la ligne est considéré avec le défaut.
            else:
                # On désactie l'affichage des options:
                # setOption(ligne_utile_sum, ligne_avant_sum, ligne_utile_min, ligne_avant_min, ligne_utile_mean, ligne_avant_mean, ligne_utile_max, ligne_avant_max)
                return False


# Verifie que la ligne de l'image utile du haut est bien codée (cas 2.39):
def DemiLigneHaut(image):
    global delta_high
    ligne_utile = image[y_debut_haut:(y_debut_haut + 1):1, y_debut_haut:y_debut_bas:1]  # Ligne limite
    ligne_avant = image[(y_debut_haut + 1):(y_debut_haut + 2):1, y_debut_haut:y_debut_bas:1]

    return DemiLigne(ligne_utile, ligne_avant)


# Verifie que la ligne de l'image utile du bas est bien codée (cas 2.39):
def DemiLigneBas(image):
    global delta_high
    ligne_utile = image[y_debut_bas:(y_debut_bas + 1):1, y_debut_haut:y_debut_bas:1]  # Ligne limite
    ligne_avant = image[(y_debut_bas - 1):y_debut_bas:1, y_debut_haut:y_debut_bas:1]

    return DemiLigne(ligne_utile, ligne_avant)


# Verifie que la colonne de gauche de l'image utile est bien codée (cas 2.39):
def DemiLigneGauche(image):
    global ligne_utile
    ligne_utile = image[y_debut_haut:y_debut_bas:1, x_debut_gauche:(x_debut_gauche + 1):1]  # Ligne limite
    ligne_avant = image[y_debut_haut:y_debut_bas:1, (x_debut_gauche + 1):(x_debut_gauche + 2):1]

    return DemiLigne(ligne_utile, ligne_avant)


# Verifie que la colonne de droite de l'image utile est bien codée (cas 2.39):
def DemiLigneDroite(image):
    global delta_high
    ligne_utile = image[y_debut_haut:y_debut_bas:1, x_debut_droite:(x_debut_droite + 1):1]  # Ligne limite
    ligne_avant = image[y_debut_haut:y_debut_bas:1, (x_debut_droite - 1):x_debut_droite:1]

    return DemiLigne(ligne_utile, ligne_avant)


# Cloturer l'analyse d'une video (en cloturant son flux ainsi que celui du rapport):
def close():
    global i_global, reader, r
    # On récupère les dernières valeurs de la liste.
    UpdateListeProbleme(i_global)  # De prime à bord, il ne faut pas incrémenter la valeur, elle l'est déjà.

    # On cloture tous les flux:
    reader.close()
    r.close()


i_global = 0

# == MAIN ==
# On ne lance le programme que si la licence est OK.
if licence:
    fichier = cf.filename.get()
    print("fichier: " + str(fichier))
    # print("Start tc: " + str(StartTimeCodeFile(fichier)))
    print("Start tc: 01:00:00:00")

    # Image quoi? RGB/NB??? En fait, cette information est importante...
    reader = imageio.get_reader(fichier, ffmpeg_params=["-an"])

    # framerate = int(cfr.getFramerate())
    framerate = int(25)

    print("Framerate: " + str(framerate))

    # Note: [-1] = dernier element de la liste.
    r.Rapport(fichier.split('/')[-1], "html")

    r.setRapport("== Debut du rapport ==\n")

    # ratio= cr.getRatio()
    ratio = '2.39'

    # Choix du ratio:
    # setRatio(ratio, cre.getResolution())
    setRatio(ratio, '1920x1080')
    # duree = reader.get_length()
    duree = 82500
    endtc_frame = duree - 1
    print("Ratio: " + str(ratio))

    # ctc.setTimecodeIn(starttc_frame)
    # ctc.setTimecodeOut(endtc_frame)

    # Choix du timecode (debut et fin) a verifier:
    # ctc.Fenetre()

    # starttc_frame= ctc.getTimecodeIn()
    # endtc_frame= ctc.getTimecodeOut()

    # On vérifie l'intégralité du fichier:
    starttc_frame = starttc_frame
    endtc_frame = endtc_frame

    # r.Start(fichier, str(duree), str(StartTimeCodeFile(fichier)), framerate, str(ratio))
    r.Start(fichier, str(duree), '01:00:00:00', framerate, str(ratio))

    # Chaque iteration équivaut à une image:
    for i, image in enumerate(reader):

        i_global = i

        # Met a jout la liste des erreurs (pour avoir un groupe de tc pour une erreur):
        UpdateListeProbleme(i)

        # Affiche l'avancement tous les 10 secondes:
        if (i % (framerate * 30)) == 0:
            print(str(i) + " / " + str(duree))

        if not DemiLigneHaut(image):
            Probleme("Demi ligne <strong>haut</strong>.", str(option_afficher), i)

        if not DemiLigneBas(image):
            Probleme("Demi ligne <strong>bas</strong>.", str(option_afficher), i)

        if not DemiLigneGauche(image):
            Probleme("Demi ligne <strong>gauche</strong>.", str(option_afficher), i)

        if not DemiLigneDroite(image):
            Probleme("Demi ligne <strong>droite</strong>.", str(option_afficher), i)

    # On récupère les dernières valeurs de la liste.
    UpdateListeProbleme(i_global)  # De prime à bord, il ne faut pas incrémenter la valeur, elle l'est déjà.

    # On cloture tous les flux:
    reader.close()
    r.close()

# close()

# == END ==
