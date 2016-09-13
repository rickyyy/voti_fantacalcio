import urllib2
import pandas as pd
import argparse

moduli_validi = ['442', '451', '433', '343', '352', '532', '541']

def download_voti(giornata):
    '''
    Questo metodo scarica da Pianetafantacalcio il file .xls contenente i voti della giornata selezionata.
    :param giornata:
    :return:
    '''
    results = 'http://www.pianetafantacalcio.it/Voti-Ufficiali-Excel.asp?giornataScelta=' + str(giornata)
    sock = urllib2.urlopen(results)
    excel = sock.read()
    sock.close()
    return excel

def estrai_coach(line):
    '''
    Estrai il nome del allenatore dal file contenente le formazioni
    :param line:
    :return:
    '''
    return line.lstrip('Coach:')

def estrai_titolari(line):
    '''
    Estrai la lista di giocatori schierati come titolari
    :param line:
    :return:
    '''
    s = line.lstrip('Titolari: ')
    s = s.split(', ', 11)
    return s

def estrai_panchina(line):
    '''
    Estrai la lista di giocatori schierati come panchinari
    :param line:
    :return:
    '''
    s = line.lstrip('Panchina: ')
    s = s.split(', ', 7)
    return s

def voti_fantacalcio(input, dataframe):
    with open(input, 'r') as infile:
        lines = infile.read().splitlines()
        for i in range (0, len(lines)):
            if "Coach" in lines[i]:
                coach = estrai_coach(lines[i])
                try:
                    titolari = estrai_titolari(lines[i+1])
                    panchina = estrai_panchina(lines[i+2])
                except IndexError:
                    titolari = None
                    panchina = None
                print "TEAM SCORE: " + str(calcola_risultato(coach, titolari, panchina, dataframe)) + '\n'


def parse_html(voti):
    '''
    Parsa il file contente i voti e ritorna un DataFrame (pandas library)
    :param voti:
    :return:
    '''
    data = pd.read_html(voti, thousands=None)
    return data[0]

def print_dict(dict):
    '''
    Metodo ausiliario per stampare un dictionary.
    :param dict:
    :return:
    '''
    s = ""
    for x in dict:
        s += x + " - "
    return s

def modificatore_difesa(difensori, portiere):
    '''
    Calcolo modificatore di difesa. Vien applicato se ci sono almeno 4 difensori con voto. Viene calcolata
    la media voto tra: portiere e 3 migliori difensori.
    Se media < 6 : 0 punti
    Se media > 6 e media < 6.5 : 1 punto
    Se media > 6.5 e media < 7 : 3 punti
    Se media > 7 : 6 punti

    In questo modificatore vengon considerati bonus e malus!

    :param difensori:
    :param portiere:
    :return:
    '''
    modif = 0.0
    if len(difensori) == 4:
        for key,value in portiere.iteritems():
            modif += value
        low = min(difensori, key=difensori.get)
        del difensori[low]
        for value in difensori.itervalues():
            modif+=value
        modif = modif/4.0
    elif len(difensori) == 5:
        for key, value in portiere.iteritems():
            modif+=value
        low = min(difensori, key=difensori.get)
        del difensori[low]
        for value in difensori.itervalues():
            modif+=value
        modif = modif/5.0
    else:
        print "Modificatore di Difesa: NO (meno di 3 difensori)"
        return 0
    if modif >= 6.0 and modif < 6.5:
        print "Modificatore di Difesa: SI (1pt - " + str(modif) + ")"
        return 1
    elif modif >= 6.5 and modif < 7.0:
        print "Modificatore di Difesa: SI (3pt - " + str(modif) + ")"
        return 3
    elif modif >= 7.0:
        print "Modificatore di Difesa: SI (6pt - " + str(modif) + ")"
        return 6
    else:
        print "Modificatore di Difesa: NO (" + str(modif) + " < 6)"
        return 0

def modificatore_centrocampo(centrocampisti):
    '''
    Calcolo modificatore di centrocampo. Solo se ci sono almeno 5 centrocampisti. Il giocatore con il voto piu basso,
    prende come voto finale la media voto degli altri 4 centrocampisti.

    In questo modificatore vengono considerati bonus e malus!

    :param centrocampisti:
    :return:
    '''
    modif = 0.0
    lowest = min(centrocampisti, key=centrocampisti.get)
    low_val = float(centrocampisti.get(lowest))
    if len(centrocampisti)== 5:
        del centrocampisti[lowest]
        for value in centrocampisti.itervalues():
            modif += value
        tot = modif/4.0
        print "Modificatore di Centrocampo: SI (+" + str(tot) + ")"
        return tot-low_val
    else:
        print "Modificatore di Centrocampo: NO"
        return 0

def calcola_voti_base(coach, portiere, difensori, centrocampisti, attaccanti):
    '''
    Somma i voti dei singoli giocatori
    :param coach:
    :param portiere:
    :param difensori:
    :param centrocampisti:
    :param attaccanti:
    :return:
    '''
    final_score = 0.0
    for value in portiere.itervalues():
        final_score += value
    for value in difensori.itervalues():
        final_score += value
    for value in centrocampisti.itervalues():
        final_score += value
    for value in attaccanti.itervalues():
        final_score += value
    print "Portiere: " + print_dict(portiere)
    print "Difesa: " + print_dict(difensori)
    print "Centrocampo: " + print_dict(centrocampisti)
    print "Attacco: " + print_dict(attaccanti)
    return final_score

