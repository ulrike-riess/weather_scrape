import requests, sys, argparse, csv, os.path
from bs4 import BeautifulSoup
from datetime import datetime

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

def gettitle_coclouds(row0):
    titlelist= [x.get_text() for x in row0.find_all("th")[1:]]
    titlelist[1]="Bedeckung (total)"
    titlelist[2]="Bedeckung (tief)"
    return titlelist

def parserow_coclouds(row): # Liest alle Werte aus einer Zeile aus (auch Ortszeit)
    cloudslist=[1,2,3] # Das ist die Liste der Spalten, die ich für clouds speichern möchte
    templist =  [cell.get_text() for cell in row.find_all("td")]
    finallist = [templist[0]]
    for i in cloudslist:
        finallist.append(templist[i])
        # Ich füge die neu gesammelten Daten an meine Liste an
    return finallist

def parsetable_coclouds(currenttable, coarseness):
    rowlist = currenttable.find_all("tr")
    titlelist=gettitle_coclouds(rowlist[0])
    unitlist=getunit_std(currenttable)
    mydict = {} 
    if not rowlist[1].find_all("th")[0].get_text()=="total":
        print("Warning, formatting seems to have changed in clouds")
    for row in rowlist[2:]:
    # ich werfe vom Resultat die erste und zweite Zeile weg, da diese nur die Überschriften enthält.
        rowresult = parserow_coclouds(row)
        print(rowresult)
        key = rowresult[0]
        mydict[key] = mydict.get(key, []) + rowresult[1:]
        # Ich füge die neu gesammelten Daten an mein dict an (aber die Ortszeit kommt weg. Die fügen wir unten beim ersten Mal dazu -die steht ja im key.)
        # Der erste Teil ist nur zur Sicherheit. Den könnte ich sicher auch weglassen.
    return titlelist, unitlist, mydict

def parserow_wind(row): # Liest alle Werte aus einer Zeile aus (auch Ortszeit)
    windlist=[1,3,4] # Das ist die Liste der Spalten, die ich für wind speichern möchte
    # ich werfe vom Resultat die erste Zeile weg, da diese nur die Überschriften enthält.
    templist =  [cell.get_text() for cell in row.find_all("td")]
    templist[1]+= " km/h" # TODO Natürlich will ich die später wegnehmen, wenn ich zum Säubern komme
    templist[3]+= " km/h"
    finallist = [templist[0]]
    key = templist[0] # Der erste Eintrag im Resultat soll immer die Ortszeit sein.
    for i in windlist:
        finallist.append(templist[i])  
    return finallist

def parsetable_wind(currenttable, coarseness):
    rowlist = currenttable.find_all("tr")
    titlelist=gettitle_std(rowlist[0])
    unitlist=getunit_std(currenttable)
    mydict= {}
    # Jetzt wird erstmal gecheckt, dass in der 2. Zeile (Einheiten-Zeile) das Erwartete steht.
    windfail = False
    unitrow=[cell.get_text() for cell in rowlist[1].find_all("th")]
    if not unitrow[0]=="km/h":
        print(f"Warning, formatting seems to have changed in wind.")
        windfail=True
    if not unitrow[2]=="km/h":
        print("Warning, formatting seems to have changed in wind.")
        windfail=True
    if not windfail:  # Das hier ist der erwartete Fall
        for row in rowlist[2:]:
            # ich werfe vom Resultat die erste Zeile weg, da diese nur die Überschriften enthält.
            rowresult = parserow_wind(row)
            print(rowresult)
            key = rowresult[0]
            mydict[key] = mydict.get(key, []) + rowresult[1:]
            # Ich füge die neu gesammelten Daten an mein dict an (aber die Ortszeit kommt weg. Die fügen wir unten beim ersten Mal dazu -die steht ja im key.)
            # Der erste Teil ist nur zur Sicherheit. Den könnte ich sicher auch weglassen.
    else: #Das hier passiert nur, wenn die Tabelle von Seiten von Wetter online geändert wurde.
            #Als Schadensbegrenzung sorge ich einfach dafür, dass hier so viele leere Felder stehen, wie ich Überschriften gesammelt habe
        print("Something went wrong in WIND")
        for x in titlelist:
            for row in rowlist[2:]:
                # ich werfe vom Resultat die erste Zeile weg, da diese nur die Überschriften enthält.
                rowresult = parserow_wind(row)
                print(rowresult)
                key = rowresult[0]
                mydict[key].append("")
    return titlelist, unitlist, mydict
    

def gettitle_std(row0):
    titlelist = [x.get_text() for x in row0.find_all("th")[1:]] # Da die Überschriften in th-Zellen sind, müssen sie separat rausgeholt werden 
            # Außerdem will ich Ortszeit nicht vielfach reinschreiben
    return titlelist

def getunit_std(currenttable):
    return []

def parserow_std(row): # Liest alle Werte aus einer Zeile aus (auch Ortszeit)
    templist =  [cell.get_text() for cell in row.find_all("td")]
    return templist

def parsetable_std(currenttable, coarseness):
    rowlist = currenttable.find_all("tr")
    titlelist=gettitle_std(rowlist[0])
    unitlist=getunit_std(currenttable)
    mydict= {}
    for row in rowlist[1:]:
        # ich werfe vom Resultat die erste Zeile weg, da diese nur die Überschriften enthält.
        rowresult = parserow_std(row)
        print(rowresult)
        key = rowresult[0]
        mydict[key] = mydict.get(key, []) + rowresult[1:]
        # Ich füge die neu gesammelten Daten an mein dict an (aber die Ortszeit kommt weg. Die fügen wir unten beim ersten Mal dazu -die steht ja im key.)
        # Der erste Teil ist nur zur Sicherheit. Den könnte ich sicher auch weglassen.
    return titlelist, unitlist, mydict

