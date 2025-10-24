tour={
    "nomi":"London",
    "narxi":"500$",
    "uchish vaqti":"2025-10-15 10:00",
    "uchish davomiyligi":"8 soat",
    "masofa":"6000 km",
    "turi":"standart",
}

def list_all_tour():
    """ Hamma tourlarni kursatadi """
    for key,value in tour.items():
        print(f"{key}:{value}")
    return "Hamma tourlar kursatildi"

def add_tour(nomi,narxi,uchish_vaqti,uchish_davomiyligi,masofa,turi):
    
    tour["nomi"]=nomi
    tour["narxi"]=narxi
    tour["uchish vaqti"]=uchish_vaqti
    tour["uchish davomiyligi"]=uchish_davomiyligi
    tour["masofa"]=masofa
    tour["turi"]=turi
    
    return "Yangi tour qo'shildi"
    
print(list_all_tour())
print(add_tour("Parij","600$","2025-11-20 12:00","7 soat","5500 km","premium"))
print(list_all_tour())