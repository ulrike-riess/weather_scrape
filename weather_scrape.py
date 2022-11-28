import requests, sys, argparse
from os.path import exists
from bs4 import BeautifulSoup

parser = argparse.ArgumentParser(
    prog = 'weather_scrape',
    description = 'Scrapes wetteronline',
    epilog = 'Text at the bottom of help')

parser.add_argument('-d', '--dummy', action='store_true', help='Activate to avoid unnecessary calls to the site.')

def online_request():
    response = requests.get('https://www.wetteronline.de/aktuelles-wetter?gid=10422&lat=51.429&locationname=M%C3%BClheim&lon=6.878')
    return response.text

# Diese Funktion nimmt den ganz normalen Quellcode von WetterOnline, 
# verwandelt es in ein soup-Objekt und sucht die relevante div aus
def extract_data_part(response):
    soup = BeautifulSoup(response, 'html.parser')
    datapart= soup.find(id="showcase") #datapart of the soup
    return datapart

def make_dict(datapart, coarseness):  #erstellt das dict, das die Daten aus den verschiedenen Tabellen zusammensammelt
    titlelist = ['Ortszeit']
    mydict ={}  # Diese Dict soll alle Daten sammeln:
        # Als keys verwende ich die Zeit
        # Zu jeder Zeit sammle ich hierin alle Daten.
    for currenttable in datapart.find_all(class_=coarseness):
        rowlist = currenttable.find_all("tr")
        if  not currenttable.parent.get('id')=="clouds" or coarseness=='hourly':  # Bei Clouds ist die Tabelle verschachtelt, da muss ich die Titel ändern
            titlelist += [x.get_text() for x in rowlist[0].find_all("th")[1:]] # Da die Überschriften in th-Zellen sind, müssen sie separat rausgeholt werden 
            # Außerdem will ich Ortszeit nicht vielfach reinschreiben
        else: 
            addedtitles= [x.get_text() for x in rowlist[0].find_all("th")[1:]]
            addedtitles[1]="Bedeckung (total)"
            addedtitles[2]="Bedeckung (tief)"
            titlelist += addedtitles
        

        #print(currenttable.parent.get('id'))
        if currenttable.parent.get('id')=="wind": # leider sind wind und clouds verschachtelte Tabellen. Da muss ich separat ran
            windlist=[1,3,4] # Das ist die Liste der Spalten, die ich für wind speichern möchte
            windfail = False
            unitrow=[cell.get_text() for cell in rowlist[1].find_all("th")]
            if not unitrow[0]=="km/h":
                print(f"Warning, formatting seems to have changed in wind.")
                windfail=True
            if not unitrow[2]=="km/h":
                print("Warning, formatting seems to have changed in wind.")
                windfail=True
            for row in rowlist[2:]:
                # ich werfe vom Resultat die erste Zeile weg, da diese nur die Überschriften enthält.
                templist =  [cell.get_text() for cell in row.find_all("td")]
                templist[1]+= " km/h"
                templist[3]+= " km/h"
                key = templist[0]
                if not windfail:
                    for i in windlist:
                        mydict[key].append(templist[i])
                    # Ich füge die neu gesammelten Daten an mein dict an (aber die Ortszeit nur beim ersten Mal)
                else: #Das hier passiert nur, wenn die Tabelle von Seiten von Wetter online geändert wurde.
                        #Als Schadensbegrenzung sorge ich einfach dafür, dass hier so viele leere Felder stehen, wie ich Überschriften gesammelt habe
                    for x in rowlist[0].find_all("th")[1:]:
                        mydict[key].append("")        
            #print(mydict)
        elif currenttable.parent.get('id')=="clouds" and coarseness == 'sixhourly': # leider sind wind und clouds verschachtelte Tabellen. Da muss ich separat ran
                            #Clouds ist aber nur i 6-stündlichen verschachtelt und im Feinen nicht.
            cloudslist=[1,2,3] # Das ist die Liste der Spalten, die ich für clouds speichern möchte
            if not rowlist[1].find_all("th")[0].get_text()=="total":
                print("Warning, formatting seems to have changed in clouds")
            for row in rowlist[2:]:
                # ich werfe vom Resultat die erste Zeile weg, da diese nur die Überschriften enthält.
                templist =  [cell.get_text() for cell in row.find_all("td")]
                key = templist[0]
                for i in cloudslist:
                    mydict[key].append(templist[i])
                # Ich füge die neu gesammelten Daten an mein dict an (aber die Ortszeit nur beim ersten Mal)
            #print(mydict)
        else:
            for row in rowlist[1:]:
                # ich werfe vom Resultat die erste Zeile weg, da diese nur die Überschriften enthält.
                templist =  [cell.get_text() for cell in row.find_all("td")]
                key = templist[0]
                mydict[key] = mydict.get(key, [key]) + templist[1:]
                # Ich füge die neu gesammelten Daten an mein dict an (aber die Ortszeit nur beim ersten Mal)
            #print(mydict) 
    return mydict, titlelist


def runscrape(dummymode=False):
    if not dummymode:
        response = online_request()
    else:
        if exists('scrape_result.html'):
            with open('scrape_result.html', 'r') as outputfile:
                response = outputfile.read()
        else:
            response = online_request()
            with open('scrape_result.html', 'w') as outputfile:
                outputfile.write(response)
    datapart = extract_data_part(response)
    coarseness = "sixhourly" # gibt an ob die grobe oder feine Zeiteinteilung untersucht wird.
# Hier sollte ich eine Unterscheidung für beide Varianten machen
    (coarsedict,titlelist)=make_dict(datapart, coarseness)
    print(titlelist)
    print(coarsedict)

    coarseness = "hourly"

    (finedict,titlelist)= make_dict(datapart, coarseness)
    print(titlelist)
    print(finedict)
 

def main(dummymode=False):
    #Hier hätte ich die Möglichkeit, das Ganze zB für mehrere Orte durchzuführen
    runscrape(dummymode=dummymode)


if __name__=="__main__":
    names = parser.parse_args(sys.argv[1:])
    main(dummymode=names.dummy)


    # TODO

    #Ich will noch Daten säubern (Einheiten rausziehen etc)
    #Ich will ein vernünftiges Log schreiben
    #Daten stattdessen direkt in einen Dataframe einlesen
    #Dataframe in CSV übertragen
    #Verschiedene CSVs des gleichen Tags zusammenfügen/direkt das alte ergänzen