def make_dict(datapart, coarseness):  #erstellt das dict, das die Daten aus den verschiedenen Tabellen zusammensammelt
    titlelist = ['Ortszeit']
    mydict ={}  # Diese Dict soll alle Daten sammeln:
        # Als keys verwende ich die Zeit
        # Zu jeder Zeit sammle ich hierin alle Daten.
    for currenttable in datapart.find_all(class_=coarseness):
        #print(currenttable.parent.get('id'))
        if currenttable.parent.get('id')=="wind": # leider sind wind und clouds verschachtelte Tabellen. Da muss ich separat ran
            print(currenttable.parent.get('id'))
            addedtitles, addedunits, addeddict = parsetable_wind(currenttable, coarseness)
            titlelist += addedtitles
            for key in addeddict:
                mydict[key] = mydict.get(key, [key]) + addeddict[key]   
            #print(mydict)
        elif currenttable.parent.get('id')=="clouds" and coarseness == 'sixhourly': # leider sind wind und clouds verschachtelte Tabellen. Da muss ich separat ran
                            #Clouds ist aber nur i 6-stündlichen verschachtelt und im Feinen nicht.
            print(currenttable.parent.get('id'))
            addedtitles, addedunits, addeddict = parsetable_coclouds(currenttable, coarseness)
            titlelist += addedtitles
            for key in addeddict:
                mydict[key] = mydict.get(key, [key]) + addeddict[key]   
            #print(mydict)
        else:
            print(currenttable.parent.get('id'))
            addedtitles, addedunits, addeddict = parsetable_std(currenttable, coarseness)
            titlelist += addedtitles
            for key in addeddict:
                mydict[key] = mydict.get(key, [key]) + addeddict[key]     
            #print(mydict) 
    return mydict, titlelist

def cleandict(datadict):
    # TODO: Hier will ich: Eine Spalte für den Abruf-Zeitpunkt einfügen
    # und alle Einheiten aussortieren. Wobei ich diesen Säuberungsschritt am besten schon vorher mache, bevor ich das Dict überhaupt erstelle.
    unitlist=[]
    print ("no cleaning done so far")
    return datadict, unitlist


def writecsv(titlelist, datadict, coarseness):
    #TODO: Überlegen welches Zeitintervall für die Benennung der CSVs gewählt werden soll? Tage?
    if (coarseness=="hourly"):
        coarseind=""
    elif (coarseness=="sixhourly"):
        coarseind="_6h"

    timestamp=datetime.now().strftime("%Y-%m-%d") #strftime("%Y-%m-%dT%Hh%M")
    csvname=f"./data/weather_data{coarseind}_{timestamp}.csv"
    addtitle= not os.path.isfile(csvname)
    with open(csvname, 'a', newline='') as outcsv:  # Schreib-Modus hier ist 'w' (write), wähle 'a' (append), wenn du an vorhandene CSV nur etwas dranhängen willst
        weatherwriter=csv.writer(outcsv, delimiter=';', quotechar="|")
        if(addtitle):
            weatherwriter.writerow(titlelist)
        for key in datadict:
            weatherwriter.writerow(datadict[key])
    print(f"got to print {coarseness}")

def runscrape(dummymode=False):
    if not dummymode:
        response = online_request()
    else:
        if os.path.exists('scrape_result.html'):
            with open('scrape_result.html', 'r') as outputfile:
                response = outputfile.read()
        else:
            response = online_request()
            with open('scrape_result.html', 'w') as outputfile:
                outputfile.write(response)
    datapart = extract_data_part(response)

    for coarseness in ["sixhourly", "hourly"]:    # gibt an ob die grobe oder feine Zeiteinteilung untersucht wird.
    # Hier sollte ich eine Unterscheidung für beide Varianten machen
        (datadict,titlelist)=make_dict(datapart, coarseness)
        (datadict, unitlist) = cleandict(datadict)
        print(titlelist)
        print(datadict)
        writecsv(titlelist, datadict, coarseness)



def main(dummymode=False):
    #Hier hätte ich die Möglichkeit, das Ganze zB für mehrere Orte durchzuführen
    runscrape(dummymode=dummymode)


if __name__=="__main__":
    names = parser.parse_args(sys.argv[1:])
    main(dummymode=names.dummy)


    # TODO

    # Bedeckung und Wolkenuntergrenze trennen in Clouds hourly
    #Ich will noch Daten säubern (Einheiten rausziehen etc)
    #Ich will ein vernünftiges Log schreiben
    #Daten stattdessen direkt in einen Dataframe einlesen
    #Dataframe in CSV übertragen
    #Verschiedene CSVs des gleichen Tags zusammenfügen/direkt das alte ergänzen

### Im Moment gibt es einen Fehler, da die Funktion parsetable_std auch für die Titel-Erstellung verwendet wird. Das gibt bei "Wind" natürlich ein Problem
#Als nächsten Schritt muss ich also die Titel-Berechnung in den jeweiligen Fall einfügen und so den Doppel-Aufruf vermeiden.