def controllo_portiere(portiere, panchina):
    '''
    Controlla se almeno un portiere e` stato schierato come titolare o in panchina
    :param portiere:
    :param panchina:
    :return:
    '''
    if len(portiere) == 1:
        return portiere
    elif len(portiere) < 1:
        for (x,y,z) in panchina:
            if (y) == 'P':
                portiere[x] = z
                return portiere
    else:
        portiere['NO KEEPER'] = 0.0
        return portiere


def controllo_squadra(difensori, centrocampisti, attaccanti, panchina):
    '''
    Metodo che implementa le sostituzioni. Il metodo di sostituzioni e` "panchina libera". Ogni giocatore schierato
    titolare che non ha preso voto, viene sostituito dal primo giocatore in panchina che ha preso voto. La sostituzione
    e` independente dal ruolo, di conseguenza il modulo della squadra puo cambiare in maniera dinamica rispetto a quello
    stabilito in partenza (formazione titolare). Tuttavia, il modulo finale deve rispettare almeno uno dei moduli
    consentiti dal fantacalcio ['442', '451', '433', '343', '352', '532', '541'].
    :param difensori:
    :param centrocampisti:
    :param attaccanti:
    :param panchina:
    :return:
    '''
    modulo = "" + str(len(difensori)) + str(len(centrocampisti)) + str(len(attaccanti))
    if modulo in moduli_validi or len(panchina) == 0:
        print "Modulo Finale Utilizzato: " + modulo
        return (difensori,centrocampisti,attaccanti)
    else:
        if len(difensori) <= 2:
            for a in panchina:
                (x,y,z) = a
                if y == 'D':
                    difensori[x] = z
                    panchina.pop(panchina.index(a))
                    return controllo_squadra(difensori,centrocampisti,attaccanti,panchina)
        elif len(centrocampisti) <=2:
            for a in panchina:
                (x,y,z) = a
                if y == 'C':
                    centrocampisti[x] = z
                    panchina.pop(panchina.index(a))
                    return controllo_squadra(difensori,centrocampisti,attaccanti,panchina)
        elif len(attaccanti) == 0:
            for a in panchina:
                (x,y,z) = a
                if y == 'A':
                    attaccanti[x] = z
                    panchina.pop(panchina.index(a))
                    return controllo_squadra(difensori,centrocampisti,attaccanti,panchina)
        else:
            for a in panchina:
                (x,y,z) = a
                if y == 'D' and len(difensori) < 5:
                    difensori[x] = z
                    panchina.pop(panchina.index(a))
                    return controllo_squadra(difensori, centrocampisti, attaccanti, panchina)
                elif y == 'C' and len(centrocampisti) < 5:
                    centrocampisti[x] = z
                    panchina.pop(panchina.index(a))
                    return controllo_squadra(difensori, centrocampisti, attaccanti, panchina)
                elif y == 'A' and len(attaccanti)<3:
                    attaccanti[x] = z
                    panchina.pop(panchina.index(a))
                    return controllo_squadra(difensori, centrocampisti, attaccanti, panchina)
                else:
                    panchina.pop(panchina.index(a))
                    return controllo_squadra(difensori, centrocampisti, attaccanti, panchina)

def substitutions(portiere, difensori, centrocampisti, attaccanti, panchina):
    portiere = controllo_portiere(portiere, panchina)
    (dif, centr, att) = controllo_squadra(difensori,centrocampisti,attaccanti, panchina)
    return (portiere, dif, centr, att)

def calcola_risultato(coach, titolari, panchina, dataframe):
    '''
    Metodo che calcola il risultato finale.
    :param coach:
    :param titolari:
    :param panchina:
    :param dataframe:
    :return:
    '''
    print "FORMAZIONE: " + coach
    voti_panchina = [('Empty', 'E', '0.0')] * len(panchina)
    final_score = 0.0
    portiere = {}
    difensori = {}
    centrocampisti = {}
    attaccanti = {}
    for index, row in dataframe.iterrows():
        a = unicode(row[1]) #unicode of the football player name
        for x in titolari:
            substitute = 0
            if (x.upper() in a) and (row[6] != 's,v,' or (row[6] == 's,v,' and row[2] == 'P')):
                player_score = float(row[32].replace(',','.'))
                final_score += player_score
                if row[2] == 'P':
                    portiere[row[1]] = player_score
                elif row[2] == 'D':
                    difensori[row[1]] = player_score
                elif row[2] == 'C':
                    centrocampisti[row[1]] = player_score
                elif row[2] == 'A':
                    attaccanti[row[1]] = player_score
                else:
                    raise NotImplementedError("Not defined Role")
            else:
                substitute += 1
        for y in panchina:
            if y.upper() in a:
                voto = float(row[32].replace(',','.'))
                voti_panchina.pop(panchina.index(y))
                voti_panchina.insert(panchina.index(y),(row[1], row[2], voto))
    (portiere, difensori, centrocampisti, attaccanti) = substitutions(portiere, difensori, centrocampisti, attaccanti, voti_panchina)
    final_score = calcola_voti_base(coach, portiere, difensori, centrocampisti, attaccanti)
    final_score += modificatore_centrocampo(centrocampisti)
    final_score += modificatore_difesa(difensori, portiere)
    return final_score


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Calcolo Voti Fantacalcio")
    parser.add_argument("giornata", type=int, help="Giornata di Campionato (Serie A)")
    parser.add_argument("file", help="File con la/e formazione/i")
    args = parser.parse_args()
    giornata = args.giornata
    voti = download_voti(giornata)
    d = parse_html(voti)
    voti_fantacalcio(args.file, d)
