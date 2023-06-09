#importy z flask, pymongo, i bson (aby nadawać unikalne id produktom w bazie.)
from flask import Flask, render_template, request, redirect, flash
from pymongo import MongoClient
from bson.objectid import ObjectId
import random
import csv


#Zainicjowanie flask
app = Flask(__name__)




#Połączenie się z bazą danych MongoDB
client = MongoClient("mongodb+srv://mateuszbalaban:x6i9WlHiOU4V2NKg@mateusz.tiexjh3.mongodb.net/")
#mongodb+srv://mateuszbalaban:<password>@mateusz.tiexjh3.mongodb.net/db = client['magazyn']
db = client['magazyn']
collection = db['produkty']

class Produkt:
    def __init__(self, nazwa, cena, ilosc):
        self.nazwa = nazwa
        self.cena = cena
        self.ilosc = ilosc
        #wygenerowanie kodu produktu za pomoca random
        self.kod_produktu = self.generate_product_code()

    def generate_product_code(self):
        return str(random.randint(100000, 999999))

#strona główna z szablonu index.html, z listą produktów i dodawaniem/usuwaniem
@app.route('/')
def index():
    products = list(collection.find())
    return render_template('index.html', products=products)


#strona dodawania nowego produktu do bazy
@app.route('/dodaj', methods=['GET', 'POST'])
def dodaj_produkt():
    if request.method == 'POST':
        nazwa = request.form['nazwa']
        cena = float(request.form['cena'])
        ilosc = int(request.form['ilosc'])

        #logika inkrementowania ilości produktu kiedy juz istnieje w bazie produkt o tej samej nazwie i cenie
        existing_product = collection.find_one({'nazwa': nazwa, 'cena': cena})
        if existing_product:
            collection.update_one({'_id': existing_product['_id']}, {'$inc': {'ilosc': ilosc}})
        else:
            produkt = Produkt(nazwa, cena, ilosc)
            collection.insert_one(produkt.__dict__)
        return redirect('/')

    return render_template('dodaj.html')


#usuwanie produktu 
@app.route('/usun', methods=['POST'])
def usun_produkt():
    kod_produktu = request.form['kod_produktu']
    ilosc_do_usuniecia = int(request.form['ilosc_do_usuniecia'])

    product = collection.find_one({'kod_produktu': kod_produktu})
    if product:
        ilosc = product['ilosc']
        #jezeli ilosc do usuniecia jest taka sama jak ilosc produktu w bazie, to usuwa produkt z bazy
        if ilosc_do_usuniecia == ilosc:
            collection.delete_one({'kod_produktu': kod_produktu})
        else:
            ilosc_po_usunieciu = ilosc - ilosc_do_usuniecia
            if ilosc_po_usunieciu > 0:
                collection.update_one({'kod_produktu': kod_produktu}, {'$set': {'ilosc': ilosc_po_usunieciu}})
            else:
                collection.delete_one({'kod_produktu': kod_produktu})

    #przekierowanie do url z potwierdzeniem usunięcia produktu
    return redirect('/usun_potwierdzenie')


@app.route('/usun_potwierdzenie')
def usun_potwierdzenie():
    return render_template('usun_potwierdzenie.html')

#Eksportowanie do pliku csv
@app.route('/export/csv')
def export_csv():
    products = list(collection.find())
    if len(products) > 0:
        keys = products[0].keys()
        with open('produkty.csv','w',newline='') as file:
            writer = csv.DictWriter(file,fieldnames = keys)
            writer.writeheader()
            writer.writerows(products)
        flash("Dane zostały wyeksportowane do pliku csv")
    else:
        flash("Nie udało się wyeksportować danych do pliku csv")
    return redirect('/')


@app.route('/wyszukiwarka', methods=['GET', 'POST'])
def wyszukaj_produkt():
    if request.method == 'POST':
        product_list = []
        nazwa_produktu = request.form['nazwa']
        products = list(collection.find())
        for product in products:
            if nazwa_produktu in product['nazwa'] or nazwa_produktu.upper() in product['nazwa']:
                product_list.append(product)
        
        return render_template('index.html', products=product_list)
    
    return redirect('/')
    
if __name__ == '__main__':
    app.secret_key = 'supersecretkey'
    app.run(debug=True, port=8080)