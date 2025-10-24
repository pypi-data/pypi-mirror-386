import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from tour_agent.dastur_kodlari.latofat.admin import admin_menu

from tour_agent.dastur_kodlari.alibek.foydalanuvchi import foydalanuvchi_menu
KOK="\033[34m"
QIZIL="\033[31m"
YASHIL="\033[32m"
RANG="\033[0m" 


def tour_main():
    while True:
        print(f"""
    {QIZIL}Shaxslar:{RANG}
            {KOK}1-foydalanuvchi
            2-admin{RANG}
            """)
        
        a=input(f"{YASHIL}Tanlang:{RANG}")

        if a=="1":
            foydalanuvchi_menu()
        elif a=="2":
            admin_menu()
        else:
            print(f"{QIZIL}Notogri buyruq kiritdingiz!!!{RANG}")
            print(f"{QIZIL}Boshidan tanlang:{RANG}")

# if '__main__'==__name__:
#     tour_main()